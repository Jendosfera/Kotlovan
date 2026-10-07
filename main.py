import os
import json
import shutil
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Scale, Translate
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import (ObjectProperty, StringProperty, NumericProperty,
                             BooleanProperty, ListProperty, DictProperty)

# ---------------------------------------------------------------------------
#  Константы и утилиты
# ---------------------------------------------------------------------------
SAVE_DIR = os.path.join(os.path.expanduser("~"), "KotlovanArrays")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
#  Виджет мерцающего кружка
# ---------------------------------------------------------------------------
class BlinkCircle(FloatLayout):
    """Маленький кружок, меняющий прозрачность (для режимов установки точки / комментария)."""
    alpha = NumericProperty(0.5)

    def __init__(self, radius=20, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (radius * 2, radius * 2)
        self.radius = radius
        self._dir = 1
        self._ev = Clock.schedule_interval(self._tick, 0.03)

    def _tick(self, dt):
        self.alpha += self._dir * 0.04
        if self.alpha >= 1:
            self.alpha = 1
            self._dir = -1
        elif self.alpha <= 0.15:
            self.alpha = 0.15
            self._dir = 1
        return True

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None


# ---------------------------------------------------------------------------
#  Виджет комментария-кружка (в режиме просмотра)
# ---------------------------------------------------------------------------
class CommentCircle(FloatLayout):
    """Неподвижный кружок комментария с подписью."""
    def __init__(self, cx, cy, radius, title="", text="", comment_id=None, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (radius * 2, radius * 2)
        self.pos = (cx - radius, cy - radius)
        self.radius = radius
        self.title = title
        self.text = text
        self.comment_id = comment_id

    def set_visual(self, alpha=0.0, blink=False, fixed_radius=None):
        """Переключение режима отображения (глаз)."""
        if fixed_radius:
            self.radius = fixed_radius
            self.size = (fixed_radius * 2, fixed_radius * 2)
        # alpha задаётся через canvas — обновление происходит во ViewerScreen


# ---------------------------------------------------------------------------
#  Экран: Главное меню
# ---------------------------------------------------------------------------
class MainMenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        title = Label(text="Котлован", font_size=42, size_hint_y=0.3)
        layout.add_widget(title)

        btn_load = Button(text="Загрузить массив", font_size=24)
        btn_load.bind(on_release=self.do_load)
        layout.add_widget(btn_load)

        btn_create = Button(text="Создать массив", font_size=24)
        btn_create.bind(on_release=self.do_create)
        layout.add_widget(btn_create)

        self.add_widget(layout)

    def do_load(self, *_):
        sm = self.manager
        if sm:
            sm.current = "file_picker"
            sm.get_screen("file_picker").set_mode("load")

    def do_create(self, *_):
        sm = self.manager
        if sm:
            sm.current = "create_array"


# ---------------------------------------------------------------------------
#  Экран: Создание массива (выбор строк / столбцов)
# ---------------------------------------------------------------------------
class CreateArrayScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()

        box = BoxLayout(orientation="vertical", padding=40, spacing=20,
                        size_hint=(0.8, 0.7), pos_hint={"center_x": 0.5, "center_y": 0.5})

        self.spinner_rows = Spinner(
            text="3", values=[str(i) for i in range(1, 21)], font_size=24)
        self.spinner_cols = Spinner(
            text="3", values=[str(i) for i in range(1, 21)], font_size=24)

        box.add_widget(Label(text="Количество строк:", font_size=20))
        box.add_widget(self.spinner_rows)
        box.add_widget(Label(text="Количество столбцов:", font_size=20))
        box.add_widget(self.spinner_cols)

        btn_confirm = Button(text="Подтвердить", font_size=24)
        btn_confirm.bind(on_release=self.on_confirm)
        box.add_widget(btn_confirm)

        self.layout.add_widget(box)
        self.add_widget(self.layout)

    def on_pre_enter(self, *_):
        self.clear_back()
        self.add_back()

    def add_back(self):
        self.back_btn = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                               pos_hint={"x": 0.02, "top": 0.98})
        self.back_btn.bind(on_release=lambda *_: self.go_back())
        self.layout.add_widget(self.back_btn)

    def clear_back(self):
        if hasattr(self, "back_btn") and self.back_btn:
            self.layout.remove_widget(self.back_btn)
            self.back_btn = None

    def go_back(self):
        self.manager.current = "main"

    def on_confirm(self, *_):
        rows = int(self.spinner_rows.text)
        cols = int(self.spinner_cols.text)
        sm = self.manager
        sm.get_screen("array_view").init_array(rows, cols)
        sm.current = "array_view"


# ---------------------------------------------------------------------------
#  Экран: Отображение массива (сетка с + кнопками)
# ---------------------------------------------------------------------------
class ArrayViewScreen(Screen):
    current_array = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        self.rows = 0
        self.cols = 0
        self.cells = {}  # (r,c) -> {"name":..., "image":..., "common_point":None,
                          #            "own_position":False, "comments":[]}
        self._grid = None

    def init_array(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.cells = {}
        for r in range(rows):
            for c in range(cols):
                self.cells[(r, c)] = {
                    "name": "",
                    "image": "",
                    "common_point": None,
                    "own_position": False,
                    "comments": [],
                }
        self.rebuild_grid()

    def on_pre_enter(self, *_):
        self._rebuild()

    def _rebuild(self):
        self.layout.clear_widgets()
        self.add_back()

        if not self.cells:
            self.layout.add_widget(Label(text="Массив не создан", font_size=24,
                                         pos_hint={"center_x": 0.5, "center_y": 0.5}))
            return

        # Кнопка сохранения внизу
        btn_save = Button(text="Сохранить массив", font_size=20,
                          size_hint=(0.4, 0.08),
                          pos_hint={"center_x": 0.5, "y": 0.02})
        btn_save.bind(on_release=self.do_save)
        self.layout.add_widget(btn_save)

        # Сетка
        scroll = GridLayout(cols=self.cols, rows=self.rows,
                            size_hint=(0.9, 0.8),
                            pos_hint={"center_x": 0.5, "center_y": 0.5},
                            spacing=6)
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells.get((r, c))
                if cell and cell["name"]:
                    btn = Button(text=cell["name"][:12], font_size=12,
                                 on_release=lambda *_args, rr=r, cc=c: self.edit_cell(rr, cc))
                    scroll.add_widget(btn)
                else:
                    btn = Button(text="+", font_size=24,
                                 on_release=lambda *_args, rr=r, cc=c: self.edit_cell(rr, cc))
                    scroll.add_widget(btn)
        self.layout.add_widget(scroll)

<<<<<<< HEAD
    def add_back(self):
        self.back_btn = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                               pos_hint={"x": 0.02, "top": 0.98})
        self.back_btn.bind(on_release=lambda *_: self.go_back())
        self.layout.add_widget(self.back_btn)

    def go_back(self):
        self.manager.current = "main"

    def edit_cell(self, r, c):
        sm = self.manager
        scr = sm.get_screen("card_edit")
        scr.set_cell(self, r, c, self.cells[(r, c)])
        sm.current = "card_edit"

    def do_save(self, *_):
        sm = self.manager
        picker = sm.get_screen("file_picker")
        picker.set_mode("save", data=self.get_save_data())
        sm.current = "file_picker"

    def get_save_data(self):
        arr = {"rows": self.rows, "cols": self.cols, "cells": {}}
        for (r, c), cell in self.cells.items():
            arr["cells"][f"{r},{c}"] = {
                "row": r, "col": c,
                "name": cell["name"],
                "image": cell["image"],
                "common_point": cell["common_point"],
                "own_position": cell["own_position"],
                "comments": cell["comments"],
            }
        return arr

    def load_from_data(self, data):
        self.rows = data.get("rows", 1)
        self.cols = data.get("cols", 1)
        self.cells = {}
        for key, cdata in data.get("cells", {}).items():
            r, c = cdata["row"], cdata["col"]
            self.cells[(r, c)] = {
                "name": cdata.get("name", ""),
                "image": cdata.get("image", ""),
                "common_point": cdata.get("common_point"),
                "own_position": cdata.get("own_position", False),
                "comments": cdata.get("comments", []),
            }
        self.rebuild_grid()

    def rebuild_grid(self):
        self._rebuild()
=======
# ========== Экран выбора размера массива ==========
class ArraySizeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'array_size'
        self.build_ui()
    
    def build_ui(self):
        layout = FloatLayout()
        
        with layout.canvas.before:
            Color(*COLOR_BG)
            Rectangle(pos=self.pos, size=self.size)
        
        # Кнопка возврата
        self.back_btn = BackButton(callback=self.go_back)
        layout.add_widget(self.back_btn)
        
        # Заголовок
        title = Label(
            text='Размер массива',
            font_size=28,
            color=COLOR_TEXT,
            size_hint=(1, None),
            height=40,
            pos_hint={'center_x': 0.5, 'top': 0.9}
        )
        layout.add_widget(title)
        
        # Поля ввода
        input_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, None),
            height=200,
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            spacing=20
        )
        
        # Строки
        rows_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60, spacing=10)
        rows_box.add_widget(Label(text='Строки:', font_size=20, color=COLOR_TEXT, size_hint=(0.4, 1)))
        self.rows_input = TextInput(text='3', font_size=24, input_filter='int', multiline=False,
                                     size_hint=(0.6, 1), background_color=COLOR_BTN)
        rows_box.add_widget(self.rows_input)
        input_layout.add_widget(rows_box)
        
        # Столбцы
        cols_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60, spacing=10)
        cols_box.add_widget(Label(text='Столбцы:', font_size=20, color=COLOR_TEXT, size_hint=(0.4, 1)))
        self.cols_input = TextInput(text='3', font_size=24, input_filter='int', multiline=False,
                                     size_hint=(0.6, 1), background_color=COLOR_BTN)
        cols_box.add_widget(self.cols_input)
        input_layout.add_widget(cols_box)
        
        layout.add_widget(input_layout)
        
        # Кнопка подтверждения
        btn_confirm = Button(
            text='Подтвердить',
            font_size=20,
            size_hint=(0.5, None),
            height=50,
            pos_hint={'center_x': 0.5, 'top': 0.3},
            background_color=COLOR_ACCENT,
            color=COLOR_TEXT
        )
        btn_confirm.bind(on_press=self.confirm)
        layout.add_widget(btn_confirm)
        
        self.add_widget(layout)
    
    def go_back(self):
        app = App.get_running_app()
        app.sm.current = 'main_menu'
    
    def confirm(self, *args):
        try:
            rows = int(self.rows_input.text) if self.rows_input.text else 1
            cols = int(self.cols_input.text) if self.cols_input.text else 1
            rows = max(1, min(rows, 20))
            cols = max(1, min(cols, 20))
        except:
            rows, cols = 3, 3
        
        app = App.get_running_app()
        app.array_data = ArrayData(rows, cols)
        # Переключаем на экран сетки
        app.sm.get_screen('grid_view').init_grid()
        app.sm.current = 'grid_view'


# ========== Экран сетки массива ==========
class GridCellWidget(Widget):
    """Виджет одной ячейки сетки"""
    def __init__(self, row, col, grid_screen, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.grid_screen = grid_screen
        self.is_plus = True
        self.has_image = False
    
    def update_canvas(self):
        self.canvas.clear()
        app = App.get_running_app()
        arr = app.array_data
        cell = arr.get_cell(self.row, self.col) if arr else None
        has_img = cell and cell.image_path
        
        a = get_icon_alpha()
        
        if has_img:
            # Показываем миниатюру
            self.is_plus = False
            self.has_image = True
            with self.canvas:
                Color(0.15, 0.15, 0.3, a)
                Rectangle(pos=self.pos, size=self.size)
                # Рамка карточки
                Color(0.3, 0.3, 0.6, a)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=1)
                
                # Заголовок
                if cell.title:
                    Color(*COLOR_TEXT, a)
                    # Текст названия - упрощённо рисуем рамку для названия
                    Color(0.2, 0.2, 0.4, a)
                    Rectangle(pos=(self.x, self.top - 20), size=(self.width, 20))
                    Color(1, 1, 1, a)
                    # Line под названием
                
                # Миниатюра изображения
                if cell.image_path and os.path.exists(cell.image_path):
                    try:
                        from kivy.core.image import Image as CoreImage
                        img = CoreImage(cell.image_path).texture
                        if img:
                            Color(1, 1, 1, a)
                            Rectangle(texture=img, pos=(self.x+4, self.y+4), 
                                      size=(self.width-8, self.height-28))
                    except:
                        pass
        else:
            # Кнопка "+"
            self.is_plus = True
            self.has_image = False
            with self.canvas:
                Color(0.1, 0.1, 0.2, a * 0.3)
                Rectangle(pos=self.pos, size=self.size)
                # Объёмная кнопка +
                cx, cy = self.center
                s = min(self.width, self.height) * 0.3
                Color(0.33, 0.84, 0.41, a)
                # Фон кнопки
                Color(0.33, 0.84, 0.41, a * 0.2)
                RoundedRectangle = None
                # Круглый фон
                Color(0.2, 0.5, 0.3, a * 0.3)
                Ellipse(pos=(cx-s, cy-s), size=(s*2, s*2))
                # Плюс
                Color(0.33, 0.84, 0.41, a)
                Line(points=[cx, cy-s*0.5, cx, cy+s*0.5], width=3)
                Line(points=[cx-s*0.5, cy, cx+s*0.5, cy], width=3)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.grid_screen.open_card_editor(self.row, self.col)
            return True
        return False


class PlusButtonWidget(Button):
    """Кнопка + для добавления соседней ячейки"""
    def __init__(self, row, col, direction, grid_screen, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.direction = direction  # 'right' or 'down'
        self.grid_screen = grid_screen
        self.background_color = (0, 0, 0, 0)
        self.size_hint = (None, None)
        self.bind(pos=self.draw, size=self.draw)
    
    def draw(self, *args):
        self.canvas.clear()
        a = get_icon_alpha()
        s = get_small_icon_size()
        with self.canvas:
            Color(0.33, 0.84, 0.41, a)
            cx, cy = self.center
            sz = min(self.width, self.height) * 0.4
            # Круглый фон
            Color(0.2, 0.5, 0.3, a * 0.3)
            Ellipse(pos=(cx-sz, cy-sz), size=(sz*2, sz*2))
            # Плюс
            Color(0.33, 0.84, 0.41, a)
            if self.direction == 'right':
                Line(points=[cx, cy-sz*0.4, cx, cy+sz*0.4], width=2.5)
                Line(points=[cx-sz*0.4, cy, cx+sz*0.4, cy], width=2.5)
            else:
                Line(points=[cx, cy-sz*0.4, cx, cy+sz*0.4], width=2.5)
                Line(points=[cx-sz*0.4, cy, cx+sz*0.4, cy], width=2.5)
    
    def on_press(self):
        if self.direction == 'right':
            self.grid_screen.open_card_editor(self.row, self.col + 1)
        else:
            self.grid_screen.open_card_editor(self.row + 1, self.col)


class GridViewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'grid_view'
        self.cell_widgets = {}
        self.plus_widgets = []
        self.layout = None
        self.build_ui()
        #исправление on_size привязывает к изменению размера экрана
        self.bind(size=self.on_size)
        self.build_ui()
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Верхняя панель: назад + название + сохранить
        top_bar = BoxLayout(size_hint_y=None, height=60, spacing=10)

        self.back_btn = IconButton(icon_type='back', size_hint=(None, None), size=(50, 50))
        self.back_btn.bind(on_press=lambda *a: setattr(self.manager, 'current', 'main_menu'))
        top_bar.add_widget(self.back_btn)

        title = Label(text='Сетка массива', font_size=20, size_hint_x=1)
        top_bar.add_widget(title)

        # Кнопка сохранения (дискета)
        self.save_btn = IconButton(icon_type='save', size_hint=(None, None), size=(50, 50))
        self.save_btn.bind(on_press=self.on_save_array)
        top_bar.add_widget(self.save_btn)

        layout.add_widget(top_bar)

        self.clear_widgets()
        self.layout = FloatLayout()
        
        with self.layout.canvas.before:
            Color(*COLOR_BG)
            Rectangle(pos=self.pos, size=self.size)
        
        # Кнопка возврата
        self.back_btn = BackButton(callback=self.go_back)
        self.layout.add_widget(self.back_btn)
        
        # Кнопка сохранения
        self.save_btn = IconButton(icon_type='save')
        self.save_btn.size_hint = (None, None)
        self.save_btn.bind(on_press=self.save_array)
        self.layout.add_widget(self.save_btn)
        
        # ScrollView для сетки
        self.scroll = ScrollView(size_hint=(1, 0.8), pos_hint={'x': 0, 'top': 0.85})
        self.grid_container = FloatLayout(size_hint=(None, None))
        self.scroll.add_widget(self.grid_container)
        self.layout.add_widget(self.scroll)
        
        self.add_widget(self.layout)
        return layout
    
    

    def on_save_array(self, *args):
        app = App.get_running_app()
        # Запрашиваем у приложения выбор папки/файла через системный диалог
        app.show_file_chooser('save_array')

    
    def on_size(self, *args):
        if self.layout:
            self.save_btn.pos = (self.width - get_back_btn_size() - 10, self.height - get_back_btn_size() - 10)
    
    def init_grid(self):
        """Инициализация сетки при создании нового массива"""
        self.refresh_grid()
    
    def refresh_grid(self):
        """Перерисовка сетки"""
        self.grid_container.clear_widgets()
        self.cell_widgets = {}
        self.plus_widgets = []
        
        app = App.get_running_app()
        arr = app.array_data
        if not arr:
            return
        
        cell_size = min(120, max(60, Window.width / (arr.cols + 1)))
        spacing = 20
        
        total_width = arr.cols * (cell_size + spacing) + spacing
        total_height = arr.rows * (cell_size + spacing) + spacing
        
        self.grid_container.size = (max(total_width, Window.width), max(total_height, Window.height))
        
        # Проверяем, есть ли хотя бы одна заполненная ячейка
        any_filled = False
        for r in range(arr.rows):
            for c in range(arr.cols):
                cell = arr.get_cell(r, c)
                if cell.image_path:
                    any_filled = True
                    break
            if any_filled:
                break
        
        if not any_filled:
            # Только первая ячейка с +
            cell = GridCellWidget(0, 0, self)
            cell.size = (cell_size, cell_size)
            cell.pos = (spacing, self.grid_container.height - cell_size - spacing)
            cell.update_canvas()
            self.grid_container.add_widget(cell)
            self.cell_widgets[(0, 0)] = cell
        else:
            # Рисуем все существующие ячейки и их плюсы
            for r in range(arr.rows):
                for c in range(arr.cols):
                    cell = arr.get_cell(r, c)
                    if cell.image_path:
                        cw = GridCellWidget(r, c, self)
                        x = spacing + c * (cell_size + spacing)
                        y = self.grid_container.height - (r + 1) * cell_size - (r + 1) * spacing
                        cw.size = (cell_size, cell_size)
                        cw.pos = (x, y)
                        cw.update_canvas()
                        self.grid_container.add_widget(cw)
                        self.cell_widgets[(r, c)] = cw
                        
                        # Плюс справа, если нет соседней ячейки
                        if c + 1 < arr.cols:
                            right_cell = arr.get_cell(r, c + 1)
                            if not right_cell.image_path:
                                pbtn = PlusButtonWidget(r, c, 'right', self)
                                pbtn.size = (spacing + 20, cell_size)
                                pbtn.pos = (x + cell_size - 10, y)
                                self.grid_container.add_widget(pbtn)
                                self.plus_widgets.append(pbtn)
                        
                        # Плюс снизу, если нет соседней ячейки
                        if r + 1 < arr.rows:
                            down_cell = arr.get_cell(r + 1, c)
                            if not down_cell.image_path:
                                pbtn = PlusButtonWidget(r, c, 'down', self)
                                pbtn.size = (cell_size, spacing + 20)
                                pbtn.pos = (x, y - spacing + 10)
                                self.grid_container.add_widget(pbtn)
                                self.plus_widgets.append(pbtn)
    
    def open_card_editor(self, row, col):
        app = App.get_running_app()
        # Проверяем, что координаты в пределах массива
        arr = app.array_data
        if not arr or row < 0 or row >= arr.rows or col < 0 or col >= arr.cols:
            return
        
        editor = app.sm.get_screen('card_edit')
        editor.set_cell(row, col)
        app.sm.current = 'card_edit'
    
    def go_back(self):
        app = App.get_running_app()
        app.sm.current = 'main_menu'
    
    def save_array(self, *args):
        app = App.get_running_app()
        app.show_file_chooser('save_array')
>>>>>>> 32dfbfd (new old progect)


# ---------------------------------------------------------------------------
#  Экран: Создание / редактирование карточки
# ---------------------------------------------------------------------------
class CardEditScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        self.array_screen = None
        self.row = 0
        self.col = 0
        self.cell = None
        self.tmp_image = ""
        self._img_widget = None

        box = BoxLayout(orientation="vertical", padding=40, spacing=15,
                        size_hint=(0.85, 0.8),
                        pos_hint={"center_x": 0.5, "center_y": 0.5})

        self.name_input = TextInput(hint_text="Название карточки",
                                   font_size=20, size_hint_y=0.15,
                                   multiline=False)
        box.add_widget(self.name_input)

        self.img_area = FloatLayout(size_hint_y=0.55)
        self.img_placeholder = Label(text="(изображение не загружено)", font_size=18)
        self.img_area.add_widget(self.img_placeholder)
        box.add_widget(self.img_area)

        row_btns = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=0.15)
        btn_load = Button(text="Загрузить", font_size=22)
        btn_load.bind(on_release=self.do_load_image)
        row_btns.add_widget(btn_load)

        btn_save = Button(text="Подтвердить", font_size=22)
        btn_save.bind(on_release=self.do_confirm)
        row_btns.add_widget(btn_save)
        box.add_widget(row_btns)

        self.layout.add_widget(box)
        self.back_btn = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                               pos_hint={"x": 0.02, "top": 0.98})
        self.back_btn.bind(on_release=lambda *_: self.go_back())
        self.layout.add_widget(self.back_btn)

        self.add_widget(self.layout)

    def set_cell(self, array_screen, r, c, cell):
        self.array_screen = array_screen
        self.row = r
        self.col = c
        self.cell = cell
        self.tmp_image = cell.get("image", "")
        self.name_input.text = cell.get("name", "")
        self._refresh_image()

    def _refresh_image(self):
        self.img_area.clear_widgets()
        if self.tmp_image and os.path.exists(self.tmp_image):
            self._img_widget = Image(source=self.tmp_image,
                                     size_hint=(1, 1), pos_hint={"center_x": 0.5, "center_y": 0.5})
            self.img_area.add_widget(self._img_widget)
        else:
            self.img_area.add_widget(Label(text="(изображение не загружено)", font_size=18))

    def do_load_image(self, *_):
        sm = self.manager
        picker = sm.get_screen("file_picker")
        picker.set_mode("pick_image", callback=self._on_image_picked)
        sm.current = "file_picker"

    def _on_image_picked(self, path):
        self.tmp_image = path
        self._refresh_image()

    def do_confirm(self, *_):
        if self.cell:
            self.cell["name"] = self.name_input.text
            self.cell["image"] = self.tmp_image
        self.array_screen.rebuild_grid()
        self.manager.current = "array_view"

    def go_back(self):
        self.manager.current = "array_view"


# ---------------------------------------------------------------------------
#  Экран: Простой файловый пикер (две кнопки + popup)
# ---------------------------------------------------------------------------
class FilePickerScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.mode = ""
        self.callback = None
        self.save_data = None
        self.layout = FloatLayout()
        self.add_widget(self.layout)

    def set_mode(self, mode, data=None, callback=None):
        self.mode = mode
        self.save_data = data
        self.callback = callback
        self._rebuild()

    def _rebuild(self):
        self.layout.clear_widgets()

        back = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                      pos_hint={"x": 0.02, "top": 0.98})
        back.bind(on_release=lambda *_: self.go_home())
        self.layout.add_widget(back)

        if self.mode in ("load", "pick_image", "save"):
            box = BoxLayout(orientation="vertical", padding=40, spacing=20,
                            size_hint=(0.85, 0.6),
                            pos_hint={"center_x": 0.5, "center_y": 0.5})

            if self.mode == "load":
                box.add_widget(Label(text="Введите путь к файлу конфигурации массива (.json)",
                                     font_size=18, size_hint_y=0.2))
                self.path_input = TextInput(hint_text="/путь/к/файлу.json",
                                           font_size=16, multiline=False,
                                           size_hint_y=0.2)
                box.add_widget(self.path_input)
                btn = Button(text="Загрузить", font_size=22)
                btn.bind(on_release=self._do_load)
                box.add_widget(btn)

            elif self.mode == "pick_image":
                box.add_widget(Label(text="Введите путь к изображению",
                                     font_size=18, size_hint_y=0.2))
                self.path_input = TextInput(hint_text="/путь/к/файлу.png",
                                           font_size=16, multiline=False,
                                           size_hint_y=0.2)
                box.add_widget(self.path_input)
                btn = Button(text="Выбрать", font_size=22)
                btn.bind(on_release=self._do_pick)
                box.add_widget(btn)

            elif self.mode == "save":
                box.add_widget(Label(text="Введите имя папки для сохранения",
                                     font_size=18, size_hint_y=0.2))
                self.path_input = TextInput(hint_text="my_array", font_size=16,
                                           multiline=False, size_hint_y=0.2)
                box.add_widget(self.path_input)
                btn = Button(text="Сохранить", font_size=22)
                btn.bind(on_release=self._do_save)
                box.add_widget(btn)

            self.layout.add_widget(box)

    def _do_load(self, *_):
        path = self.path_input.text.strip()
        if path and os.path.exists(path):
            data = load_json(path)
            if data:
                sm = self.manager
                av = sm.get_screen("array_view")
                av.load_from_data(data)
                sm.current = "array_view"
                return
        self._show_error("Файл не найден или повреждён")

    def _do_pick(self, *_):
        path = self.path_input.text.strip()
        if path and os.path.exists(path):
            if self.callback:
                self.callback(path)
            self.manager.current = "card_edit"
            return
        self._show_error("Файл не найден")

    def _do_save(self, *_):
        name = self.path_input.text.strip()
        if not name:
            self._show_error("Введите имя")
            return
        ensure_dir(SAVE_DIR)
        folder = os.path.join(SAVE_DIR, name)
        ensure_dir(folder)
        data = self.save_data
        if not data:
            return
<<<<<<< HEAD
=======
        
        self.image_view.load_image(cell.image_path)
        
        # Установка viewport
        if cell.own_position:
            # Используем собственные координаты
            if cell.common_point:
                cx, cy = cell.common_point
                self.image_view.set_viewport(cx + cell.own_offset_x, cy + cell.own_offset_y, cell.own_zoom)
            else:
                self.image_view.fit_viewport()
        else:
            # Используем общие координаты
            if cell.common_point:
                cx, cy = cell.common_point
                self.image_view.set_viewport(cx + arr.shared_offset_x, cy + arr.shared_offset_y, arr.shared_zoom)
            else:
                # Общая точка ещё не установлена — центр изображения
                iw, ih = self.image_view.img_width, self.image_view.img_height
                cell.common_point = [iw / 2, ih / 2]
                cx, cy = cell.common_point
                self.image_view.set_viewport(cx + arr.shared_offset_x, cy + arr.shared_offset_y, arr.shared_zoom)
                if not arr.shared_zoom or arr.shared_zoom == 1.0:
                    self.image_view.fit_viewport()
                    arr.shared_zoom = self.image_view.zoom
        
        arr.current_row = self.current_row
        arr.current_col = self.current_col
        self.draw_overlays()
    
    def save_viewport_state(self):
        """Сохранение состояния viewport"""
        app = App.get_running_app()
        arr = app.array_data
        cell = arr.get_cell(self.current_row, self.current_col)
        
        if cell.own_position:
            if cell.common_point:
                cell.own_offset_x = self.image_view.view_x - cell.common_point[0]
                cell.own_offset_y = self.image_view.view_y - cell.common_point[1]
            cell.own_zoom = self.image_view.zoom
        else:
            if cell.common_point:
                arr.shared_offset_x = self.image_view.view_x - cell.common_point[0]
                arr.shared_offset_y = self.image_view.view_y - cell.common_point[1]
            arr.shared_zoom = self.image_view.zoom
    
    def next_col(self):
        app = App.get_running_app()
        arr = app.array_data
        if self.current_col + 1 < arr.cols:
            self.save_viewport_state()
            self.current_col += 1
            self.load_current_cell()
    
    def prev_col(self):
        app = App.get_running_app()
        arr = app.array_data
        if self.current_col > 0:
            self.save_viewport_state()
            self.current_col -= 1
            self.load_current_cell()
    
    def next_row(self):
        app = App.get_running_app()
        arr = app.array_data
        if self.current_row + 1 < arr.rows:
            self.save_viewport_state()
            self.current_row += 1
            self.load_current_cell()
    
    def prev_row(self):
        app = App.get_running_app()
        arr = app.array_data
        if self.current_row > 0:
            self.save_viewport_state()
            self.current_row -= 1
            self.load_current_cell()
    
    def go_back(self):
        self.save_viewport_state()
        app = App.get_running_app()
        app.sm.get_screen('grid_view').refresh_grid()
        app.sm.current = 'grid_view'
    
    def on_flashlight_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            # Двойное касание
            now = Clock.get_time()
            if not hasattr(self, '_last_flash_touch'):
                self._last_flash_touch = 0
            if now - self._last_flash_touch < 0.5:
                self.toggle_flashlight()
            self._last_flash_touch = now
    
    def toggle_flashlight(self):
        if HAS_FLASHLIGHT:
            try:
                if self.flashlight_on:
                    flashlight.off()
                    self.flashlight_on = False
                else:
                    flashlight.on()
                    self.flashlight_on = True
            except:
                pass
        self.flashlight_btn.update_canvas()
    
    def on_eye_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            now = Clock.get_time()
            if not hasattr(self, '_last_eye_touch'):
                self._last_eye_touch = 0
            if now - self._last_eye_touch < 0.5:
                self.eye_mode = (self.eye_mode + 1) % 3
                self.update_eye_icon()
                self.draw_overlays()
            self._last_eye_touch = now
    
    def update_eye_icon(self):
        if self.eye_mode == 0:
            self.eye_btn.icon_type = 'eye_closed'
        elif self.eye_mode == 1:
            self.eye_btn.icon_type = 'eye_open_narrow'
        else:
            self.eye_btn.icon_type = 'eye_open_wide'
        self.eye_btn.update_canvas()
    
    def show_context_menu(self, *args):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
        btn_cp = Button(text='Общая точка', font_size=16, size_hint_y=None, height=45,
                        background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_cp.bind(on_press=lambda x: self.set_mode_common_point())
        content.add_widget(btn_cp)
        
        own_text = 'Свое положение: ' + ('true' if cell.own_position else 'false')
        btn_op = Button(text=own_text, font_size=16, size_hint_y=None, height=45,
                        background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_op.bind(on_press=lambda x: self.toggle_own_position())
        content.add_widget(btn_op)
        
        btn_comment = Button(text='Установить комментарий', font_size=16, size_hint_y=None, height=45,
                             background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_comment.bind(on_press=lambda x: self.set_mode_comment_place())
        content.add_widget(btn_comment)
        
        btn_settings = Button(text='Настройки', font_size=16, size_hint_y=None, height=45,
                              background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_settings.bind(on_press=lambda x: self.show_settings())
        content.add_widget(btn_settings)
        
        popup = Popup(
            title='Меню',
            content=content,
            size_hint=(0.8, 0.4),
            background_color=COLOR_BG,
            title_color=COLOR_TEXT
        )
        
        for btn in [btn_cp, btn_op, btn_comment, btn_settings]:
            btn.bind(on_press=lambda x: popup.dismiss())
        
        popup.open()
    
    def set_mode_common_point(self):
        self.mode = 'common_point'
        # Скрываем иконки
        self.menu_btn.opacity = 0
        self.eye_btn.opacity = 0
        self.flashlight_btn.opacity = 0
        self.confirm_btn.opacity = 1
        self.draw_overlays()
    
    def set_mode_comment_place(self):
        self.mode = 'comment_place'
        self.menu_btn.opacity = 0
        self.eye_btn.opacity = 0
        self.flashlight_btn.opacity = 0
        self.confirm_btn.opacity = 1
        self.comment_circle = None
        self.draw_overlays()
    
    def toggle_own_position(self):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        cell.own_position = not cell.own_position
        if cell.own_position:
            cell.own_zoom = self.image_view.zoom
            if cell.common_point:
                cell.own_offset_x = self.image_view.view_x - cell.common_point[0]
                cell.own_offset_y = self.image_view.view_y - cell.common_point[1]
        self.show_context_menu()
    
    def show_settings(self):
        global ICON_SCALE, ICON_ALPHA
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # Размер иконок
        lbl_size = Label(text=f'Размер иконок: x{ICON_SCALE:.1f}', font_size=16, color=COLOR_TEXT, size_hint_y=None, height=30)
        content.add_widget(lbl_size)
        
        slider_size = Slider(min=0.1, max=3.0, value=ICON_SCALE, step=0.1, size_hint_y=None, height=40)
        
        def update_size_label(val):
            lbl_size.text = f'Размер иконок: x{val:.1f}'
        
        slider_size.bind(value=update_size_label)
        content.add_widget(slider_size)
        
        # Прозрачность
        lbl_alpha = Label(text=f'Прозрачность: {int(ICON_ALPHA*100)}%', font_size=16, color=COLOR_TEXT, size_hint_y=None, height=30)
        content.add_widget(lbl_alpha)
        
        slider_alpha = Slider(min=0.1, max=1.0, value=ICON_ALPHA, step=0.05, size_hint_y=None, height=40)
        
        def update_alpha_label(val):
            lbl_alpha.text = f'Прозрачность: {int(val*100)}%'
        
        slider_alpha.bind(value=update_alpha_label)
        content.add_widget(slider_alpha)
        
        btn_close = Button(text='Закрыть', font_size=16, size_hint_y=None, height=45,
                           background_color=COLOR_ACCENT, color=COLOR_TEXT)
        content.add_widget(btn_close)
        
        popup = Popup(
            title='Настройки',
            content=content,
            size_hint=(0.85, 0.5),
            background_color=COLOR_BG,
            title_color=COLOR_TEXT
        )
        
        def apply_and_close(*args):
            global ICON_SCALE, ICON_ALPHA
            ICON_SCALE = slider_size.value
            ICON_ALPHA = slider_alpha.value
            self.refresh_icons()
            popup.dismiss()
        
        btn_close.bind(on_press=apply_and_close)
        popup.open()
    
    def refresh_icons(self):
        self.back_btn.refresh()
        self.menu_btn.refresh()
        self.eye_btn.refresh()
        self.flashlight_btn.refresh()
        self.confirm_btn.refresh()
        self.delete_btn.refresh()
        self.update_icon_positions()
    
    def on_confirm_mode(self, *args):
        if self.mode == 'common_point':
            self.confirm_common_point()
        elif self.mode == 'comment_place':
            self.confirm_comment_place()
        elif self.mode == 'comment_edit':
            self.save_comment()
    
    def confirm_common_point(self):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        # Общая точка = центр viewport
        cell.common_point = [self.image_view.view_x, self.image_view.view_y]
        # Сбрасываем offset
        if cell.own_position:
            cell.own_offset_x = 0
            cell.own_offset_y = 0
        else:
            app.array_data.shared_offset_x = 0
            app.array_data.shared_offset_y = 0
        self.mode = 'view'
        self.menu_btn.opacity = 1
        self.eye_btn.opacity = 1
        self.flashlight_btn.opacity = 1
        self.confirm_btn.opacity = 0
        self.draw_overlays()
    
    def confirm_comment_place(self):
        # Центр viewport = позиция кружка
        ix = self.image_view.view_x
        iy = self.image_view.view_y
        # Размер кружка = фиксированный (не зависит от масштаба)
        circle_size = 20  # пиксели на экране
        self.comment_circle = {'x': ix, 'y': iy, 'size': circle_size}
        self.mode = 'comment_edit'
        self.confirm_btn.opacity = 1  # кнопка подтверждения
        self.delete_btn.opacity = 1
        # Показываем поля ввода
        self.comment_input_layout.opacity = 1
        self.comment_title_input.text = ''
        self.comment_text_input.text = ''
        self.draw_overlays()
    
    def save_comment(self):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        
        if self.editing_comment_idx >= 0 and self.editing_comment_idx < len(cell.comments):
            # Редактирование существующего
            comment = cell.comments[self.editing_comment_idx]
            comment['title'] = self.comment_title_input.text
            comment['text'] = self.comment_text_input.text
            if self.comment_circle:
                comment['x'] = self.comment_circle['x']
                comment['y'] = self.comment_circle['y']
                comment['size'] = self.comment_circle['size']
        else:
            # Новый
            if self.comment_circle:
                cell.comments.append({
                    'x': self.comment_circle['x'],
                    'y': self.comment_circle['y'],
                    'size': self.comment_circle['size'],
                    'title': self.comment_title_input.text,
                    'text': self.comment_text_input.text,
                })
        
        self.editing_comment_idx = -1
        self.comment_circle = None
        self.mode = 'view'
        self.menu_btn.opacity = 1
        self.eye_btn.opacity = 1
        self.flashlight_btn.opacity = 1
        self.confirm_btn.opacity = 0
        self.delete_btn.opacity = 0
        self.comment_input_layout.opacity = 0
        self.draw_overlays()
    
    def on_delete_comment(self, *args):
        if self.editing_comment_idx >= 0:
            content = BoxLayout(orientation='vertical', spacing=10, padding=20)
            lbl = Label(text='Удалить комментарий?', font_size=18, color=COLOR_TEXT)
            content.add_widget(lbl)
            
            btn_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
            btn_yes = Button(text='Да', background_color=COLOR_ACCENT, color=COLOR_TEXT)
            btn_no = Button(text='Нет', background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
            btn_box.add_widget(btn_yes)
            btn_box.add_widget(btn_no)
            content.add_widget(btn_box)
            
            popup = Popup(title='Подтверждение', content=content, size_hint=(0.7, 0.3),
                          background_color=COLOR_BG, title_color=COLOR_TEXT)
            
            def do_delete(*args):
                app = App.get_running_app()
                cell = app.array_data.get_cell(self.current_row, self.current_col)
                if self.editing_comment_idx < len(cell.comments):
                    del cell.comments[self.editing_comment_idx]
                self.editing_comment_idx = -1
                self.comment_circle = None
                self.mode = 'view'
                self.menu_btn.opacity = 1
                self.eye_btn.opacity = 1
                self.flashlight_btn.opacity = 1
                self.confirm_btn.opacity = 0
                self.delete_btn.opacity = 0
                self.comment_input_layout.opacity = 0
                popup.dismiss()
                self.draw_overlays()
            
            def cancel_delete(*args):
                popup.dismiss()
            
            btn_yes.bind(on_press=do_delete)
            btn_no.bind(on_press=cancel_delete)
            popup.open()
    
    def edit_comment(self, idx):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        if idx < 0 or idx >= len(cell.comments):
            return
        
        comment = cell.comments[idx]
        self.editing_comment_idx = idx
        self.mode = 'comment_edit'
        self.comment_circle = {'x': comment['x'], 'y': comment['y'], 'size': comment['size']}
        
        self.menu_btn.opacity = 0
        self.eye_btn.opacity = 0
        self.flashlight_btn.opacity = 0
        self.confirm_btn.opacity = 1
        self.delete_btn.opacity = 1
        
        self.comment_input_layout.opacity = 1
        self.comment_title_input.text = comment.get('title', '')
        self.comment_text_input.text = comment.get('text', '')
        self.draw_overlays()
    
    def show_comment_text(self, idx):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.current_row, self.current_col)
        if idx < 0 or idx >= len(cell.comments):
            return
        
        comment = cell.comments[idx]
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        title = Label(text=comment.get('title', ''), font_size=22, color=COLOR_ACCENT, size_hint_y=None, height=40)
        content.add_widget(title)
        
        text_label = Label(text=comment.get('text', ''), font_size=16, color=COLOR_TEXT,
                          size_hint_y=None, height=120, halign='left', valign='top')
        text_label.bind(width=lambda s, w: setattr(s, 'text_size', (w, None)))
        content.add_widget(text_label)
        
        btn_close = Button(text='Закрыть', font_size=16, size_hint_y=None, height=45,
                          background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        content.add_widget(btn_close)
        
        popup = Popup(title='Комментарий', content=content, size_hint=(0.8, 0.45),
                     background_color=COLOR_BG, title_color=COLOR_TEXT)
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
    
    def draw_overlays(self, *args):
        """Отрисовка оверлеев: кружки комментариев, мерцающий кружок и т.д."""
        self.overlay_widget.canvas.clear()
        a = get_icon_alpha()
        
        if self.mode == 'view':
            # Рисуем кружки комментариев
            app = App.get_running_app()
            cell = app.array_data.get_cell(self.current_row, self.current_col)
            
            for i, comment in enumerate(cell.comments):
                sx, sy = self.image_view.img_to_screen(comment['x'], comment['y'])
                size = comment['size']
                
                if self.eye_mode == 2:
                    # Все кружки одинакового размера
                    draw_size = get_small_icon_size() * 0.8
                else:
                    draw_size = size
                
                # Проверяем, что кружок в пределах экрана
                if sx < -50 or sx > self.width + 50 or sy < -50 or sy > self.height + 50:
                    continue
                
                with self.overlay_widget.canvas:
                    if self.eye_mode == 1:
                        # Мерцающие кружки
                        t = Clock.get_time()
                        alpha_val = 0.3 + 0.4 * (math.sin(t * 3) * 0.5 + 0.5)
                        Color(0.91, 0.27, 0.37, alpha_val)
                    else:
                        Color(0.91, 0.27, 0.37, 0.7 * a)
                    
                    Ellipse(pos=(sx - draw_size/2, sy - draw_size/2), size=(draw_size, draw_size))
                    Color(1, 1, 1, a)
                    Line(circle=(sx, sy, draw_size/2), width=1.5)
                    
                    # Название над кружком
                    if comment.get('title'):
                        title_size = max(10, int(draw_size * 0.4))
                        # Упрощённо — рисуем фон для текста
                        Color(0, 0, 0, 0.7 * a)
                        Rectangle(pos=(sx - draw_size, sy + draw_size/2 + 2),
                                  size=(draw_size * 2, title_size + 4))
        
        elif self.mode == 'common_point':
            # Мерцающий кружок в центре viewport
            cx = self.overlay_widget.x + self.overlay_widget.width / 2
            cy = self.overlay_widget.y + self.overlay_widget.height / 2
            t = Clock.get_time()
            alpha_val = 0.3 + 0.6 * (math.sin(t * 4) * 0.5 + 0.5)
            
            with self.overlay_widget.canvas:
                Color(0.33, 0.84, 0.41, alpha_val)
                r = 12
                Ellipse(pos=(cx - r, cy - r), size=(r*2, r*2))
                Color(1, 1, 1, 1)
                Line(circle=(cx, cy, r), width=2)
        
        elif self.mode == 'comment_place':
            # Мерцающий кружок в центре viewport
            cx = self.overlay_widget.x + self.overlay_widget.width / 2
            cy = self.overlay_widget.y + self.overlay_widget.height / 2
            t = Clock.get_time()
            alpha_val = 0.3 + 0.6 * (math.sin(t * 4) * 0.5 + 0.5)
            
            with self.overlay_widget.canvas:
                Color(0.91, 0.27, 0.37, alpha_val)
                r = 20
                Ellipse(pos=(cx - r, cy - r), size=(r*2, r*2))
                Color(1, 1, 1, 1)
                Line(circle=(cx, cy, r), width=2)
        
        elif self.mode == 'comment_edit':
            # Статичный кружок с нулевой прозрачностью (но с обводкой)
            if self.comment_circle:
                sx, sy = self.image_view.img_to_screen(self.comment_circle['x'], self.comment_circle['y'])
                with self.overlay_widget.canvas:
                    Color(0.91, 0.27, 0.37, 0.0)  # нулевая прозрачность заливки
                    r = self.comment_circle['size']
                    Ellipse(pos=(sx - r, sy - r), size=(r*2, r*2))
                    Color(1, 1, 1, a * 0.8)
                    Line(circle=(sx, sy, r), width=1.5)
    
    def _animate(self, dt):
        """Анимация мерцания кружков"""
        if self.mode in ('common_point', 'comment_place') or self.eye_mode == 1:
            self.draw_overlays()
    
    def on_touch_down(self, touch):
        # Проверка нажатий на кружки комментариев в режиме просмотра
        if self.mode == 'view':
            app = App.get_running_app()
            cell = app.array_data.get_cell(self.current_row, self.current_col)
            
            for i, comment in enumerate(cell.comments):
                sx, sy = self.image_view.img_to_screen(comment['x'], comment['y'])
                draw_size = comment['size']
                if self.eye_mode == 2:
                    draw_size = get_small_icon_size() * 0.8
                
                dist = math.sqrt((touch.x - sx)**2 + (touch.y - sy)**2)
                if dist < draw_size / 2 + 5:
                    # Нажатие на кружок
                    now = Clock.get_time()
                    if not hasattr(self, '_last_comment_touch'):
                        self._last_comment_touch = (now, i, touch.x, touch.y)
                    else:
                        lt, li, lx, ly = self._last_comment_touch
                        if now - lt < 0.5 and li == i and abs(touch.x - lx) < 20 and abs(touch.y - ly) < 20:
                            # Двойное касание — показать текст
                            self.show_comment_text(i)
                            self._last_comment_touch = None
                            return True
                        else:
                            self._last_comment_touch = (now, i, touch.x, touch.y)
                    
                    # Одиночное касание — ждём, может быть долгое нажатие
                    self._comment_touch_start = (now, i, touch.x, touch.y)
                    return True
            
            # Проверка долгого нажатия
            if hasattr(self, '_comment_touch_start') and self._comment_touch_start:
                pass  # Проверяем при отпускании
            
            # Передаём касание виджету изображения
            self.image_view.on_touch_down(touch)
            return True
        elif self.mode in ('common_point', 'comment_place'):
            # В этих режимах касания управляют viewport
            self.image_view.on_touch_down(touch)
            return True
        elif self.mode == 'comment_edit':
            # Тоже позволяем панорамировать
            self.image_view.on_touch_down(touch)
            return True
        
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        # Проверка долгого нажатия на кружок комментария
        if self.mode == 'view' and hasattr(self, '_comment_long_start') and self._comment_long_start:
            lt, li, lx, ly = self._comment_long_start
            if abs(touch.x - lx) > 15 or abs(touch.y - ly) > 15:
                self._comment_long_start = None
        
        # Передаём виджету изображения
        if self.mode in ('view', 'common_point', 'comment_place', 'comment_edit'):
            self.image_view.on_touch_move(touch)
        return True
    
    def on_touch_up(self, touch):
        # Проверка долгого нажатия на кружок комментария
        if self.mode == 'view' and hasattr(self, '_comment_long_start') and self._comment_long_start:
            lt, li, lx, ly = self._comment_long_start
            if Clock.get_time() - lt > 0.8 and abs(touch.x - lx) < 15 and abs(touch.y - ly) < 15:
                self.edit_comment(li)
                self._comment_long_start = None
                return True
            self._comment_long_start = None
        
        if self.mode in ('view', 'common_point', 'comment_place', 'comment_edit'):
            self.image_view.on_touch_up(touch)
        return True


# ========== Главный класс приложения ==========
class KotlovanApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.array_data = ArrayData()
        self.file_chooser_popup = None
        self.pending_action = None
        self.save_dir = os.path.join(os.path.expanduser('~'), 'Kotlovan')
        self.config_file = None
        
    def show_file_chooser(self, action, initial_path=None):
        """
        action: 'save_array' — сохранить весь массив (папка)
                'load_config' — загрузить config.json
        """
        self.pending_action = action

        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView()
        if initial_path and os.path.exists(initial_path):
            file_chooser.path = initial_path
        else:
            # Для Android лучше начинать с user_data_dir — это гарантированно доступно
            file_chooser.path = self.user_data_dir

        content.add_widget(file_chooser)

        btn_box = BoxLayout(size_hint_y=None, height=50)
        btn_ok = Button(text='Выбрать', size_hint_x=0.5)
        btn_cancel = Button(text='Отмена', size_hint_x=0.5)

        def on_select(*args):
            selected = file_chooser.selection
            if selected:
                chosen_path = selected[0]
                if action == 'save_array':
                    # Передаём путь в экран сетки, где лежит save_array_to_dir
                    grid_screen = self.root.get_screen('grid_view')
                    if grid_screen:
                        grid_screen.save_array_to_dir(chosen_path)
                elif action == 'load_config':
                    self.load_array_config(chosen_path)
            popup.dismiss()

        btn_ok.bind(on_press=on_select)
        btn_cancel.bind(on_press=popup.dismiss)
        btn_box.add_widget(btn_ok)
        btn_box.add_widget(btn_cancel)
        content.add_widget(btn_box)

        popup = Popup(
            title='Выберите папку для сохранения',
            content=content,
            size_hint=(0.9, 0.8)
        )
        popup.open()
    
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.15, 1)
        
        self.sm = KotlovanScreenManager()
        self.sm.transition = SlideTransition(direction='left')
        
        # Добавляем экраны
        self.sm.add_widget(MainMenuScreen())
        self.sm.add_widget(ArraySizeScreen())
        self.sm.add_widget(GridViewScreen())
        self.sm.add_widget(CardEditScreen())
        self.sm.add_widget(ViewModeScreen())
        
        # Загружаем настройки
        self.load_settings()
        
        return self.sm
    
    def load_settings(self):
        global ICON_SCALE, ICON_ALPHA
        settings_path = os.path.join(os.path.expanduser('~'), '.kotlovan_settings.json')
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    s = json.load(f)
                    ICON_SCALE = s.get('icon_scale', 1.0)
                    ICON_ALPHA = s.get('icon_alpha', 1.0)
        except:
            pass
    
    def save_settings(self):
        global ICON_SCALE, ICON_ALPHA
        settings_path = os.path.join(os.path.expanduser('~'), '.kotlovan_settings.json')
        try:
            with open(settings_path, 'w') as f:
                json.dump({'icon_scale': ICON_SCALE, 'icon_alpha': ICON_ALPHA}, f)
        except:
            pass
    
    def show_file_chooser(self, action_type):
        """Показ файлового менеджера"""
        content = BoxLayout(orientation='vertical')
        
        fc = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*.json'] if action_type in ('load_config',) else ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif'],
            size_hint=(1, 0.9)
        )
        content.add_widget(fc)
        
        btn_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        btn_cancel = Button(text='Отмена', background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_select = Button(text='Выбрать', background_color=COLOR_ACCENT, color=COLOR_TEXT)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_select)
        content.add_widget(btn_box)
        
        popup = Popup(
            title='Выбор файла',
            content=content,
            size_hint=(0.9, 0.9),
            background_color=COLOR_BG,
            title_color=COLOR_TEXT
        )
        
        def on_select(*args):
            selection = fc.selection
            if selection:
                self.on_file_selected(action_type, selection[0])
            popup.dismiss()
        
        def on_cancel(*args):
            popup.dismiss()
        
        btn_select.bind(on_press=on_select)
        btn_cancel.bind(on_press=on_cancel)
        #fc.bind(on_submit=lambda x, y: on_select() if y else None)
        
        popup.open()
    
    def on_file_selected(self, action_type, filepath):
        if action_type == 'load_config':
            self.load_array_from_config(filepath)
        elif action_type == 'load_image':
            self.on_image_selected(filepath)
        elif action_type == 'save_array':
            self.save_array_to_dir(filepath)
    
    def load_array_from_config(self, config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.array_data = ArrayData.from_dict(data)
            self.array_data.config_path = config_path
            # Переключаем на экран просмотра
            self.sm.get_screen('view_mode').enter_view_mode()
            self.sm.current = 'view_mode'
        except Exception as e:
            self.show_error(f'Ошибка загрузки: {str(e)}')
    
    def on_image_selected(self, filepath):
        if self.pending_action and self.pending_action[0] == 'card_edit_load':
            row, col = self.pending_action[1]
            cell = self.array_data.get_cell(row, col)
            cell.image_path = filepath
            cell.image_filename = os.path.basename(filepath)
            # Обновляем экран редактирования
            editor = self.sm.get_screen('card_edit')
            if self.sm.current == 'card_edit':
                editor.update_image()
    
    def save_array_to_dir(self, dir_path):
        if not self.array_data:
            return
        
        if os.path.isfile(dir_path):
            dir_path = os.path.dirname(dir_path)
        
        # Создаём папку массива
        array_dir = os.path.join(dir_path, self.array_data.array_name or 'KotlovanArray')
        if not os.path.exists(array_dir):
            os.makedirs(array_dir)
        
>>>>>>> 32dfbfd (new old progect)
        # Копируем изображения
        for key, cell in data.get("cells", {}).items():
            img = cell.get("image", "")
            if img and os.path.exists(img):
                dst = os.path.join(folder, os.path.basename(img))
                try:
                    shutil.copy2(img, dst)
                    cell["image"] = dst
                except Exception:
                    pass
        save_json(data, os.path.join(folder, "config.json"))

        # Переход в режим просмотра
        sm = self.manager
        viewer = sm.get_screen("viewer")
        viewer.load_array(data)
        sm.current = "viewer"

    def _show_error(self, msg):
        popup = Popup(title="Ошибка", content=Label(text=msg, font_size=18),
                      size_hint=(0.7, 0.4))
        popup.open()

    def go_home(self):
        self.manager.current = "main"


# ---------------------------------------------------------------------------
#  Экран: Режим просмотра (основной)
# ---------------------------------------------------------------------------
class ViewerScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        self.array_data = None
        self.rows = 0
        self.cols = 0
        self.cells = {}
        self.cur_row = 0
        self.cur_col = 0
        self.zoom = 1.0
        self.vp_x = 0.0  # смещение viewport относительно общей точки
        self.vp_y = 0.0
        self.eye_mode = 0  # 0=normal, 1=blink, 2=equal
        self.icon_scale = 1.0
        self.icon_alpha = 1.0
        self.mode = "view"  # view, common_point, comment_place, comment_edit
        self.comment_circles = []
        self._touches = {}
        self._pinch_dist = 0
        self._swipe_start = None
        self._img_widget = None
        self._comment_circle_blink = None
        self._editing_comment = None
        self._comment_radius = 20
        self._flashlight_on = False

    # ----------------- загрузка -----------------
    def load_array(self, data):
        self.array_data = data
        self.rows = data.get("rows", 1)
        self.cols = data.get("cols", 1)
        self.cells = {}
        for key, cdata in data.get("cells", {}).items():
            r, c = cdata["row"], cdata["col"]
            self.cells[(r, c)] = {
                "name": cdata.get("name", ""),
                "image": cdata.get("image", ""),
                "common_point": cdata.get("common_point"),
                "own_position": cdata.get("own_position", False),
                "comments": cdata.get("comments", []),
            }
        self.cur_row = 0
        self.cur_col = 0
        # Инициализация общих точек
        self._init_common_points()
        self._show_cell()

    def _init_common_points(self):
        for (r, c), cell in self.cells.items():
            if cell["common_point"] is None and not cell["own_position"]:
                # Центр изображения — используем заглушку (500,500)
                cell["common_point"] = [500, 500]

    # ----------------- отображение -----------------
    def on_pre_enter(self, *_):
        self._show_cell()

    def _show_cell(self):
        self.layout.clear_widgets()
        self.mode = "view"
        self.comment_circles = []

        cell = self.cells.get((self.cur_row, self.cur_col))
        if not cell:
            self.layout.add_widget(Label(text="Нет данных", font_size=24,
                                         pos_hint={"center_x": 0.5, "center_y": 0.5}))
            self._add_overlay()
            return

        img_path = cell["image"]
        if img_path and os.path.exists(img_path):
            self._img_widget = Image(source=img_path,
                                     size_hint=(1, 1),
                                     pos_hint={"center_x": 0.5, "center_y": 0.5},
                                     allow_stretch=True,
                                     keep_ratio=False)
            self.layout.add_widget(self._img_widget)
        else:
            self.layout.add_widget(Label(text="Изображение не загружено",
                                         font_size=22,
                                         pos_hint={"center_x": 0.5, "center_y": 0.5}))

        # Кружки комментариев
        self._draw_comments(cell)

        # Overlay UI
        self._add_overlay()

    def _add_overlay(self):
        # Кнопка возврата (верхний левый)
        back = Button(text="<", font_size=30,
                      size_hint=(0.1 * self.icon_scale, 0.08 * self.icon_scale),
                      pos_hint={"x": 0.02, "top": 0.98},
                      opacity=self.icon_alpha)
        back.bind(on_release=lambda *_: self.go_back())
        self.layout.add_widget(back)

        # Иконка глаза (нижний левый)
        eye_texts = ["👁", "👁", "👁"]
        eye = Button(text=eye_texts[self.eye_mode],
                     font_size=int(20 * self.icon_scale),
                     size_hint=(0.1 * self.icon_scale, 0.08 * self.icon_scale),
                     pos_hint={"x": 0.02, "y": 0.02},
                     opacity=self.icon_alpha)
        eye.bind(on_release=self._toggle_eye)
        self.layout.add_widget(eye)

        # Иконка фонарика (середина сверху)
        flashlight = Button(text="🔦", font_size=int(20 * self.icon_scale),
                            size_hint=(0.1 * self.icon_scale, 0.08 * self.icon_scale),
                            pos_hint={"center_x": 0.5, "top": 0.98},
                            opacity=self.icon_alpha)
        flashlight.bind(on_release=self._toggle_flashlight)
        self.layout.add_widget(flashlight)

        # Контекстное меню (правый верхний)
        ctx = Button(text="☰", font_size=int(20 * self.icon_scale),
                     size_hint=(0.1 * self.icon_scale, 0.08 * self.icon_scale),
                     pos_hint={"right": 0.98, "top": 0.98},
                     opacity=self.icon_alpha)
        ctx.bind(on_release=self._show_context_menu)
        self.layout.add_widget(ctx)

    def go_back(self):
        self.manager.current = "main"

    # ----------------- контекстное меню -----------------
    def _show_context_menu(self, *_):
        cell = self.cells.get((self.cur_row, self.cur_col))
        own_pos = "true" if cell and cell["own_position"] else "false"

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        btn_cp = Button(text="Общая точка", font_size=18)
        btn_cp.bind(on_release=lambda *_: self._enter_common_point())
        content.add_widget(btn_cp)

        btn_op = Button(text=f"Свое положение: {own_pos}", font_size=18)
        btn_op.bind(on_release=lambda *_: self._toggle_own_position())
        content.add_widget(btn_op)

        btn_comment = Button(text="Установить комментарий", font_size=18)
        btn_comment.bind(on_release=lambda *_: self._enter_comment_place())
        content.add_widget(btn_comment)

        btn_settings = Button(text="Настройки", font_size=18)
        btn_settings.bind(on_release=lambda *a: self._show_settings(popup))
        content.add_widget(btn_settings)

        popup = Popup(title="Меню", content=content,
                      size_hint=(0.7, 0.5))
        popup.open()

    def _show_settings(self, parent_popup, *_):
        parent_popup.dismiss()
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        content.add_widget(Label(text="Размер иконок", font_size=16))
        sl_size = Slider(min=0.1, max=3.0, value=self.icon_scale)
        lbl_size_val = Label(text=f"x{self.icon_scale:.1f}", font_size=16)
        sl_size.bind(value=lambda *_a, v: lbl_size_val.setter("text")(lbl_size_val, f"x{v:.1f}"))
        sl_size.bind(value=lambda *_a, v: setattr(self, "icon_scale", v))
        content.add_widget(sl_size)
        content.add_widget(lbl_size_val)

        content.add_widget(Label(text="Прозрачность иконок", font_size=16))
        sl_alpha = Slider(min=0.1, max=1.0, value=self.icon_alpha)
        lbl_alpha_val = Label(text=f"{int(self.icon_alpha * 100)}%", font_size=16)
        sl_alpha.bind(value=lambda *_a, v: lbl_alpha_val.setter("text")(lbl_alpha_val, f"{int(v*100)}%"))
        sl_alpha.bind(value=lambda *_a, v: setattr(self, "icon_alpha", v))
        content.add_widget(sl_alpha)
        content.add_widget(lbl_alpha_val)

        btn_close = Button(text="Закрыть", font_size=18)
        btn_close.bind(on_release=lambda *_: settings_popup.dismiss())
        content.add_widget(btn_close)

        settings_popup = Popup(title="Настройки", content=content,
                               size_hint=(0.7, 0.5))
        settings_popup.open()

    # ----------------- общая точка -----------------
    def _enter_common_point(self, *_):
        self.mode = "common_point"
        self.layout.clear_children_ui = True
        self.layout.clear_widgets()

        # Только кнопка возврата
        back = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                      pos_hint={"x": 0.02, "top": 0.98})
        back.bind(on_release=lambda *_: self._show_cell())
        self.layout.add_widget(back)

        # Кружок в центре
        self._comment_circle_blink = BlinkCircle(radius=15)
        self._comment_circle_blink.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.layout.add_widget(self._comment_circle_blink)

        # Кнопка подтверждения (нижний левый)
        confirm = Button(text="✓", font_size=30, size_hint=(0.1, 0.08),
                         pos_hint={"x": 0.02, "y": 0.02})
        confirm.bind(on_release=self._confirm_common_point)
        self.layout.add_widget(confirm)

    def _confirm_common_point(self, *_):
        cell = self.cells.get((self.cur_row, self.cur_col))
        if cell:
            # Сохраняем центр viewport как общую точку
            cp = cell["common_point"] or [500, 500]
            cp[0] += self.vp_x
            cp[1] += self.vp_y
            cell["common_point"] = cp
        if self._comment_circle_blink:
            self._comment_circle_blink.stop()
            self._comment_circle_blink = None
        self._show_cell()

    # ----------------- своё положение -----------------
    def _toggle_own_position(self, *_):
        cell = self.cells.get((self.cur_row, self.cur_col))
        if cell:
            cell["own_position"] = not cell["own_position"]
        self._show_cell()

    # ----------------- комментарий -----------------
    def _enter_comment_place(self, *_):
        self.mode = "comment_place"
        self.layout.clear_widgets()

        back = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                      pos_hint={"x": 0.02, "top": 0.98})
        back.bind(on_release=lambda *_: self._show_cell())
        self.layout.add_widget(back)

        self._comment_circle_blink = BlinkCircle(radius=20)
        self._comment_circle_blink.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.layout.add_widget(self._comment_circle_blink)

        confirm = Button(text="✓", font_size=30, size_hint=(0.1, 0.08),
                         pos_hint={"x": 0.02, "y": 0.02})
        confirm.bind(on_release=self._confirm_comment_place)
        self.layout.add_widget(confirm)

    def _confirm_comment_place(self, *_):
        if self._comment_circle_blink:
            self._comment_circle_blink.stop()
        self.mode = "comment_edit"
        self._enter_comment_edit()

    def _enter_comment_edit(self, existing=None):
        self.layout.clear_widgets()

        back = Button(text="<", font_size=30, size_hint=(0.1, 0.08),
                      pos_hint={"x": 0.02, "top": 0.98})
        back.bind(on_release=lambda *_: self._show_cell())
        self.layout.add_widget(back)

        box = BoxLayout(orientation="vertical", padding=30, spacing=15,
                        size_hint=(0.85, 0.7),
                        pos_hint={"center_x": 0.5, "center_y": 0.5})

        self._comment_title_input = TextInput(hint_text="Короткое название",
                                              font_size=18, multiline=False,
                                              size_hint_y=0.15)
        box.add_widget(self._comment_title_input)

        self._comment_text_input = TextInput(hint_text="Текст комментария",
                                             font_size=18, multiline=True,
                                             size_hint_y=0.5)
        box.add_widget(self._comment_text_input)

        row_btns = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=0.15)

        btn_del = Button(text="Удалить", font_size=18)
        btn_del.bind(on_release=self._delete_comment)
        row_btns.add_widget(btn_del)

        btn_save = Button(text="Сохранить", font_size=18)
        btn_save.bind(on_release=self._save_comment)
        row_btns.add_widget(btn_save)
        box.add_widget(row_btns)

        self.layout.add_widget(box)

        if existing:
            self._comment_title_input.text = existing.get("title", "")
            self._comment_text_input.text = existing.get("text", "")

    def _save_comment(self, *_):
        cell = self.cells.get((self.cur_row, self.cur_col))
        if cell:
            comment = {
                "x": 500 + self.vp_x,
                "y": 500 + self.vp_y,
                "size": self._comment_radius,
                "title": self._comment_title_input.text,
                "text": self._comment_text_input.text,
            }
            cell["comments"].append(comment)
        self._show_cell()

    def _delete_comment(self, *_):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text="Удалить комментарий?", font_size=18))
        row = BoxLayout(orientation="horizontal", spacing=10)
        btn_yes = Button(text="Да", font_size=18)
        btn_no = Button(text="Нет", font_size=18)
        row.add_widget(btn_yes)
        row.add_widget(btn_no)
        content.add_widget(row)

        popup = Popup(title="Подтверждение", content=content,
                      size_hint=(0.6, 0.35))

        btn_yes.bind(on_release=lambda *_: self._do_delete_comment(popup))
        btn_no.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _do_delete_comment(self, popup, *_):
        popup.dismiss()
        cell = self.cells.get((self.cur_row, self.cur_col))
        if cell and self._editing_comment and self._editing_comment in cell["comments"]:
            cell["comments"].remove(self._editing_comment)
            self._editing_comment = None
        self._show_cell()

    # ----------------- кружки комментариев на экране -----------------
    def _draw_comments(self, cell):
        """Рисует кружки комментариев для текущей ячейки."""
        for i, com in enumerate(cell.get("comments", [])):
            cx = com["x"]
            cy = com["y"]
            r = com["size"] if self.eye_mode == 0 else 20

            circle = CommentCircle(cx, cy, r,
                                   title=com.get("title", ""),
                                   text=com.get("text", ""),
                                   comment_id=i)
            with circle.canvas:
                Color(1, 0.3, 0.3, 0.7 if self.eye_mode != 1 else 0.5)
                Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                if com.get("title"):
                    Color(1, 1, 1, 1)
            self.layout.add_widget(circle)
            self.comment_circles.append(circle)

    # ----------------- глаз -----------------
    def _toggle_eye(self, *_):
        self.eye_mode = (self.eye_mode + 1) % 3
        self._show_cell()

    # ----------------- фонарик -----------------
    def _toggle_flashlight(self, *_):
        self._flashlight_on = not self._flashlight_on
        try:
            from plyer import flash
            if self._flashlight_on:
                flash.on()
            else:
                flash.off()
        except Exception:
            pass

    # ----------------- навигация -----------------
    def _next_cell_row(self, direction):
        new_col = self.cur_col + direction
        if 0 <= new_col < self.cols:
            self.cur_col = new_col
            self._show_cell()

    def _next_cell_col(self, direction):
        new_row = self.cur_row + direction
        if 0 <= new_row < self.rows:
            self.cur_row = new_row
            self._show_cell()

    # ----------------- touch -----------------
    def on_touch_down(self, touch):
        if self.mode != "view":
            return super().on_touch_down(touch)
        self._touches[touch.id] = touch
        if len(self._touches) == 1:
            self._swipe_start = (touch.x, touch.y)
        elif len(self._touches) == 2:
            ids = list(self._touches.keys())
            t1, t2 = self._touches[ids[0]], self._touches[ids[1]]
            self._pinch_dist = ((t1.x - t2.x) ** 2 + (t1.y - t2.y) ** 2) ** 0.5
        return True

    def on_touch_move(self, touch):
        if self.mode != "view":
            return super().on_touch_move(touch)
        if touch.id not in self._touches:
            return True
        if len(self._touches) == 2:
            ids = list(self._touches.keys())
            t1, t2 = self._touches[ids[0]], self._touches[ids[1]]
            dist = ((t1.x - t2.x) ** 2 + (t1.y - t2.y) ** 2) ** 0.5
            if self._pinch_dist > 0:
                self.zoom *= dist / self._pinch_dist
                self.zoom = max(0.1, min(10.0, self.zoom))
            self._pinch_dist = dist
            # Перемещение
            self.vp_x += (t1.dx + t2.dx) / 2
            self.vp_y += (t1.dy + t2.dy) / 2
        return True

    def on_touch_up(self, touch):
        if self.mode != "view":
            return super().on_touch_up(touch)
        if touch.id in self._touches:
            del self._touches[touch.id]

        if len(self._touches) == 0 and self._swipe_start:
            dx = touch.x - self._swipe_start[0]
            dy = touch.y - self._swipe_start[1]
            threshold = 50
            if abs(dx) > threshold and abs(dx) > abs(dy):
                self._next_cell_row(1 if dx < 0 else -1)
            elif abs(dy) > threshold and abs(dy) > abs(dx):
                self._next_cell_col(1 if dy < 0 else -1)
            self._swipe_start = None
        return True


# ---------------------------------------------------------------------------
#  Приложение
# ---------------------------------------------------------------------------
class KotlovanApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main"))
        sm.add_widget(CreateArrayScreen(name="create_array"))
        sm.add_widget(ArrayViewScreen(name="array_view"))
        sm.add_widget(CardEditScreen(name="card_edit"))
        sm.add_widget(FilePickerScreen(name="file_picker"))
        sm.add_widget(ViewerScreen(name="viewer"))
        return sm


if __name__ == "__main__":
    KotlovanApp().run()
