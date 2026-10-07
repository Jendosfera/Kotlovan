[app]
title = Котлован
package.name = kotlovan
package.domain = com.kotlovan

source.dir = .
source.name = main

version = 1.0

requirements = python3,kivy,plyer,Pillow

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 31
android.minapi = 21
android.arch = arm64-v8a, armeabi-v7a

# Зафиксировать версию python-for-android

p4a.branch = v2024.01.21

# Ориентация
orientation = all
