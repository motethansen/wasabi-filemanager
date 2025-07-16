import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from wasabi_config import WasabiConfigDialog
import sync_metadata
import wasabi_client

class FileManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wasabi Filemanager")
        self.geometry("800x500")
        self.folder = None
        self.sync_meta = {}
        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menubar = tk.Menu(self)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Wasabi Configuration", command=self.open_wasabi_config)
        menubar.add_cascade(label="Config", menu=config_menu)
        self.config(menu=menubar)

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(top_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Sync Now", command=self.sync_now).pack(side=tk.LEFT, padx=5)
        self.folder_label = tk.Label(top_frame, text="No folder selected")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        self.tree = ttk.Treeview(self, columns=("status",), show="headings")
        self.tree.heading("status", text="Sync Status")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.toggle_sync_status)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Save Local Storage", command=self.save_local_storage)

    def open_wasabi_config(self):
        WasabiConfigDialog(self)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder = folder
            self.folder_label.config(text=folder)
            self.load_files()

    def load_files(self):
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            return
        self.sync_meta = sync_metadata.load_sync_metadata(self.folder)
        for fname in os.listdir(self.folder):
            fpath = os.path.join(self.folder, fname)
            if os.path.isfile(fpath):
                status = self.sync_meta.get(fname, "both")
                self.tree.insert("", "end", iid=fname, values=(status,))

    def toggle_sync_status(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            current = self.tree.set(item, "status")
            new_status = "object_storage_only" if current == "both" else "both"
            self.tree.set(item, "status", new_status)
            self.sync_meta[item] = new_status
            sync_metadata.save_sync_metadata(self.folder, self.sync_meta)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def save_local_storage(self):
        selected = self.tree.selection()
        if not selected:
            return
        for fname in selected:
            fpath = os.path.join(self.folder, fname)
            # Upload to Wasabi
            wasabi_client.upload_file(fpath, fname)
            # Delete local file
            os.remove(fpath)
            # Update sync status
            self.sync_meta[fname] = "object_storage_only"
        sync_metadata.save_sync_metadata(self.folder, self.sync_meta)
        self.load_files()
        messagebox.showinfo("Done", "Selected files uploaded and deleted locally.")

    def sync_now(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Please select a folder first.")
            return
        errors = []
        for fname in os.listdir(self.folder):
            fpath = os.path.join(self.folder, fname)
            if not os.path.isfile(fpath):
                continue
            status = self.sync_meta.get(fname, "both")
            try:
                if status == "both":
                    wasabi_client.upload_file(fpath, fname)
                    # File remains locally
                elif status == "object_storage_only":
                    wasabi_client.upload_file(fpath, fname)
                    if os.path.exists(fpath):
                        resp = messagebox.askyesno(
                            "Delete Local File?",
                            f"'{fname}' is set to object storage only. Delete local copy after upload?"
                        )
                        if resp:
                            os.remove(fpath)
                            self.sync_meta[fname] = "object_storage_only"
            except Exception as e:
                errors.append(f"{fname}: {e}")
        sync_metadata.save_sync_metadata(self.folder, self.sync_meta)
        self.load_files()
        if errors:
            messagebox.showerror("Sync Errors", "Some files failed to sync:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Sync Complete", "All files synced successfully.")

if __name__ == "__main__":
    app = FileManagerApp()
    app.mainloop() 