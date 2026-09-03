#!/bin/bash
# Installs a launchd agent that starts the MENU-BAR app (dist/AthanApp.app)
# automatically at login, wrapped in `caffeinate -dims` so the Mac stays
# awake for prayer times. This mirrors the reference setup.
#
# Uses the same agent label as the headless installer (com.apa.athan-app),
# so installing one replaces the other — you never get two athans at once.

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer the installed copy: dist/ is a build directory, and setup.sh empties
# it on every run. An agent pointed there stops working the next time you build.
if [[ -n "${ATHAN_APP_BUNDLE:-}" && -x "${ATHAN_APP_BUNDLE}/Contents/MacOS/AthanApp" ]]; then
  APP_BINARY="${ATHAN_APP_BUNDLE}/Contents/MacOS/AthanApp"
elif [[ -x "/Applications/AthanApp.app/Contents/MacOS/AthanApp" ]]; then
  APP_BINARY="/Applications/AthanApp.app/Contents/MacOS/AthanApp"
else
  APP_BINARY="$APP_DIR/dist/AthanApp.app/Contents/MacOS/AthanApp"
fi
PLIST_SOURCE="$APP_DIR/macos/com.apa.athan-menubar.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_TARGET="$LAUNCH_AGENTS_DIR/com.apa.athan-app.plist"
CONFIG_DIR="${ATHAN_APP_CONFIG_DIR:-$HOME/.athan_app}"
STDOUT_LOG="$CONFIG_DIR/launchd.stdout.log"
STDERR_LOG="$CONFIG_DIR/launchd.stderr.log"

if [[ ! -x "$APP_BINARY" ]]; then
  echo "❌ No built app found. Looked in:"
  echo "   /Applications/AthanApp.app"
  echo "   $APP_DIR/dist/AthanApp.app"
  echo "Build and install it first:"
  echo "   ./setup.sh"
  exit 1
fi

mkdir -p "$LAUNCH_AGENTS_DIR" "$CONFIG_DIR"

python3 - <<PY
from pathlib import Path

source = Path(r"""$PLIST_SOURCE""").read_text(encoding="utf-8")
rendered = (
    source
    .replace("__APP_BINARY__", r"""$APP_BINARY""")
    .replace("__APP_DIR__", r"""$APP_DIR""")
    .replace("__STDOUT_LOG__", r"""$STDOUT_LOG""")
    .replace("__STDERR_LOG__", r"""$STDERR_LOG""")
)
Path(r"""$PLIST_TARGET""").write_text(rendered, encoding="utf-8")
PY

launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/com.apa.athan-app"
launchctl kickstart -k "gui/$(id -u)/com.apa.athan-app"

echo
echo "✅ Menu-bar athan agent installed and started."
echo "   Look for the green crescent icon in the menu bar (top-right)."
echo "   It will start automatically every time you log in."
echo
echo "Check status:  launchctl print gui/\$(id -u)/com.apa.athan-app | head"
echo "Logs:          tail -f $STDOUT_LOG"
