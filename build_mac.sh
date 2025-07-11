#!/bin/bash
# macOS build script for Wasabi File Manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller --windowed --onefile --icon=icon_mac.icns --add-data "icon_mac.icns:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py 