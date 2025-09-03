# -*- mode: python ; coding: utf-8 -*-

import os, sys, subprocess
from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = []

if sys.platform == "darwin":
    try:
        prefix = subprocess.check_output(["brew", "--prefix", "hdf5"]).decode().strip()
        lib = os.path.join(prefix, "lib", "libhdf5.dylib")
        if os.path.exists(lib):
            binaries.append((lib, "."))
        # often needed too:
        for name in ("libhdf5_hl.dylib", "libaec.dylib", "libsz.dylib"):
            path = os.path.join(prefix, "lib", name)
            if os.path.exists(path):
                binaries.append((path, "."))
    except Exception:
        pass

# Optionally let PyInstaller pull in any other linked libs from h5py:
binaries += collect_dynamic_libs("h5py")

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    binaries=binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
