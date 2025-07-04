# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for TCC Analyzer
Builds a single executable file for the CLI application
"""

import sys
from pathlib import Path

# Get the project root directory (where this spec file is located)
import os
spec_root = Path(SPECPATH)  # SPECPATH is provided by PyInstaller
project_root = spec_root
src_dir = project_root / "src"

# Analysis configuration
a = Analysis(
    [str(src_dir / "tcc_analyzer" / "__main__.py")],  # Entry point
    pathex=[str(src_dir)],  # Path to search for modules
    binaries=[],
    datas=[],
    hiddenimports=[
        # Pandas dependencies that might not be auto-detected
        "pandas._libs.tslibs.timedeltas",
        "pandas._libs.tslibs.np_datetime",
        "pandas._libs.tslibs.nattype",
        "pandas._libs.hashtable",
        "pandas._libs.algos",
        "pandas._libs.join",
        "pandas._libs.reduction",
        # Rich dependencies
        "rich.console",
        "rich.table",
        "rich.text",
        "rich.style",
        # Click dependencies
        "click.core",
        "click.decorators",
        "click.exceptions",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        "tkinter",
        "matplotlib",
        "IPython",
        "jupyter",
        "notebook",
        "qtpy",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ (Python ZIP) archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="tcc-analyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Add version information for Windows
    version="version_info.txt" if sys.platform == "win32" else None,
)
