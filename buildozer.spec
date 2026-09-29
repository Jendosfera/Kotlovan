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

p4a.source = https://github.com/kivy/python-for-android.git
p4a.tag = 2024.01.13

# Ориентация
orientation = all
