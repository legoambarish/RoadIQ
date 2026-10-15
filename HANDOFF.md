# RoadIQ handoff

## Date/time and task owner

- Date/time: 2026-10-15 20:06 Asia/Calcutta
- Task: A - scoring engine
- Human owner: not assigned in `TASKS.md`; review is pending.

## Current branch and implementation commit

- Branch: `task/a-scoring-engine`
- Base: `8b0df94` (`origin/main`), fetched before implementation; the working tree was clean.
- Task implementation commit: `8bfba348270b4d0cd9fe0350f08cc84954a42f62` (`Implement provisional RSQI scoring service`).
- Push: blocked; after the human completed Git Credential Manager sign-in, GitHub rejected the push with HTTP 403 (`Permission to Sine-Ads/RoadIQ.git denied to varunkumar-1234`). The remote task branch has not been confirmed present, and no pull request has been opened. An SSH read check also failed, so no alternate authorized identity was available.

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

An organization or repository owner must grant write access to `varunkumar-1234` (or provide an authorized contributor identity). Then push `task/a-scoring-engine` with `git push --set-upstream origin task/a-scoring-engine` and open a pull request against `main`. After review, Task A and Task C should agree the component input and reference-set contract; Task D can then integrate the scorer into its image-analysis route.
