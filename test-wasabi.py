import json
import boto3
import os

CONFIG_FILE = ".wasabi_config.json"

def main():
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found: .wasabi_config.json")
        return
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=config["access_key"],
            aws_secret_access_key=config["secret_key"],
            region_name=config["region"],
            endpoint_url=config["endpoint"]
        )
        response = s3.list_buckets()
        print("Connection successful! Buckets:")
        for b in response.get('Buckets', []):
            print("-", b['Name'])
    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    main() 