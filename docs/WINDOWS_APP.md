# Windows desktop app

RoadIQ can be built as a single-file Windows desktop package. It bundles the FastAPI service, its Python runtime and dependencies, and the compiled dashboard in `dist\RoadIQ.exe`.

The current optional **model-enabled** build and clean CPU environment are documented below and in [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md). Use `-PythonPath .venv-package/Scripts/python.exe -IncludeModels` only after the two genuine assets pass provenance/readiness checks. It embeds the evaluated detector/ROI and notices. The default smaller package explicitly reports learned inference unavailable. Actual fresh standalone outcomes and hashes are in [VALIDATION_REPORT.md](VALIDATION_REPORT.md); earlier package outcomes are historical. The previously tested Windows EXE predates the provisional-score UI change; rebuild from the current PR source to include it. The latest code has **not** yet had a Windows EXE rebuild/runtime verification.

## Build the current PR #18 version

Use a Windows 10/11 x64 machine, Python 3.12, Node.js 24 LTS with npm, Git, and internet access for dependencies. Keep a trusted copy of the completed local checkpoints from the training machine: model files and datasets are intentionally not committed or downloaded by this guide.

### 1. Get the branch

For a fresh checkout:

~~~powershell
git clone --branch feat/india-p0-implementation https://github.com/legoambarish/RoadIQ.git
Set-Location RoadIQ
git status --short --branch
git rev-parse --short HEAD
~~~

For an existing checkout, switch to the PR source branch and fast-forward from the fork:

~~~powershell
git switch pr-18
git pull --ff-only https://github.com/legoambarish/RoadIQ.git feat/india-p0-implementation
~~~

Confirm `README.md`, `docs/WINDOWS_APP.md`, and the image-indicator component are present at the updated revision. Do not use an older `dist\RoadIQ.exe` as proof that the latest score UI is included.

### 2. Place and verify the trained model assets

To build an EXE that performs model inference, provide the completed, trusted checkpoint and provenance files under these exact paths:

~~~text
models\india-yolo11n-coco-v2\detector.pt
models\india-yolo11n-coco-v2\detector.json
models\india-roi-v5\roi.pt
models\india-roi-v5\roi-evaluation.json
~~~

These large assets are excluded from Git. Transfer them from the machine that completed the documented training run using an approved private file-transfer method. Do not substitute a checkpoint from another branch, an unfinished run, or an untrusted download. Check that `detector.json` is adjacent to `detector.pt` and that the ROI evaluation sidecar matches the checkpoint. The builder loads both models and stops if provenance checks fail.

Verify the checkpoint hashes against [MODEL_CARD.md](MODEL_CARD.md):

~~~powershell
Get-FileHash .\models\india-yolo11n-coco-v2\detector.pt -Algorithm SHA256
Get-FileHash .\models\india-roi-v5\roi.pt -Algorithm SHA256
~~~

Expected detector hash: `173d10ec44da536c2848343cb4275f634e6f2494101c317f11f7863316fa9167`. Expected ROI hash: `677ccbc74afc29e1c1e3a28b94c5a602d7ac613618632d48f1fae76a2ac18b83`. If they differ, stop and review the corresponding model metadata and evaluation; do not relabel a different checkpoint as this experiment.

If the checkpoints are not available, use [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md) to acquire data, train, evaluate and validate them. That process requires substantial disk space and an NVIDIA GPU for U-Net training. The dashboard-only package below can be built without models, but learned image results and the provisional image score will be unavailable.

### 3. Create a clean CPU packaging environment and build

~~~powershell
py -3.12 -m venv .venv-package
.\.venv-package\Scripts\python.exe -m pip install --upgrade pip
.\.venv-package\Scripts\python.exe -m pip install torch==2.9.1+cpu torchvision==0.24.1+cpu --index-url https://download.pytorch.org/whl/cpu
.\.venv-package\Scripts\python.exe -m pip install -r backend\requirements-build.txt -r backend\requirements-detector.txt
.\scripts\build_windows.ps1 -PythonPath .venv-package\Scripts\python.exe -IncludeModels
Test-Path .\dist\RoadIQ.exe
Get-FileHash .\dist\RoadIQ.exe -Algorithm SHA256
~~~

The script installs frontend dependencies with `npm ci`, runs the TypeScript/Vite production build, then creates `dist\RoadIQ.exe`. Keep the CUDA training environment separate from this CPU-only bundle. The model-enabled EXE is large; allow sufficient disk space and time. Do not commit `dist\`, `build\`, local datasets, or model weights.

To build the smaller dashboard/quality-only package instead, use a separate environment with the build requirements and run `.\scripts\build_windows.ps1` without `-IncludeModels`. That package is not an image-analysis substitute: readiness must report models unavailable, and model-derived scores are absent.

### 4. Run and check an image

~~~powershell
.\dist\RoadIQ.exe
~~~

The app opens its local dashboard in the default browser and serves only on loopback. Upload a supported road image (at least 320x240 pixels; JPEG, PNG or WebP, up to the documented request limit). In the image report, check that model readiness is loaded and inspect the experimental image measurements panel. The provisional score is computed from that image's current detector/mask outputs; it is a demo heuristic, **not** RSQI, a percentile or a validated road-condition grade. A high value, including 100, can result from missed detections. RSQI correctly remains Unrated without the required evidence. The 56.9 value from the previously shared limited-preview sample is a recorded smoke-test result, not an expected score for other images.

The current Windows EXE must be rebuilt after code changes. Re-running an older binary will not update it. The most recent model-enabled EXE evidence verifies an earlier package's readiness, real inference and restart lifecycle, but not the new provisional-score UI. Record the new executable hash and actual Windows smoke result in [VALIDATION_REPORT.md](VALIDATION_REPORT.md) before describing it as verified.

For an isolated real-package check, choose a known candidate-producing JPEG from the heldout demo inputs and run the package smoke harness from the repository root:

~~~powershell
.\.venv-package\Scripts\python.exe -m backend.scripts.smoke_windows_package `
  --executable .\dist\RoadIQ.exe `
  --image .\path\to\known-candidate.jpg `
  --output .\artifacts\windows-score-smoke `
  --require-models
~~~

The harness checks model readiness, a real candidate-producing upload, contract v1.2, a numeric provisional indicator, standalone startup outside the repository, and the owned restart/shutdown lifecycle. Replace the example image path with a real JPEG from the heldout demo inputs; do not use a synthetic control as model-quality evidence. The check does not establish accuracy or validate the score formula.

## Build

Build on Windows with Python 3.12, supported Node.js 24 LTS and npm. From the repository root, create a Python 3.12 virtual environment and install the build requirements:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-build.txt
.\scripts\build_windows.ps1
~~~

The build script installs the frontend dependencies, compiles the dashboard with the local API prefix, and packages the app with PyInstaller. The output is `dist\RoadIQ.exe`. A Python 3.12 interpreter and internet access are needed to prepare the build environment; Node/npm and internet access are needed for the frontend dependency install. Generated `build/` and `dist/` directories are ignored by Git.

## Run

Double-click `dist\RoadIQ.exe`, or run it from PowerShell:

~~~powershell
.\dist\RoadIQ.exe
~~~

The launcher binds the service to an available loopback port (`127.0.0.1`), waits for both the health endpoint and dashboard to pass, and opens the default browser. If the browser does not open, the error dialog and log show the local URL.

The bundled app does not require separately installed Python/Node, model downloads, API credentials, or a map-provider key at runtime. The dashboard uses illustrative fixture records. The prior model-enabled package passed genuine inference and owned restart/shutdown outside the checkout on this Windows 11 host, with Python/Node absent from its child PATH. That package predates the provisional-score UI change. See the validation report for the limits of that check and the failed model-quality gates.

Launching the same executable again safely requests a graceful restart only after verifying the recorded process is the same `RoadIQ.exe`; it then opens the newly started dashboard. Closing the browser does not stop the background service. To stop it, end `RoadIQ.exe` from Task Manager or shut down Windows.

## Local files and troubleshooting

- Rotating log: `%LOCALAPPDATA%\RoadIQ\logs\RoadIQ.log`
- Instance lock: `%LOCALAPPDATA%\RoadIQ\instance.lock`
- The app does not persist uploaded images; the dashboard preview stays in the browser.
- If startup or restart cannot be verified, the app reports an error and logs details. It does not stop a process based only on a port number.

The package and startup/restart flow were exercised on the development Windows 11 machine. Startup was tested with Python and Node removed from the inherited `PATH`, then verified through the local health endpoint and dashboard. This was not a clean virtual machine test or compatibility test across other Windows versions.

## Current model-enabled result

`dist/RoadIQ.exe`: **281,615,820 bytes**, SHA-256 `7027b04b7ba850af0a8345ed22727fd2371ba528230f1d8e8cb24926a7fb8734`. Both embedded India-trained checkpoints loaded and a real heldout image produced the expected alligator candidate. The standalone copy is `../RoadIQ_Package_Smoke/full/RoadIQ.exe`; its isolated test instances were shut down. The separate source app can be started with `.venv-package/Scripts/python -m backend.scripts.serve_local --port 8123`. [Build evidence](evidence/windows-model-build.json), [standalone runtime evidence](evidence/windows-model-smoke.json).

## Historical package test results

- `.\.venv\Scripts\python.exe -m pytest backend/tests -q`: 93 passed, 2 skipped; one existing Starlette deprecation warning.
- Frontend `npm run build` and `npm run lint`: passed.
- `scripts/build_windows.ps1`: produced a 24,040,596-byte `dist\RoadIQ.exe`.
- Runtime sequence: health `GET /api/v1/health` returned `{"status":"ok","service":"RoadIQ API"}`, dashboard returned HTTP 200, an unauthenticated internal restart request returned 403, and a second launch gracefully replaced the verified first instance.
