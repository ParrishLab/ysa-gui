# -*- mode: python ; coding: utf-8 -*-

import os, sys, subprocess
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.datastruct import Tree

binaries = []
# Optionally let PyInstaller pull in any other linked libs from h5py:
# binaries += collect_dynamic_libs("h5py")

hiddenimports = [
    "zstandard",
    "urllib3",
    "h5py.defs",
    "h5py.utils",
    "h5py._proxy",
    "ysa_signal",
]

# ---- Data files ----
datas = [
    ("resources/icon.ico", "resources"),
    ("resources/icon.icns", "resources"),
    ("resources/fonts/GeistMonoNerdFontMono-Regular.otf", "."),
]
# h5py package data (equivalent to --collect-data h5py)
datas += collect_data_files("h5py")

hook_paths = ['hooks'] if os.path.isdir('hooks') else []

# --- Collect Qt plugins without importing PyQt5 ---
# Copy all Qt plugin files (platforms, imageformats, etc.)
datas += collect_data_files("PyQt5.Qt5.plugins", includes=["**/*"], include_py_files=False)

# Collect all ysa_signal Python modules
ysa_signal_hidden = collect_submodules('ysa_signal')

# Collect any compiled libs (.so/.pyd) that ship with ysa_signal and sz_se_detect
ysa_signal_bins = collect_dynamic_libs('ysa_signal')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries = binaries + ysa_signal_bins,
    datas=datas,
    hiddenimports = hiddenimports + ysa_signal_hidden + ['sz_se_detect'],
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

# Prepare extra Trees for COLLECT
extra_trees = []
if os.path.isdir("docs/_build"):
    extra_trees.append(Tree("docs/_build", prefix="."))
if os.path.isdir("src/helpers/mat"):
    extra_trees.append(Tree("src/helpers/mat", prefix="."))

# First create COLLECT with all binaries and resources
coll = COLLECT(
    exe,
    a.binaries, a.zipfiles, a.datas,
    *extra_trees,
    binaries=binaries,   # dynamic HDF5 list from earlier
    strip=False, upx=False, name='YsaGUI'
)

# macOS: wrap COLLECT in .app bundle with proper structure
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,  # Bundle the COLLECT, not just the EXE
        name='YsaGUI.app',
        icon='resources/icon.icns',
        bundle_identifier='edu.byu.parrishlab.ysagui',
        info_plist={
            "CFBundleName": "YsaGUI",
            "CFBundleDisplayName": "YsaGUI",
            # Optionally set versions:
            # "CFBundleShortVersionString": "1.0.0",
            # "CFBundleVersion": "100",
        },
    )
