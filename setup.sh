#!/usr/bin/env bash
#
# Athan App — one command that installs or updates everything.
#
#   ./setup.sh                  install or update, then build the menu-bar app
#   ./setup.sh --clean          throw away this app's Python environment first
#   ./setup.sh --autostart      also start the app automatically at login
#   ./setup.sh --no-app         set up Python only; skip building the .app
#   ./setup.sh --help
#
# WHAT GETS REPLACED, AND WHAT DOES NOT
#
# Shared programs — Homebrew, Python, VLC, ffmpeg — are UPGRADED in place and
# never uninstalled. Uninstalling VLC to reinstall it would take it away from
# everything else on the machine that uses it, and a half-finished download
# would leave you with no VLC at all. `brew upgrade` already gets you the
# current version, which is the actual goal.
#
# What IS deleted and rebuilt every run is what belongs to this app alone:
# build/ and dist/, so a stale bundle can never be mistaken for a fresh one.
# With --clean the Python environment (.venv) goes too, which is the real
# "wipe it and start over" — every Python package is then downloaded fresh at
# its newest version. Nothing outside this folder is touched.

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

CLEAN=0
AUTOSTART=0
BUILD_APP=1
MIN_PY_MINOR=10          # 3.10+

for arg in "$@"; do
  case "$arg" in
    --clean)     CLEAN=1 ;;
    --autostart) AUTOSTART=1 ;;
    --no-app)    BUILD_APP=0 ;;
    -h|--help)
      sed -n '3,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      cat <<'HELP'
Shared programs (Homebrew, Python, VLC, ffmpeg) are upgraded, never removed.
build/ and dist/ are rebuilt every run. --clean also deletes .venv, so every
Python package is downloaded fresh. Nothing outside this folder is touched.
HELP
      exit 0 ;;
    *) echo "Unknown option: $arg  (try --help)" >&2; exit 2 ;;
  esac
done

step()  { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
ok()    { printf '  ✅ %s\n' "$*"; }
warn()  { printf '  ⚠️  %s\n' "$*"; }
die()   { printf '\n❌ %s\n' "$*" >&2; exit 1; }

case "$OSTYPE" in
  darwin*)  OS=macos ;;
  linux*)   OS=linux ;;
  *)        die "Unsupported system: $OSTYPE" ;;
esac

[[ $EUID -eq 0 ]] && die "Do not run this with sudo. It installs into your own account."

printf '\n🕌  Athan App setup — %s\n' "$OS"
printf '    %s\n' "$APP_DIR"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------

install_macos_deps() {
  if ! xcode-select -p >/dev/null 2>&1; then
    step "Command Line Tools"
    warn "macOS needs its developer tools before Homebrew will work."
    xcode-select --install || true
    die "A macOS installer window should have opened. Let it finish, then run this script again."
  fi

  if ! command -v brew >/dev/null 2>&1; then
    step "Installing Homebrew"
    NONINTERACTIVE=1 /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Apple Silicon puts brew somewhere the default PATH does not look.
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [[ -x "$candidate" ]]; then eval "$("$candidate" shellenv)"; break; fi
    done
    command -v brew >/dev/null 2>&1 || die "Homebrew installed but is not on PATH. Open a new Terminal and run this again."
    # Make it stick for future shells.
    for profile in "$HOME/.zprofile" "$HOME/.bash_profile"; do
      [[ -e "$profile" ]] || continue
      if grep -q 'brew shellenv' "$profile" 2>/dev/null; then continue; fi
      # shellcheck disable=SC2016  # the $(...) is meant to stay literal in the profile
      printf '\neval "$(%s shellenv)"\n' "$(command -v brew)" >> "$profile"
    done
    ok "Homebrew installed"
  else
    ok "Homebrew present"
  fi

  step "Updating Homebrew packages"
  brew update >/dev/null 2>&1 || warn "brew update failed; continuing with what is cached"

  # python-tk is the one people miss. Homebrew's Python ships WITHOUT tkinter,
  # and a build from such a Python produces a valid-looking .app whose menu-bar
  # icon opens nothing at all. It is a separate formula, and it must match the
  # Python version it is for.
  for formula in python python-tk vlc ffmpeg; do
    if [[ "$formula" == vlc ]]; then
      if brew list --cask vlc >/dev/null 2>&1; then
        brew upgrade --cask vlc >/dev/null 2>&1 || true
        ok "VLC up to date"
      else
        brew install --cask vlc || die "Could not install VLC. Install it from videolan.org and run this again."
        ok "VLC installed"
      fi
      continue
    fi
    if brew list "$formula" >/dev/null 2>&1; then
      brew upgrade "$formula" >/dev/null 2>&1 || true
      ok "$formula up to date"
    else
      brew install "$formula" >/dev/null || warn "Could not install $formula"
      ok "$formula installed"
    fi
  done
}

install_linux_deps() {
  step "Installing system packages (sudo will ask for your password)"
  sudo apt-get update -qq
  sudo apt-get install -y --only-upgrade \
    python3 python3-venv python3-dev python3-tk build-essential \
    vlc libvlc-dev libasound2-dev ffmpeg 2>/dev/null || true
  sudo apt-get install -y \
    python3 python3-venv python3-dev python3-tk build-essential \
    vlc libvlc-dev libasound2-dev ffmpeg
  ok "System packages installed"
}

if [[ "$OS" == macos ]]; then install_macos_deps; else install_linux_deps; fi

# ---------------------------------------------------------------------------
# 2. Pick a Python that is new enough AND has tkinter
# ---------------------------------------------------------------------------

step "Choosing a Python"

python_is_usable() {
  local candidate="$1"
  [[ -x "$candidate" ]] || return 1
  "$candidate" - "$MIN_PY_MINOR" <<'PY' >/dev/null 2>&1
import sys
minimum = int(sys.argv[1])
if sys.version_info[0] != 3 or sys.version_info[1] < minimum:
    raise SystemExit(1)
import tkinter          # noqa: F401 — the whole point of the check
PY
}

# macOS still ships bash 3.2, where expanding an empty array under `set -u` is
# an error and `sort -V` may not exist. A newline-separated string avoids both.
PYTHON=""
CANDIDATES=""

add_candidate() { [[ -n "$1" ]] && CANDIDATES="$CANDIDATES$1"$'\n'; return 0; }

if command -v brew >/dev/null 2>&1; then
  BREW_PREFIX="$(brew --prefix)"
  # Newest first, so 3.14 wins over 3.10. An explicit descending list rather
  # than `sort -V`, which BSD sort has not always had.
  for minor in 20 19 18 17 16 15 14 13 12 11 10; do
    add_candidate "$BREW_PREFIX/bin/python3.$minor"
  done
  add_candidate "$BREW_PREFIX/bin/python3"
fi
add_candidate "$(command -v python3 2>/dev/null || true)"
add_candidate /usr/bin/python3

while IFS= read -r candidate; do
  [[ -n "$candidate" ]] || continue
  if python_is_usable "$candidate"; then PYTHON="$candidate"; break; fi
done <<< "$CANDIDATES"

if [[ -z "$PYTHON" ]]; then
  # Almost always a missing python-tk for the version brew just installed.
  if [[ "$OS" == macos ]] && command -v brew >/dev/null 2>&1; then
    series="$("$(brew --prefix)/bin/python3" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
    if [[ -n "$series" ]]; then
      warn "Python $series has no tkinter — installing python-tk@$series"
      brew install "python-tk@$series" >/dev/null 2>&1 || true
      if python_is_usable "$(brew --prefix)/bin/python3"; then
        PYTHON="$(brew --prefix)/bin/python3"
      fi
    fi
  fi
fi

[[ -n "$PYTHON" ]] || die "No Python 3.$MIN_PY_MINOR+ with tkinter was found. On macOS: brew install python python-tk"
ok "Using $PYTHON ($("$PYTHON" -c 'import sys,tkinter; print("Python %d.%d.%d, Tk %s" % (sys.version_info[:3] + (tkinter.TkVersion,)))'))"

# ---------------------------------------------------------------------------
# 3. The Python environment
# ---------------------------------------------------------------------------

# Always: a stale bundle must never survive a setup run and be mistaken for
# the build you just made.
rm -rf build dist

if [[ $CLEAN -eq 1 ]]; then
  step "Removing the old Python environment (--clean)"
  rm -rf .venv
  ok "Deleted .venv — every package will be downloaded fresh"
fi

# A venv built by a Python that has since been upgraded away is broken in a
# confusing way; rebuild rather than debug it.
if [[ -d .venv ]] && ! .venv/bin/python -c "import tkinter" >/dev/null 2>&1; then
  warn "The existing environment is stale or has lost tkinter — rebuilding it"
  rm -rf .venv
fi

if [[ ! -d .venv ]]; then
  step "Creating the Python environment"
  "$PYTHON" -m venv .venv
  ok "Created .venv"
fi

step "Installing Python packages (newest versions)"
.venv/bin/python -m pip install --quiet --upgrade pip setuptools wheel
.venv/bin/python -m pip install --quiet --upgrade -r requirements.txt -r requirements-desktop.txt
ok "$(.venv/bin/python -m pip list --format=freeze 2>/dev/null | wc -l | tr -d ' ') packages installed"

# ---------------------------------------------------------------------------
# 4. Checks
# ---------------------------------------------------------------------------

step "Checking it works"

if .venv/bin/python -c "import tkinter" >/dev/null 2>&1; then
  ok "tkinter — the dashboard window can open"
else
  die "tkinter is missing from the environment; the dashboard would not open."
fi

if .venv/bin/python -c "import vlc; vlc.Instance('--intf','dummy')" >/dev/null 2>&1; then
  ok "VLC — audio can play"
else
  warn "python-vlc could not reach a VLC installation. On Apple Silicon make sure"
  warn "you have the arm64 VLC build, not the Intel one."
fi

for suite in tests/test_quran_library.py tests/test_app_commands.py; do
  [[ -f "$suite" ]] || continue
  if .venv/bin/python "$suite" >/dev/null 2>&1; then
    ok "$(basename "$suite") passed"
  else
    warn "$(basename "$suite") reported failures — run it directly to see them"
  fi
done

# ---------------------------------------------------------------------------
# 5. The menu-bar app
# ---------------------------------------------------------------------------

if [[ $BUILD_APP -eq 1 && "$OS" == macos ]]; then
  step "Building the menu-bar app"
  .venv/bin/pyinstaller --noconfirm --clean --log-level WARN \
    packaging/pyinstaller/athan_app.spec
  [[ -d dist/AthanApp.app ]] || die "The build finished but dist/AthanApp.app is not there."
  ok "Built dist/AthanApp.app"

  if [[ -w /Applications ]]; then
    rm -rf "/Applications/AthanApp.app"
    cp -R dist/AthanApp.app /Applications/
    ok "Installed to /Applications/AthanApp.app"
  else
    warn "/Applications is not writable; the app stays in dist/"
  fi
fi

if [[ $AUTOSTART -eq 1 && "$OS" == macos ]]; then
  step "Starting at login"
  chmod +x macos/install_menubar_agent.sh
  ./macos/install_menubar_agent.sh
fi

# ---------------------------------------------------------------------------

printf '\n\033[1m🎉 Done.\033[0m\n\n'
if [[ "$OS" == macos && $BUILD_APP -eq 1 ]]; then
  printf '  Open the app:      open /Applications/AthanApp.app\n'
  printf '  Start at login:    ./setup.sh --autostart\n'
else
  printf '  Run it:            .venv/bin/python main.py\n'
  printf '  Without a screen:  .venv/bin/python main_headless.py\n'
fi
printf '  Logs:              ~/.athan_app/athan_app.log\n'
printf '  Update later:      ./setup.sh\n'
printf '  Start over:        ./setup.sh --clean\n\n'
