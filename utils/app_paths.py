"""
Path helpers for portable runtime behavior.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


def get_bundle_root() -> Path:
    """Return the root directory for bundled application resources."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_project_root() -> Path:
    """Return the source project root for non-bundled execution."""
    return Path(__file__).resolve().parent.parent


def get_config_dir() -> Path:
    """Return the user config directory, allowing an env override."""
    override = os.environ.get("ATHAN_APP_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".athan_app"


def get_log_file_path() -> Path:
    """Return the main app log file path."""
    return get_config_dir() / "athan_app.log"


def get_launchd_stdout_log_path() -> Path:
    """Return the launchd stdout log file path."""
    return get_config_dir() / "launchd.stdout.log"


def get_launchd_stderr_log_path() -> Path:
    """Return the launchd stderr log file path."""
    return get_config_dir() / "launchd.stderr.log"


def get_asset_roots() -> list[Path]:
    """Directories a relative "assets/..." path may resolve against, in
    priority order.

    Four of them, and each earns its place:

      1. the user's config dir  — overrides, so a custom athan wins
      2. the bundle root        — what shipped inside AthanApp.app
      3. the project root       — a source checkout (historical layout)
      4. the project's docs/    — a source checkout TODAY

    (4) is the live one. The audio used to be stored twice, once for the
    desktop app in assets/ and once for the website in docs/assets/, eleven
    byte-identical files in each. docs/ is the copy that cannot move, because
    GitHub Pages only serves from there, so that copy became the only copy.
    (3) stays so an old checkout, or a bundle built before the change, still
    resolves.
    """
    roots = [
        get_config_dir(),
        get_bundle_root(),
        get_project_root(),
        get_project_root() / "docs",
    ]
    unique = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def resolve_asset(relative_path) -> Path | None:
    """First existing match for a relative "assets/..." path, or None."""
    for root in get_asset_roots():
        candidate = root / relative_path
        if candidate.exists():
            return candidate
    return None


def get_audio_search_dirs() -> list[Path]:
    """Return audio directories to search in priority order."""
    dirs = []
    for root in get_asset_roots():
        path = root / "assets" / "audio"
        if path not in dirs:
            dirs.append(path)
    return dirs


def ensure_runtime_dirs() -> None:
    """Create the runtime directories used by the app."""
    config_dir = get_config_dir()
    (config_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    (config_dir / "logs").mkdir(parents=True, exist_ok=True)
