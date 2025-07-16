import boto3
import json
import os
from tkinter import messagebox

CONFIG_FILE = ".wasabi_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def upload_file(filepath, filename):
    config = load_config()
    if not config:
        messagebox.showerror("Config Error", "Wasabi config not found.")
        return
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=config["access_key"],
            aws_secret_access_key=config["secret_key"],
            region_name=config["region"],
            endpoint_url=config["endpoint"]
        )
        s3.upload_file(filepath, config["bucket_name"], filename)
    except Exception as e:
        messagebox.showerror("Upload Error", f"Failed to upload {filename}: {e}") 