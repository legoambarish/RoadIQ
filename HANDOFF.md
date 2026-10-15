# RoadIQ handoff

## Task D integration/release preparation — 2026-10-15

- **Date/time and owner:** 2026-10-15 22:31 Asia/Calcutta; a human Task D owner is not recorded in TASKS.md.
- **Branch/base:** task/d-integration-release is based on fetched origin/main at 7995ff4, which merges Task A PR #1. The previous D pointer is preserved as local backup/task-d-integration-release-prebase-7995ff4.
- **Live dependency state:** PR #1 is merged. PR #2 for Task B is open at 4718ac6; GitHub reported no submitted reviews or check runs at inspection. Task C is at origin/task/c-computer-vision commit 2afa289, five commits behind and ten ahead of main, with no PR. Its own handoff marks the implementation not ready for integration. No Task D route or runtime contract change has been made.
- **Preparation completed:** updated TASKS.md to reflect live task status and add the Task D integration checklist; added docs/INTEGRATION_CHECKLIST.md with field names, units, status/provenance/null conventions, unresolved proposals, scenario matrix, commands, and environment needs; updated CHANGELOG.md. No shared runtime contract or A/B/C implementation was changed. README.md was not changed because no verified startup or demo instruction correction was identified.
- **Verification run on this Task D checkout:**
  - From frontend: npm install — passed; 27 packages installed, zero vulnerabilities reported.
  - From frontend: npm run build — passed; TypeScript check and Vite production build completed.
  - From frontend: npm run lint — passed; Oxlint completed.
  - From frontend: npm run dev -- --host 0.0.0.0 — Vite started; GET http://127.0.0.1:5173/ returned HTTP 200. This verifies the current main frontend scaffold, not PR #2’s dashboard.
  - From repository root: pytest backend/tests -q — could not start; pytest is not recognized. No backend tests ran.
  - From backend: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 — could not start; uvicorn is not recognized. The host has Python 3.11.15 on PATH and Python 3.14 through the launcher, while README requires 3.12.x. No root .venv exists.
  - Task B’s handoff reports its frontend TypeScript build, Oxlint, and Vite production build passed; that report was not independently rerun against PR #2. Task C’s handoff reports 21 backend tests passed in a temporary environment; that historical result was not rerun here.
  - git diff --cached --check passed for all four staged Task D documentation files.
- **Demo available today:** the current main frontend can be served and its page returns HTTP 200, but the backend health endpoint could not be started in this environment. PR #2 contains a fixture-backed schematic dashboard and local-only image preview with an Unrated report shell; it has no live image/segment API. No complete frontend/backend demo sequence is currently verified.
- **Known issues and release readiness:** no approved Task B integration, no Task C PR or agreed scorer mapping, no active India-only model, no image-analysis route, no labelled aggregate/metal dataset, no held-out evaluation, and no backend test/startup pass on this host. Task A’s default profiles remain empty, so its scorer is unrated without a complete fixed profile. The integration/release goal is not complete.
- **Release commit:** none; this change is Task D preparation only. Record the Task D documentation commit and push/PR outcome after they occur.
- **Exact next action:** review PR #2 with its owner; have the Task C owner align its branch to current main and agree output fields and Task A mapping with affected owners; then implement and test the Task D route only after that agreement. Keep the PR unmerged pending human task-owner approval.

## Previous handoff: Task A scoring engine (preserved)

## Date/time and task owner

- Date/time: 2026-10-15 21:14 Asia/Calcutta
- Task: A - scoring engine
- Human owner: not assigned in `TASKS.md`; review is pending.

## Current branch and implementation commit

- Branch: `task/a-scoring-engine`
- Base: `8b0df94` (`origin/main`), fetched before implementation; the working tree was clean.
- Task implementation commit: `8bfba348270b4d0cd9fe0350f08cc84954a42f62` (`Implement provisional RSQI scoring service`).
- Push: succeeded; `origin/task/a-scoring-engine` tracks the published task branch.
- Pull request: [#1 — Implement provisional RSQI scoring service](https://github.com/Sine-Ads/RoadIQ/pull/1), open against `main`.

## Completed work

- Added `backend/app/services/scoring.py`: typed inputs, finite/unit/provenance validation, fixed surface-type and capture-profile normalization references, configurable versioned weights/labels, formula and contribution explanations, evidence gates, and `unrated` behavior without imputing missing values or renormalizing weights.
- The default config has no normalization references and therefore returns `unrated`. No RoadIQ training-derived reference ranges or calibration are claimed.
- Confidence and spatial evidence coverage remain null. Walking, cycling, two-wheeler, car, and bus suitability remain null because their formulas and evidence requirements are unresolved.
- The `rsqi` payload serializes to the proposed object in `docs/API_CONTRACT.md`. No shared runtime schema, HTTP route, frontend code, or dependency manifest changed.
- Updated `TASKS.md`, `CHANGELOG.md`, `README.md`, `docs/SCORING_SPEC.md`, and `docs/ARCHITECTURE.md` to reflect the implementation and limits.

## Files changed

- `backend/app/services/scoring.py`
- `backend/tests/test_scoring.py`
- `TASKS.md`
- `CHANGELOG.md`
- `README.md`
- `docs/SCORING_SPEC.md`
- `docs/ARCHITECTURE.md`
- `HANDOFF.md`

## Verification

- Python 3.12.14 with the pinned `backend/requirements.txt`: `python -m pytest backend/tests -q -p no:cacheprovider` - passed, 60 tests. One existing Starlette/AnyIO deprecation warning was emitted.
- `git diff --check` - passed.
- Frontend build and lint were not run; no frontend files changed.

## Known limitations and readiness

- The service requires Task C or its caller to provide all five component-level measurements, their units/provenance, quality/ROI/resolution gates, material type, capture profile, and fixed reference ranges. No labelled dataset is available to derive and validate RoadIQ ranges.
- Initial weights and label thresholds remain provisional. Confidence, evidence-coverage calibration, mode-specific suitability, image inference, and an HTTP scoring route remain unimplemented.
- Ready for human review on the task branch; end-to-end integration depends on Task A and Task C agreeing the component input boundary and frozen reference sets, followed by Task D API integration.

## Exact next action

Review and approve PR #1. Before end-to-end integration, Task A and Task C should agree the component input and reference-set contract; Task D can then integrate the scorer into its image-analysis route.
