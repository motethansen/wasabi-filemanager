from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import json
import os
from model.wasabi_client import WasabiClient

class WasabiConfigScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.layout)
        self.layout.add_widget(Label(text="Wasabi Configuration", font_size=24))
        self.access_key = TextInput(hint_text="Access Key")
        self.secret_key = TextInput(hint_text="Secret Key", password=True)
        self.bucket_name = TextInput(hint_text="Bucket Name")
        self.region = TextInput(hint_text="Region")
        self.endpoint = TextInput(hint_text="Endpoint")
        self.layout.add_widget(self.access_key)
        self.layout.add_widget(self.secret_key)
        self.layout.add_widget(self.bucket_name)
        self.layout.add_widget(self.region)
        self.layout.add_widget(self.endpoint)
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_layout.add_widget(Button(text="Save", on_press=self.save))
        btn_layout.add_widget(Button(text="Load", on_press=self.load))
        btn_layout.add_widget(Button(text="Test Connection", on_press=self.test_connection))
        self.layout.add_widget(btn_layout)
        self.load()

    def save(self, *args):
        config = {
            "access_key": self.access_key.text.strip(),
            "secret_key": self.secret_key.text.strip(),
            "bucket_name": self.bucket_name.text.strip(),
            "region": self.region.text.strip(),
            "endpoint": self.endpoint.text.strip(),
        }
        with open(WasabiClient.CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        self.show_popup("Saved", "Configuration saved.")

    def load(self, *args):
        if os.path.exists(WasabiClient.CONFIG_FILE):
            with open(WasabiClient.CONFIG_FILE, "r") as f:
                config = json.load(f)
            self.access_key.text = config.get("access_key", "")
            self.secret_key.text = config.get("secret_key", "")
            self.bucket_name.text = config.get("bucket_name", "")
            self.region.text = config.get("region", "")
            self.endpoint.text = config.get("endpoint", "")
            self.show_popup("Loaded", "Configuration loaded.")
        else:
            self.show_popup("Not found", "No configuration file found.")

    def test_connection(self, *args):
        try:
            client = WasabiClient()
            if not client.s3:
                raise Exception("Config not loaded.")
            resp = client.s3.list_buckets()
            self.show_popup("Success", "Connection successful! Buckets: " + ", ".join([b['Name'] for b in resp.get('Buckets', [])]))
        except Exception as e:
            self.show_popup("Error", f"Connection failed: {e}")

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.3))
        popup.open() 