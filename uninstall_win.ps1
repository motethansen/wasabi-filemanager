# Windows PowerShell uninstall script for Wasabi File Manager
$ErrorActionPreference = 'Stop'

Write-Host 'Removing virtual environment, build, and config files...'
Remove-Item -Recurse -Force venv, dist, build, main.spec, app_config.json, bookmarks.json -ErrorAction SilentlyContinue

# Remove desktop shortcut
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = "$desktop\Wasabi File Manager.lnk"
if (Test-Path $shortcut) { Remove-Item $shortcut -Force }

Write-Host 'Uninstallation complete.' 