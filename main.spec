# -*- mode: python ; coding: utf-8 -*-

import os, sys, subprocess
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.datastruct import Tree

# ---- Dynamic HDF5 libs (Homebrew path differs per arch) ----
binaries = []
if sys.platform == "darwin":
    try:
        prefix = subprocess.check_output(["brew", "--prefix", "hdf5"]).decode().strip()
        for name in ("libhdf5.dylib", "libhdf5_hl.dylib", "libaec.dylib", "libsz.dylib"):
            p = os.path.join(prefix, "lib", name)
            if os.path.exists(p):
                binaries.append((p, "."))
    except Exception:
        pass

# Optionally let PyInstaller pull in any other linked libs from h5py:
# binaries += collect_dynamic_libs("h5py")

hiddenimports = [
    "h5py.defs",
    "h5py.utils",
    "h5py._proxy",
]

datas = [
    ("resources/icon.ico", "resources"),
    ("resources/icon.icns", "resources"),
    ("resources/fonts/GeistMonoNerdFontMono-Regular.otf", "."),
] + Tree("docs/_build", prefix=".") + Tree("src/helpers/mat", prefix=".")

hook_paths = ['hooks'] if os.path.isdir('hooks') else []

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=hook_paths,
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,               # entrypoint(s)
    [],                      # no extra binaries here (we add them in COLLECT)
    exclude_binaries=True,   # True for onedir; COLLECT will add binaries
    name='YsaGUI',           
    icon='resources/icon.icns' if sys.platform == 'darwin' else 'resources/icon.ico',
    console=False,           # False == windowed app (no terminal)
    debug=False,
    strip=False,             
    upx=False,               # leave False on macOS; UPX often unavailable/iffy
    bootloader_ignore_signals=False,
    disable_windowed_traceback=False,
    argv_emulation=False,    # set True on macOS only if you need Finder drag&drop args
    target_arch=None,        
    codesign_identity=None,  # fill if you sign
    entitlements_file=None,  # fill if you sign with entitlements
)

# macOS: wrap as .app bundle and set bundle identifier
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='YsaGUI.app',
        icon='resources/icon.icns',
        bundle_identifier='edu.byu.parrishlab.ysagui',   # pick and keep this stable
        info_plist={
            "CFBundleName": "YsaGUI",
            "CFBundleDisplayName": "YsaGUI",
            # Optionally set versions:
            # "CFBundleShortVersionString": "1.0.0",
            # "CFBundleVersion": "100",
        },
    )
    coll_input = app
else:
    coll_input = exe

coll = COLLECT(
    coll_input,
    a.binaries, a.zipfiles, a.datas,
    binaries=binaries,   # dynamic HDF5 list from earlier
    strip=False, upx=False, name='YsaGUI'
)
