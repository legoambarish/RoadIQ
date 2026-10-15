# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_submodules

repo_root = Path(SPECPATH).resolve().parent
frontend_build = repo_root / 'build' / 'windows-frontend'
if not (frontend_build / 'index.html').is_file():
    raise RuntimeError('Build the Vite frontend before packaging RoadIQ.')

a = Analysis(
    [str(repo_root / 'launcher.py')],
    pathex=[str(repo_root / 'backend')],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('uvicorn') + collect_submodules('PIL'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.datas += Tree(str(frontend_build), prefix='frontend/dist')
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RoadIQ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)