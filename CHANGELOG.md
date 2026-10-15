# Changelog

## Unreleased
- Enforced the project owner's India-only data direction: block the legacy multinational road-damage checkpoint and mark production inference unavailable until an India-only model is reviewed and pinned. Audited India-specific dataset leads and documented limits on geography, labels, licensing, checkpoint availability, and split evidence; ACAD and non-Indian road data are excluded.
- Added the Task C observation schema and image-analysis service, with safe input validation, explicit unavailable measurements, separate stone-aggregate/metal-fragment fields, and a mockable RF-DETR adapter.
- Originally added pinned optional RF-DETR setup/download workflow; this checkpoint is now blocked because it was trained on multinational data, and no India-only checkpoint is active.
- Added focused image-pipeline tests and updated architecture, task status, API notes, README, and handoff.
- Aligned the product objective around image-based pavement analysis, with aggregate structure, visible defects, and texture proxies as core evidence.
- Added a provisional image-feature RSQI proposal, measurement/calibration constraints, dataset annotation/split requirements, and held-out evaluation metrics; no metrics or model results are claimed.
- Updated Task A-D ownership/acceptance criteria and the proposed image-analysis API payload. Task C provides image validation, heuristic quality observations, and a named texture proxy; active damage inference, aggregate/material/ROI analysis, scoring, UI, HTTP upload route, and RoadIQ evaluation remain unimplemented.
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
