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
