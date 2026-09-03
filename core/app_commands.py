"""A one-shot command channel from the dashboard window to the daemon.

The dashboard is a SEPARATE process — the tray spawns it, because Tk on macOS
insists on the main thread — so a Play button there cannot touch the daemon's
QuranPlayer directly. It leaves a small JSON file instead, and the daemon's
existing watcher thread picks it up and deletes it.

Deleting on read is what makes this safe: a command is consumed exactly once,
and the file's continued existence is how the dashboard learns the daemon is
not running. Nothing here retries, and nothing queues — the last write wins,
which is the right behaviour for "play this now".
"""

import json
import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

COMMAND_FILENAME = ".command"

# A command older than this is a leftover from a daemon that was not running
# when the button was pressed. Acting on it minutes later would start audio
# nobody asked for any more.
MAX_AGE_SECONDS = 30


def command_path():
    from utils.app_paths import get_config_dir
    return get_config_dir() / COMMAND_FILENAME


def send(action: str, **fields) -> bool:
    """Write a command for the daemon. Atomic, so a half-written file is never
    read: the daemon may be polling at the exact moment this runs."""
    path = command_path()
    payload = dict(fields)
    payload["action"] = action
    payload["at"] = time.time()
    try:
        os.makedirs(str(path.parent), exist_ok=True)
        handle, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".command-")
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, str(path))
        return True
    except Exception as exc:
        logger.error("Could not write the command file: %s", exc)
        return False


def pending() -> bool:
    """Has the daemon not consumed the last command yet?"""
    try:
        return command_path().exists()
    except Exception:
        return False


def take() -> dict:
    """Read and delete the pending command. {} when there is none.

    Deletes before acting, so a command that raises cannot be replayed on the
    next poll forever.
    """
    path = command_path()
    try:
        if not path.exists():
            return {}
        raw = path.read_text(encoding="utf-8")
        path.unlink(missing_ok=True)
        command = json.loads(raw)
        if not isinstance(command, dict) or not command.get("action"):
            return {}
        age = time.time() - float(command.get("at") or 0)
        if age > MAX_AGE_SECONDS:
            logger.info("Ignoring a %.0fs-old command: %s", age, command.get("action"))
            return {}
        return command
    except Exception as exc:
        logger.error("Could not read the command file: %s", exc)
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return {}


def clear():
    try:
        command_path().unlink(missing_ok=True)
    except Exception:
        pass
