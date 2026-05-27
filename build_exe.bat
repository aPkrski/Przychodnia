@echo off
REM Build the application executable using PyInstaller.
REM Run this from the project root: build_exe.bat

setlocal
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo PyInstaller installation failed.
    exit /b 1
)

pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp main.py
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)
echo Build complete. Executable is in the dist folder.
endlocal
