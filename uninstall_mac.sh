#!/bin/bash
# macOS uninstall script for Wasabi File Manager
set -e

echo 'Removing virtual environment, build, and config files...'
rm -rf venv dist build main.spec app_config.json bookmarks.json

# Remove Applications shortcut
if [ -L "$HOME/Applications/Wasabi File Manager" ]; then
  rm "$HOME/Applications/Wasabi File Manager"
fi

echo 'Uninstallation complete.' 