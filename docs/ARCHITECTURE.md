# RoadIQ architecture

## Component responsibilities

### Frontend
The frontend is a React + TypeScript + Vite application located under `frontend/`. It provides the landing page and a minimal API client boundary. Its responsibilities are intentionally limited to:
- rendering the RoadIQ status page,
- connecting to the backend through a configurable base URL,
- preparing the application structure for future feature pages and shared types.

### Backend
The backend is a FastAPI application located under `backend/`. It exposes a versioned API and centralizes validation, schemas, fixtures, and future business logic. This initial scaffold includes:
- FastAPI application creation,
- versioned routing under `/api/v1`,
- health endpoint, and
- a validated sample road-segment model.

### Computer vision
A placeholder service module exists under `backend/app/services/vision.py`. It documents the future interface for image processing without downloading model weights or performing inference during this scaffold phase.

### Mapping
Map integration is intentionally isolated behind a future provider abstraction. The initial scaffold does not add a full map UI, and the architecture allows a swap between Leaflet/OpenStreetMap and Google Maps without rewriting business logic.

## Data flow
1. The frontend reads a configured API base URL from environment variables.
2. The browser requests the backend health endpoint.
3. FastAPI validates requests and returns documented responses.
4. Demo data is represented by a Pydantic model, not a database-backed persistence layer.

## Interfaces
- Frontend to backend: HTTP JSON over the `VITE_API_BASE_URL` value.
- Backend to future model layer: a service boundary using structured image or frame payloads.
- Shared schema: road-segment validation remains defined in Pydantic rather than ad hoc dictionaries.

## Planned system architecture
- Public landing page and status page
- Road-segment inspection screens and scoring visualizations
- Backend endpoints for road metrics, health checks, and future uploads
- Road-defect inference behind a dedicated service module
- Map orchestration with provider abstraction and a simple adapter layer

This architecture remains intentionally minimal for the initial scaffold and does not claim production-ready behavior.
