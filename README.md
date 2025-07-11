# Wasabi Object storage File Manager

A cross-platform file manager application with cloud storage integration for Wasabi (S3-compatible) storage.

## Features

- Cross-platform support (Linux, macOS, Windows)
- Wasabi cloud storage integration
- Secure credential management
- File upload/download capabilities
- User-friendly GUI interface
- Desktop shortcut creation

## Prerequisites

### All Platforms
- Python 3.8 or higher
- pip (Python package installer)

### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip

# CentOS/RHEL/Fedora
sudo yum install python3 python3-venv python3-pip
# or for newer versions:
sudo dnf install python3 python3-venv python3-pip
```

### macOS
```bash
# Install Python 3 (if not already installed)
brew install python3

# Or download from https://www.python.org/downloads/
```

### Windows
- Download and install Python 3 from https://www.python.org/downloads/
- During installation, make sure to check "Add Python to PATH"
- Ensure pip is installed (usually included with Python)

## Installation

### Option 1: Automated Installation (Recommended)

#### Linux
```bash
# Clone the repository
git clone <repository-url>
cd wasabi-filemanager

# Make the script executable and run
chmod +x install_linux.sh
./install_linux.sh
```

#### macOS
```bash
# Clone the repository
git clone <repository-url>
cd wasabi-filemanager

# Make the script executable and run
chmod +x install_mac.sh
./install_mac.sh
```

#### Windows
```powershell
# Clone the repository
git clone <repository-url>
cd wasabi-filemanager

# Run the PowerShell script
.\install_win.ps1
```

### Option 2: Cross-Platform Python Installation

```bash
# Clone the repository
git clone <repository-url>
cd wasabi-filemanager

# Run the Python installer
python3 install.py
```

### Option 3: Manual Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd wasabi-filemanager
```

2. **Create and activate virtual environment:**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Build the application:**
```bash
# Linux
pyinstaller --onefile --windowed --icon=icon_linux.png --add-data "icon_linux.png:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py

# macOS
pyinstaller --onefile --windowed --icon=icon_mac.icns --add-data "icon_mac.icns:." --add-data "app_config.json:." --add-data "bookmarks.json:." main.py

# Windows
pyinstaller --onefile --windowed --icon=icon_win.ico --add-data "icon_win.ico;." --add-data "app_config.json;." --add-data "bookmarks.json;." main.py
```

## Running the Application

### After Installation

#### Linux
```bash
# Run from dist directory
./dist/main

# Or if desktop shortcut was created, double-click the desktop icon
```

#### macOS
```bash
# Run from dist directory
./dist/main

# Or if Applications shortcut was created, find it in Applications folder
```

#### Windows
```cmd
# Run from dist directory
dist\main.exe

# Or if desktop shortcut was created, double-click the desktop icon
```

### Development Mode (Without Building)

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run directly
python main.py
```

## Configuration

### First Time Setup

1. **Run the application** - The first time you run the application, you'll need to configure your Wasabi credentials.

2. **Set up credentials** - You can either:
   - Use the GUI to enter your credentials
   - Run the setup script: `python setup_credentials.py`

3. **Required credentials:**
   - Access Key ID
   - Secret Access Key
   - Bucket Name
   - Region (optional, defaults to us-east-1)

### Configuration Files

- `app_config.json` - Application configuration
- `bookmarks.json` - User bookmarks
- `secret.key` - Encryption key for stored credentials

## Troubleshooting

### Common Issues

1. **Missing dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Permission errors on Linux/macOS:**
   ```bash
   chmod +x install_linux.sh  # or install_mac.sh
   chmod +x dist/main
   ```

3. **Python not found:**
   - Ensure Python 3.8+ is installed
   - Check PATH environment variable
   - Try using `python3` instead of `python`

4. **PyInstaller issues:**
   ```bash
   pip install --upgrade pyinstaller
   ```

### Platform-Specific Issues

#### Linux
- Install required system libraries:
  ```bash
  sudo apt install python3-tk python3-dev build-essential
  ```

#### macOS
- If you get permission errors, try:
  ```bash
  sudo xcode-select --install
  ```

#### Windows
- Ensure Microsoft Visual C++ Redistributable is installed
- Run PowerShell as Administrator if needed

## Uninstallation

### Linux
```bash
./uninstall_linux.sh
```

### macOS
```bash
./uninstall_mac.sh
```

### Windows
```powershell
.\uninstall_win.ps1
```

### Manual Uninstall
```bash
python uninstall.py
```

## Development

### Project Structure
```
wasabi-filemanager/
├── main.py                 # Main application file
├── app_config.json         # Application configuration
├── bookmarks.json          # User bookmarks
├── requirements.txt        # Python dependencies
├── install.py             # Cross-platform installer
├── install_linux.sh       # Linux installer
├── install_mac.sh         # macOS installer
├── install_win.ps1        # Windows installer
├── uninstall.py           # Cross-platform uninstaller
├── setup_credentials.py   # Credential setup utility
├── icon_linux.png         # Linux application icon
├── icon_mac.icns          # macOS application icon
└── icon_win.ico           # Windows application icon
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on your target platform
5. Submit a pull request

## License

This project is licensed under GNU AFFERO GENERAL PUBLIC LICENSE - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing issues on the repository
3. Create a new issue if your problem isn't covered

## Version History

- **v1.0.0** - Initial release with basic file management and Wasabi integration
