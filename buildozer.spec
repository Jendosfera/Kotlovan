[app]

# Название приложения
title = Котлован

# Пакет
package.name = kotlovan
package.domain = org.kotlovan

# Исходный код
source.dir = .
source.include_exts = py,png,jpg,jpeg,bmp,gif,json

# Версия
version = 1.0

# Требования
requirements = python3,kivy,plyer,Pillow

# Ориентация
orientation = all

# Полноэкранный режим
fullscreen = 1

# Разрешения
android.permissions = STORAGE, CAMERA, FLASHLIGHT

# API
android.api = 31
android.minapi = 21

# Архитектура
android.archs = arm64-v8a, armeabi-v7a

# Иконка (можно заменить на свою)
# android.icon = icon.png

# Buildozer
buildozer.log_level = 2
buildozer.warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
