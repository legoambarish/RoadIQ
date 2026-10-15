# RoadIQ

RoadIQ is a hackathon prototype whose primary objective is image-based road-surface quality assessment. Image analysis focuses on visible pavement structure—individual stone aggregates, their boundaries/gaps and coverage, surface texture, and deterioration. Literal metal fragments are a separate analysis target from stone aggregates. Mapping and transport-mode dashboards are secondary.

## Current status
- Frontend: React + TypeScript + Vite dashboard with an interactive schematic map, five illustrative travel-profile overlays, filters, rankings, charts, distinct Everyday/Engineer assessment views, and a local-only image preview shell
- Backend scaffold: FastAPI + Pydantic
- Computer vision: Task C provides image validation, heuristic quality observations, a named pixel-texture proxy, and an explicitly untrained texture-region candidate baseline. An experimental India-only road/pothole segmentation trainer and optional RLE masks exist, but no trained checkpoint is active. Individual aggregate/material analysis, validated damage detection, and an HTTP image route remain unavailable.
- Scoring: a deterministic provisional RSQI scorer exists in `backend/app/services/scoring.py`. Its default normalization references are intentionally empty, so it returns `unrated` until fixed references and adequate component evidence are supplied. Weights and label cutoffs remain unvalidated hypotheses.
- Dataset/evaluation: no labelled RoadIQ dataset or held-out evaluation metrics are available
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

## API status
The initial backend exposes a versioned health endpoint:
- `GET /api/v1/health`

The endpoint returns a simple status payload and intentionally avoids external dependencies, model downloads, or network calls.

Road-segment retrieval and image-analysis routes are planned but are not implemented. Task C exposes an image-analysis service for direct backend integration; see [`docs/VISION_PIPELINE.md`](docs/VISION_PIPELINE.md) for its exact call, model setup, and limitations. It does not calculate scores. The proposed HTTP response shape and measurement rules are documented in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md); the scoring and dataset/evaluation proposal is in [`docs/SCORING_SPEC.md`](docs/SCORING_SPEC.md).

## Core image-analysis workflow (planned, not yet available)

The intended first image-analysis demo is:
1. Submit a road image and identify any available camera/calibration metadata.
2. Reject or mark low-confidence images that fail quality checks; isolate the usable pavement region.
3. Classify asphalt/bituminous, cement-concrete, or unknown; segment visible individual aggregates only where resolution permits.
4. Report pixel-space aggregate size, coverage, boundaries/gaps, visible defect detections, and named image-texture proxies with provenance and confidence.
5. Report physical measurements (such as aggregates/m² or gap widths in mm) only if ground scale, usable physical area, and resolution support them.
6. Show an annotated image and transparent provisional surface index, or **Unrated** when required evidence is unavailable.

This sequence is a product goal, not implemented functionality. The dashboard currently previews a selected local image in the browser but does not upload it or analyze it; report values and annotated overlays remain unavailable. Map segments, quality values, and mode profiles are illustrative fixtures only. A 2D image does not measure true 3D roughness, subsurface strength, weather resistance, or skid resistance. Counts per square metre and physical widths require calibration. Missing or unreliable evidence is unavailable, not zero. There are no labelled-data evaluation results yet; do not claim model quality until held-out metrics are reported. See [`TASKS.md`](TASKS.md) for task ownership and boundaries.

## Notes
- This repository remains a prototype scaffold and is not production-ready. The Task C vision service is partial and has no RoadIQ held-out evaluation.
- Image-quality checks, a named texture proxy, an untrained high-frequency texture-region heuristic, and a documented dataset-manifest validator are implemented in the Task C service. The texture heuristic does not segment/count individual particles and reports confidence/physical values as unknown. The former crack/pothole checkpoint is blocked because it used multinational road data. A single free India-only road segmentation dataset has been downloaded and audited; a compact experimental trainer is in place, but no usable checkpoint has been trained. Semantic ROI/pothole inference remains inactive, and surface classification, aggregate/metal-fragment instance segmentation, broader validated defect classes, calibrated RSQI output, annotated report UI, image API, and held-out RoadIQ evaluation remain unavailable.
