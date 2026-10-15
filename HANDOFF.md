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
- **Status:** partial implementation committed as `Add Task C road image analysis MVP` on `task/c-computer-vision`; not ready for integration as the aggregate/metal/ROI/material requirements remain unmet. A later India-only policy change disables the checkpoint described below.
- **Implemented:** synchronous `app.services.vision.analyze_road_image(image_bytes, *, source_name="unknown", calibration=None, detector=None, confidence_threshold=0.25)`; JPEG/PNG/WebP validation; byte/dimension guards; heuristic quality checks; image-texture proxy; a mockable detector adapter; structured unavailable values, calibration binding, and processing errors. It does not add an HTTP route or scoring. Production damage inference is currently unavailable.
- **Legacy model, disabled:** `dronefreak/rdd2022-rfdetr-nano`, immutable revision `66429f39b916e56c6a33243d776718088f5f43ad`; checkpoint SHA-256 `2d1fba21b829ebc42f7c74f76285d97b2e3295aebe8d97e497d0cc186be98cc9`. It was trained on a six-country RDD2022 corpus, so loading is rejected under the owner's India-only data policy. The old smoke test was plumbing-only and is not an India-focused model result.
- **Owner direction:** stone aggregates and literal metal fragments are separate targets. Neither has an available validated detector; both measurements remain null.
- **Dependencies:** Task A needs stable observations; Task D must review service-to-HTTP mapping before exposing extra fields (`image`, `reason`, bounding-box detections, `metal_fragments`). No Task A/D owners or sibling implementation threads were available for direct coordination in this workspace.
- **Known gaps:** no pavement ROI, asphalt/concrete classifier, stone/metal instance segmentation, aggregate geometry/loss, raveling, defect masks/area, or RoadIQ held-out evaluation. The complete Task C acceptance list is not met.
- **Data policy:** the owner directed India-only data and specifically excluded all other sources; ACAD was initially considered but must not be used. Current aggregate and literal metal labels remain unavailable.
- **Verification:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/roadiq-taskc-venv/bin/pytest backend/tests -q` — 20 passed, 1 existing Starlette/AnyIO deprecation warning. `python -m py_compile` passed for the service, schema, and both scripts; `git diff --check` passed. The documented CLI with pinned RF-DETR weights loaded on CPU and returned 1 crack/0 potholes on a synthetic image (smoke check only, no quality claim).
- **Environment:** host Python 3.10.12, no usable NVIDIA driver/GPU; project docs recommend Python 3.12. The optional CPU model stack and checkpoint were installed in temporary `/tmp` environments/cache only, not committed.
- **Push/PR:** `git push origin task/c-computer-vision` could not authenticate (`could not read Username for 'https://github.com': No such device or address`); `gh` is not installed. No PR was opened. Retry push and create a PR against `main` from an authenticated GitHub environment.

## Task C India-only continuation — 2026-10-15

- **Branch:** `task/c-computer-vision`; fetched `origin/task/c-computer-vision` and confirmed it still points to `8595ccca93246f0ac97c656f6e3f96eb7839aaf4` before this continuation. Local working tree includes the India-only checkpoint guard, test, dataset review, and documentation updates; commit/push status must be refreshed after verification.
- **Owner direction:** India-only imagery for training, validation, and evaluation; literal metal fragments and stone aggregates remain separate classes. The owner chose not to use ACAD/non-Indian data.
- **India-specific candidates reviewed:**
  - [Siddhesh Road Damage Detection India v2](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2): Roboflow lists CC BY 4.0, 7,706 images, 5,394/1,541/771 splits, object-detection exports, and stretch-resize to 720×720. No export was acquired; verify original source relation, taxonomy, provenance, duplicate/group leakage, and exact license before training/evaluation.
  - [Indian Roads semantic segmentation dataset](https://platform.ultralytics.com/ultralytics/datasets/indian-roads-semantic-segmentation): road/footpath/pothole-related masks may help ROI or visible damage; page was inaccessible during review. A public catalog reports GPL-2.0 and 3,227 images; confirm against original publisher before use. It has no aggregate-instance or metal-fragment labels.
  - [Indian Footpath Damage Segmentation dataset](https://zenodo.org/records/17154852): 583 Indian footpath images with pixel masks, 4.5 GB archive. This is Pune footpath data, not road-pavement validation; review the archive license and masks before considering adjacent-domain experiments.
  - [iWatchRoadv2 paper/data lead](https://arxiv.org/html/2510.16375v1): describes 7,000+ India-collected, box-annotated pothole frames and links a Kaggle set. Paper license is CC BY-NC-SA 4.0; confirm data license, access, and split grouping independently. This is a preprint and not RoadIQ evaluation.
  - [DriveIndia paper](https://arxiv.org/html/2507.19912v1): India traffic-object boxes include pothole but not aggregate or metal classes; the paper describes academic/non-commercial release via TiHAN. Verify availability and data terms if considered.
  - User's [roadside-debris Roboflow link](https://universe.roboflow.com/rds-hkpkm/roadside-debris) was not inspectable. Its India origin, class taxonomy, and license could not be confirmed; generic debris labels are not sufficient for a metal-fragment detector.
  - User's [Siddhesh India road damage project](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2) is the same candidate listed above.
- **Implementation change:** loader refuses the pinned six-country checkpoint and reports no India-only model configured. Detector mocks remain available for wrapper tests only. No India dataset was downloaded and no training/evaluation metrics are claimed.
- **Verification:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/roadiq-taskc-venv/bin/pytest backend/tests -q` — 21 passed, 1 existing Starlette/AnyIO deprecation warning. `python3 -m py_compile backend/app/services/vision.py backend/app/schemas/image_analysis.py backend/scripts/analyze_road_image.py` passed. `git diff --check` passed. Frontend checks were not run because no frontend files changed.
- **Commit/push/PR:** continuation changes are not yet committed at handoff update time. Push and PR status to be refreshed after commit attempt. Real model training remains blocked on auditable India-only data, split/license review, and model/annotation coverage for aggregate plus metal-fragment targets.
