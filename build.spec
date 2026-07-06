# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Trans Pro (Windows onefile build).

Usage: pyinstaller build.spec
"""
import os

from PyInstaller.utils.hooks import collect_all

datas = [("src/resources", "resources")]
binaries = []
hiddenimports = []

# rembg/onnxruntime/pymatting bundle native binaries and data files that
# PyInstaller's static import analysis can miss — collect them explicitly.
# pymatting (rembg's alpha-matting dependency) reads its own package metadata
# via importlib.metadata.version() at import time and does not catch
# PackageNotFoundError, unlike rembg itself; without its dist-info bundled,
# `from rembg import remove` fails with an ImportError at runtime (surfaced
# to the user as "배경 제거 기능을 사용할 수 없습니다").
for pkg in ("rembg", "onnxruntime", "pymatting"):
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

# PyInstaller는 Qt6Core.dll 등의 바이너리 의존성을 빌드 시점의 시스템 PATH에서
# 이름만으로 찾아서 함께 묶는다. 이 개발 PC에 설치된 Anaconda3의 "Library\bin"이
# 시스템 PATH에 올라가 있으면, PySide6/shiboken6 전용 사본(msvcp140/vcruntime140
# 계열)이나 Qt6Core.dll이 참조하는 icuuc.dll 대신 Anaconda가 번들한, 버전이 다른
# 동명 DLL을 집어와 _internal 최상위(공용 검색 경로)에 놓아버린다. 한 프로세스에서
# 같은 이름의 DLL은 처음 로드된 것이 계속 재사용되므로, 이 최상위 사본이 먼저
# 로드되면서 QtGui가 기대하는 내보내기(export)가 없어 "DLL load failed while
# importing QtGui: 지정된 프로시저를 찾을 수 없습니다" 오류로 이어진다(비-Anaconda
# venv를 쓰는 것과는 별개로, PyInstaller의 바이너리 의존성 스캔 자체가 시스템 PATH를
# 참조하기 때문에 발생 — 프로젝트 초기에 겪은 Anaconda DLL 충돌과 같은 근본 원인의
# 다른 발현). PySide6/shiboken6 폴더 안의 정합성 있는 사본만 남기고, 최상위에
# 중복 배치된 사본은 제거해 항상 시스템(System32) 버전이나 PySide6 동봉 버전이
# 쓰이도록 한다.
_STRAY_ROOT_DLL_NAMES = {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140_1.dll"}


def _is_stray_root_binary(dest_name: str) -> bool:
    base = os.path.basename(dest_name).lower()
    if os.path.dirname(dest_name) != "":
        return False  # PySide6/shiboken6 폴더 안의 정상 사본은 그대로 둔다
    return base in _STRAY_ROOT_DLL_NAMES or base == "icuuc.dll" or base.startswith("icudt")


a.binaries = [b for b in a.binaries if not _is_stray_root_binary(b[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TransPro",
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
