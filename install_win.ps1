# Windows PowerShell install script for Wasabi File Manager
$ErrorActionPreference = 'Stop'

Write-Host 'Setting up virtual environment...'
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

Write-Host 'Building executable...'
pyinstaller --onefile --windowed --icon=icon_win.ico --add-data "icon_win.ico;." --add-data "app_config.json;." --add-data "bookmarks.json;." main.py

# Create desktop shortcut (optional, requires Windows Scripting Host)
$desktop = [Environment]::GetFolderPath('Desktop')
$target = (Resolve-Path .\dist\main.exe).Path
$shortcut = "$desktop\Wasabi File Manager.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcut)
$sc.TargetPath = $target
$sc.IconLocation = (Resolve-Path .\icon_win.ico).Path
$sc.Save()

Write-Host 'Installation complete! Shortcut created on Desktop.' 