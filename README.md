# Poradnia Finance Manager

Python desktop app for managing invoices, payroll, and revenue for medical clinics.

## Technology stack

- Python 3.12+
- PySide6
- SQLite
- SQLAlchemy
- pandas
- openpyxl
- matplotlib

## Features

- Modern Windows 11-inspired UI
- Light and dark themes
- Location and clinic selection
- Invoice, payroll, and revenue management
- Date filtering, search, sorting, and summaries
- Financial analysis dashboard with charts
- Excel export support
- Professional Windows installer

## Installation

### From installer (recommended)

Download `PoradniaFinanceApp_Setup.exe` and run it. The installer will:
- Install the application
- Create Start Menu shortcuts
- Create a Desktop shortcut (optional)
- Configure the database

### From source

1. Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the application:

```powershell
python main.py
```

## Building executable

### Step 1: Build the .exe

Run the build script:

```powershell
.\build_exe.ps1
```

Or on command prompt:

```cmd
build_exe.bat
```

The executable will be created in the `dist` folder as `PoradniaFinanceApp.exe`.

### Step 2: Create installer (optional)

To create a professional Windows installer:

1. Install **Inno Setup** from: https://jrsoftware.org/isdl.php

2. Run the Inno Setup compiler:

```powershell
iscc PoradniaFinanceApp.iss
```

3. The installer will be created in the `Output` folder as `PoradniaFinanceApp_Setup.exe`

## Application icon

Place your application icon as `assets/app_icon.ico` (256x256 pixels minimum). If not found, the application will build without an icon.

## Database

The application uses SQLite database `poradnie.db` created automatically on first run. Database is stored in the application directory.

## Recent improvements

- ✓ Date selection without accidental scroll increment
- ✓ Month dropdown (Styczeń-Grudzień) in Payroll and Revenue modules
- ✓ Improved financial analysis dashboard
- ✓ Invoice module expanded with Category and Company fields
- ✓ Enhanced summary view with color-coded results
- ✓ Auto-refresh of data after edits
- ✓ Standardized Excel export filenames
- ✓ Proper clinic sorting by number

## License

Proprietary - All rights reserved

