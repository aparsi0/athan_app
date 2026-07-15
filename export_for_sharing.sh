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
echo "Your friend should:"
echo "  1. Install Python 3.10+ and VLC (brew install --cask vlc)"
echo "  2. cd $DEST"
echo "  3. python3 -m venv .venv && source .venv/bin/activate"
echo "  4. pip install -r requirements.txt"
echo "  5. caffeinate -i python3 main.py"
