from pathlib import Path
import os
import sys


def _configure_vlc_env() -> None:
    if not getattr(sys, "frozen", False):
        return

    resources_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    lib_dir = resources_dir / "VLC" / "lib"
    plugin_dir = resources_dir / "VLC" / "plugins"

    libvlc_path = lib_dir / "libvlc.dylib"
    if libvlc_path.exists():
        os.environ["PYTHON_VLC_LIB_PATH"] = str(libvlc_path)

    if plugin_dir.exists():
        os.environ["PYTHON_VLC_MODULE_PATH"] = str(plugin_dir)


_configure_vlc_env()
