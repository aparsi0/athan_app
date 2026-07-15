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


def get_audio_search_dirs() -> list[Path]:
    """Return audio directories to search in priority order."""
    config_audio_dir = get_config_dir() / "assets" / "audio"
    bundle_audio_dir = get_bundle_root() / "assets" / "audio"
    project_audio_dir = get_project_root() / "assets" / "audio"

    dirs = []
    for path in (config_audio_dir, bundle_audio_dir, project_audio_dir):
        if path not in dirs:
            dirs.append(path)
    return dirs


def ensure_runtime_dirs() -> None:
    """Create the runtime directories used by the app."""
    config_dir = get_config_dir()
    (config_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    (config_dir / "logs").mkdir(parents=True, exist_ok=True)
