# Drag and Drop Fix for Wasabi File Manager

## Problem
The application was crashing with the error:
```
_tkinter.TclError: invalid command name "tkdnd::drop_target"
```

This error occurred because the `tkinterdnd2` library was not properly initialized or the system tkdnd library was not available.

## Solution
I've implemented a robust drag and drop initialization that handles multiple scenarios:

### 1. System Dependencies
First, I installed the system tkdnd library:
```bash
sudo apt install tkdnd
```

### 2. Updated Requirements
Updated `requirements.txt` to use a specific version of tkinterdnd2:
```
tkinterdnd2==0.4.3
```

### 3. Improved Initialization Code
Modified the `setup_drag_and_drop()` method to:
- Try multiple initialization approaches
- Handle different platform requirements
- Gracefully fall back if drag and drop isn't available
- Provide user feedback about the status

### 4. Error Handling
The application now:
- Doesn't crash if drag and drop fails to initialize
- Shows appropriate status messages
- Provides alternative instructions (use Upload button)

## Testing
The application now starts successfully without crashing. You can test it by running:
```bash
python test_startup.py
```

## Usage
- **If drag and drop works**: You can drag files directly onto the file list
- **If drag and drop doesn't work**: Use the "Upload" button in the toolbar

## Files Modified
- `requirements.txt` - Updated with specific versions
- `main.py` - Improved drag and drop initialization
- `test_startup.py` - Added startup test script

## Notes
- The application prioritizes stability over drag and drop functionality
- All core features (upload, download, delete, etc.) work regardless of drag and drop status
- The system tkdnd library provides better compatibility on Linux systems
