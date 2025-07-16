import os
import json

SYNC_META_FILENAME = ".wasabi_sync.json"

def load_sync_metadata(folder):
    meta_path = os.path.join(folder, SYNC_META_FILENAME)
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)
    return {}

def save_sync_metadata(folder, metadata):
    meta_path = os.path.join(folder, SYNC_META_FILENAME)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2) 