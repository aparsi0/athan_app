#!/bin/bash

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SOURCE="$APP_DIR/macos/com.apa.athan-app.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_TARGET="$LAUNCH_AGENTS_DIR/com.apa.athan-app.plist"
CONFIG_DIR="${ATHAN_APP_CONFIG_DIR:-$HOME/.athan_app}"
STDOUT_LOG="$CONFIG_DIR/launchd.stdout.log"
STDERR_LOG="$CONFIG_DIR/launchd.stderr.log"

if [[ -x "$APP_DIR/.venv/bin/python" ]]; then
  PYTHON_EXECUTABLE="$APP_DIR/.venv/bin/python"
else
  PYTHON_EXECUTABLE="$(command -v python3)"
fi

mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$CONFIG_DIR"

python3 - <<PY
from pathlib import Path

source = Path(r"""$PLIST_SOURCE""").read_text(encoding="utf-8")
rendered = (
    source
    .replace("__APP_DIR__", r"""$APP_DIR""")
    .replace("__PYTHON_EXECUTABLE__", r"""$PYTHON_EXECUTABLE""")
    .replace("__STDOUT_LOG__", r"""$STDOUT_LOG""")
    .replace("__STDERR_LOG__", r"""$STDERR_LOG""")
)
Path(r"""$PLIST_TARGET""").write_text(rendered, encoding="utf-8")
PY

launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/com.apa.athan-app"
launchctl kickstart -k "gui/$(id -u)/com.apa.athan-app"

echo "Installed and started launch agent:"
echo "  $PLIST_TARGET"
echo
echo "Useful commands:"
echo "  launchctl print gui/$(id -u)/com.apa.athan-app"
echo "  launchctl kickstart -k gui/$(id -u)/com.apa.athan-app"
echo "  launchctl bootout gui/$(id -u) $PLIST_TARGET"
