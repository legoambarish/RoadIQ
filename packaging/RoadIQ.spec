# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import sys

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

repo_root = Path(SPECPATH).resolve().parent
frontend_build = repo_root / 'build' / 'windows-frontend'
if not (frontend_build / 'index.html').is_file():
    raise RuntimeError('Build the Vite frontend before packaging RoadIQ.')

include_models = os.getenv('ROADIQ_BUNDLE_MODELS') == '1'
model_datas = []
extra_imports = []
if include_models:
    import torch
    if torch.version.cuda is not None:
        raise RuntimeError('Model-enabled desktop build requires the documented CPU PyTorch environment, not CUDA training DLLs.')
    sys.path.insert(0, str(repo_root / 'backend'))
    from app.services.india_detector import IndiaRoadDamageDetector
    from app.services.india_road_segmentation import IndiaRoadSegmentationModel
    IndiaRoadDamageDetector(repo_root / 'models/india-yolo11n-coco-v2/detector.pt', device='cpu')
    IndiaRoadSegmentationModel(repo_root / 'models/india-roi-v5/roi.pt', device='cpu')
    for relative in ('models/india-yolo11n-coco-v2/detector.pt', 'models/india-yolo11n-coco-v2/detector.json',
                     'models/india-roi-v5/roi.pt', 'models/india-roi-v5/roi-evaluation.json'):
        source = repo_root / relative
        model_datas.append((str(source), str(Path(relative).parent)))
    for name in ('MODEL_CARD.md', 'DATASET_AND_RIGHTS_REGISTER.md'):
        model_datas.append((str(repo_root / 'docs' / name), 'notices'))
    model_datas += collect_data_files('ultralytics') + copy_metadata('ultralytics') + copy_metadata('torch') + copy_metadata('torchvision')
    extra_imports = collect_submodules('ultralytics')

a = Analysis(
    [str(repo_root / 'launcher.py')],
    pathex=[str(repo_root / 'backend')],
    binaries=[],
    datas=model_datas,
    hiddenimports=collect_submodules('uvicorn') + collect_submodules('PIL') + extra_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[] if include_models else ['torch', 'torchvision', 'ultralytics', 'cv2', 'numpy', 'polars', 'scipy', 'matplotlib'],
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
