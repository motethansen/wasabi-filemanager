from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from model.sync_metadata import SyncMetadata
from model.wasabi_client import WasabiClient
import os
import time

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
        top_bar.add_widget(Button(text="Refresh", on_press=lambda x: self.refresh_file_list()))
        top_bar.add_widget(Button(text="Wasabi Config", on_press=self.open_config))
        self.layout.add_widget(top_bar)
        self.folder_label = Label(text="No folder selected", size_hint_y=None, height=30)
        self.layout.add_widget(self.folder_label)
        self.scrollview = ScrollView(size_hint=(1, 1))
        self.file_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.file_list.bind(minimum_height=self.file_list.setter('height'))
        self.scrollview.add_widget(self.file_list)
        self.layout.add_widget(self.scrollview)
        self.current_folder = None

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
        if self.current_folder is None:
            self.current_folder = self.folder
        # Add '..' row if not at root
        if os.path.abspath(self.current_folder) != os.path.abspath(self.folder):
            row = BoxLayout(size_hint_y=None, height=30)
            up_btn = Button(text="..", size_hint_x=0.2)
            def go_up(instance):
                self.current_folder = os.path.dirname(self.current_folder)
                self.refresh_file_list()
            up_btn.bind(on_press=go_up)
            row.add_widget(up_btn)
            row.add_widget(Label(text="Go up", size_hint_x=0.8))
            self.file_list.add_widget(row)
        for fname in os.listdir(self.current_folder):
            fpath = os.path.join(self.current_folder, fname)
            is_folder = os.path.isdir(fpath)
            status = self.sync_meta.get_status(os.path.relpath(fpath, self.folder))
            label_text = f"[DIR] {fname}" if is_folder else fname
            row = BoxLayout(size_hint_y=None, height=30)
            # Folder navigation
            if is_folder:
                folder_btn = Button(text=label_text, size_hint_x=0.7)
                def make_folder_callback(fpath=fpath):
                    def callback(instance):
                        self.current_folder = fpath
                        self.refresh_file_list()
                    return callback
                folder_btn.bind(on_press=make_folder_callback())
                row.add_widget(folder_btn)
            else:
                row.add_widget(Label(text=label_text, size_hint_x=0.7))
            # Three-state toggle
            toggle_states = ["both", "object_storage_only", "no_sync"]
            toggle_labels = {"both": "Both", "object_storage_only": "Cloud Only", "no_sync": "No Sync"}
            toggle = Button(text=toggle_labels.get(status, "Both"), size_hint_x=0.3)
            def make_toggle_callback(fpath=fpath, toggle=toggle):
                def callback(instance):
                    relpath = os.path.relpath(fpath, self.folder)
                    current = self.sync_meta.get_status(relpath)
                    idx = toggle_states.index(current) if current in toggle_states else 0
                    new_status = toggle_states[(idx + 1) % len(toggle_states)]
                    toggle.text = toggle_labels[new_status]
                    self.sync_meta.set_status(relpath, new_status)
                return callback
            toggle.bind(on_press=make_toggle_callback())
            row.add_widget(toggle)
            self.file_list.add_widget(row)

    def sync_now(self, *args):
        if not self.folder or not self.sync_meta:
            self.show_popup("No folder", "Please select a folder first.")
            return
        
        # Show sync analysis popup
        stats = self.sync_meta.get_sync_stats(self.folder)
        analysis_text = f"Total files: {stats['total_files']}\nNeeds sync: {stats['needs_sync']}\nAlready synced: {stats['synced']}"
        
        # Create progress popup
        progress_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        progress_layout.add_widget(Label(text="Sync Progress", font_size=18))
        progress_layout.add_widget(Label(text=analysis_text))
        
        progress_bar = ProgressBar(max=stats['needs_sync'])
        progress_layout.add_widget(progress_bar)
        
        status_label = Label(text="Preparing sync...")
        progress_layout.add_widget(status_label)
        
        progress_popup = Popup(title="Sync Progress", content=progress_layout, size_hint=(0.8, 0.6))
        progress_popup.open()
        
        errors = []
        synced_count = 0
        health_issues = []
        
        def sync_path(path, status):
            nonlocal synced_count
            relpath = os.path.relpath(path, self.folder)
            if status == "no_sync":
                return  # Skip this file/folder and its children
            
            if os.path.isdir(path):
                for child in os.listdir(path):
                    child_path = os.path.join(path, child)
                    child_status = self.sync_meta.get_status(os.path.relpath(child_path, self.folder))
                    # Inherit parent status if child is not explicitly set to no_sync
                    if child_status == "no_sync":
                        continue
                    sync_path(child_path, status)
            elif os.path.isfile(path):
                # Only sync if file needs syncing
                if self.sync_meta.needs_sync(path):
                    try:
                        if status == "both":
                            self.client.upload_file(path, relpath)
                            # Update file info after successful upload
                            file_hash = self.sync_meta.get_file_hash(path)
                            self.sync_meta.update_file_info(path, file_hash, time.time())
                        elif status == "object_storage_only":
                            self.client.upload_file(path, relpath)
                            if os.path.exists(path):
                                os.remove(path)
                                self.sync_meta.set_status(relpath, "object_storage_only")
                            else:
                                # File was uploaded, update info
                                file_hash = self.sync_meta.get_file_hash(path)
                                self.sync_meta.update_file_info(path, file_hash, time.time())
                        
                        synced_count += 1
                        progress_bar.value = synced_count
                        status_label.text = f"Synced: {synced_count}/{stats['needs_sync']} - {relpath}"
                        
                        # Verify upload by checking hash
                        if os.path.exists(path):
                            current_hash = self.sync_meta.get_file_hash(path)
                            stored_info = self.sync_meta.get_file_info(path)
                            if stored_info and current_hash != stored_info.get("hash"):
                                health_issues.append(f"{relpath}: Hash mismatch")
                        
                    except Exception as e:
                        errors.append(f"{relpath}: {e}")
        
        # Start sync process
        for fname in os.listdir(self.folder):
            fpath = os.path.join(self.folder, fname)
            status = self.sync_meta.get_status(os.path.relpath(fpath, self.folder))
            sync_path(fpath, status)
        
        progress_popup.dismiss()
        self.refresh_file_list()
        
        # Show results
        result_text = f"Sync Complete!\nSynced: {synced_count} files"
        if errors:
            result_text += f"\nErrors: {len(errors)}"
        if health_issues:
            result_text += f"\nHealth Issues: {len(health_issues)}"
        
        self.show_popup("Sync Results", result_text)
        
        if errors:
            error_text = "Sync Errors:\n" + "\n".join(errors)
            self.show_popup("Sync Errors", error_text)
        
        if health_issues:
            health_text = "Health Issues:\n" + "\n".join(health_issues)
            self.show_popup("Health Issues", health_text)

    def open_config(self, *args):
        self.manager.current = 'wasabi_config'

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.3))
        popup.open() 