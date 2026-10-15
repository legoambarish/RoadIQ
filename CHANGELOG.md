# Changelog

## Unreleased
- Added a sticky, responsive dashboard control dock with all five full travel-profile names and the Everyday/Engineer switch visible while scrolling; refined spacing and a comfortable sage/forest palette while preserving a distinct Engineer theme.
- Reworked Everyday and Engineer into distinct assessment experiences: Everyday gets profile-specific plain-language briefs; Engineer gets evidence/status/provenance tables and record-readiness audits. Surface condition, mode suitability, and pedestrian infrastructure remain separate, with all fixture values identified as illustrative.
- Updated the Task B branch against the latest `main` integration checklist and refreshed the Task B/C/D status from their current branches. No score formula, API contract, backend scorer, or Task C inference code changed.
- Added Task D integration preparation with a cross-task field audit, unresolved mapping proposals, end-to-end failure scenarios, and verified environment requirements. No route, shared contract, or end-to-end integration is claimed.
- Updated live task status: Task A PR #1, Task B dashboard PR #2, Task B view distinction PR #5, and Task D checklist PR #3 are merged. Task C has an India-only experimental baseline and evaluation scaffold on its branch but no active trained checkpoint or PR. The RDD2022 detector remains disabled under the India-only policy, not for technical incompatibility.

- Added the Task A deterministic candidate RSQI scoring service with configurable weights and labels, fixed surface/capture-specific reference normalization, strict evidence gates, auditable component contributions, null confidence/coverage, and null mode-suitability outputs. No RoadIQ normalization references, inference, API route, or calibrated evaluation are claimed.
- Added focused scoring tests for the formula, thresholds, normalization, evidence gates, units/provenance, deterministic output, mode outputs, and proposed API object shape.
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

## 2026-10-15 — Task C India-only segmentation experiment

- Added a compact PyTorch U-Net training/inference path for the one selected free India-only e-Yantra/IIT Bombay road semantic segmentation dataset. It supports road ROI and semantic pothole pixels, not aggregate instances or metal fragments.
- Added optional row-major binary RLE masks to pavement ROI and defect observations. Semantic pothole masks leave instance count unavailable; image-space ratios are not physical measurements.
- Added safe extraction of only the primary raw-image and mask files, sequence split checks, metadata-bearing checkpoints, and CPU/CUDA selection. Sample/batch-limited runs never save checkpoints.
- Audited and extracted 3,227 paired images/masks; source archive SHA-256: `a25aa4922fa4b7af7098832fad3f31f226721d4638abca1970081c0fe35a09af`.
- Verification: full backend suite 26 passed; Python compileall and `git diff --check` passed. A one-batch CPU smoke run verified the loader/model/metrics path but produced plumbing-only metrics and no checkpoint. No CUDA device was visible in the runner, so full training and quality evaluation were not run.

## 2026-10-15 — Task C PR handoff snapshot

- Recorded actual Task C implementation and remaining work in `TASKS.md` and `HANDOFF.md`. Branch `task/c-computer-vision` is at `023da26f3a23b63ed75b3cdce580be1ef326598d`, pushed and clean before this documentation update.
- PR #4 targets `main`; it was subsequently updated with merge commit `b6f23a33777ecae88d1c52ebbe3499d5f2927740` to bring in newer main work. A live GitHub check then showed the PR open with 15 commits, 19 changed files, and no conflicts with the base branch. It was not merged.
- Handoff docs were committed as `65ee031`, rebased onto `b6f23a3` to preserve newer remote work, and pushed successfully using a normal fast-forward update. A final documentation correction may advance the branch tip; confirm the exact final hash with `git log -1`.
- Tests actually run for implementation: backend suite 26 passed; compileall and `git diff --check` passed; one-batch CPU smoke run completed with plumbing-only macro IoU 0.0148, no checkpoint. These are historical results, not rerun for this documentation-only handoff. No full model training/evaluation was completed.
