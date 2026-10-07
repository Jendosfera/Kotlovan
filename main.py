"""
Котлован — приложение для просмотра инженерных чертежей
Сравнение одинаковых помещений на схемах разных коммуникаций
"""

import os
import json
import math
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Translate, Scale
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty, AliasProperty
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from PIL import Image as PILImage
import io

# Попытка импорта фонарика
try:
    from plyer import flashlight
    HAS_FLASHLIGHT = True
except:
    HAS_FLASHLIGHT = False

# ========== Глобальные настройки ==========
ICON_SCALE = 1.0
ICON_ALPHA = 1.0

def get_icon_size():
    return 40 * ICON_SCALE

def get_icon_alpha():
    return ICON_ALPHA

def get_small_icon_size():
    return 30 * ICON_SCALE

def get_back_btn_size():
    return 50 * ICON_SCALE

# ========== Цвета ==========
COLOR_BG = get_color_from_hex('#1a1a2e')
COLOR_BTN = get_color_from_hex('#16213e')
COLOR_BTN_ACTIVE = get_color_from_hex('#0f3460')
COLOR_ACCENT = get_color_from_hex('#e94560')
COLOR_TEXT = get_color_from_hex('#eeeeee')
COLOR_PLUS = get_color_from_hex('#53d769')
COLOR_CARD = get_color_from_hex('#2a2a4a')
COLOR_PLUS_BTN = get_color_from_hex('#3a7bd5')


# ========== Иконки (рисуются программно) ==========
class IconButton(Button):
    """Кнопка с програмно рисуемой иконкой"""
    icon_type = StringProperty('back')
    icon_scale = NumericProperty(1.0)
    icon_alpha_val = NumericProperty(1.0)
    
    def __init__(self, icon_type='back', **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.icon_scale = ICON_SCALE
        self.icon_alpha_val = ICON_ALPHA
        self.size_hint = (None, None)
        self.background_color = (0, 0, 0, 0)
        self.update_size()
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.update_canvas()
    
    def update_size(self):
        s = get_back_btn_size()
        self.size = (s, s)
    
    def update_canvas(self, *args):
        self.canvas.clear()
        a = get_icon_alpha()
        with self.canvas:
            if self.icon_type == 'back':
                # Стрелка назад
                Color(1, 1, 1, a)
                Line(points=[
                    self.right - 10*self.icon_scale, self.center_y,
                    self.x + 10*self.icon_scale, self.center_y
                ], width=2)
                Line(points=[
                    self.x + 10*self.icon_scale, self.center_y,
                    self.x + 20*self.icon_scale, self.center_y + 10*self.icon_scale
                ], width=2)
                Line(points=[
                    self.x + 10*self.icon_scale, self.center_y,
                    self.x + 20*self.icon_scale, self.center_y - 10*self.icon_scale
                ], width=2)
            elif self.icon_type == 'plus':
                Color(0.33, 0.84, 0.41, a)
                Line(points=[
                    self.center_x, self.y + 8*self.icon_scale,
                    self.center_x, self.top - 8*self.icon_scale
                ], width=3)
                Line(points=[
                    self.x + 8*self.icon_scale, self.center_y,
                    self.right - 8*self.icon_scale, self.center_y
                ], width=3)
                # Объёмная рамка
                Color(0.33, 0.84, 0.41, a * 0.5)
                Line(rectangle=(self.x+2, self.y+2, self.width-4, self.height-4), width=1.5)
            elif self.icon_type == 'menu':
                Color(1, 1, 1, a)
                Line(points=[self.x + 8*self.icon_scale, self.top - 10*self.icon_scale, 
                              self.right - 8*self.icon_scale, self.top - 10*self.icon_scale], width=2)
                Line(points=[self.x + 8*self.icon_scale, self.center_y,
                              self.right - 8*self.icon_scale, self.center_y], width=2)
                Line(points=[self.x + 8*self.icon_scale, self.y + 10*self.icon_scale,
                              self.right - 8*self.icon_scale, self.y + 10*self.icon_scale], width=2)
            elif self.icon_type == 'eye_closed':
                # Полуприкрытый глаз
                Color(1, 1, 1, a)
                # Веко
                Line(points=self._eye_shape(self.center_x, self.center_y, 16*self.icon_scale, 8*self.icon_scale), width=1.5)
                # Нижнее веко (прикрыто)
                Color(1, 1, 1, a)
                Line(points=[
                    self.center_x - 12*self.icon_scale, self.center_y - 2*self.icon_scale,
                    self.center_x + 12*self.icon_scale, self.center_y - 2*self.icon_scale
                ], width=2)
            elif self.icon_type == 'eye_open_narrow':
                # Открытый глаз, суженный зрачок
                Color(1, 1, 1, a)
                Line(points=self._eye_shape(self.center_x, self.center_y, 16*self.icon_scale, 8*self.icon_scale), width=1.5)
                Color(1, 1, 1, a)
                d = 3*self.icon_scale
                Ellipse(pos=(self.center_x - d, self.center_y - d), size=(d*2, d*2))
            elif self.icon_type == 'eye_open_wide':
                # Открытый глаз, широкий зрачок
                Color(1, 1, 1, a)
                Line(points=self._eye_shape(self.center_x, self.center_y, 16*self.icon_scale, 8*self.icon_scale), width=1.5)
                Color(1, 1, 1, a)
                d = 6*self.icon_scale
                Ellipse(pos=(self.center_x - d, self.center_y - d), size=(d*2, d*2))
            elif self.icon_type == 'flashlight':
                Color(1, 1, 0, a)
                # Корпус фонарика
                Line(rectangle=(self.center_x - 5*self.icon_scale, self.center_y - 10*self.icon_scale, 
                                10*self.icon_scale, 14*self.icon_scale), width=1.5)
                # Свет
                Color(1, 1, 0.3, a * 0.7)
                Line(points=[
                    self.center_x - 3*self.icon_scale, self.center_y + 4*self.icon_scale,
                    self.center_x - 10*self.icon_scale, self.center_y + 12*self.icon_scale
                ], width=1.5)
                Line(points=[
                    self.center_x + 3*self.icon_scale, self.center_y + 4*self.icon_scale,
                    self.center_x + 10*self.icon_scale, self.center_y + 12*self.icon_scale
                ], width=1.5)
                Line(points=[
                    self.center_x, self.center_y + 4*self.icon_scale,
                    self.center_x, self.center_y + 14*self.icon_scale
                ], width=1.5)
            elif self.icon_type == 'check':
                Color(0.33, 0.84, 0.41, a)
                Line(points=[
                    self.x + 8*self.icon_scale, self.center_y,
                    self.center_x - 4*self.icon_scale, self.y + 10*self.icon_scale,
                    self.right - 8*self.icon_scale, self.top - 10*self.icon_scale
                ], width=2.5)
            elif self.icon_type == 'delete':
                Color(0.91, 0.27, 0.37, a)
                Line(points=[
                    self.x + 10*self.icon_scale, self.y + 10*self.icon_scale,
                    self.right - 10*self.icon_scale, self.top - 10*self.icon_scale
                ], width=2)
                Line(points=[
                    self.right - 10*self.icon_scale, self.y + 10*self.icon_scale,
                    self.x + 10*self.icon_scale, self.top - 10*self.icon_scale
                ], width=2)
            elif self.icon_type == 'save':
                Color(1, 1, 1, a)
                # Дискета
                Line(rectangle=(self.x + 8*self.icon_scale, self.y + 8*self.icon_scale,
                                self.width - 16*self.icon_scale, self.height - 16*self.icon_scale), width=1.5)
                Line(rectangle=(self.x + 14*self.icon_scale, self.center_y,
                                self.width - 28*self.icon_scale, self.height - 24*self.icon_scale), width=1.5)
            elif self.icon_type == 'folder':
                Color(1, 0.8, 0.2, a)
                Line(points=[
                    self.x + 6*self.icon_scale, self.top - 8*self.icon_scale,
                    self.x + 14*self.icon_scale, self.top - 8*self.icon_scale,
                    self.x + 18*self.icon_scale, self.top - 14*self.icon_scale,
                    self.right - 6*self.icon_scale, self.top - 14*self.icon_scale
                ], width=1.5)
                Line(rectangle=(self.x + 6*self.icon_scale, self.y + 6*self.icon_scale,
                                self.width - 12*self.icon_scale, self.height - 20*self.icon_scale), width=1.5)
    
    def _eye_shape(self, cx, cy, w, h):
        points = []
        steps = 12
        for i in range(steps + 1):
            t = i / steps * math.pi
            x = cx - w + (2*w) * (i / steps)
            y = cy - h * math.sin(t)
            points.extend([x, y])
        return points
    
    def refresh(self):
        self.icon_scale = ICON_SCALE
        self.icon_alpha_val = ICON_ALPHA
        self.update_size()
        self.update_canvas()


class BackButton(IconButton):
    def __init__(self, callback=None, **kwargs):
        super().__init__(icon_type='back', **kwargs)
        self.callback = callback
        self.bind(on_press=self._on_press)
    
    def _on_press(self, *args):
        if self.callback:
            self.callback()


# ========== Модель данных ==========
class CellData:
    """Данные одной ячейки массива"""
    def __init__(self):
        self.title = ""
        self.image_path = ""
        self.image_filename = ""
        self.own_position = False  # "Свое положение"
        self.common_point = None  # [x, y] в координатах изображения
        self.comments = []  # [{x, y, size, title, text}]
        # Собственный viewport для own_position=True
        self.own_zoom = 1.0
        self.own_offset_x = 0.0
        self.own_offset_y = 0.0
    
    def to_dict(self):
        return {
            "title": self.title,
            "image_path": self.image_path,
            "image_filename": self.image_filename,
            "own_position": self.own_position,
            "common_point": self.common_point,
            "comments": self.comments,
            "own_zoom": self.own_zoom,
            "own_offset_x": self.own_offset_x,
            "own_offset_y": self.own_offset_y,
        }
    
    @staticmethod
    def from_dict(d):
        c = CellData()
        c.title = d.get("title", "")
        c.image_path = d.get("image_path", "")
        c.image_filename = d.get("image_filename", "")
        c.own_position = d.get("own_position", False)
        c.common_point = d.get("common_point", None)
        c.comments = d.get("comments", [])
        c.own_zoom = d.get("own_zoom", 1.0)
        c.own_offset_x = d.get("own_offset_x", 0.0)
        c.own_offset_y = d.get("own_offset_y", 0.0)
        return c


class ArrayData:
    """Данные всего массива"""
    def __init__(self, rows=0, cols=0):
        self.rows = rows
        self.cols = cols
        self.cells = {}  # key = "row,col" -> CellData
        # Общие параметры viewport (для ячеек без own_position)
        self.shared_zoom = 1.0
        self.shared_offset_x = 0.0
        self.shared_offset_y = 0.0
        self.current_row = 0
        self.current_col = 0
        self.config_path = ""
        self.array_name = "Без названия"
    
    def get_cell(self, row, col):
        key = f"{row},{col}"
        if key not in self.cells:
            self.cells[key] = CellData()
        return self.cells[key]
    
    def set_cell(self, row, col, cell):
        self.cells[f"{row},{col}"] = cell
    
    def cell_exists(self, row, col):
        return f"{row},{col}" in self.cells and self.cells[f"{row},{col}"].image_path
    
    def to_dict(self):
        cells_dict = {}
        for key, cell in self.cells.items():
            if cell.image_path or cell.title:
                cells_dict[key] = cell.to_dict()
        return {
            "rows": self.rows,
            "cols": self.cols,
            "array_name": self.array_name,
            "shared_zoom": self.shared_zoom,
            "shared_offset_x": self.shared_offset_x,
            "shared_offset_y": self.shared_offset_y,
            "current_row": self.current_row,
            "current_col": self.current_col,
            "cells": cells_dict,
        }
    
    @staticmethod
    def from_dict(d):
        arr = ArrayData(d.get("rows", 0), d.get("cols", 0))
        arr.array_name = d.get("array_name", "Без названия")
        arr.shared_zoom = d.get("shared_zoom", 1.0)
        arr.shared_offset_x = d.get("shared_offset_x", 0.0)
        arr.shared_offset_y = d.get("shared_offset_y", 0.0)
        arr.current_row = d.get("current_row", 0)
        arr.current_col = d.get("current_col", 0)
        for key, cd in d.get("cells", {}).items():
            arr.cells[key] = CellData.from_dict(cd)
        return arr
    
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @staticmethod
    def from_json(json_str):
        return ArrayData.from_dict(json.loads(json_str))


# ========== Менеджер экранов ==========
class KotlovanScreenManager(ScreenManager):
    pass


# ========== Главный экран ==========
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main_menu'
        self.build_ui()
    
    def build_ui(self):
        layout = FloatLayout()
        
        with layout.canvas.before:
            Color(*COLOR_BG)
            Rectangle(pos=self.pos, size=self.size)
        
        # Заголовок
        title = Label(
            text='Котлован',
            font_size=42,
            color=COLOR_ACCENT,
            size_hint=(1, None),
            height=60,
            pos_hint={'center_x': 0.5, 'top': 0.85}
        )
        layout.add_widget(title)
        
        subtitle = Label(
            text='Просмотр инженерных чертежей',
            font_size=16,
            color=COLOR_TEXT,
            size_hint=(1, None),
            height=30,
            pos_hint={'center_x': 0.5, 'top': 0.78}
        )
        layout.add_widget(subtitle)
        
        # Кнопки
        btn_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, None),
            height=130,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=15
        )
        
        btn_load = Button(
            text='Загрузить массив',
            font_size=20,
            background_color=COLOR_BTN_ACTIVE,
            color=COLOR_TEXT
        )
        btn_load.bind(on_press=self.load_array)
        btn_layout.add_widget(btn_load)
        
        btn_create = Button(
            text='Создать массив',
            font_size=20,
            background_color=COLOR_BTN_ACTIVE,
            color=COLOR_TEXT
        )
        btn_create.bind(on_press=self.create_array)
        btn_layout.add_widget(btn_create)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
    
    def load_array(self, *args):
        app = App.get_running_app()
        app.show_file_chooser('load_config')
    
    def create_array(self, *args):
        app = App.get_running_app()
        app.array_data = None
        app.sm.current = 'array_size'


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


# ========== Экран редактирования карточки ==========
class CardEditScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'card_edit'
        self.row = 0
        self.col = 0
        self.build_ui()
    
    def build_ui(self):
        self.layout = FloatLayout()
        
        with self.layout.canvas.before:
            Color(*COLOR_BG)
            Rectangle(pos=self.pos, size=self.size)
        
        # Кнопка возврата
        self.back_btn = BackButton(callback=self.go_back)
        self.layout.add_widget(self.back_btn)
        
        # Заголовок
        self.title_label = Label(
            text='Карточка ячейки',
            font_size=22,
            color=COLOR_TEXT,
            size_hint=(1, None),
            height=40,
            pos_hint={'center_x': 0.5, 'top': 0.93}
        )
        self.layout.add_widget(self.title_label)
        
        # Поле ввода названия
        self.name_input = TextInput(
            hint_text='Введите название',
            font_size=20,
            size_hint=(0.8, None),
            height=50,
            pos_hint={'center_x': 0.5, 'top': 0.87},
            multiline=False,
            background_color=COLOR_BTN
        )
        self.layout.add_widget(self.name_input)
        
        # Область изображения
        self.img_widget = Widget(size_hint=(0.85, 0.55), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.img_widget.bind(pos=self.update_image, size=self.update_image)
        self.layout.add_widget(self.img_widget)
        
        # Кнопки
        btn_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(0.8, None),
            height=55,
            pos_hint={'center_x': 0.5, 'bottom': 0.08},
            spacing=20
        )
        
        btn_load = Button(text='Загрузить', font_size=18, background_color=COLOR_BTN_ACTIVE, color=COLOR_TEXT)
        btn_load.bind(on_press=self.load_image)
        btn_layout.add_widget(btn_load)
        
        btn_confirm = Button(text='Подтвердить', font_size=18, background_color=COLOR_ACCENT, color=COLOR_TEXT)
        btn_confirm.bind(on_press=self.confirm)
        btn_layout.add_widget(btn_confirm)
        
        self.layout.add_widget(btn_layout)
        self.add_widget(self.layout)
    
    def set_cell(self, row, col):
        self.row = row
        self.col = col
        app = App.get_running_app()
        cell = app.array_data.get_cell(row, col)
        self.name_input.text = cell.title
        self.update_image()
    
    def update_image(self, *args):
        self.img_widget.canvas.clear()
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.row, self.col)
        a = get_icon_alpha()
        
        with self.img_widget.canvas:
            Color(0.15, 0.15, 0.25, 1)
            Rectangle(pos=self.img_widget.pos, size=self.img_widget.size)
            Color(0.3, 0.3, 0.5, 0.8)
            Line(rectangle=(self.img_widget.x, self.img_widget.y, self.img_widget.width, self.img_widget.height), width=1.5)
            
            if cell.image_path and os.path.exists(cell.image_path):
                try:
                    from kivy.core.image import Image as CoreImage
                    img = CoreImage(cell.image_path).texture
                    if img:
                        # Масштабируем с сохранением пропорций
                        iw, ih = img.width, img.height
                        ww, wh = self.img_widget.width - 10, self.img_widget.height - 10
                        scale = min(ww/iw, wh/ih)
                        dw, dh = iw*scale, ih*scale
                        dx = self.img_widget.x + (self.img_widget.width - dw) / 2
                        dy = self.img_widget.y + (self.img_widget.height - dh) / 2
                        Color(1, 1, 1, 1)
                        Rectangle(texture=img, pos=(dx, dy), size=(dw, dh))
                except Exception as e:
                    Color(0.5, 0.5, 0.5, 0.5)
                    Label(text='Ошибка загрузки')
            else:
                # Пустое место с подсказкой
                Color(0.4, 0.4, 0.5, 0.3)
                cx, cy = self.img_widget.center
                s = min(self.img_widget.width, self.img_widget.height) * 0.15
                Ellipse(pos=(cx-s, cy-s), size=(s*2, s*2))
                Color(0.4, 0.4, 0.5, 0.5)
                Line(points=[cx, cy-s*0.5, cx, cy+s*0.5], width=3)
                Line(points=[cx-s*0.5, cy, cx+s*0.5, cy], width=3)
    
    def load_image(self, *args):
        app = App.get_running_app()
        app.pending_action = ('card_edit_load', (self.row, self.col))
        app.show_file_chooser('load_image')
    
    def confirm(self, *args):
        app = App.get_running_app()
        cell = app.array_data.get_cell(self.row, self.col)
        cell.title = self.name_input.text
        # Возврат к сетке
        app.sm.get_screen('grid_view').refresh_grid()
        app.sm.current = 'grid_view'
    
    def go_back(self):
        app = App.get_running_app()
        app.sm.get_screen('grid_view').refresh_grid()
        app.sm.current = 'grid_view'


# ========== Виджет просмотра изображения с мультитач ==========
class ImageViewportWidget(Widget):
    """Виджет для просмотра изображения с зумом, панорамированием и свайпами"""
    
    def __init__(self, view_screen, **kwargs):
        super().__init__(**kwargs)
        self.view_screen = view_screen
        self.texture = None
        self.img_width = 0
        self.img_height = 0
        
        # Viewport: центр в координатах изображения и масштаб
        self.view_x = 0.0  # центр viewport по X в координатах изображения
        self.view_y = 0.0  # центр viewport по Y в координатах изображения
        self.zoom = 1.0
        
        # Трекинг касаний
        self.touches = {}  # id -> (x, y)
        self.pinch_initial_dist = 0
        self.pinch_initial_zoom = 1.0
        self.pinch_center_img = None  # центр между пальцами в координатах изображения
        self.pan_initial_mid = None
        self.pan_initial_view = None
        self.swipe_start = None
        self.swipe_moved = False
        
        # Для определения свайпа
        self.swipe_threshold = 50
        
        self.bind(pos=self.redraw, size=self.redraw)
    
    def load_image(self, path):
        if path and os.path.exists(path):
            try:
                from kivy.core.image import Image as CoreImage
                self.texture = CoreImage(path).texture
                self.img_width = self.texture.width
                self.img_height = self.texture.height
                return True
            except:
                pass
        self.texture = None
        self.img_width = 0
        self.img_height = 0
        return False
    
    def set_viewport(self, cx, cy, zoom):
        self.view_x = cx
        self.view_y = cy
        self.zoom = zoom
        self.redraw()
    
    def screen_to_img(self, sx, sy):
        """Преобразование экранных координат в координаты изображения"""
        dw = self.width
        dh = self.height
        # Размер видимой области в координатах изображения
        vis_w = dw / self.zoom
        vis_h = dh / self.zoom
        # Левый верхний угол viewport в координатах изображения
        left = self.view_x - vis_w / 2
        top = self.view_y + vis_h / 2
        # Экранные координаты относительно центра
        rx = sx - self.x - dw / 2
        ry = sy - self.y - dh / 2
        ix = self.view_x + rx / self.zoom
        iy = self.view_y - ry / self.zoom
        return ix, iy
    
    def img_to_screen(self, ix, iy):
        """Преобразование координат изображения в экранные"""
        rx = (ix - self.view_x) * self.zoom
        ry = (iy - self.view_y) * self.zoom
        sx = self.x + self.width / 2 + rx
        sy = self.y + self.height / 2 - ry
        return sx, sy
    
    def fit_viewport(self):
        """Подгонка viewport для отображения всего изображения"""
        if self.img_width == 0 or self.img_height == 0:
            return
        self.view_x = self.img_width / 2
        self.view_y = self.img_height / 2
        zx = self.width / self.img_width
        zy = self.height / self.img_height
        self.zoom = min(zx, zy) * 0.9
        self.redraw()
    
    def redraw(self, *args):
        self.canvas.clear()
        if not self.texture:
            with self.canvas:
                Color(0.08, 0.08, 0.12, 1)
                Rectangle(pos=self.pos, size=self.size)
            return
        
        dw = self.width
        dh = self.height
        # Размер видимой области в координатах изображения
        vis_w = dw / self.zoom
        vis_h = dh / self.zoom
        
        with self.canvas:
            # Тёмный фон
            Color(0.08, 0.08, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Вычисляем позицию и размер изображения на экране
            sx, sy = self.img_to_screen(0, self.img_height)
            screen_w = self.img_width * self.zoom
            screen_h = self.img_height * self.zoom
            
            Color(1, 1, 1, 1)
            Rectangle(texture=self.texture, pos=(sx, sy), size=(screen_w, screen_h))
        
        # Рисуем дополнительные слои (комментарии и т.д.)
        self.view_screen.draw_overlays()
    
    def on_touch_down(self, touch):
        self.touches[touch.id] = (touch.x, touch.y)
        
        if len(self.touches) == 1:
            self.swipe_start = (touch.x, touch.y)
            self.swipe_moved = False
        elif len(self.touches) == 2:
            # Два пальца — зум и пан
            self.swipe_start = None
            ids = list(self.touches.keys())
            t1 = self.touches[ids[0]]
            t2 = self.touches[ids[1]]
            self.pinch_initial_dist = Vector(t1).distance(t2)
            self.pinch_initial_zoom = self.zoom
            
            # Центр между пальцами в координатах изображения
            mid_x = (t1[0] + t2[0]) / 2
            mid_y = (t1[1] + t2[1]) / 2
            self.pinch_center_img = self.screen_to_img(mid_x, mid_y)
            
            self.pan_initial_mid = (mid_x, mid_y)
            self.pan_initial_view = (self.view_x, self.view_y)
        
        return True
    
    def on_touch_move(self, touch):
        if touch.id in self.touches:
            self.touches[touch.id] = (touch.x, touch.y)
        
        if len(self.touches) >= 2:
            # Двухпальцевые жесты: зум + пан
            ids = list(self.touches.keys())
            t1 = self.touches[ids[0]]
            t2 = self.touches[ids[1]]
            dist = Vector(t1).distance(t2)
            
            if self.pinch_initial_dist > 0:
                # Центр экрана
                scx = self.x + self.width / 2
                scy = self.y + self.height / 2
                
                # Текущий центр между пальцами на экране
                mid_x = (t1[0] + t2[0]) / 2
                mid_y = (t1[1] + t2[1]) / 2
                
                # Смещение центра пальцев относительно начального положения
                pan_dx = mid_x - self.pan_initial_mid[0]
                pan_dy = mid_y - self.pan_initial_mid[1]
                
                # Новый масштаб
                scale = dist / self.pinch_initial_dist
                new_zoom = max(0.1, min(self.pinch_initial_zoom * scale, 50.0))
                self.zoom = new_zoom
                
                # Viewport = точка под начальным центром пальцев + смещение от пана
                # Минус смещение от зума (точка под центром пальцев должна остаться на месте)
                self.view_x = self.pinch_center_img[0] + pan_dx / self.zoom - (mid_x - scx) / self.zoom
                self.view_y = self.pinch_center_img[1] - pan_dy / self.zoom + (mid_y - scy) / self.zoom
                # Упрощаем: точка pinch_center_img должна быть под начальной позицией пальцев
                # + смещение пана
                self.view_x = self.pinch_center_img[0] + pan_dx / self.zoom
                self.view_y = self.pinch_center_img[1] - pan_dy / self.zoom
            
            self.redraw()
            self.view_screen.save_viewport_state()
        elif len(self.touches) == 1 and self.swipe_start:
            dx = touch.x - self.swipe_start[0]
            dy = touch.y - self.swipe_start[1]
            if abs(dx) > 5 or abs(dy) > 5:
                self.swipe_moved = True
        
        return True
    
    def on_touch_up(self, touch):
        if touch.id in self.touches:
            del self.touches[touch.id]
        
        if len(self.touches) == 0 and self.swipe_start and self.swipe_moved:
            # Определяем свайп
            dx = touch.x - self.swipe_start[0]
            dy = touch.y - self.swipe_start[1]
            
            if abs(dx) > abs(dy):
                # Горизонтальный свайп — листание по столбцам
                if abs(dx) > self.swipe_threshold:
                    if dx < 0:
                        self.view_screen.next_col()
                    else:
                        self.view_screen.prev_col()
            else:
                # Вертикальный свайп — листание по строкам
                if abs(dy) > self.swipe_threshold:
                    if dy < 0:
                        self.view_screen.next_row()
                    else:
                        self.view_screen.prev_row()
            
            self.swipe_start = None
            self.swipe_moved = False
        elif len(self.touches) == 1:
            # Остался один палец — обновляем состояние для возможного свайпа
            ids = list(self.touches.keys())
            self.swipe_start = self.touches[ids[0]]
            self.swipe_moved = False
        
        return True


# ========== Экран режима просмотра ==========
class ViewModeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'view_mode'
        self.mode = 'view'  # 'view', 'common_point', 'comment_place', 'comment_edit'
        self.eye_mode = 0  # 0=closed, 1=open narrow, 2=open wide
        self.flashlight_on = False
        self.current_row = 0
        self.current_col = 0
        self.comment_circle = None  # {x, y, size} — текущий размещаемый кружок
        self.editing_comment_idx = -1
        self.build_ui()
    
    def build_ui(self):
        self.layout = FloatLayout()
        
        with self.layout.canvas.before:
            Color(0, 0, 0, 1)
            Rectangle(pos=self.pos, size=self.size)
        
        # Виджет просмотра изображения
        self.image_view = ImageViewportWidget(self)
        self.layout.add_widget(self.image_view)
        
        # Верхняя панель с иконками
        # Кнопка возврата (верхний левый угол)
        self.back_btn = BackButton(callback=self.go_back)
        self.layout.add_widget(self.back_btn)
        
        # Иконка фонарика (по центру сверху)
        self.flashlight_btn = IconButton(icon_type='flashlight')
        self.flashlight_btn.bind(on_touch_down=self.on_flashlight_touch)
        self.layout.add_widget(self.flashlight_btn)
        
        # Иконка контекстного меню (правый верхний угол)
        self.menu_btn = IconButton(icon_type='menu')
        self.menu_btn.bind(on_press=self.show_context_menu)
        self.layout.add_widget(self.menu_btn)
        
        # Иконка глаза (нижний левый угол)
        self.eye_btn = IconButton(icon_type='eye_closed')
        self.eye_btn.bind(on_touch_down=self.on_eye_touch)
        self.layout.add_widget(self.eye_btn)
        
        # Иконка подтверждения (появляется в спецрежимах, нижний левый угол)
        self.confirm_btn = IconButton(icon_type='check')
        self.confirm_btn.bind(on_press=self.on_confirm_mode)
        self.confirm_btn.opacity = 0
        self.layout.add_widget(self.confirm_btn)
        
        # Иконка удаления (в режиме редактирования комментария)
        self.delete_btn = IconButton(icon_type='delete')
        self.delete_btn.bind(on_press=self.on_delete_comment)
        self.delete_btn.opacity = 0
        self.layout.add_widget(self.delete_btn)
        
        # Слои для кружков комментариев и мерцающего кружка
        self.overlay_widget = Widget()
        self.overlay_widget.bind(pos=self.draw_overlays, size=self.draw_overlays)
        self.layout.add_widget(self.overlay_widget)
        
        # Поле ввода комментария (скрытое)
        self.comment_input_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.8, None),
            height=160,
            pos_hint={'center_x': 0.5, 'bottom': 0.1},
            spacing=10
        )
        self.comment_input_layout.opacity = 0
        
        comment_title_label = Label(text='Название:', font_size=14, color=COLOR_TEXT, size_hint=(1, None), height=20)
        self.comment_input_layout.add_widget(comment_title_label)
        self.comment_title_input = TextInput(hint_text='Короткое название', font_size=16, multiline=False, 
                                              size_hint=(1, None), height=40, background_color=COLOR_BTN)
        self.comment_input_layout.add_widget(self.comment_title_input)
        
        self.comment_text_input = TextInput(hint_text='Текст комментария', font_size=16, multiline=True,
                                             size_hint=(1, None), height=70, background_color=COLOR_BTN)
        self.comment_input_layout.add_widget(self.comment_text_input)
        
        self.layout.add_widget(self.comment_input_layout)
        
        # Попап для чтения комментария
        self.read_popup = None
        
        self.add_widget(self.layout)
        self.update_icon_positions()
        # Анимация мерцания
        Clock.schedule_interval(self._animate, 1/30.0)
    
    def update_icon_positions(self):
        s = get_back_btn_size()
        ms = get_small_icon_size()
        self.back_btn.pos = (10, self.height - s - 10)
        self.menu_btn.pos = (self.width - ms - 10, self.height - ms - 10)
        self.flashlight_btn.pos = (self.width/2 - ms/2, self.height - ms - 10)
        self.eye_btn.pos = (10, 10)
        self.confirm_btn.pos = (10, 10)
        self.delete_btn.pos = (self.width - ms - 10, self.height - ms - 10)
    
    def on_size(self, *args):
        self.update_icon_positions()
        self.draw_overlays()
    
    def enter_view_mode(self, row=None, col=None):
        """Вход в режим просмотра"""
        app = App.get_running_app()
        arr = app.array_data
        if not arr:
            return
        
        if row is not None and col is not None:
            self.current_row = row
            self.current_col = col
        else:
            self.current_row = arr.current_row
            self.current_col = arr.current_col
        
        self.mode = 'view'
        self.load_current_cell()
    
    def load_current_cell(self):
        """Загрузка текущей ячейки"""
        app = App.get_running_app()
        arr = app.array_data
        cell = arr.get_cell(self.current_row, self.current_col)
        
        if not cell.image_path or not os.path.exists(cell.image_path):
            return
        
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
        
        # Копируем изображения
        import shutil
        for key, cell in self.array_data.cells.items():
            if cell.image_path and os.path.exists(cell.image_path):
                dst = os.path.join(array_dir, cell.image_filename or os.path.basename(cell.image_path))
                if os.path.abspath(cell.image_path) != os.path.abspath(dst):
                    try:
                        shutil.copy2(cell.image_path, dst)
                    except:
                        pass
                # Обновляем путь в данных
                cell.image_path = dst
        
        # Сохраняем конфиг
        config_path = os.path.join(array_dir, 'config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(self.array_data.to_json())
        
        self.array_data.config_path = config_path
        
        # Переход в режим просмотра
        self.sm.get_screen('view_mode').enter_view_mode()
        self.sm.current = 'view_mode'
    
    def show_error(self, message):
        content = BoxLayout(orientation='vertical', padding=20)
        lbl = Label(text=message, color=COLOR_TEXT)
        content.add_widget(lbl)
        btn = Button(text='OK', size_hint_y=None, height=40, background_color=COLOR_ACCENT, color=COLOR_TEXT)
        content.add_widget(btn)
        popup = Popup(title='Ошибка', content=content, size_hint=(0.7, 0.3),
                      background_color=COLOR_BG, title_color=COLOR_TEXT)
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_pause(self):
        # Сохранение состояния при сворачивании
        if self.array_data:
            self.save_state()
        return True
    
    def on_stop(self):
        # Сохранение состояния при выходе
        if self.array_data:
            self.save_state()
        self.save_settings()
    
    def save_state(self):
        """Сохранение состояния в кэш"""
        cache_path = os.path.join(os.path.expanduser('~'), '.kotlovan_cache.json')
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(self.array_data.to_json())
        except:
            pass


# ========== Точка входа ==========
if __name__ == '__main__':
    KotlovanApp().run()
