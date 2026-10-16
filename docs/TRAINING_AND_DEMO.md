# Rebuild, train and run locally

Use the repository root. Python 3.12 and supported Node 24 LTS are the reproduction targets. A CUDA GPU is required by the full ROI training command; CPU inference is supported. Training was actually executed on Windows/RTX 4060 Laptop; final measurements are in MODEL_CARD.md and VALIDATION_REPORT.md. Do not substitute the old synthetic texture demo for the genuine pipeline.

## Environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-detector.txt
cd frontend
npm ci
npm run build
cd ..
```

For CPU-only deployment, use the official `https://download.pytorch.org/whl/cpu` index instead. Do not install the legacy multinational RF-DETR checkpoint. The owner approved the official Ultralytics YOLO11n COCO checkpoint at `https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt` for detector initialization only; the trainer enforces SHA-256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`. All RoadIQ fine-tuning and evaluation imagery remains India-only. The U-Net remains randomly initialized. The optional ML framework/model license and each dataset's separate rights are recorded in DATASET_AND_RIGHTS_REGISTER.md. Base UI/quality tests can use only backend/requirements.txt and explicit unavailable model states.

## Acquire and freeze the two India tracks

```powershell
.\.venv\Scripts\python.exe -u -m backend.scripts.acquire_india_data
.\.venv\Scripts\python.exe -u -m backend.scripts.prepare_rdd_india --archive data/sources/RDD2022_India.zip
.\.venv\Scripts\python.exe -u -m backend.scripts.prepare_remote_segmentation
```

Acquisition emits timestamped progress, reuses correct-size range chunks and validates archive members. It stores only the India nested ZIP from official Figshare and original image/mask members from the second source. It deliberately does not claim whole-archive hashes for archives not fully downloaded. A primary URL/version/length/rights change requires review; do not relabel a changed source as the old version.

Manifests and ledgers are local:

- `data/sources/rdd2022-official-record.json`, `rdd2022-india-acquisition.json`, nested-member directory metadata.
- `data/rdd2022-india-v1/manifest.jsonl`, `split-audit.json`, `manifest-validation.json`, dataset.yaml and explicit image lists.
- `data/indian-roads-v2/acquisition.json`: each selected member CRC/SHA-256.
- `models/india-roi-v5/roi-manifest.jsonl`, `roi-split-audit.json`: sequence split frozen before training; this experiment uses the same source identities as the earlier ROI runs.

Preparation refuses to overwrite a frozen manifest. A changed split or experiment uses a fresh output/version. Failed/unfrozen preparation files and incomplete runs remain separate evidence; never erase a failed result to improve the report. The full manifest records source-relative paths, labels, IDs, groups and hashes; small committed ledgers permit checking identity without publishing raw datasets.

## Train and evaluate

```powershell
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -u -m backend.scripts.train_india_detector --pretrained-model https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt --output models/india-yolo11n-coco-v2 --name india-yolo11n-coco-transfer-v2 --batch 4 --epochs 90 --patience 20 --class-weight-cap 4
.\.venv\Scripts\python.exe -u -m backend.scripts.train_india_roi --output models/india-roi-v5 --name indian-roads-unet-v5 --positive-repeat 8 --pothole-weight-min 48 --dice-weight 1.0 --batch 4 --epochs 80 --patience 15 --preserve-aspect
```

Execute GPU jobs sequentially on smaller devices. The commands use batch 4 for a 6 GiB GPU. Detector class loss weights are derived only from training-box counts using capped inverse-square-root frequency; U-Net class weights, positive-image sampling and pothole Dice loss are also training-only. The U-Net selects and early-stops on validation mean road/pothole IoU. Each trainer writes a final evaluation only after model selection; the ROI script computes model-grid and source-resolution metrics from one holdout pass. Do not rerun, tune or choose a model based on test metrics. Detector AMP is off; the official pretrained checkpoint is explicitly requested and its SHA-256 is retained. The final full API benchmark evaluates the already selected weights and is not a tuning loop. Training JSON epoch records show actual losses and validation metrics. To retain logs in PowerShell, append `*> artifacts/detector-training.log` (create artifacts/ first); follow with `Get-Content ... -Tail 2 -Wait` in a separate terminal.

Expected actual assets after successful evaluation:

- `models/india-yolo11n-coco-v2/detector.pt` + `detector.json`, `experiment.json`, `heldout-metrics.json`, fit/results.csv and heldout plots/predictions.
- `models/india-roi-v5/roi.pt` + `roi-evaluation.json` containing training history, validation selection, model-grid and one-pass source-resolution heldout IoU/Dice, and hashes.
- Historical only: `models/india-roi-v3-letterbox-v1/roi.pt` was a deployment export of v3 parameters, not a separately trained experiment. The v5 training command creates and evaluates its own aspect-preserving checkpoint.

Earlier scratch/v2/v3/v4 experiment evidence remains immutable. The v5 U-Net is configured with letterbox preprocessing, so its trained checkpoint will itself be the runtime checkpoint; no parameter-reusing export is necessary. Test metrics must never be used to select epochs, weights, operating thresholds or later model versions.

The detector adapter verifies weights hash, India fine-tuning provenance, the approved pretraining source/hash/license, class order and heldout evaluation. The ROI adapter requires matching completed evaluation/checkpoint/manifest identities. Unfinished checkpoints cannot pass these readiness checks. Sidecars are provenance checks for **trusted local assets**, not an authentication mechanism for arbitrary untrusted checkpoints. Never upload/load foreign pickle weights through the image API.

## Real demo and application

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.demo_trained_pipeline --samples 993 --device cpu
cd frontend
npm run build
cd ..
.\.venv\Scripts\python.exe -m backend.scripts.serve_local --port 8123
```

Open [RoadIQ local application](http://127.0.0.1:8123/#image-report). The single-origin launcher discovers the two evaluated local checkpoints and serves the built frontend and API. It fails if required models are absent. `--allow-unavailable-models` is an explicit UI/quality-only mode. `--device 0` chooses CUDA; normal CPU inference needs no GPU. Port 8123 avoids the unrelated service observed on port 8000; never terminate an unknown port owner.

The demo runs all 993 frozen labelled holdout images at the fixed application threshold and writes genuine inputs, exact HTTP JSON, predicted-box previews, error examples, readiness, operating-point counts with conditional source-block bootstrap intervals and latency summaries to `artifacts/genuine-demo/`. A faster `--samples 60` subset is also available and explicitly identified as a subset. The black and low-resolution controls are synthetic/transformed plumbing checks, not road-accuracy evidence. The no-supported-source-box example is a false-positive challenge, not a certified healthy road. Choose these inputs in the live browser to reproduce Everyday and Engineer reports. Enable the experimental mask overlay to inspect road/pothole predictions. No numeric road grade, metric depth or percentile should appear.

For separate frontend development: export `VITE_API_BASE_URL=http://127.0.0.1:8123/api/v1` before `npm run dev`; export matching CORS_ORIGINS for that development origin. `.env.example` documents shell variables; the backend does not silently load a root .env file.

## Verification and Windows package

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m pytest backend/integration_tests -q
cd frontend
npm run test
npm run lint
npm run build
cd ..
```

Real integration tests intentionally **fail when weights or source-heldout images are missing**. Ordinary unit tests remain usable with optional ML absent. They never silently swap a mock into the trained-model gate.

Use a **clean CPU** environment for the model-enabled EXE; the CUDA training DLLs are too large for the intended distribution:

```powershell
py -3.12 -m venv .venv-package
.\.venv-package\Scripts\python.exe -m pip install torch==2.9.1+cpu torchvision==0.24.1+cpu --index-url https://download.pytorch.org/whl/cpu
.\.venv-package\Scripts\python.exe -m pip install -r backend/requirements-build.txt -r backend/requirements-detector.txt
.\scripts\build_windows.ps1 -PythonPath .venv-package/Scripts/python.exe -IncludeModels
```

This validates and embeds only the evaluated detector/ROI assets and notices, not training datasets or optimizer checkpoints. Default packaging without `-IncludeModels` is a smaller dashboard/quality package with explicit unavailable learned inference. The model-enabled bundle discovers embedded weights and uses CPU inference. Exact fresh build/runtime outcomes and omissions belong in VALIDATION_REPORT.md; the repository's old 24 MB EXE result is historical and cannot verify this release.
