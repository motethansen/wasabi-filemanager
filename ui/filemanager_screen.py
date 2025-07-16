from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from model.sync_metadata import SyncMetadata
from model.wasabi_client import WasabiClient
import os

class FileManagerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder = None
        self.sync_meta = None
        self.client = WasabiClient()
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)
        top_bar = BoxLayout(size_hint_y=None, height=40, spacing=10)
        top_bar.add_widget(Button(text="Select Folder", on_press=self.select_folder))
        top_bar.add_widget(Button(text="Sync Now", on_press=self.sync_now))
        top_bar.add_widget(Button(text="Wasabi Config", on_press=self.open_config))
        self.layout.add_widget(top_bar)
        self.folder_label = Label(text="No folder selected", size_hint_y=None, height=30)
        self.layout.add_widget(self.folder_label)
        self.file_list = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.file_list)

    def select_folder(self, *args):
        chooser = FileChooserIconView(dirselect=True)
        box = BoxLayout(orientation='vertical')
        box.add_widget(chooser)
        btn = Button(text="Select Folder", size_hint_y=None, height=40)
        box.add_widget(btn)
        popup = Popup(title="Select Folder", content=box, size_hint=(0.9, 0.9))

        def on_select(instance):
            if chooser.selection:
                selected = chooser.selection[0]
                if os.path.isdir(selected):
                    self.folder = selected
                    self.folder_label.text = self.folder
                    self.sync_meta = SyncMetadata(self.folder)
                    self.refresh_file_list()
                    popup.dismiss()
        btn.bind(on_press=on_select)
        popup.open()

    def refresh_file_list(self):
        self.file_list.clear_widgets()
        if not self.folder:
            return
        for fname in os.listdir(self.folder):
            fpath = os.path.join(self.folder, fname)
            if os.path.isfile(fpath):
                status = self.sync_meta.get_status(fname)
                row = BoxLayout(size_hint_y=None, height=30)
                row.add_widget(Label(text=fname))
                toggle = Button(text="Cloud Only" if status=="object_storage_only" else "Both")
                def make_toggle_callback(fname=fname, toggle=toggle):
                    def callback(instance):
                        new_status = "object_storage_only" if toggle.text=="Both" else "both"
                        toggle.text = "Cloud Only" if new_status=="object_storage_only" else "Both"
                        self.sync_meta.set_status(fname, new_status)
                    return callback
                toggle.bind(on_press=make_toggle_callback())
                row.add_widget(toggle)
                self.file_list.add_widget(row)

    def sync_now(self, *args):
        if not self.folder or not self.sync_meta:
            self.show_popup("No folder", "Please select a folder first.")
            return
        errors = []
        for fname in os.listdir(self.folder):
            fpath = os.path.join(self.folder, fname)
            if not os.path.isfile(fpath):
                continue
            status = self.sync_meta.get_status(fname)
            try:
                if status == "both":
                    self.client.upload_file(fpath, fname)
                elif status == "object_storage_only":
                    self.client.upload_file(fpath, fname)
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        self.sync_meta.set_status(fname, "object_storage_only")
            except Exception as e:
                errors.append(f"{fname}: {e}")
        self.refresh_file_list()
        if errors:
            self.show_popup("Sync Errors", "Some files failed to sync:\n" + "\n".join(errors))
        else:
            self.show_popup("Sync Complete", "All files synced successfully.")

    def open_config(self, *args):
        self.manager.current = 'wasabi_config'

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.3))
        popup.open() 