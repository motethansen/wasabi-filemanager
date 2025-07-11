#!/bin/bash
# macOS install script for Wasabi File Manager
set -e

echo 'Setting up virtual environment...'
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo 'Building app bundle...'
pyinstaller --windowed --onefile --icon=icon_mac.icns --add-data "icon_mac.icns:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py

# Set permissions
chmod +x dist/main

# Create Applications shortcut (optional)
if [ -d "$HOME/Applications" ]; then
  ln -sf "$(pwd)/dist/main" "$HOME/Applications/Wasabi File Manager"
fi

echo 'Installation complete! App available in dist/ and shortcut in ~/Applications.' 