@echo off
REM Windows build script for Wasabi File Manager
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --onefile --windowed --icon=icon_win.ico --add-data "icon_win.ico;." --add-data "app_config.json;." --add-data "bookmarks.json;." main.py 