import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import boto3
import os

CONFIG_FILE = ".wasabi_config.json"

class WasabiConfigDialog(simpledialog.Dialog):
    def __init__(self, parent):
        self.config = self.load_config()
        super().__init__(parent, title="Wasabi Configuration")

    def body(self, master):
        tk.Label(master, text="Access Key:").grid(row=0)
        tk.Label(master, text="Secret Key:").grid(row=1)
        tk.Label(master, text="Bucket Name:").grid(row=2)
        tk.Label(master, text="Region:").grid(row=3)
        tk.Label(master, text="Endpoint:").grid(row=4)

        self.access_key = tk.Entry(master, width=40)
        self.secret_key = tk.Entry(master, width=40, show="*")
        self.bucket_name = tk.Entry(master, width=40)
        self.region = tk.Entry(master, width=40)
        self.endpoint = tk.Entry(master, width=40)

        self.access_key.grid(row=0, column=1)
        self.secret_key.grid(row=1, column=1)
        self.bucket_name.grid(row=2, column=1)
        self.region.grid(row=3, column=1)
        self.endpoint.grid(row=4, column=1)

        # Load existing config
        if self.config:
            self.access_key.insert(0, self.config.get("access_key", ""))
            self.secret_key.insert(0, self.config.get("secret_key", ""))
            self.bucket_name.insert(0, self.config.get("bucket_name", ""))
            self.region.insert(0, self.config.get("region", ""))
            self.endpoint.insert(0, self.config.get("endpoint", ""))

        tk.Button(master, text="Save", command=self.save).grid(row=5, column=0)
        tk.Button(master, text="Load", command=self.load).grid(row=5, column=1)
        tk.Button(master, text="Test Connection", command=self.test_connection).grid(row=6, column=0, columnspan=2)

    def save(self):
        config = {
            "access_key": self.access_key.get(),
            "secret_key": self.secret_key.get(),
            "bucket_name": self.bucket_name.get(),
            "region": self.region.get(),
            "endpoint": self.endpoint.get(),
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        messagebox.showinfo("Saved", "Configuration saved.")

    def load(self):
        config = self.load_config()
        if config:
            self.access_key.delete(0, tk.END)
            self.secret_key.delete(0, tk.END)
            self.bucket_name.delete(0, tk.END)
            self.region.delete(0, tk.END)
            self.endpoint.delete(0, tk.END)
            self.access_key.insert(0, config.get("access_key", ""))
            self.secret_key.insert(0, config.get("secret_key", ""))
            self.bucket_name.insert(0, config.get("bucket_name", ""))
            self.region.insert(0, config.get("region", ""))
            self.endpoint.insert(0, config.get("endpoint", ""))
            messagebox.showinfo("Loaded", "Configuration loaded.")
        else:
            messagebox.showwarning("Not found", "No configuration file found.")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}

    def test_connection(self):
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=self.access_key.get(),
                aws_secret_access_key=self.secret_key.get(),
                region_name=self.region.get(),
                endpoint_url=self.endpoint.get()
            )
            s3.list_buckets()
            messagebox.showinfo("Success", "Connection successful!")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")

    def apply(self):
        # Called when dialog is closed with OK
        self.save() 