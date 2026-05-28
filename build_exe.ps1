Write-Host "Building PoradniaFinanceApp.exe using PyInstaller..."

# Install PyInstaller
python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install PyInstaller."
    exit 1
}

# Check if icon exists
$iconPath = "assets/app_icon.ico"
$hasIcon = Test-Path $iconPath

# Build with or without icon
if ($hasIcon) {
    Write-Host "Building with icon: $iconPath"
    pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp --icon=$iconPath main.py
} else {
    Write-Host "Icon not found, building without icon."
    pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp main.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

Write-Host "Build complete. Executable is in the dist folder."
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. To create an installer, install Inno Setup: https://jrsoftware.org/isdl.php"
Write-Host "2. Run: iscc PoradniaFinanceApp.iss"
Write-Host "3. The installer will be created in the Output folder."

