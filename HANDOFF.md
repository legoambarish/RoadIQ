# RoadIQ handoff

## Date/time and task owner

- Date/time: 2026-10-15 13:53 UTC
- Task owner: Core requirements alignment

## Current branch and latest commit hash

- Branch: `main`
- Base commit: `a0df601` (`Record coordination workflow handoff`), verified after fetching `origin`.
- Alignment commit: `3a4f776` (`Align RoadIQ requirements around image analysis`); handoff metadata commit: `3950cb6` (`Record image-analysis alignment handoff`).
- Push: attempted `git push origin main`; blocked because Git could not obtain a password/credential. Local `main` is ahead of `origin/main`; push must be performed by an authenticated repository owner.

## Goal and completed work

- Recentered the product objective on image-based pavement analysis, especially visible stone aggregates, aggregate boundaries/gaps, surface texture, aggregate-loss indicators, and deterioration.
- Documented a candidate image-feature RoadIQ Surface Quality Index (RSQI), evidence/confidence rules, calibration limits, labelled dataset structure, grouped split hygiene, and held-out evaluation metrics.
- Updated task ownership: C aggregate/image analysis, A scoring, B frontend/reporting, D integration/evaluation. Existing branch names are preserved.
- Updated the architecture pipeline, proposed image-analysis API payload, README core demo goal/limitations, task acceptance criteria, and changelog.
- No image-analysis, scoring, frontend, API route, dataset, or evaluation implementation was started. No model metrics are available or claimed.

## Files changed

- `TASKS.md`
- `docs/SCORING_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACT.md`
- `README.md`
- `CHANGELOG.md`
- `HANDOFF.md`

## Tests/builds run and actual results

- `.venv/bin/pytest backend/tests -q` — passed, 9 tests; one Starlette deprecation warning for `anyio.abc.BlockingPortal`.
- `cd frontend && npm run build && npm run lint` — passed; TypeScript/Vite production build and oxlint succeeded.
- Parsed fenced JSON examples in `docs/API_CONTRACT.md` and `docs/SCORING_SPEC.md` with Python's standard JSON parser — passed.
- `git diff --check` — passed.

## Tests not run

- No image-analysis, scoring, or evaluation tests exist yet; these capabilities remain unimplemented.
- No separate frontend unit-test suite was run; the repository verification path is build/type-check and lint.

## Known issues and blockers

- Confirm with project owner that “metal chips” means stone aggregates.
- No labelled RoadIQ dataset, annotated images, trained/fine-tuned model, or held-out metrics exist in this repository.
- Feature definitions, image-quality/resolution thresholds, normalization references, RSQI weights, confidence calibration/cutoffs, and evaluation acceptance criteria need owner/domain review.
- Image-analysis endpoint, image-specific runtime schemas, upload/storage/privacy policy, calibration format, and annotated-image handling remain proposed only.
- Human names are unassigned for all four task owners; task branches should be created from current `main` when work begins.

## Contract or dependency changes

- Documentation-only proposal for a future image-analysis request/response with units, provenance, confidence, and explicit unavailable values.
- No implementation schema, API runtime, or dependency manifest changed. The future image contract requires review and coordinated backend/frontend schema/test changes before implementation.
- Candidate RSQI feature weights are hypotheses, not approved engineering standards.

## Exact next action

An authenticated repository owner should push the existing `main` commits, assign the four human task owners, and confirm aggregate terminology with the project owner. Then Task C should define/validate the annotation and inference output contract with Task A and Task D before implementing image/aggregate analysis on `task/c-computer-vision`.


## Task C computer-vision handoff — 2026-10-15

- **Branch/base:** `task/c-computer-vision`, based on fetched `origin/main` at `8b0df94`; working tree was clean before this task.
- **Status:** partial implementation committed as `Add Task C road image analysis MVP` on `task/c-computer-vision`; not ready for integration as the aggregate/metal/ROI/material requirements remain unmet.
- **Implemented:** synchronous `app.services.vision.analyze_road_image(image_bytes, *, source_name="unknown", calibration=None, detector=None, confidence_threshold=0.25)`; JPEG/PNG/WebP validation; byte/dimension guards; heuristic quality checks; image-texture proxy; optional RF-DETR crack/pothole observations and normalized/pixel bounding boxes; structured unavailable values, calibration binding, and processing errors. It does not add an HTTP route or scoring.
- **Model:** `dronefreak/rdd2022-rfdetr-nano`, immutable revision `66429f39b916e56c6a33243d776718088f5f43ad`; checkpoint SHA-256 `2d1fba21b829ebc42f7c74f76285d97b2e3295aebe8d97e497d0cc186be98cc9`. Publisher reports Apache-2.0 model; RDD2022 training data is CC BY-SA 4.0. No RoadIQ training or evaluation. Runtime setup and limitations are in `docs/VISION_PIPELINE.md`.
- **Owner direction:** stone aggregates and literal metal fragments are separate targets. Neither has an available validated detector; both measurements remain null.
- **Dependencies:** Task A needs stable observations; Task D must review service-to-HTTP mapping before exposing extra fields (`image`, `reason`, bounding-box detections, `metal_fragments`). No Task A/D owners or sibling implementation threads were available for direct coordination in this workspace.
- **Known gaps:** no pavement ROI, asphalt/concrete classifier, stone/metal instance segmentation, aggregate geometry/loss, raveling, defect masks/area, or RoadIQ held-out evaluation. The complete Task C acceptance list is not met.
- **Verification:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/roadiq-taskc-venv/bin/pytest backend/tests -q` — 20 passed, 1 existing Starlette/AnyIO deprecation warning. `python -m py_compile` passed for the service, schema, and both scripts; `git diff --check` passed. The documented CLI with pinned RF-DETR weights loaded on CPU and returned 1 crack/0 potholes on a synthetic image (smoke check only, no quality claim).
- **Environment:** host Python 3.10.12, no usable NVIDIA driver/GPU; project docs recommend Python 3.12. The optional CPU model stack and checkpoint were installed in temporary `/tmp` environments/cache only, not committed.
- **Push/PR:** `git push origin task/c-computer-vision` could not authenticate (`could not read Username for 'https://github.com': No such device or address`); `gh` is not installed. No PR was opened. Retry push and create a PR against `main` from an authenticated GitHub environment.
