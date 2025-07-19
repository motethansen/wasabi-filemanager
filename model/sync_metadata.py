import os
import json
import hashlib
import time

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
        # Now supports 'both', 'object_storage_only', and 'no_sync'
        return self.metadata.get(filename, "both")

    def set_status(self, filename, status):
        # status can be 'both', 'object_storage_only', or 'no_sync'
        self.metadata[filename] = status
        self.save()

    def get_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        if not os.path.exists(filepath):
            return None
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def get_file_info(self, filepath):
        """Get stored file info (hash, timestamp)"""
        relpath = os.path.relpath(filepath, self.folder)
        return self.metadata.get(f"{relpath}_info", {})

    def update_file_info(self, filepath, hash_value, timestamp):
        """Update stored file info"""
        relpath = os.path.relpath(filepath, self.folder)
        self.metadata[f"{relpath}_info"] = {
            "hash": hash_value,
            "timestamp": timestamp
        }
        self.save()

    def needs_sync(self, filepath):
        """Check if file needs syncing based on hash comparison"""
        if not os.path.exists(filepath):
            return False
        
        current_hash = self.get_file_hash(filepath)
        stored_info = self.get_file_info(filepath)
        
        if not stored_info:
            return True  # New file, needs sync
        
        return current_hash != stored_info.get("hash")

    def get_sync_stats(self, folder_path):
        """Get sync statistics for a folder"""
        total_files = 0
        needs_sync_count = 0
        synced_count = 0
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                total_files += 1
                if self.needs_sync(filepath):
                    needs_sync_count += 1
                else:
                    synced_count += 1
        
        return {
            "total_files": total_files,
            "needs_sync": needs_sync_count,
            "synced": synced_count
        } 