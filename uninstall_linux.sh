#!/bin/bash
# Linux uninstall script for Wasabi File Manager
set -e

echo 'Removing virtual environment, build, and config files...'
rm -rf venv dist build main.spec app_config.json bookmarks.json

# Remove desktop shortcut
shortcut="$HOME/Desktop/Wasabi-File-Manager.desktop"
if [ -f "$shortcut" ]; then
  rm "$shortcut"
fi

echo 'Uninstallation complete.' 