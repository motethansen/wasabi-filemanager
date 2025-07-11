import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import boto3
import keyring
import tempfile
import re
import json
import ssl
import logging
import socket
from pathlib import Path
from datetime import datetime

# --- Constants and Config ---
DB_FILE = 'wasabi_users.db'
BOOKMARKS_FILE = 'bookmarks.json'
CONFIG_FILE = 'app_config.json'
LOG_FILE = 'app.log'
SERVICE_NAME = 'WasabiFileManager'

# --- Logging Setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f'App started on {sys.platform} with Python {sys.version}')

# --- Secure Credential Storage with Keyring ---
def store_credential(profile_name, access_key, secret_key):
    keyring.set_password(SERVICE_NAME, f'{profile_name}_access', access_key)
    keyring.set_password(SERVICE_NAME, f'{profile_name}_secret', secret_key)

def get_credential(profile_name):
    access_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_access')
    secret_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_secret')
    return access_key, secret_key

def delete_credential(profile_name):
    keyring.delete_password(SERVICE_NAME, f'{profile_name}_access')
    keyring.delete_password(SERVICE_NAME, f'{profile_name}_secret')

# --- Input Validation ---
def validate_bucket_name(name):
    return bool(re.match(r'^[a-z0-9.-]{3,63}$', name))

def validate_profile_name(name):
    return bool(re.match(r'^[\w\- ]{1,50}$', name))

def validate_path(path):
    p = Path(path).resolve()
    base = Path.cwd().resolve()
    try:
        p.relative_to(base)
        return True
    except ValueError:
        return False

# --- SSL/TLS Verification ---
def get_s3_client(access_key, secret_key, endpoint_url, verify_ssl=True, ca_file=None):
    # Determine region from endpoint URL
    region = 'us-east-1'  # Default region
    if 'ap-southeast-1' in endpoint_url:
        region = 'ap-southeast-1'
    elif 'us-west-1' in endpoint_url:
        region = 'us-west-1'
    elif 'eu-central-1' in endpoint_url:
        region = 'eu-central-1'
    elif 'ap-northeast-1' in endpoint_url:
        region = 'ap-northeast-1'
    
    session = boto3.session.Session()
    return session.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        region_name=region,
        verify=ca_file if ca_file else verify_ssl
    )

# --- Network/Offline Detection ---
def is_online(host='8.8.8.8', port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

# --- Retry Decorator ---
def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f'Retry {attempt+1}/{max_retries} failed: {e}')
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(delay)
        return wrapper
    return decorator

# --- Configuration Management ---
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {
            'ui': {'theme': 'default', 'default_download_folder': '', 'default_upload_folder': ''},
            'profiles': [],
            'last_profile': None,
            'ssl': {'verify': True, 'ca_file': ''}
        }

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

# --- Main Application ---
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Wasabi S3 File Manager')
        self.geometry('1000x600')
        self.user_id = None
        self.bucket_id = None
        self.s3 = None
        self.current_bucket = None
        self.current_prefix = ''
        self.buckets = []
        self.advanced_search_filters = {}
        self.bookmarks = []
        self.load_bookmarks()
        self.config_data = load_config()
        self.create_menu()
        self.create_toolbar()
        self.create_main_panes()
        self.create_statusbar()
        self.setup_drag_and_drop()
        self.show_login()

    # --- Menu Bar ---
    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)
        editmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=editmenu)
        viewmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='View', menu=viewmenu)
        toolsmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Tools', menu=toolsmenu)
        bookmarks_menu = tk.Menu(menubar, tearoff=0)
        bookmarks_menu.add_command(label='Manage Bookmarks', command=self.show_bookmarks_dialog)
        self.bookmarks_menu = bookmarks_menu
        menubar.add_cascade(label='Bookmarks', menu=bookmarks_menu)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label='Preferences', command=self.show_preferences_dialog)
        settings_menu.add_command(label='Manage Connection Profiles', command=self.show_profiles_dialog)
        settings_menu.add_command(label='Import Config', command=self.import_config)
        settings_menu.add_command(label='Export Config', command=self.export_config)
        menubar.add_cascade(label='Settings', menu=settings_menu)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'Wasabi S3 File Manager'))
        menubar.add_cascade(label='Help', menu=helpmenu)
        self.config(menu=menubar)

    # --- Toolbar ---
    def create_toolbar(self):
        toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)
        self.bucket_var = tk.StringVar()
        self.bucket_combo = ttk.Combobox(toolbar, textvariable=self.bucket_var, state='readonly', width=30)
        self.bucket_combo.pack(side='left', padx=5)
        self.bucket_combo.bind('<<ComboboxSelected>>', lambda e: self.on_bucket_select())
        tk.Button(toolbar, text='Upload', command=self.upload_file).pack(side='left', padx=2)
        tk.Button(toolbar, text='Download', command=self.download_file).pack(side='left', padx=2)
        tk.Button(toolbar, text='Delete', command=self.delete_file).pack(side='left', padx=2)
        tk.Button(toolbar, text='New Folder', command=self.create_folder).pack(side='left', padx=2)
        tk.Button(toolbar, text='Bookmark', command=self.add_bookmark).pack(side='left', padx=2)
        tk.Label(toolbar, text='Search:').pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side='left', padx=2)
        tk.Button(toolbar, text='Go', command=self.search_files).pack(side='left', padx=2)
        tk.Button(toolbar, text='Filters', command=self.show_search_filter_dialog).pack(side='left', padx=2)
        toolbar.pack(side='top', fill='x')

    # --- Main Panes (Tree + File List) ---
    def create_main_panes(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        # Tree view (left)
        tree_frame = tk.Frame(main_pane)
        self.tree = ttk.Treeview(tree_frame, columns=('fullpath',), show='tree')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_expand)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        main_pane.add(tree_frame, minsize=200)
        # File list (right)
        file_frame = tk.Frame(main_pane)
        self.file_list = ttk.Treeview(file_frame, columns=('Name', 'Size', 'Modified'), show='headings', selectmode='extended')
        self.file_list.heading('Name', text='Name')
        self.file_list.heading('Size', text='Size')
        self.file_list.heading('Modified', text='Modified')
        self.file_list.column('Name', width=300)
        self.file_list.column('Size', width=100, anchor='e')
        self.file_list.column('Modified', width=180)
        self.file_list.pack(fill='both', expand=True)
        self.file_list.bind('<Button-3>', self.show_file_context_menu)
        main_pane.add(file_frame, minsize=400)
        main_pane.pack(fill='both', expand=True)
        # Progress bar
        self.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.progress.pack(side='bottom', fill='x')

    # --- Status Bar ---
    def create_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_var.set('Not connected')
        statusbar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w')
        statusbar.pack(side='bottom', fill='x')

    # --- Login/Profile Selection ---
    def show_login(self):
        login_win = tk.Toplevel(self)
        login_win.title('Login')
        login_win.geometry('300x200')
        login_win.transient(self)
        login_win.grab_set()
        tk.Label(login_win, text='Select Profile').pack(pady=10)
        profile_combo = ttk.Combobox(login_win, state='readonly')
        profile_combo.pack()
        profiles = [p['name'] for p in self.config_data.get('profiles', [])]
        profile_combo['values'] = profiles
        tk.Button(login_win, text='Login', command=lambda: self.login(profile_combo.get(), login_win)).pack(pady=5)
        tk.Button(login_win, text='Add Profile', command=lambda: self.add_profile(login_win, profile_combo)).pack(pady=5)

    def login(self, profile, win):
        if not profile:
            messagebox.showerror('Error', 'Please select a profile.')
            return
        self.user_id = 1  # For demo, single user
        win.destroy()
        self.load_buckets()

    def add_profile(self, win, combo):
        name = simpledialog.askstring('Add Profile', 'Enter profile name:', parent=win)
        if not name or not validate_profile_name(name):
            messagebox.showerror('Error', 'Invalid profile name.')
            return
        ak = simpledialog.askstring('Access Key', 'Enter Wasabi access key:', parent=win)
        sk = simpledialog.askstring('Secret Key', 'Enter Wasabi secret key:', parent=win, show='*')
        if not ak or not sk:
            messagebox.showerror('Error', 'Access and Secret Key required.')
            return
        store_credential(name, ak, sk)
        profile = {
            'name': name,
            'endpoint_url': 'https://s3.wasabisys.com',
            'ssl_verify': True,
            'ca_file': ''
        }
        self.config_data['profiles'].append(profile)
        save_config(self.config_data)
        combo['values'] = [p['name'] for p in self.config_data['profiles']]

    # --- Bucket Management ---
    def load_buckets(self):
        # Use bucket_name from profiles
        self.buckets = [p.get('bucket_name', '') for p in self.config_data.get('profiles', []) if p.get('bucket_name')]
        self.bucket_combo['values'] = self.buckets
        if self.buckets:
            self.bucket_combo.current(0)
            self.on_bucket_select()
        else:
            self.status_var.set('No buckets configured. Add one via Settings.')

    def on_bucket_select(self):
        bucket = self.bucket_combo.get()
        if not bucket:
            return
        # Find profile by bucket_name
        profile = next((p for p in self.config_data['profiles'] if p.get('bucket_name') == bucket), None)
        if not profile:
            self.status_var.set('Profile not found.')
            return
        pname = profile['name']
        access_key, secret_key = get_credential(pname)
        endpoint_url = profile.get('endpoint_url', 'https://s3.wasabisys.com')
        verify_ssl = profile.get('ssl_verify', True)
        ca_file = profile.get('ca_file', None)
        self.s3 = get_s3_client(access_key, secret_key, endpoint_url, verify_ssl, ca_file)
        self.current_bucket = bucket
        self.current_prefix = ''
        self.status_var.set(f'Connected to {bucket}')
        self.populate_tree()
        self.populate_file_list()
        self.update_bookmarks_menu()

    # --- Tree View (Folder Navigation) ---
    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        root_id = self.tree.insert('', 'end', text=self.current_bucket, values=('',), open=True)
        self.populate_tree_level(root_id, '')

    def populate_tree_level(self, parent_id, prefix):
        if not self.s3:
            return
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.current_bucket, Prefix=prefix, Delimiter='/'):
                for cp in page.get('CommonPrefixes', []):
                    folder = cp['Prefix']
                    folder_name = folder[len(prefix):].rstrip('/')
                    if folder_name is None:
                        folder_name = ''
                    node_id = self.tree.insert(parent_id, 'end', text=str(folder_name), values=(folder,))
                    self.tree.insert(node_id, 'end', text='...', values=('DUMMY',))
        except Exception as e:
            pass

    def on_tree_expand(self, event):
        item_id = self.tree.focus()
        prefix = self.tree.item(item_id, 'values')[0]
        for child in self.tree.get_children(item_id):
            if self.tree.item(child, 'values')[0] == 'DUMMY':
                self.tree.delete(child)
        self.populate_tree_level(item_id, prefix)

    def on_tree_select(self, event):
        item_id = self.tree.focus()
        prefix = self.tree.item(item_id, 'values')[0]
        self.current_prefix = prefix
        self.populate_file_list()

    # --- File List View (with threading, lazy loading, caching) ---
    @retry_on_failure(max_retries=3, delay=2)
    def safe_list_objects(self, **kwargs):
        return self.s3.list_objects_v2(**kwargs)

    def populate_file_list(self):
        self.file_list.delete(*self.file_list.get_children())
        if not self.s3:
            return
        if not is_online():
            self.status_var.set('Offline mode: No network connection.')
            logger.error('Offline mode detected.')
            return
        def load_files():
            try:
                response = self.safe_list_objects(Bucket=self.current_bucket, Prefix=self.current_prefix, Delimiter='/', MaxKeys=1000)
                for obj in response.get('Contents', []):
                    key = obj['Key']
                    if key == self.current_prefix:
                        continue
                    name = key[len(self.current_prefix):]
                    if '/' in name:
                        continue
                    size = obj['Size']
                    mtime = obj.get('LastModified')
                    mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S') if mtime else ''
                    self.file_list.insert('', 'end', values=(str(name), size, mtime_str))
            except Exception as e:
                self.status_var.set(f'Error: {str(e)}')
                logger.error(f'File list error: {e}')
        threading.Thread(target=load_files).start()

    # --- Toolbar Operations (threaded, progress, validation) ---
    @retry_on_failure(max_retries=3, delay=2)
    def safe_upload_file(self, *args, **kwargs):
        return self.s3.upload_file(*args, **kwargs)

    def upload_file(self):
        if not self.s3 or not self.current_bucket:
            return
        file_paths = filedialog.askopenfilenames()
        if not file_paths:
            return
        file_paths = [Path(p) for p in file_paths]
        self.progress['value'] = 0
        self.progress['maximum'] = len(file_paths)
        def do_upload():
            for idx, file_path in enumerate(file_paths, 1):
                file_name = file_path.name
                key = self.current_prefix + file_name
                if not validate_path(file_path):
                    self.status_var.set(f'Invalid file path: {file_path}')
                    continue
                try:
                    self.safe_upload_file(str(file_path), self.current_bucket, key, Callback=lambda bytes_transferred: self.update_progress(idx, len(file_paths), file_name, bytes_transferred, file_path.stat().st_size))
                    self.status_var.set(f'Uploaded {file_name}')
                    logger.info(f'Uploaded {file_name} to {self.current_bucket}/{key}')
                except Exception as e:
                    self.status_var.set(f'Upload failed: {str(e)}')
                    logger.error(f'Upload failed for {file_name}: {e}')
                self.progress['value'] = idx
            self.populate_file_list()
        threading.Thread(target=do_upload).start()

    @retry_on_failure(max_retries=3, delay=2)
    def safe_download_file(self, *args, **kwargs):
        return self.s3.download_file(*args, **kwargs)

    def download_file(self):
        if not self.s3 or not self.current_bucket:
            return
        selections = self.file_list.selection()
        if not selections:
            return
        self.progress['value'] = 0
        self.progress['maximum'] = len(selections)
        def do_download():
            for idx, sel in enumerate(selections, 1):
                name = self.file_list.item(sel, 'values')[0]
                key = self.current_prefix + name
                save_path = filedialog.asksaveasfilename(initialfile=name)
                if not save_path or not validate_path(save_path):
                    continue
                save_path = Path(save_path)
                try:
                    self.safe_download_file(self.current_bucket, key, str(save_path), Callback=lambda bytes_transferred: self.update_progress(idx, len(selections), name, bytes_transferred, 1))
                    self.status_var.set(f'Downloaded {name}')
                    logger.info(f'Downloaded {name} from {self.current_bucket}/{key}')
                except Exception as e:
                    self.status_var.set(f'Download failed: {str(e)}')
                    logger.error(f'Download failed for {name}: {e}')
                self.progress['value'] = idx
        threading.Thread(target=do_download).start()

    # --- Bookmarks, Preferences, Profiles, and More ---
    def load_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, 'r') as f:
                self.bookmarks = json.load(f)
        except Exception:
            self.bookmarks = []

    def show_bookmarks_dialog(self):
        self.load_bookmarks()
        win = tk.Toplevel(self)
        win.title('Manage Bookmarks')
        listbox = tk.Listbox(win, width=60)
        for bm in self.bookmarks:
            listbox.insert('end', f'{bm["name"]} ({bm["bucket"]}:{bm["prefix"]})' if 'bucket' in bm and 'prefix' in bm else bm.get('name', ''))
        listbox.pack(padx=10, pady=10)
        def delete_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            del self.bookmarks[idx]
            with open(BOOKMARKS_FILE, 'w') as f:
                json.dump(self.bookmarks, f)
            win.destroy()
            self.update_bookmarks_menu()
        tk.Button(win, text='Delete Selected', command=delete_selected).pack(pady=5)

    def show_preferences_dialog(self):
        win = tk.Toplevel(self)
        win.title('Preferences')
        theme_var = tk.StringVar(value=self.config_data['ui'].get('theme', 'default'))
        tk.Label(win, text='Theme:').grid(row=0, column=0, sticky='e')
        theme_entry = tk.Entry(win, textvariable=theme_var)
        theme_entry.grid(row=0, column=1)
        tk.Label(win, text='Default Download Folder:').grid(row=1, column=0, sticky='e')
        download_var = tk.StringVar(value=self.config_data['ui'].get('default_download_folder', ''))
        download_entry = tk.Entry(win, textvariable=download_var, width=30)
        download_entry.grid(row=1, column=1)
        tk.Label(win, text='Default Upload Folder:').grid(row=2, column=0, sticky='e')
        upload_var = tk.StringVar(value=self.config_data['ui'].get('default_upload_folder', ''))
        upload_entry = tk.Entry(win, textvariable=upload_var, width=30)
        upload_entry.grid(row=2, column=1)
        def save_prefs():
            self.config_data['ui']['theme'] = theme_var.get()
            self.config_data['ui']['default_download_folder'] = download_var.get()
            self.config_data['ui']['default_upload_folder'] = upload_var.get()
            save_config(self.config_data)
            win.destroy()
        tk.Button(win, text='Save', command=save_prefs).grid(row=3, column=0, columnspan=2, pady=8)

    def show_profiles_dialog(self):
        win = tk.Toplevel(self)
        win.title('Connection Profiles')
        profiles = self.config_data.get('profiles', [])
        listbox = tk.Listbox(win, width=60)
        for p in profiles:
            bucket_display = p.get('bucket_name', '')
            listbox.insert('end', f"{p['name']} ({bucket_display}) [{p.get('endpoint_url', '')}]")
        listbox.pack(padx=10, pady=10)
        def add_profile():
            pwin = tk.Toplevel(win)
            pwin.title('Add Profile')
            tk.Label(pwin, text='Profile Name:').grid(row=0, column=0, sticky='e')
            name_var = tk.StringVar()
            tk.Entry(pwin, textvariable=name_var).grid(row=0, column=1)
            tk.Label(pwin, text='Bucket Name:').grid(row=1, column=0, sticky='e')
            bucket_var = tk.StringVar()
            tk.Entry(pwin, textvariable=bucket_var).grid(row=1, column=1)
            tk.Label(pwin, text='Access Key:').grid(row=2, column=0, sticky='e')
            ak_var = tk.StringVar()
            tk.Entry(pwin, textvariable=ak_var).grid(row=2, column=1)
            tk.Label(pwin, text='Secret Key:').grid(row=3, column=0, sticky='e')
            sk_var = tk.StringVar()
            tk.Entry(pwin, textvariable=sk_var, show='*').grid(row=3, column=1)
            tk.Label(pwin, text='Endpoint URL:').grid(row=4, column=0, sticky='e')
            ep_var = tk.StringVar(value='https://s3.wasabisys.com')
            tk.Entry(pwin, textvariable=ep_var).grid(row=4, column=1)
            tk.Label(pwin, text='SSL Verify:').grid(row=5, column=0, sticky='e')
            ssl_var = tk.BooleanVar(value=True)
            tk.Checkbutton(pwin, variable=ssl_var).grid(row=5, column=1, sticky='w')
            tk.Label(pwin, text='CA File (optional):').grid(row=6, column=0, sticky='e')
            ca_var = tk.StringVar()
            tk.Entry(pwin, textvariable=ca_var).grid(row=6, column=1)
            def save_profile():
                pname = name_var.get()
                bucket_name = bucket_var.get()
                if not validate_profile_name(pname):
                    messagebox.showerror('Invalid Name', 'Profile name is invalid.')
                    return
                if not bucket_name or not validate_bucket_name(bucket_name):
                    messagebox.showerror('Invalid Bucket', 'Bucket name is invalid.')
                    return
                if not ak_var.get() or not sk_var.get():
                    messagebox.showerror('Missing Credentials', 'Access and Secret Key required.')
                    return
                store_credential(pname, ak_var.get(), sk_var.get())
                profile = {
                    'name': pname,
                    'bucket_name': bucket_name,
                    'endpoint_url': ep_var.get(),
                    'ssl_verify': ssl_var.get(),
                    'ca_file': ca_var.get()
                }
                self.config_data['profiles'].append(profile)
                save_config(self.config_data)
                win.destroy()
                self.show_profiles_dialog()
                pwin.destroy()
            tk.Button(pwin, text='Save', command=save_profile).grid(row=7, column=0, columnspan=2, pady=8)
        def delete_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            pname = profiles[idx]['name']
            delete_credential(pname)
            del self.config_data['profiles'][idx]
            save_config(self.config_data)
            win.destroy()
            self.show_profiles_dialog()
        tk.Button(win, text='Add Profile', command=add_profile).pack(side='left', padx=5)
        tk.Button(win, text='Delete Selected', command=delete_selected).pack(side='left', padx=5)

    def import_config(self):
        path = filedialog.askopenfilename(title='Import Config', filetypes=[('JSON Files', '*.json')])
        if not path:
            return
        try:
            with open(path, 'r') as f:
                imported = json.load(f)
            self.config_data = imported
            save_config(self.config_data)
            messagebox.showinfo('Import', 'Configuration imported successfully!')
        except Exception as e:
            messagebox.showerror('Import Error', str(e))

    def export_config(self):
        path = filedialog.asksaveasfilename(title='Export Config', defaultextension='.json', filetypes=[('JSON Files', '*.json')])
        if not path:
            return
        try:
            with open(path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            messagebox.showinfo('Export', 'Configuration exported successfully!')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def delete_file(self):
        if not self.s3 or not self.current_bucket:
            return
        selection = self.file_list.selection()
        if not selection:
            return
        name = self.file_list.item(selection[0], 'values')[0]
        key = self.current_prefix + name
        if not messagebox.askyesno('Confirm', f'Delete {name}?'):
            return
        self.status_var.set(f'Deleting {name}...')
        def do_delete():
            try:
                self.s3.delete_object(Bucket=self.current_bucket, Key=key)
                self.status_var.set(f'Deleted {name}')
                self.populate_file_list()
                logger.info(f'Deleted {name} from {self.current_bucket}/{key}')
            except Exception as e:
                self.status_var.set(f'Delete failed: {str(e)}')
                logger.error(f'Delete failed for {name}: {e}')
        threading.Thread(target=do_delete).start()

    def create_folder(self):
        if not self.s3 or not self.current_bucket:
            return
        folder_name = simpledialog.askstring('New Folder', 'Enter folder name:')
        if not folder_name:
            return
        key = self.current_prefix + folder_name.rstrip('/') + '/'
        self.status_var.set(f'Creating folder {folder_name}...')
        def do_create():
            try:
                self.s3.put_object(Bucket=self.current_bucket, Key=key)
                self.status_var.set(f'Created folder {folder_name}')
                self.populate_tree()
                self.populate_file_list()
                logger.info(f'Created folder {folder_name} in {self.current_bucket}/{key}')
            except Exception as e:
                self.status_var.set(f'Create folder failed: {str(e)}')
                logger.error(f'Create folder failed for {folder_name}: {e}')
        threading.Thread(target=do_create).start()

    def add_bookmark(self):
        if not self.current_bucket:
            messagebox.showerror('Error', 'No bucket selected.')
            return
        name = simpledialog.askstring('Bookmark Name', 'Enter a name for this bookmark:')
        if not name:
            return
        bookmark = {
            'name': name,
            'bucket': self.current_bucket,
            'prefix': self.current_prefix
        }
        self.load_bookmarks()
        self.bookmarks.append(bookmark)
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(self.bookmarks, f)
        self.update_bookmarks_menu()
        messagebox.showinfo('Bookmark Added', f'Bookmark "{name}" added!')

    def search_files(self):
        query = self.search_var.get().strip().lower()
        filters = getattr(self, 'advanced_search_filters', {})
        self.file_list.delete(*self.file_list.get_children())
        if not self.s3:
            self.status_var.set('Not connected to a bucket.')
            return
        def do_search():
            try:
                response = self.safe_list_objects(Bucket=self.current_bucket, Prefix=self.current_prefix)
                for obj in response.get('Contents', []):
                    key = obj['Key']
                    name = key[len(self.current_prefix):]
                    if query and query not in name.lower():
                        continue
                    # Advanced filters
                    if filters:
                        if filters.get('type') and not name.endswith(filters['type']):
                            continue
                        if filters.get('min_size'):
                            try:
                                if obj['Size'] < int(filters['min_size']):
                                    continue
                            except:
                                pass
                        if filters.get('max_size'):
                            try:
                                if obj['Size'] > int(filters['max_size']):
                                    continue
                            except:
                                pass
                        if filters.get('after'):
                            try:
                                after = datetime.strptime(filters['after'], '%Y-%m-%d')
                                if obj.get('LastModified') and obj['LastModified'] < after:
                                    continue
                            except:
                                pass
                        if filters.get('before'):
                            try:
                                before = datetime.strptime(filters['before'], '%Y-%m-%d')
                                if obj.get('LastModified') and obj['LastModified'] > before:
                                    continue
                            except:
                                pass
                    size = obj['Size']
                    mtime = obj.get('LastModified')
                    mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S') if mtime else ''
                    self.file_list.insert('', 'end', values=(str(name), size, mtime_str))
            except Exception as e:
                self.status_var.set(f'Error: {str(e)}')
                logger.error(f'Search failed: {e}')
        threading.Thread(target=do_search).start()

    def show_file_context_menu(self, event):
        iid = self.file_list.identify_row(event.y)
        if iid:
            self.file_list.selection_set(iid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='Delete', command=self.delete_file)
        menu.add_command(label='Rename', command=self.rename_file if hasattr(self, 'rename_file') else None)
        menu.add_separator()
        menu.add_command(label='Bookmark', command=self.add_bookmark)
        menu.post(event.x_root, event.y_root)

    def show_search_filter_dialog(self):
        win = tk.Toplevel(self)
        win.title('Advanced Search Filters')
        tk.Label(win, text='File name contains:').grid(row=0, column=0, sticky='e')
        name_var = tk.StringVar(value=self.search_var.get())
        name_entry = tk.Entry(win, textvariable=name_var, width=20)
        name_entry.grid(row=0, column=1)
        tk.Label(win, text='Type (e.g. .jpg, .txt):').grid(row=1, column=0, sticky='e')
        type_var = tk.StringVar()
        type_entry = tk.Entry(win, textvariable=type_var, width=10)
        type_entry.grid(row=1, column=1)
        tk.Label(win, text='Min size (bytes):').grid(row=2, column=0, sticky='e')
        min_size_var = tk.StringVar()
        min_size_entry = tk.Entry(win, textvariable=min_size_var, width=10)
        min_size_entry.grid(row=2, column=1)
        tk.Label(win, text='Max size (bytes):').grid(row=3, column=0, sticky='e')
        max_size_var = tk.StringVar()
        max_size_entry = tk.Entry(win, textvariable=max_size_var, width=10)
        max_size_entry.grid(row=3, column=1)
        tk.Label(win, text='Modified after (YYYY-MM-DD):').grid(row=4, column=0, sticky='e')
        after_var = tk.StringVar()
        after_entry = tk.Entry(win, textvariable=after_var, width=12)
        after_entry.grid(row=4, column=1)
        tk.Label(win, text='Modified before (YYYY-MM-DD):').grid(row=5, column=0, sticky='e')
        before_var = tk.StringVar()
        before_entry = tk.Entry(win, textvariable=before_var, width=12)
        before_entry.grid(row=5, column=1)
        def apply_filters():
            self.advanced_search_filters = {
                'name': name_var.get(),
                'type': type_var.get(),
                'min_size': min_size_var.get(),
                'max_size': max_size_var.get(),
                'after': after_var.get(),
                'before': before_var.get(),
            }
            win.destroy()
            self.search_files()
        tk.Button(win, text='Apply', command=apply_filters).grid(row=6, column=0, columnspan=2, pady=8)

    def update_progress(self, idx, total, name, transferred, total_size):
        percent = int((transferred / total_size) * 100) if total_size else 0
        self.status_var.set(f'Uploading {name}: {percent}% ({idx}/{total})')

    def update_bookmarks_menu(self):
        self.load_bookmarks()
        self.bookmarks_menu.delete(0, 'end')
        for bm in self.bookmarks:
            self.bookmarks_menu.add_command(label=bm.get('name', ''), command=lambda b=bm: self.goto_bookmark(b))
        self.bookmarks_menu.add_separator()
        self.bookmarks_menu.add_command(label='Manage Bookmarks', command=self.show_bookmarks_dialog)

    def setup_drag_and_drop(self):
        # Drag and drop support for uploads (Windows, Linux, macOS)
        try:
            import tkinterdnd2 as tkdnd
            # Try to initialize tkinterdnd2 properly
            # First try to load the tkdnd package
            try:
                self.tk.call('package', 'require', 'tkdnd')
            except:
                # If package require fails, try to load the library directly
                import sys
                import os
                if sys.platform.startswith('linux'):
                    # Try to load the system tkdnd library
                    self.tk.call('load', '', 'tkdnd')
                else:
                    # For other platforms, try the bundled version
                    tkdnd_path = os.path.join(os.path.dirname(tkdnd.__file__), 'tkdnd')
                    self.tk.call('lappend', 'auto_path', tkdnd_path)
                    self.tk.call('package', 'require', 'tkdnd')
            
            # Enable drag and drop on the file list
            self.file_list.drop_target_register(tkdnd.DND_FILES)
            self.file_list.dnd_bind('<<Drop>>', self.on_drop_files)
            self.status_var.set('Drag and drop enabled')
        except Exception as e:
            # Fallback - show a message but don't crash the application
            self.status_var.set('Drag and drop not available - use Upload button instead')
            # Add a note about drag and drop in the UI
            self.file_list.bind('<Button-1>', lambda e: self.status_var.set('Tip: Use the Upload button to add files') if not self.s3 else None)

    def on_drop_files(self, event):
        if not self.s3 or not self.current_bucket:
            return
        files = self.tk.splitlist(event.data)
        self.progress['value'] = 0
        self.progress['maximum'] = len(files)
        def do_upload():
            for idx, file_path in enumerate(files, 1):
                file_name = os.path.basename(file_path)
                key = self.current_prefix + file_name
                try:
                    self.s3.upload_file(file_path, self.current_bucket, key, 
                                      Callback=lambda bytes_transferred: self.update_progress(idx, len(files), file_name, bytes_transferred, os.path.getsize(file_path)))
                    self.status_var.set(f'Uploaded {file_name}')
                    logger.info(f'Uploaded {file_name} to {self.current_bucket}/{key}')
                except Exception as e:
                    self.status_var.set(f'Upload failed: {str(e)}')
                    logger.error(f'Upload failed for {file_name}: {e}')
                self.progress['value'] = idx
            self.populate_file_list()
        threading.Thread(target=do_upload).start()

    def goto_bookmark(self, bookmark):
        # Navigate to bookmarked location
        if 'bucket' in bookmark and 'prefix' in bookmark:
            # Switch to the bookmarked bucket if different
            if bookmark['bucket'] != self.current_bucket:
                # Find and select the bucket
                bucket_name = bookmark['bucket']
                if bucket_name in self.bucket_combo['values']:
                    self.bucket_combo.set(bucket_name)
                    self.on_bucket_select()
            # Navigate to the prefix
            self.current_prefix = bookmark['prefix']
            self.populate_file_list()
            self.status_var.set(f'Navigated to bookmark: {bookmark["name"]}')


if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()
