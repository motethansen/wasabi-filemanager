import os
import sys
from pathlib import Path
import shutil

print('Removing virtual environment, build, and config files...')
for item in ['venv', 'dist', 'build', 'main.spec', 'app_config.json', 'bookmarks.json']:
    p = Path(item)
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

# Remove desktop/Applications shortcut
try:
    if sys.platform == 'win32':
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        shortcut = os.path.join(desktop, 'Wasabi File Manager.lnk')
        if os.path.exists(shortcut):
            os.remove(shortcut)
    elif sys.platform == 'darwin':
        shortcut = Path.home() / 'Applications' / 'Wasabi File Manager'
        if shortcut.exists():
            shortcut.unlink()
    else:
        shortcut = Path.home() / 'Desktop' / 'Wasabi-File-Manager.desktop'
        if shortcut.exists():
            shortcut.unlink()
    print('Shortcut removed.')
except Exception as e:
    print(f'Could not remove shortcut: {e}')

print('Uninstallation complete.') 