# Changelog

## Unreleased
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
