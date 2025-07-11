#!/bin/bash
# Linux install script for Wasabi File Manager
set -e

# Check for required dependencies
for dep in python3 python3-venv pip3; do
  if ! command -v $dep &> /dev/null; then
    echo "$dep is required. Please install it first."
    exit 1
  fi
done

echo 'Setting up virtual environment...'
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo 'Building app...'
pyinstaller --windowed --onefile --icon=icon_linux.png --add-data "icon_linux.png:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py

chmod +x dist/main

# Create desktop shortcut (optional)
desktop_file="$HOME/Desktop/Wasabi-File-Manager.desktop"
echo "[Desktop Entry]
Type=Application
Name=Wasabi File Manager
Exec=$(pwd)/dist/main
Icon=$(pwd)/icon_linux.png
Terminal=false" > "$desktop_file"
chmod +x "$desktop_file"

echo 'Installation complete! App available in dist/ and shortcut on Desktop.' 