# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPECPATH).resolve().parents[1]
vlc_root = Path("/Applications/VLC.app/Contents/MacOS")

# The audio and the reciter table now live under docs/, which is the only copy
# — GitHub Pages can serve nothing outside that directory, so it is docs/ that
# could not move. They are still placed at "assets/..." INSIDE the bundle, so
# every path in config/settings.py keeps working untouched.
#
# Only what the desktop app actually uses is bundled. docs/assets also holds
# twenty sky photographs and the local reciter overrides, which belong to the
# website and would add tens of megabytes to the .app for nothing.
datas = []

audio_source = project_root / "docs" / "assets" / "audio"
if audio_source.exists():
    for audio_file in sorted(audio_source.glob("*.m4a")):
        datas.append((str(audio_file), "assets/audio"))

# Without this the frozen app finds no reciters, and every Quran feature —
# the morning window included — silently does nothing. It was missing until
# 2026-09-03, which is exactly how that looked.
reciters_json = project_root / "docs" / "assets" / "reciters.json"
if reciters_json.exists():
    datas.append((str(reciters_json), "assets"))

icons_source = project_root / "docs" / "assets" / "icons"
if icons_source.exists():
    datas.append((str(icons_source), "assets/icons"))

if (vlc_root / "plugins").exists():
    datas.append((str(vlc_root / "plugins"), "VLC/plugins"))

if (vlc_root / "share").exists():
    datas.append((str(vlc_root / "share"), "VLC/share"))

binaries = []
for lib_name in ("libvlc.dylib", "libvlccore.dylib", "libvlc.5.dylib", "libvlccore.9.dylib"):
    lib_path = vlc_root / "lib" / lib_name
    if lib_path.exists():
        binaries.append((str(lib_path), "VLC/lib"))

hiddenimports = [
    "pystray._darwin",
    "pystray._win32",
    "PIL",
    "vlc",
    "gui.main_window",
    "gui.settings_window",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
]

block_cipher = None

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyinstaller" / "runtime_hook_vlc.py")],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AthanApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AthanApp",
)

app = BUNDLE(
    coll,
    name="AthanApp.app",
    icon=None,
    bundle_identifier="com.apa.athan-app",
)
