# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for TransImage Lite (Windows onefile build).

Usage: pyinstaller build.spec
"""
from PyInstaller.utils.hooks import collect_all

datas = [("src/resources", "resources")]
binaries = []
hiddenimports = []

# rembg/onnxruntime bundle native binaries and data files that PyInstaller's
# static import analysis can miss — collect them explicitly.
for pkg in ("rembg", "onnxruntime"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TransImageLite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["src/resources/icons/app.ico"],
)
