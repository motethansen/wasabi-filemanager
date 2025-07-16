import boto3
import json
import os

class WasabiClient:
    CONFIG_FILE = ".wasabi_config.json"

    def __init__(self):
        self.config = self.load_config()
        self.s3 = self.create_client() if self.config else None

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                return json.load(f)
        return None

    def create_client(self):
        cfg = self.config
        return boto3.client(
            's3',
            aws_access_key_id=cfg["access_key"],
            aws_secret_access_key=cfg["secret_key"],
            region_name=cfg["region"],
            endpoint_url=cfg["endpoint"]
        )

    def upload_file(self, filepath, filename):
        if not self.s3:
            raise Exception("Wasabi config not loaded.")
        self.s3.upload_file(filepath, self.config["bucket_name"], filename) 