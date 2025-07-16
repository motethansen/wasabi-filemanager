from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from ui.filemanager_screen import FileManagerScreen
from ui.wasabi_config_screen import WasabiConfigScreen

class WasabiFileManagerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(FileManagerScreen(name='filemanager'))
        sm.add_widget(WasabiConfigScreen(name='wasabi_config'))
        return sm

if __name__ == '__main__':
    WasabiFileManagerApp().run()
