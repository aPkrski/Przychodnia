Write-Host "Building PoradniaFinanceApp.exe using PyInstaller..."

python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install PyInstaller."
    exit 1
}

pyinstaller --noconfirm --windowed --onefile --name PoradniaFinanceApp main.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

Write-Host "Build complete. Executable is in the dist folder."
