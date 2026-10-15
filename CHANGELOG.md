# Changelog

## Unreleased
- Reworked the Task B dashboard presentation with a larger, earlier schematic map, higher-contrast road network styling, clearer type sizes, and a dark, data-inspection Engineer mode. Everyday and Engineer views now show different summary metrics and copy; map geometry remains fixture-only with no basemap.
- Added the Task B fixture-backed map/dashboard: selectable schematic road segments, Road Quality and five travel-profile overlays, ranked/filterable lists, quality/profile charts, Everyday/Engineer detail views, and a local-only image preview with explicitly unavailable report outputs. No live basemap, segment API, upload, inference, or score generation is connected.
- Added nine typed illustrative dashboard fixtures and documented the demo boundaries in the frontend, root README, and architecture guide. No dependency or shared API-contract changes were made.
- Aligned the product objective around image-based pavement analysis, with aggregate structure, visible defects, and texture proxies as core evidence.
- Added a provisional image-feature RSQI proposal, measurement/calibration constraints, dataset annotation/split requirements, and held-out evaluation metrics; no metrics or model results are claimed.
- Updated Task A-D ownership/acceptance criteria, architecture pipeline, proposed image-analysis API payload, README goal/limitations, and handoff. No inference, scoring engine, image API, or evaluation feature was implemented.
- Added a mandatory model-agnostic agent workflow covering repository inspection, task branches, ownership, contract coordination, verification, handoff, commits, and pull requests.
- Recorded the four agreed task branch names, ownership boundaries, owner-assignment placeholders, and kickoff checklist.
- Standardized the handoff template; no feature task implementation or runtime contract change was made.
- Froze a shared, unit-explicit road-segment contract with GeoJSON geometry, explicit unknown values, status, confidence, coverage, suitability, and provenance.
- Aligned backend Pydantic validation and frontend TypeScript types; updated the demo fixture to remain unrated when evidence is absent.
- Documented provisional damage scoring, ranking constraints, planned (not implemented) segment API routes, task boundaries, and unresolved decisions.
- Added backend contract validation tests; no scoring engine, segment retrieval routes, dashboard, or computer-vision inference was implemented.

## 0.1.0 - 2026-10-15
- Created a minimal FastAPI backend with a versioned health endpoint at `/api/v1/health`.
- Created a minimal React + TypeScript + Vite frontend landing page.
- Added a validated road-segment schema and deterministic sample fixture.
- Documented architecture, API contract, scoring assumptions, and key tooling decisions.
- Added baseline backend tests for health and schema validation.
- Established repository-level instructions and handoff notes for future agents.
