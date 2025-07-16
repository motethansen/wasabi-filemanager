import os
import json

class SyncMetadata:
    SYNC_META_FILENAME = ".wasabi_sync.json"

    def __init__(self, folder):
        self.folder = folder
        self.meta_path = os.path.join(folder, self.SYNC_META_FILENAME)
        self.metadata = self.load()

    def load(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                return json.load(f)
        return {}

    def save(self):
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def get_status(self, filename):
        return self.metadata.get(filename, "both")

    def set_status(self, filename, status):
        self.metadata[filename] = status
        self.save() 