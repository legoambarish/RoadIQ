# Windows desktop app

RoadIQ can be built as a single-file Windows desktop package. It bundles the FastAPI service, its Python runtime and dependencies, and the compiled dashboard in `dist\RoadIQ.exe`.

The current optional **model-enabled** build and clean CPU environment are documented in [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md). Use `-PythonPath .venv-package/Scripts/python.exe -IncludeModels` only after the two genuine assets pass readiness. It embeds the evaluated detector/ROI and notices. The default smaller package explicitly reports learned inference unavailable. Actual fresh standalone outcomes and hashes are in [VALIDATION_REPORT.md](VALIDATION_REPORT.md); earlier package outcomes are historical.

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

The bundled app does not require separately installed Python/Node, model downloads, API credentials, or a map-provider key at runtime. The dashboard uses illustrative fixture records. Image uploads return actual candidate observations; RSQI stays Unrated because required evidence and fixed normalization profiles are unavailable. The fresh model-enabled package passed genuine inference and owned restart/shutdown outside the checkout on this Windows 11 host, with Python/Node absent from its child PATH. See the validation report for the limits of that check and failed model-quality gates.

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
