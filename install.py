import os
import sys
import subprocess
from pathlib import Path

print('Setting up virtual environment...')
venv_dir = Path('venv')
if not venv_dir.exists():
    subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
if sys.platform == 'win32':
    activate = venv_dir / 'Scripts' / 'activate.bat'
else:
    activate = venv_dir / 'bin' / 'activate'

pip = venv_dir / ('Scripts/pip.exe' if sys.platform == 'win32' else 'bin/pip')
subprocess.check_call([str(pip), 'install', '--upgrade', 'pip'])
subprocess.check_call([str(pip), 'install', '-r', 'requirements.txt'])

print('Building app...')
pyinstaller = venv_dir / ('Scripts/pyinstaller.exe' if sys.platform == 'win32' else 'bin/pyinstaller')
icon = 'icon_win.ico' if sys.platform == 'win32' else ('icon_mac.icns' if sys.platform == 'darwin' else 'icon_linux.png')

# Check if icon file exists, create a placeholder if not
if not Path(icon).exists():
    print(f'Warning: Icon file {icon} not found. Creating placeholder...')
    try:
        from PIL import Image
        if icon.endswith('.png'):
            img = Image.new('RGB', (32, 32), color='blue')
            img.save(icon, 'PNG')
        elif icon.endswith('.ico'):
            img = Image.new('RGB', (32, 32), color='blue')
            img.save(icon, 'ICO')
        else:  # .icns
            img = Image.new('RGB', (32, 32), color='blue')
            img.save(icon, 'PNG')  # Basic approach for macOS
    except ImportError:
        print('Warning: PIL not available. Building without icon.')
        icon = None

# Check if bookmarks.json exists, create if not
if not Path('bookmarks.json').exists():
    print('Creating empty bookmarks.json...')
    with open('bookmarks.json', 'w') as f:
        f.write('[]')

add_data = []
if icon:
    add_data.append(f'--add-data={icon}{";." if sys.platform == "win32" else ":."}') 
if Path('app_config.json').exists():
    add_data.append('--add-data=app_config.json:.')
if Path('bookmarks.json').exists():
    add_data.append('--add-data=bookmarks.json:.')

cmd = [str(pyinstaller), '--onefile', '--windowed']
if icon:
    cmd.append(f'--icon={icon}')
cmd.extend(add_data + ['main.py'])

subprocess.check_call(cmd)

# Create desktop shortcut (optional)
try:
    if sys.platform == 'win32':
        import winshell
        from win32com.client import Dispatch
        desktop = winshell.desktop()
        path = os.path.join(desktop, 'Wasabi File Manager.lnk')
        target = str(Path('dist') / 'main.exe')
        icon_path = str(Path(icon))
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.IconLocation = icon_path
        shortcut.save()
    elif sys.platform == 'darwin':
        apps = Path.home() / 'Applications'
        (apps / 'Wasabi File Manager').symlink_to(Path('dist') / 'main')
    else:
        desktop_file = Path.home() / 'Desktop' / 'Wasabi-File-Manager.desktop'
        with open(desktop_file, 'w') as f:
            f.write(f"""[Desktop Entry]\nType=Application\nName=Wasabi File Manager\nExec={Path.cwd()}/dist/main\nIcon={Path.cwd()}/{icon}\nTerminal=false\n""")
        os.chmod(desktop_file, 0o755)
    print('Shortcut created on Desktop/Applications.')
except Exception as e:
    print(f'Could not create shortcut: {e}')

print('Installation complete! App available in dist/.') 