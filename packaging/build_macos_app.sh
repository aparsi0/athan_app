#!/bin/bash

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$APP_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-desktop.txt

# Preflight: the build interpreter MUST have tkinter.
#
# The spec already lists tkinter in hiddenimports, but PyInstaller can only
# bundle what it can import. Homebrew's python ships WITHOUT tkinter (it lives
# in the separate python-tk formula), so a build from such a venv emits a
# "hidden import not found" warning somewhere in its output and then produces
# a perfectly valid-looking .app with no Tk in it at all. That is exactly what
# shipped on 2026-08-25: the menu-bar icon worked, and clicking it opened
# nothing, because the helper window died on `import tkinter` every time.
#
# Fail loudly here instead of discovering it weeks later.
if ! python -c "import tkinter" >/dev/null 2>&1; then
  echo "ERROR: this venv's Python has no tkinter, so the built app would have" >&2
  echo "       no dashboard window (the menu-bar icon would open nothing)." >&2
  echo >&2
  echo "  Homebrew keeps it separate. Install it and rebuild the venv:" >&2
  echo "    brew install python-tk@3.14" >&2
  echo "    rm -rf .venv && python3 -m venv .venv" >&2
  echo >&2
  echo "  Verify with:  .venv/bin/python -c 'import tkinter; print(tkinter.TkVersion)'" >&2
  exit 1
fi
echo "Preflight OK: tkinter $(python -c 'import tkinter; print(tkinter.TkVersion)') available."

pyinstaller --noconfirm --clean packaging/pyinstaller/athan_app.spec

echo
echo "Build complete."
echo "App bundle:"
echo "  $APP_DIR/dist/AthanApp.app"
