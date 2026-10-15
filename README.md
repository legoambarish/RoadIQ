# RoadIQ

RoadIQ is a hackathon prototype whose primary objective is image-based road-surface quality assessment. Image analysis focuses on visible pavement structure—individual stone aggregates, their boundaries/gaps and coverage, surface texture, and deterioration. Literal metal fragments are a separate analysis target from stone aggregates. Mapping and transport-mode dashboards are secondary.

## Current status
- Frontend: React + TypeScript + Vite dashboard with an interactive schematic map, five illustrative travel-profile overlays, filters, rankings, charts, distinct Everyday/Engineer assessment views, and a local-only image preview shell
- Backend scaffold: FastAPI + Pydantic
- Computer vision: Task C has a working local image-analysis service and one-command demo. It produces an annotated texture-candidate preview, structured observations, quality warnings, a named texture proxy, and optional experimental road-ROI gating. It has no active trained checkpoint or HTTP endpoint; individual aggregate/metal analysis remains unavailable. The multi-country RDD2022 detector is disabled under the India-only dataset policy, not because it is technically incompatible with Indian roads.
- Scoring: deterministic provisional RSQI scorer exists in `backend/app/services/scoring.py`; default normalization references are intentionally empty, so results remain `unrated` until fixed surface-type/capture-specific references and adequate component evidence are supplied. Weights and label cutoffs are unvalidated hypotheses.
- Dataset/evaluation: no labelled India-road aggregate dataset or held-out RoadIQ road metrics are available. A 20-image, visually reviewed low-occlusion ACAD synthetic-concrete test sample produced pixel IoU 0.488 / precision 0.822 / recall 0.545 for the texture-region baseline; it does not measure individual counting or road performance.
- Mapping: Leaflet-based boundary ready for future provider swap
- Testing: backend pytest checks include image-validation and inference-wrapper cases; frontend build/type validation remains available

## Repository structure
- `frontend/` — Vite React + TypeScript application
- `backend/` — FastAPI application, schemas, fixtures, and tests
- `docs/` — architecture, scoring, API, and decision documentation
- `AGENTS.md` — repository instructions for coding agents
- `.env.example` — placeholder environment variables
- `.gitignore` — generated-file and local-environment exclusions

## Prerequisites
- Node.js 20+ and npm
- Python 3.12.x
- A local terminal with internet access to install project dependencies

> Python 3.14 is not compatible with the selected Pydantic release in this scaffold, so the supported backend environment is Python 3.12.

## Local setup
1. Create and activate a virtual environment.
   ```bash
   cd /workspaces/RoadIQ
   python3.12 -m venv .venv
   . .venv/bin/activate
   ```
2. Install backend dependencies.
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Install frontend dependencies.
   ```bash
   cd frontend
   npm install
   ```
4. Copy the environment template and adjust values as needed.
   ```bash
   cd ..
   cp .env.example .env
   ```

## Windows desktop app

RoadIQ can be built as a single-file Windows desktop package. It bundles the FastAPI service, its Python runtime and dependencies, and the compiled dashboard in `dist\RoadIQ.exe`.

### Build

Build on Windows with Python 3.12, Node.js 20+ and npm. From the repository root, create a Python 3.12 virtual environment and install the build requirements:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-build.txt
.\scripts\build_windows.ps1
~~~

The build script installs the frontend dependencies, compiles the dashboard with the local API prefix, and packages the app with PyInstaller. The output is `dist\RoadIQ.exe`. A Python 3.12 interpreter and internet access are needed to prepare the build environment; Node/npm and internet access are needed for the frontend dependency install. Generated `build/` and `dist/` directories are ignored by Git.

### Run

Double-click `dist\RoadIQ.exe`, or run it from PowerShell:

~~~powershell
.\dist\RoadIQ.exe
~~~

The launcher binds the service to an available loopback port (`127.0.0.1`), waits for both the health endpoint and dashboard to pass, and opens the default browser. If the browser does not open, the error dialog and log show the local URL.

The bundled app does not require Python, Node, model downloads, API credentials, a map-provider key, or a network connection at runtime. The browser communicates with the local app. The current dashboard uses illustrative fixture records and a local-only image preview. It has no live segment retrieval or image-analysis endpoint, and does not produce a model prediction or RSQI.

Launching the same executable again safely requests a graceful restart only after verifying the recorded process is the same `RoadIQ.exe`; it then opens the newly started dashboard. Closing the browser does not stop the background service. To stop it, end `RoadIQ.exe` from Task Manager or shut down Windows.

### Local files and troubleshooting

- Rotating log: `%LOCALAPPDATA%\RoadIQ\logs\RoadIQ.log`
- Instance lock: `%LOCALAPPDATA%\RoadIQ\instance.lock`
- The app does not persist uploaded images; the dashboard preview stays in the browser.
- If startup or restart cannot be verified, the app reports an error and logs details. It does not stop a process based only on a port number.

The package and startup/restart flow were exercised on the development Windows 11 machine. Startup was tested with Python and Node removed from the inherited `PATH`, then verified through the local health endpoint and dashboard. This was not a clean virtual machine test or compatibility test across other Windows versions.

### Test results recorded for the package

- `.\.venv\Scripts\python.exe -m pytest backend/tests -q`: 93 passed, 2 skipped; one existing Starlette deprecation warning.
- Frontend `npm run build` and `npm run lint`: passed.
- `scripts/build_windows.ps1`: produced a 24,040,596-byte `dist\RoadIQ.exe`.
- Runtime sequence: health `GET /api/v1/health` returned `{"status":"ok","service":"RoadIQ API"}`, dashboard returned HTTP 200, an unauthenticated internal restart request returned 403, and a second launch gracefully replaced the verified first instance.

## Development commands

### Backend
```bash
cd /workspaces/RoadIQ/backend
. ../.venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd /workspaces/RoadIQ/frontend
npm run dev -- --host 0.0.0.0
```

### Tests
```bash
cd /workspaces/RoadIQ
. .venv/bin/activate
pytest backend/tests -q
cd frontend
npm run build
npm run lint
```

### Task C synthetic vision demo

One command makes a deterministic **synthetic** asphalt-like texture image, analyzes it with the Task C baseline, and saves an annotated JPEG and structured JSON report together. It requires no external model, network access, dataset, or private road photo.

```bash
cd /workspaces/RoadIQ
. .venv/bin/activate
PYTHONPATH=backend python -m scripts.demo_road_image --output-dir /tmp/roadiq-demo --seed 42
```

Open `/tmp/roadiq-demo/annotated-preview.jpg` to see the high-frequency texture candidates. `/tmp/roadiq-demo/analysis-report.json` labels the method as an untrained baseline and keeps particle counts, physical measurements, confidence, and RSQI unavailable/unrated. Synthetic output validates the demo plumbing only; it is not evidence of real-world model performance. To analyze a local road image with the same one-command flow, add `--image /path/to/road.jpg`; it writes only the annotation and report to the output directory and does not upload the image.

If an experimental India-road semantic checkpoint is available, set `ROADIQ_SEGMENTATION_MODEL_PATH=/path/to/checkpoint.pt` (and optionally `ROADIQ_SEGMENTATION_DEVICE=cpu`) before running the demo. The predicted road mask then gates the texture candidates and the report/preview label this behavior. The optional checkpoint is not bundled or configured by default; its road predictions are uncalibrated and do not turn texture into aggregate segmentation.

## API status
The initial backend exposes a versioned health endpoint:
- `GET /api/v1/health`

The endpoint returns a simple status payload and intentionally avoids external dependencies, model downloads, or network calls.

Road-segment retrieval and image-analysis routes are planned but are not implemented. Task C exposes an image-analysis service for direct backend integration; see [`docs/VISION_PIPELINE.md`](docs/VISION_PIPELINE.md) for its exact call, model setup, and limitations. It does not calculate scores. The proposed HTTP response shape and measurement rules are documented in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md); the scoring and dataset/evaluation proposal is in [`docs/SCORING_SPEC.md`](docs/SCORING_SPEC.md).

## Task C local image-analysis MVP (available)

The local Task C service accepts a road image and returns a structured observation report. The demo command above exercises the image validation and quality gate, named texture proxy, untrained high-frequency texture-candidate mask, annotated JPEG, and JSON report. A configured India-road segmentation checkpoint can optionally gate candidate regions with its predicted road mask; this remains experimental and uncalibrated.

The texture overlay is not a confirmed pavement, aggregate, or defect segmentation. Particle count, material classification, metal-fragment observations, physical measurements, and calibrated confidence remain unavailable; analysis status stays **Unrated**. The supplemental ACAD result is limited to synthetic-concrete region overlap and is not India-road or instance-count evidence.

## Full image-analysis workflow (planned; browser/API integration unavailable)

The intended first image-analysis demo is:
1. Upload a road image through the dashboard and identify any available camera/calibration metadata.
2. Reject or mark low-confidence images that fail quality checks; isolate the usable pavement region.
3. Classify asphalt/bituminous, cement-concrete, or unknown; segment visible individual aggregates only where resolution permits.
4. Report pixel-space aggregate size, coverage, boundaries/gaps, visible defect detections, and named image-texture proxies with provenance and confidence.
5. Report physical measurements (such as aggregates/m² or gap widths in mm) only if ground scale, usable physical area, and resolution support them.
6. Show an annotated image and transparent provisional surface index, or **Unrated** when required evidence is unavailable.

The browser upload/report experience and HTTP image-analysis endpoint are not implemented; they remain owned by Tasks B and D. The local service/demo is available independently and does not upload images. Map segments, quality values, and mode profiles are illustrative fixtures only. A 2D image does not measure true 3D roughness, subsurface strength, weather resistance, or skid resistance. Counts per square metre and physical widths require calibration. Missing or unreliable evidence is unavailable, not zero. The limited synthetic result is not a held-out RoadIQ road evaluation; do not claim model quality until suitable held-out road metrics are reported. See [`TASKS.md`](TASKS.md) for task ownership and boundaries.

## Notes
- This repository remains a prototype scaffold and is not production-ready. The Task C local demo is functional, but the broader vision task remains partial and has no RoadIQ held-out evaluation.
- Image-quality checks, a named texture proxy, an untrained high-frequency texture-region heuristic, and a documented dataset-manifest validator are implemented in the Task C service. The optional semantic road ROI can restrict texture candidates when an India-only checkpoint is explicitly configured; this does not segment/count individual particles and reports confidence/physical values as unknown. The former crack/pothole checkpoint is blocked because it used multinational road data. A single free India-only road segmentation dataset has been downloaded and audited; its compact experimental trainer has a weak CPU feasibility result, and no checkpoint is active by default. Surface classification, aggregate/metal-fragment instance segmentation, broader validated defect classes, calibrated RSQI output, annotated report UI, image API, and held-out RoadIQ aggregate evaluation remain unavailable.
