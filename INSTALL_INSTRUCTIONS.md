# Installation & Build Instructions

## Quick Setup

### 1. Generate Application Icon

The application needs an icon file (`assets/app_icon.ico`) to look professional. Generate it with:

```powershell
python generate_icon.py
```

This script creates:
- `assets/app_icon.ico` - Main icon for the executable
- `assets/app_icon.png` - Preview/reference image

**Note:** Requires Pillow library. If not installed:
```powershell
pip install Pillow
```

### 2. Build Executable

Build the `.exe` file using PyInstaller:

```powershell
.\build_exe.ps1
```

Or on Command Prompt:
```cmd
build_exe.bat
```

The executable will be created at `dist/PoradniaFinanceApp.exe`

### 3. Create Windows Installer (Optional)

To create a professional installer that users can run:

#### Prerequisites:
- Download and install **Inno Setup** from: https://jrsoftware.org/isdl.php

#### Build installer:

```powershell
iscc PoradniaFinanceApp.iss
```

The installer will be created at `Output/PoradniaFinanceApp_Setup.exe`

## What Each Component Does

### `generate_icon.py`
- Creates professional icon combining medical cross + finance chart
- Uses blue (medical) and green (finance) theme
- Outputs: `.ico` (Windows), `.png` (reference)
- **Required** for building the executable with icon

### `build_exe.bat` / `build_exe.ps1`
- Uses PyInstaller to bundle Python code into executable
- Includes all dependencies
- Detects and includes icon if present
- Output directory: `dist/`

### `PoradniaFinanceApp.iss`
- Inno Setup installer script
- Creates professional Windows installer
- Includes Start Menu shortcuts
- Optional Desktop shortcut
- Creates uninstaller

## Distribution

### Method 1: Direct Executable
- Distribute `dist/PoradniaFinanceApp.exe` directly
- Users double-click to run (no installation)
- ~100MB file size

### Method 2: Professional Installer
- Distribute `Output/PoradniaFinanceApp_Setup.exe`
- Professional installation experience
- Smaller file size (~50MB with UPX compression)
- Creates Start Menu shortcuts

## Troubleshooting

### Icon not showing
- Ensure `assets/app_icon.ico` exists
- Run `python generate_icon.py` again
- Rebuild executable: `.\build_exe.ps1`

### PyInstaller errors
- Update PyInstaller: `pip install --upgrade pyinstaller`
- Clear old builds: `Remove-Item -Recurse dist, build`
- Rebuild: `.\build_exe.ps1`

### Inno Setup not found
- Install from: https://jrsoftware.org/isdl.php
- Ensure it's in system PATH
- Or use full path: `"C:\Program Files (x86)\Inno Setup 6\iscc.exe" PoradniaFinanceApp.iss`

## Release Checklist

- [ ] Run `python generate_icon.py` to create icon
- [ ] Run `.\build_exe.ps1` to build executable
- [ ] Test `dist/PoradniaFinanceApp.exe` thoroughly
- [ ] Run `iscc PoradniaFinanceApp.iss` to create installer
- [ ] Test `Output/PoradniaFinanceApp_Setup.exe` installation
- [ ] Verify database creation and functionality
- [ ] Create version tag: `git tag -a v1.0`
- [ ] Prepare release notes

## Post-Installation Notes

First run will:
- Create SQLite database (`poradnie.db`)
- Initialize locations and clinics
- Create necessary directories

Database is stored in the application directory for portable operation.

## Support

For issues or questions:
1. Check the README.md
2. Review application logs (if available)
3. Contact support at: https://example.com/support
