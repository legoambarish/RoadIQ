# Windows desktop app

RoadIQ can be built as a single-file Windows desktop package. It bundles the FastAPI service, its Python runtime and dependencies, and the compiled dashboard in `dist\RoadIQ.exe`.

## Build

Build on Windows with Python 3.12, Node.js 20+ and npm. From the repository root, create a Python 3.12 virtual environment and install the build requirements:

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

The bundled app does not require Python, Node, model downloads, API credentials, or a map-provider key at runtime. The dashboard uses illustrative fixture records. The integrated app includes local image upload and report UI; current uploads return Unrated because the required RSQI evidence and fixed normalization profiles are unavailable. The Windows package has not yet been rebuilt or runtime-tested with this integration.

Launching the same executable again safely requests a graceful restart only after verifying the recorded process is the same `RoadIQ.exe`; it then opens the newly started dashboard. Closing the browser does not stop the background service. To stop it, end `RoadIQ.exe` from Task Manager or shut down Windows.

## Local files and troubleshooting

- Rotating log: `%LOCALAPPDATA%\RoadIQ\logs\RoadIQ.log`
- Instance lock: `%LOCALAPPDATA%\RoadIQ\instance.lock`
- The app does not persist uploaded images; the dashboard preview stays in the browser.
- If startup or restart cannot be verified, the app reports an error and logs details. It does not stop a process based only on a port number.

The package and startup/restart flow were exercised on the development Windows 11 machine. Startup was tested with Python and Node removed from the inherited `PATH`, then verified through the local health endpoint and dashboard. This was not a clean virtual machine test or compatibility test across other Windows versions.

## Test results recorded for the package

- `.\.venv\Scripts\python.exe -m pytest backend/tests -q`: 93 passed, 2 skipped; one existing Starlette deprecation warning.
- Frontend `npm run build` and `npm run lint`: passed.
- `scripts/build_windows.ps1`: produced a 24,040,596-byte `dist\RoadIQ.exe`.
- Runtime sequence: health `GET /api/v1/health` returned `{"status":"ok","service":"RoadIQ API"}`, dashboard returned HTTP 200, an unauthenticated internal restart request returned 403, and a second launch gracefully replaced the verified first instance.
