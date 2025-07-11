#!/bin/bash
# Linux build script for Wasabi File Manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller --windowed --onefile --icon=icon_linux.png --add-data "icon_linux.png:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py

# AppImage (requires appimagetool)
# Uncomment if you have appimagetool installed
# mkdir -p AppDir/usr/bin
# cp dist/main AppDir/usr/bin/wasabi-filemanager
# cp icon_linux.png AppDir/
# appimagetool AppDir

# .deb package (requires fpm)
# Uncomment if you have fpm installed
# fpm -s dir -t deb -n wasabi-filemanager -v 1.0.0 dist/main=/usr/bin/wasabi-filemanager icon_linux.png=/usr/share/pixmaps/icon_linux.png 