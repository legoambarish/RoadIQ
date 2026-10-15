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

- **Branch:** `task/c-computer-vision`; fetched `origin/task/c-computer-vision` at `8595ccca93246f0ac97c656f6e3f96eb7839aaf4`. India-only policy implementation commit: `aebb91b` (`Enforce India-only vision model policy`).
- **Owner direction:** India-only imagery for training, validation, and evaluation; literal metal fragments and stone aggregates remain separate classes. The owner chose not to use ACAD/non-Indian data.
- **India-specific candidates reviewed:**
  - [Siddhesh Road Damage Detection India v2](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2): Roboflow lists CC BY 4.0, 7,706 images, 5,394/1,541/771 splits, object-detection exports, and stretch-resize to 720×720. No export was acquired; verify original source relation, taxonomy, provenance, duplicate/group leakage, and exact license before training/evaluation.
  - [Indian Roads semantic segmentation dataset](https://platform.ultralytics.com/ultralytics/datasets/indian-roads-semantic-segmentation): road/footpath/pothole-related masks may help ROI or visible damage; page was inaccessible during review. A public catalog reports GPL-2.0 and 3,227 images; confirm against original publisher before use. It has no aggregate-instance or metal-fragment labels.
  - [Indian Footpath Damage Segmentation dataset](https://zenodo.org/records/17154852): 583 Indian footpath images with pixel masks, 4.5 GB archive. This is Pune footpath data, not road-pavement validation; review the archive license and masks before considering adjacent-domain experiments.
  - [iWatchRoadv2 paper/data lead](https://arxiv.org/html/2510.16375v1): describes 7,000+ India-collected, box-annotated pothole frames and links a Kaggle set. Paper license is CC BY-NC-SA 4.0; confirm data license, access, and split grouping independently. This is a preprint and not RoadIQ evaluation.
  - [DriveIndia paper](https://arxiv.org/html/2507.19912v1): India traffic-object boxes include pothole but not aggregate or metal classes; the paper describes academic/non-commercial release via TiHAN. Verify availability and data terms if considered.
  - User's [roadside-debris Roboflow link](https://universe.roboflow.com/rds-hkpkm/roadside-debris) was not inspectable. Its India origin, class taxonomy, and license could not be confirmed; generic debris labels are not sufficient for a metal-fragment detector.
  - User's [Siddhesh India road damage project](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2) is the same candidate listed above.
  - Official [IDD semantic segmentation](https://insaan.iiit.ac.in/datasets/) is an India-only ROI candidate but requires registration and data-term review. A public [IDD drivable-area baseline](https://github.com/SenorPsycho/idd-road-segmentation) reports 0.9649 validation IoU and an MIT code license, but no accessible checkpoint artifact/hash was confirmed; “drivable” is a proxy, not necessarily a pavement mask.
  - The RDS workspace [H4B](https://universe.roboflow.com/rds-hkpkm/h4b) page lists 599 generic `Garbage`/`Debris` images and CC BY 4.0, but India provenance is unverified and its classes do not identify metal. Excluded under the India-only policy.
  - A [rural India road-boundary dataset on Zenodo](https://zenodo.org/records/15869374) advertises polygon labels but no populated license field; do not use without permission terms. [ThirdEye's India dataset](https://huggingface.co/datasets/thirdeyelabs/indian-road-dataset) advertises CC BY 4.0 but uses machine-generated, unverified labels and requires acceptance of access conditions; do not use as ground-truth evaluation.
  - A similarly named [IRD-Dataset on Zenodo](https://zenodo.org/records/21370736) advertises 4,352 images with boxes/polygons/masks, but the metadata identifies Baghdad, Iraq as the collection site. Explicitly excluded from all RoadIQ work under the India-only policy.
- **Implementation change:** loader refuses the pinned six-country checkpoint and reports no India-only model configured. Detector mocks remain available for wrapper tests only. No India dataset was downloaded and no training/evaluation metrics are claimed.
- **Verification:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/roadiq-taskc-venv/bin/pytest backend/tests -q` — 21 passed, 1 existing Starlette/AnyIO deprecation warning. `python3 -m py_compile backend/app/services/vision.py backend/app/schemas/image_analysis.py backend/scripts/analyze_road_image.py` passed. `git diff --check` passed. Frontend checks were not run because no frontend files changed.
- **Push/PR:** `git push origin task/c-computer-vision` failed because this environment has no GitHub HTTPS credentials (`could not read Username for 'https://github.com': No such device or address`). No PR was opened. Commits `aebb91b`, `a31e425`, and `6bed43a` remain local and ahead of origin. Real model training remains blocked on auditable India-only data, split/license review, and model/annotation coverage for aggregate plus metal-fragment targets.

## Task C India-only follow-up — 2026-10-15

- Re-read the required repository instructions, task tracker, handoff, architecture, API, and scoring documents on `task/c-computer-vision`; working tree was clean at the start of this session.
- Added the public [RSPNet](https://github.com/YLong-maker/RSPNet) IDD segmentation weights as an ROI candidate only. Its README links Semantic-FPN/U-Net `.pth` files and reports mIoU, but this review did not fetch/hash the weights; repository code/weight licensing, preprocessing, and mask semantics are not established. Do not enable it until those are reviewed. Road/drivable masks may not equal the usable pavement area.
- The user is looking for India road images with distinct stone-aggregate and metal-fragment labels. No data has been received or used yet; no non-Indian imagery or ACAD is permitted.
- **Current branch tip before this follow-up:** `a936cb1` (`Record non-India dataset exclusion`); branch remains ahead of origin. This update is documentation-only; prior backend verification remains 21 passed with one pre-existing Starlette/AnyIO deprecation warning. `git diff --check` passed for the follow-up documentation changes.
- **Remaining:** implement reviewed ROI/material/aggregate/metal/defect models and held-out India evaluation once suitable labeled data and reviewed weights are available; coordinate observation mapping with Task A/D. Push and PR remain blocked by absent GitHub credentials (see prior entry).

## Task C user-provided data-source audit — 2026-10-15

- Rechecked the eight links supplied by the owner against the India-only policy. Findings and restrictions are recorded in `docs/VISION_PIPELINE.md`.
- Siddhesh Roboflow currently lists 7,706 images, CC BY 4.0, and nine RDD-style damage box classes; no aggregate or metal class. India-only image provenance and duplicate-safe splits still need export review.
- Mendeley RDD2020 is mixed India/Japan/Czechia and CC BY-NC 3.0. Do not use the full set; a verified India-only partition could be considered only if the owner accepts non-commercial-only data.
- BharatPotHole is described by its associated project as 7,000+ India dashcam pothole frames, but the Kaggle card/license was inaccessible. Treat as a pothole-only candidate pending rights and split review. Mitangshu's Kaggle dataset license and labels were also not independently verified; do not download/use yet.
- TiHAN describes DriveIndia as an annotated India camera dataset with pothole among its traffic classes, but access requires an EULA/request. It has no aggregate/metal masks. The user's RDS Roboflow debris URL remains inaccessible and generic debris labels cannot identify metal.
- ThirdEye's Hugging Face record confirms CC BY 4.0 and Delhi NCR coverage, but labels are machine-generated, not human-verified, and access requires acceptance of the repository conditions. Do not use it for gold held-out evaluation.
- No aggregate/metal-labeled images were received in this update. The owner said they are looking for such labels.
- **Verification:** web source review only plus `git diff --check`; no data was downloaded and no model trained or evaluated. Existing backend result remains 21 tests passed with one existing deprecation warning.
- **Open product choice:** none on non-commercial-only use; the owner approved non-commercial licensed sources for the free prototype.

## Task C free/open-source constraint — 2026-10-15

- The owner clarified that all tools and data must be free; paid APIs and paid dataset tiers are out. They also approved non-commercial licenses for this prototype.
- RDD2020's CC BY-NC 3.0 license is therefore eligible for consideration, but only an India-only partition may be used. Its public metadata lists 1.85 GB total files. Mendeley's file download endpoint returned an internal error while retrieving the small file-structure listing, so no archive or image was fetched.
- No paid service or dataset export was used. The Kaggle card for BharatPotHole and the other Kaggle source still needs a verifiable license and free-access path.
- No model/data implementation changed in this step; only documentation was updated. Continue by resolving free India-only image/label access and verify source split grouping before training or evaluation.
- A free e-Yantra/IIT Bombay Indian Roads segmentation dataset lead is now recorded: 3,227 India images, four pixel-labeled classes (road, footpath, shallow path, pothole), GPL-2.0, and an indicated Kaggle source. It can support ROI/pothole experimentation after original-source access and split review; it has no aggregate/metal classes and no checkpoint is configured.

## Task C India-only road/pothole segmentation experiment — 2026-10-15

- **Branch:** `task/c-computer-vision`.
- **Data choice:** following the owner's India-only, free-only direction, only one dataset was downloaded: [e-Yantra/IIT Bombay Indian Roads semantic segmentation](https://platform.ultralytics.com/ultralytics/datasets/indian-roads-semantic-segmentation), Kaggle ID `eyantraiit/semantic-segmentation-datasets-of-indian-roads`. Public Kaggle metadata reports GPL-2.0. This prototype is non-commercial. Archive size: 2,881,656,373 bytes; SHA-256: `a25aa4922fa4b7af7098832fad3f31f226721d4638abca1970081c0fe35a09af`; ZIP CRC test passed. Extracted only primary JPEG and PNG label masks (excluded duplicate NumPy copy): 3,227/3,227 pairs. Published split: 2,475 train / 752 validation; four train sequence IDs and three disjoint validation sequence IDs. No independent test split. All stems paired and no duplicate raw-image SHA-256 was found.
- **Label scope:** source IDs map 0 road, 2 footpath, 3 shallow path, 4 pothole, 255 ignore. It supports semantic road ROI and pothole pixels only. No individual stone aggregate or metal-fragment labels are present. Do not interpret semantic masks as instance counts or physical dimensions. The owner still needs to provide or help source India-labeled stone and metal data for those targets.
- **Code:** `backend/app/services/india_road_segmentation.py` has dataset adapter, compact U-Net, checkpoint inference, and `row_major_binary_rle_v1` encoder. `backend/scripts/train_indian_road_segmentation.py` safely prepares data and trains/evaluates on published train/validation sequences. Set `ROADIQ_SEGMENTATION_MODEL_PATH` to a trained checkpoint to enable the optional segmenter. The synchronous Task D call is `analyze_road_image(image_bytes, source_name="road.jpg", calibration=None)`; injected `segmentation_model` is intended for tests. Task D should review the optional `pavement_region.mask_rle` and `defects[].mask_rle` additions before freezing its HTTP response mapping.
- **Compute/results:** this runner has Torch 2.5.1+cu121 but reports `torch.cuda.is_available() == False`; `nvidia-smi` cannot communicate with the driver. The user reports GPU visibility in their own terminal, so the discrepancy may be runner/sandbox passthrough. A 1-train-batch/1-validation-batch CPU smoke run at 128×64 completed, reported macro IoU 0.0148 and saved no checkpoint. This tiny run is plumbing-only and not model-quality evidence; no full training, held-out testing, or active checkpoint exists. Recheck GPU in the same execution environment before deciding whether to train.
- **RLE contract:** `encoding="row_major_binary_rle_v1"`, `size_px=[height,width]`, `counts` starts with background (possibly zero) and alternates background/foreground; counts sum to pixel count. Masks are optional. Pothole instance count stays unavailable for semantic masks.
- **Verification:** `PYTHONPATH=/home/ads/.local/lib/python3.10/site-packages /tmp/roadiq-venv/bin/python -m pytest -q backend/tests` — 26 passed. `python3 -m compileall -q backend/app backend/scripts backend/tests` and `git diff --check` passed. `/tmp/roadiq-venv` is temporary and not part of the repository.
- **Remaining:** the segmentation model is not trained or enabled; aggregate/metal detection, material classification, broader damage detection, held-out evaluation, and Task D endpoint integration remain open. Full Task C is not integration-ready. Push/PR status must be checked after commit; prior GitHub HTTPS auth failed in this environment.
- **Latest implementation commit:** `d218820` (`Add India road segmentation experiment`); it is local on `task/c-computer-vision` and not pushed. Push attempt failed with `could not read Username for 'https://github.com': No such device or address`; no PR was created. Once GitHub credentials are available, push this branch and open a PR against `main`.

## Task C aggregate/metal manual-data preparation — 2026-10-15

- Searched for free India-only road-surface data with both stone-aggregate instances and metal-fragment labels. No suitable source was found. The Indian Footpath Damage dataset labels footpath damage masks, so it does not close either class gap and was not downloaded.
- Added `docs/INDIA_AGGREGATE_METAL_ANNOTATION_GUIDE.md` with India provenance, route-group split, distinct per-object polygon labels, review rules, and evaluation expectations. RoadIQ's current trainer still only supports semantic road/pothole classes; a COCO instance adapter is still required after labels arrive.
- No images or annotations were added. The owner may provide close-range Indian road photographs, separately masked polygons for `stone_aggregate` and `metal_fragment`, a route/session-grouped train/validation/test manifest, and license/permission evidence.
