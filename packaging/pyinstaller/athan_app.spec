# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPECPATH).resolve().parents[1]
vlc_root = Path("/Applications/VLC.app/Contents/MacOS")

datas = []
for relative_path in ("assets",):
    source = project_root / relative_path
    if source.exists():
        datas.append((str(source), relative_path))

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
