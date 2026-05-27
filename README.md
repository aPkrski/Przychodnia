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

## Run

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

## Build executable

Aby wygenerować plik `.exe`, użyj `PyInstaller`:

```powershell
build_exe.bat
```

lub w PowerShell:

```powershell
.\build_exe.ps1
```

Po zakończeniu procesu plik `PoradniaFinanceApp.exe` znajdziesz w katalogu `dist`.
