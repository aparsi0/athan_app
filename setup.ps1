# Athan App - one command that installs or updates everything (Windows).
#
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Clean
#
# Shared programs (Python, VLC) are upgraded through winget, never uninstalled.
# What is deleted and rebuilt is this app's own .venv, build\ and dist\.

param(
    [switch]$Clean,
    [switch]$NoApp
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Step($m) { Write-Host "`n> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  [ok] $m" }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

Write-Host "`nAthan App setup - Windows"
Write-Host "  $PSScriptRoot"

# --- system packages ------------------------------------------------------

Step "Python and VLC"
if (Get-Command winget -ErrorAction SilentlyContinue) {
    # --silent so this stays one command; upgrade is a no-op when current.
    winget install --id Python.Python.3.12 --silent --accept-package-agreements `
        --accept-source-agreements --disable-interactivity 2>$null | Out-Null
    winget upgrade --id Python.Python.3.12 --silent --disable-interactivity 2>$null | Out-Null
    winget install --id VideoLAN.VLC --silent --accept-package-agreements `
        --accept-source-agreements --disable-interactivity 2>$null | Out-Null
    winget upgrade --id VideoLAN.VLC --silent --disable-interactivity 2>$null | Out-Null
    Ok "Python and VLC installed or already current"
} else {
    Warn "winget is not available on this Windows version."
    Warn "Install Python 3.10+ from python.org (tick 'Add Python to PATH')"
    Warn "and VLC from videolan.org, then run this again."
}

# --- pick a Python --------------------------------------------------------

Step "Choosing a Python"
$python = $null
foreach ($candidate in @('py -3', 'python', 'python3')) {
    $exe, $flag = $candidate.Split(' ')
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $probe = 'import sys,tkinter; raise SystemExit(0 if sys.version_info[:2] >= (3,10) else 1)'
    if ($flag) { & $exe $flag -c $probe 2>$null } else { & $exe -c $probe 2>$null }
    if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
}
if (-not $python) {
    Die "No Python 3.10+ with tkinter was found. Reinstall Python from python.org and tick 'tcl/tk and IDLE'."
}
Ok "Using $python"

# --- the Python environment ----------------------------------------------

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

if ($Clean -and (Test-Path .venv)) {
    Step "Removing the old Python environment (-Clean)"
    Remove-Item -Recurse -Force .venv
    Ok "Deleted .venv - every package will be downloaded fresh"
}

if (-not (Test-Path .venv)) {
    Step "Creating the Python environment"
    $exe, $flag = $python.Split(' ')
    if ($flag) { & $exe $flag -m venv .venv } else { & $exe -m venv .venv }
    Ok "Created .venv"
}

Step "Installing Python packages (newest versions)"
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip setuptools wheel
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade -r requirements.txt -r requirements-desktop.txt
Ok "Packages installed"

# --- checks ---------------------------------------------------------------

Step "Checking it works"
& .\.venv\Scripts\python.exe -c "import tkinter" 2>$null
if ($LASTEXITCODE -eq 0) { Ok "tkinter - the dashboard window can open" }
else { Die "tkinter is missing from the environment; the dashboard would not open." }

& .\.venv\Scripts\python.exe -c "import vlc; vlc.Instance('--intf','dummy')" 2>$null
if ($LASTEXITCODE -eq 0) { Ok "VLC - audio can play" }
else { Warn "python-vlc could not reach a VLC installation." }

foreach ($suite in @('tests\test_quran_library.py', 'tests\test_app_commands.py')) {
    if (-not (Test-Path $suite)) { continue }
    & .\.venv\Scripts\python.exe $suite 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "$suite passed" } else { Warn "$suite reported failures" }
}

# --- the desktop app ------------------------------------------------------

if (-not $NoApp -and (Test-Path 'packaging\build_windows_app.ps1')) {
    Step "Building the desktop app"
    & .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --log-level WARN `
        packaging\pyinstaller\athan_app.spec
    Ok "Built dist\AthanApp"
}

Write-Host "`nDone.`n" -ForegroundColor Green
Write-Host "  Run it:        .\.venv\Scripts\python.exe main.py"
Write-Host "  No window:     .\.venv\Scripts\python.exe main_headless.py"
Write-Host "  Update later:  powershell -ExecutionPolicy Bypass -File .\setup.ps1"
Write-Host "  Start over:    powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Clean`n"
