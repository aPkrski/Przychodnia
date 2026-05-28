@echo off
REM Build the application executable using PyInstaller.
REM Run this from the project root: build_exe.bat

setlocal
echo Building PoradniaFinanceApp.exe using PyInstaller...

python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo PyInstaller installation failed.
    exit /b 1
)

REM Check if icon exists
if exist "assets\app_icon.ico" (
    echo Building with icon: assets\app_icon.ico and assets folder
    pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp --icon=assets\app_icon.ico --add-data "assets;assets" main.py
) else (
    echo Building without icon, including assets folder
    pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp --add-data "assets;assets" main.py
)

if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo.
echo Build complete. Executable is in the dist folder.
echo.
echo Next steps:
echo 1. To create an installer, install Inno Setup: https://jrsoftware.org/isdl.php
echo 2. Run: iscc PoradniaFinanceApp.iss
echo 3. The installer will be created in the Output folder.
echo.
endlocal
