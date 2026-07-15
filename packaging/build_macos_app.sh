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

pyinstaller --noconfirm --clean packaging/pyinstaller/athan_app.spec

echo
echo "Build complete."
echo "App bundle:"
echo "  $APP_DIR/dist/AthanApp.app"
