# RoadIQ

RoadIQ is a hackathon project intended to estimate road-surface quality and provide mode-specific road intelligence. This repository is in its initial scaffold phase and intentionally stops short of a production dashboard, scoring engine, or live computer-vision pipeline.

## Current status
- Frontend scaffold: React + TypeScript + Vite
- Backend scaffold: FastAPI + Pydantic
- Computer vision: placeholder module only
- Mapping: Leaflet-based boundary ready for future provider swap
- Testing: backend pytest checks and frontend build/type validation

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

Road-segment retrieval routes are planned but are not implemented. The shared road-segment shape and provisional scoring assumptions are documented in [`docs/SCORING_SPEC.md`](docs/SCORING_SPEC.md) and [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md). The backend validates the contract; it does not calculate scores.

## Notes
- This repository is intentionally scoped to the initial scaffold and documentation required for review.
- Production features such as road-quality scoring, machine-vision inference, and dashboard behavior remain planned work rather than implemented functionality.
