# Changelog

## Unreleased
- Added Task D integration preparation with a cross-task field audit, unresolved mapping proposals, end-to-end failure scenarios, and verified environment requirements. No route, shared contract, or end-to-end integration is claimed.
- Updated live task status: Task A PR #1 is merged, Task B PR #2 is open, Task C has a partial branch without a PR or active India-only model, and Task D preparation PR #3 is open.

- Added the Task A deterministic candidate RSQI scoring service with configurable weights and labels, fixed surface/capture-specific reference normalization, strict evidence gates, auditable component contributions, null confidence/coverage, and null mode-suitability outputs. No RoadIQ normalization references, inference, API route, or calibrated evaluation are claimed.
- Added focused scoring tests for the formula, thresholds, normalization, evidence gates, units/provenance, deterministic output, mode outputs, and proposed API object shape.
- Aligned the product objective around image-based pavement analysis, with aggregate structure, visible defects, and texture proxies as core evidence.
- Added a provisional image-feature RSQI proposal, measurement/calibration constraints, dataset annotation/split requirements, and held-out evaluation metrics; no metrics or model results are claimed.
- Updated Task A-D ownership/acceptance criteria, architecture pipeline, proposed image-analysis API payload, README demo goal/limitations, and handoff. No inference, scoring, UI, image API, or evaluation feature was implemented.
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
