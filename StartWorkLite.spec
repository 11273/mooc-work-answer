# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
# python-docx uses parts/../templates paths; keep the physical parts directory too.
datas = collect_data_files("docx", include_py_files=True) + [(str(root / "pyproject.toml"), ".")]
a = Analysis(
    [str(root / "StartWork.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
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
    [("X utf8", None, "OPTION")],
    name=os.environ.get("MOOC_BUILD_NAME", "MoocWorkAnswer-lite"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=str(root / "images" / "icon.ico") if sys.platform == "win32" else None,
)
