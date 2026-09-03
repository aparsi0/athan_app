#!/bin/bash
# Creates a clean, shareable copy of athan_app at ~/Desktop/athan_app_share/
# Run from inside the athan_app folder.

set -e

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/athan_app_share"

echo "Creating clean copy at $DEST ..."

rm -rf "$DEST"
rsync -a \
  --exclude='.venv' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='athan_app.log' \
  --exclude='*.log' \
  --exclude='.reload_request' \
  --exclude='legacy_snapshots' \
  --exclude='export_for_sharing.sh' \
  "$SRC/" "$DEST/"

echo ""
echo "Done. Shareable folder: $DEST"
echo "Size: $(du -sh "$DEST" | cut -f1)"
echo ""
echo "Your friend should run one command:"
echo ""
echo "  cd \"$DEST\" && ./setup.sh"
echo ""
echo "That installs Python, Tkinter and VLC if they are missing, builds the"
echo "menu-bar app, and puts it in /Applications. On Windows:"
echo ""
echo "  powershell -ExecutionPolicy Bypass -File .\\setup.ps1"
echo ""
echo "Or skip all of it — the web version needs nothing installed:"
echo "  https://aparsi0.github.io/athan_app/"
