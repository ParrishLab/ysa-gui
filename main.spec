# -*- mode: python ; coding: utf-8 -*-

import os, sys, subprocess
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.datastruct import Tree

binaries = []
hdf5_libs = []

# ---- Vendor HDF5 libs (from conda env) on macOS only ----
if sys.platform == "darwin":
    hdf5_vendor_root = os.path.join("vendor", "hdf5", "mac")
    if os.path.isdir(hdf5_vendor_root):
        for name in os.listdir(hdf5_vendor_root):
            if name.startswith("libhdf5") and name.endswith(".dylib"):
                hdf5_libs.append((os.path.join(hdf5_vendor_root, name), "."))

binaries += hdf5_libs

# ---- C++ extension + any other dynamic libs from ysa_signal/sz_se_detect ----
binaries += collect_dynamic_libs("ysa_signal")
binaries += collect_dynamic_libs("sz_se_detect")

hiddenimports = [
    "zstandard",
    "urllib3",
    "h5py.defs",
    "h5py.utils",
    "h5py._proxy",
    "ysa_signal",
    "certifi",
]

# ---- Data files ----
datas = [
    ("resources/icon.ico", "resources"),
    ("resources/icon.icns", "resources"),
    ("resources/fonts/GeistMonoNerdFontMono-Regular.otf", "."),
]
# h5py package data (equivalent to --collect-data h5py)
datas += collect_data_files("h5py")
datas += collect_data_files("certifi")

hook_paths = ['hooks'] if os.path.isdir('hooks') else []

# --- Collect Qt plugins without importing PyQt5 ---
# Copy all Qt plugin files (platforms, imageformats, etc.)
datas += collect_data_files("PyQt5.Qt5.plugins", includes=["**/*"], include_py_files=False)

# Collect all ysa_signal Python modules
ysa_signal_hidden = collect_submodules('ysa_signal')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries = binaries,
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
    binaries=binaries,
    strip=False, upx=False, name='YsaGUI'
)

# macOS: wrap COLLECT in .app bundle with proper structure
# Optionally set versions:
            # "CFBundleShortVersionString": "1.0.0",
            # "CFBundleVersion": "100",
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='YsaGUI.app',
        icon='resources/icon.icns',
        bundle_identifier='edu.byu.parrishlab.ysagui',
        info_plist={
            "CFBundleName": "YsaGUI",
            "CFBundleDisplayName": "YsaGUI",
        },
    )
