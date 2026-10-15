# RoadIQ architecture

## Current implementation

RoadIQ remains an initial prototype scaffold; it is not production-ready.

- **Frontend:** React + TypeScript + Vite under `frontend/`, with a landing/status page, minimal health API client, and TypeScript road-segment contract. A dashboard and segment retrieval UI are not implemented.
- **Backend:** FastAPI + Pydantic under `backend/`. The implemented HTTP API exposes `GET /api/v1/health` and `/`. `backend/app/schemas/road_segment.py` validates the shared road-segment shape. A deterministic demo fixture is isolated in `backend/app/fixtures/`.
- **Computer vision:** `backend/app/services/vision.py` is a placeholder only. It does not perform inference, calibrate pixels to ground dimensions, or download model weights.
- **Scoring:** no scoring engine is implemented. [SCORING_SPEC.md](./SCORING_SPEC.md) describes provisional rules and explicit evidence limits.
- **Persistence and mapping:** no segment database, segment retrieval API, or dashboard map exists. Mapping provider choice remains open.

## Shared contract

The canonical JSON contract is specified in [SCORING_SPEC.md](./SCORING_SPEC.md), validated by the backend Pydantic schema, and mirrored in `frontend/src/types/road-segment.ts`. Keep field names and units identical across the API and clients. `segment_id` is stable and opaque, while its generation/lifecycle are unresolved.

GeoJSON `LineString` coordinates are WGS 84 `[longitude, latitude]`. Each measurement explicitly declares its unit, status, and source. Unknowns use null and `unavailable`; they are never converted to zero. Provenance values distinguish `sensor`, `image_inference`, `user_input`, and `demo_fixture`.

Scores are nullable. Surface quality is distinct from mode-specific travel suitability. Pedestrian access/context (footpaths, crossings, comfort) is separately represented and must not be inferred from surface score or missing lane markings. Longitudinal grade is along the segment; crossfall is across it. Neither is derived from image pixels without calibration.

## Component boundaries

| Task | Responsibility | Owned implementation area |
| --- | --- | --- |
| A — scoring | Configurable normalization, evidence sufficiency, score calculation, confidence and explanations. | New backend scoring service and its focused tests; must consume the frozen schema and document configuration/version. |
| B — dashboard | User-facing segment and score visualization, explicit unrated/uncertainty states, API client. | `frontend/` application, components, and API integration; shared types only change by contract coordination. |
| C — computer vision | Image inference and measurements with provenance, uncertainty, and calibration limitations. | `backend/app/services/vision.py` and isolated inference tests; no production-grade inference assumed. |
| D — integration/release | Retrieval routes, service wiring, persistence boundary if approved, contract integration and release checks. | `backend/app/api/routes/`, `backend/app/main.py`, API/integration tests, release checks. |

The shared schema is a cross-task interface. Changes to it require compatibility agreement among the affected owners and updates to backend tests, frontend types, examples, and API documentation. The `docs/` specifications establish shared assumptions; no task may silently convert missing evidence to zero or claim unsupported safety conclusions.

## Planned data flow (not implemented end-to-end)

1. Survey inputs and image-derived observations enter through future ingestion boundaries.
2. Task C may produce estimated measurements, each attributed to `image_inference`; calibration and uncertainty accompany output.
3. Task A accepts only supported, normalized inputs, computes provisional surface scoring when evidence is sufficient, and otherwise emits an unrated record. Mode suitability remains separate.
4. Task D exposes validated records through the planned read endpoints in [API_CONTRACT.md](./API_CONTRACT.md).
5. Task B presents evidence date, sample/coverage, confidence, explanation, and unrated states without interpreting missing values as good.

No database, inference execution, scoring execution, segment API, or production dashboard is implied by this proposed flow.

## Unresolved architecture decisions

- Data persistence, stable segment IDs, segment split/merge lifecycle, and survey version history.
- Authentication, authorization, retention, and external service requirements.
- Scoring calibration, confidence, evidence minimums, ranking comparability, and mode-specific definitions.
- Vision model, image collection, calibration, and deployment approach.
- Map provider and handling of licensed basemaps/geocoding.
- API pagination/error envelope and generated frontend contract strategy.
