$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $PSScriptRoot
Set-Location $AppDir

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-desktop.txt

pyinstaller --noconfirm --clean packaging/pyinstaller/athan_app.spec

Write-Host ""
Write-Host "Build complete."
Write-Host "Windows app folder:"
Write-Host "  $AppDir\dist\AthanApp"
