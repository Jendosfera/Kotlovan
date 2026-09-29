from kivy.app import App
from kivy.uix.label import Label

class KotlovanApp(App):
    def build(self):
        return Label(text="Котлован", font_size=48)

if __name__ == '__main__':
    KotlovanApp().run()
