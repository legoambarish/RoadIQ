# RoadIQ handoff

## Task D integration/release preparation — 2026-10-15

- **Date/time and owner:** 2026-10-15 22:31 Asia/Calcutta; a human Task D owner is not recorded in TASKS.md.
- **Branch/base/commit:** task/d-integration-release is based on fetched origin/main at 7995ff4, which merges Task A PR #1. Task D documentation preparation commit ef647675adf8b1e723c69c0d5559155c7b6aebba is pushed to origin/task/d-integration-release and is under review in [PR #3](https://github.com/Sine-Ads/RoadIQ/pull/3). The previous D pointer is preserved as local backup/task-d-integration-release-prebase-7995ff4.
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
- **Release commit:** none; this is Task D documentation preparation only. The preparation commit is ef647675adf8b1e723c69c0d5559155c7b6aebba; it is pushed and PR #3 is open. No integration or release code has been committed.
- **Exact next action:** review PR #3 and PR #2 with their owners; have the Task C owner align its branch to current main and agree output fields and Task A mapping with affected owners; then implement and test the Task D route only after that agreement. Keep all PRs unmerged pending their approved review process and human task-owner approval.

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

An authenticated repository owner should push the existing `main` commits, assign the four human task owners, and confirm aggregate terminology with the project owner. Then Task C should define/validate the annotation and inference output contract with Task A and Task D before implementing image/aggregate analysis on `task/c-computer-vision`.

---

## Task B — Map and dashboard handoff

### Date/time and ownership

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

## Task C branch publication update — 2026-10-15

- The SSH-authenticated push succeeded. `origin/task/c-computer-vision` now points to `35d88c03ffedbdd29f50b1b9c50b6527589c1954` (`Document India aggregate and metal annotation needs`); the worktree is clean and branch is synchronized.
- The latest added annotation guide documents the manual Indian image/label needs. Eight original selected-dataset frames were visually reviewed; the road-scene views do not resolve individual aggregate grains and have no metal-fragment labels.
- No PR has been created. The GitHub comparison page is available at `https://github.com/Sine-Ads/RoadIQ/compare/main...task/c-computer-vision`, but this browser session is signed out. Continue PR creation after the owner authenticates in the open browser tab, or the owner may create it directly.

## Task C complete-session handoff — 2026-10-15

- **Branch / tip:** `task/c-computer-vision`; handoff commit `65ee031` (`Record Task C agent handoff`) is on top of `b6f23a33777ecae88d1c52ebbe3499d5f2927740` (`Merge branch 'main' into task/c-computer-vision`). That merge commit brought in newer main work and was fetched from GitHub in this session. The handoff commit was rebased onto it without conflicts and pushed successfully with a normal fast-forward update. This final status correction may advance the exact branch tip; use `git log -1` for the final hash.
- **Implemented:** India-only policy disables the prior multinational damage checkpoint; image validation and quality observations, a named pixel-texture proxy, structured observation schema/service, mockable detector adapter, India road/pothole semantic segmentation trainer and optional binary RLE masks; one India-only road dataset downloaded/audited (3,227 image/mask pairs); aggregate/metal annotation guide. The segmentation path is experimental and no trained checkpoint is enabled. It does not fulfill aggregate or metal detection.
- **Incomplete:** no active India-only model/checkpoint; no full CUDA training or held-out model-quality evaluation; no pavement/material classifier, aggregate instance segmenter, metal-fragment detector, broad validated damage/raveling coverage, calibrated physical aggregate measurements, or image HTTP route; Task D has not frozen/reviewed the optional mask mapping. The dataset has road/footpath/shallow/pothole semantic labels only, no aggregate instances or metal. Full Task C acceptance criteria are not met; not ready for integration as a complete Task C MVP.
- **Actual verification on implementation:** `PYTHONPATH=/home/ads/.local/lib/python3.10/site-packages /tmp/roadiq-venv/bin/python -m pytest -q backend/tests` — 26 passed; `python3 -m compileall -q backend/app backend/scripts backend/tests` — passed; `git diff --check` — passed. One-batch CPU smoke run completed, macro IoU 0.0148, no checkpoint; plumbing-only, not quality evidence. In the earlier trainer environment, PyTorch reported CUDA unavailable and `nvidia-smi` could not communicate with the driver. These are historical results and were not rerun during this documentation handoff.
- **PR #4:** `https://github.com/Sine-Ads/RoadIQ/pull/4`, title “Task C: India-only road segmentation baseline”, base `main`, head `task/c-computer-vision`. Initial live observation showed conflicts in `CHANGELOG.md`, `HANDOFF.md`, `README.md`, `TASKS.md`, `docs/ARCHITECTURE.md`, and `docs/SCORING_SPEC.md`. The branch was subsequently updated with merge commit `b6f23a3` from `main`. A current signed-in GitHub page shows PR #4 still Open, now 15 commits and 19 files changed, with “No conflicts with base branch” and automatic merging available. It has not been merged. The Task C owner did not merge it in this handoff.
- **Blockers / local changes:** no implementation working-tree changes were present before preparing this handoff. This handoff-only commit was rebased onto the fetched branch merge to preserve newer work; verify its push below. Runner CUDA visibility is unresolved. New India-only annotated aggregate/metal photos and rights evidence are still needed.
- **Next agent exact steps:**
  1. Read `AGENTS.md`, `TASKS.md`, `HANDOFF.md`, `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, `docs/SCORING_SPEC.md`, and `docs/VISION_PIPELINE.md`; inspect `git status`, branch, and remotes.
  2. Confirm the final handoff commit is pushed; the initial push was rejected because remote had advanced, so the handoff was rebased onto fetched merge commit `b6f23a3` and then pushed with a normal fast-forward update. Do not force-push.
  3. PR #4's prior six conflict paths were resolved by the already-pushed merge commit `b6f23a3` from `main`; a live PR page showed “No conflicts with base branch.” Do not merge the PR as part of handoff unless the owner explicitly asks.
  4. Recheck `nvidia-smi` and `torch.cuda.is_available()` inside the exact runner/container that will execute training. Do not assume host GPU visibility transfers into the trainer.
  5. Ask the owner for India-only close-up images, usage permission/license evidence, separate reviewed `stone_aggregate` and `metal_fragment` polygons/masks, and route/session IDs. Keep captures from each route/session grouped in a held-out split. The owner said they can look for labeled images; none were received in this handoff.
  6. Coordinate output/schema changes with Task A and Task D. Implement the instance-data adapter and appropriate model path only after suitable labels and split/provenance review; run focused tests, full backend tests, training, and held-out evaluation with actual metrics. Document unsupported physical measurements without calibration.
  7. Update the PR description/status and handoff with resulting commit, exact test/training metrics, dataset/license/split details, and unresolved gaps. Ask the owner for review; do not mark the goal complete until all acceptance criteria are evidenced.
- **Handoff update verification:** `git diff --check` passed. The edits were restricted to `TASKS.md`, `CHANGELOG.md`, and `HANDOFF.md`; the documentation-only commit was rebased onto the fetched remote merge commit without conflicts. GitHub access was initially unavailable by DNS but later worked over SSH and in the signed-in browser. No tests were rerun because the change is documentation-only. At the moment this paragraph was written, verify final commit hash, cleanliness, and push state before handing off.

- The project owner has since pushed the original Task B branch; this follow-up is based on and tracks `origin/task/b-map-dashboard`.
- Made the schematic map the first major dashboard panel, before summary metrics, and made its interactive route colors and no-basemap status more visible.
- Added larger, clearer text and a warm editorial Everyday palette. Engineer mode now switches to a dark inspection-console theme, changes the page heading and summary metrics, and keeps technical provenance/evidence details visible.
- The map is still schematic fixture geometry; a real tile basemap remains unavailable pending map-provider selection and integration.
- Verification: frontend TypeScript build check, Oxlint, and Vite production build passed after the UI changes. Browser accessibility snapshot confirmed the map is present immediately after the header/notice and the dashboard has differentiated Everyday/Engineer content.
- Latest changes are recorded in the follow-up commit on `task/b-map-dashboard`.

### Task B latest-upstream alignment — 2026-10-15

- **Branch:** `task/b-map-dashboard`; fast-forwarded to `origin/task/b-map-dashboard` at `4718ac6`, which includes a merge of current `main` (`7995ff4`). No rebase, reset, or force push was used.
- **Latest Task A state:** PR #1's scorer is merged into `main` at `backend/app/services/scoring.py`. It uses a provisional 35/20/15/15/15 weighting across visible defect burden, aggregate loss, gap anomaly, texture anomaly, and aggregate-distribution anomaly. The default normalization profiles are empty, so the scorer returns `unrated`; confidence/coverage are null and travel-mode scores are not produced.
- **Latest Task C state checked:** `origin/task/c-computer-vision` at `2afa289` contains a partial image-analysis service, schema, and tests, but is not merged into `main` and has no HTTP endpoint. The prior multi-country damage model is disabled under the India-only policy; ROI/material classification and aggregate/metal models are unavailable. The C response schema and dependencies have not been reviewed with Task A/D for integration.
- **Task B update:** the image-report shell now displays the scorer's candidate weights and the evidence/default-reference reasons no numeric RSQI is shown. It distinguishes stone aggregates from literal metal fragments and keeps all not-connected outputs explicitly unavailable. Updated Task B status docs to reflect the merged A scorer and partial, unintegrated C work. No scoring, inference, shared runtime schema, API route, or dependency implementation was added.
- **Verification:** from `frontend/`, `node_modules/.bin/tsc.CMD -b`, `node_modules/.bin/oxlint.CMD`, and `node_modules/.bin/vite.CMD build` all passed. Browser accessibility inspection confirmed the updated RSQI weights, status text, and unavailable evidence fields render. `git diff --check` passed. PR #2 is open and GitHub reports no conflicts with `main`.
- **Remaining:** live scoring/report integration awaits reviewed C-to-A observation mapping and Task D's API endpoint. The fixture map/values remain illustrative; no basemap, live segment feed, or travel-suitability calculation is connected.

### Task B mode distinction follow-up — 2026-10-15

- **Scope:** Everyday and Engineer presentation only. No scoring formula, scoring weights, API contract, backend scorer, or Task C inference code was changed.
- **Commits:** implementation `8e03561` (`Differentiate everyday and engineer dashboard views`); latest-main merge `660c368` (`Merge latest main into Task B dashboard branch`). The branch now includes current `origin/main` at `5bbf491` and had four commits not on `origin/main` before this handoff note was committed.
- **Publication:** GitHub confirms original Task B PR #2 is already merged. These follow-up commits are local and require a new PR after push. Push attempts failed because Git Credential Manager could not access saved credentials (`Access is denied`); no remote changes were made.
- **Everyday:** selected travel profile now receives a plain-language traveler brief with profile-specific considerations and a clear note that fixture scores are not route/safety recommendations.
- **Engineer:** selected profile now receives its contract evidence ledger with current values, availability/status, and provenance, plus confidence/coverage and formula-readiness gates. Insights switch to a measurement availability/provenance audit instead of the Everyday summaries.
- **Separate pedestrian context:** footpath, crossings, and comfort display independently from surface score. Unknown is distinguished from observed absence; copy states that lane markings are not a walkability proxy and that traffic exposure/accessibility are not represented by current fields.
- **Task C clarification:** the multi-country RDD2022 checkpoint remains disabled to follow the India-only data policy; this is a policy choice, not a claim of technical incompatibility with Indian roads.
- **Latest upstream status checked:** Task C remote `023da26` records an audited download of the India-only 3,227-image semantic road/pothole dataset and a U-Net training/checkpoint path; only CPU smoke plumbing is reported, with no trained/active checkpoint, aggregate/metal labels, or held-out quality result. Task D's integration checklist merged in PR #3; it adds no runtime API integration.
- **Verification:** `node_modules/.bin/tsc.CMD -b`, `node_modules/.bin/oxlint.CMD`, `node_modules/.bin/vite.CMD build`, and `git diff --check` passed. Browser accessibility inspection confirmed Everyday traveler brief and Engineer evidence ledger/provenance audit render and switch correctly.
- **Remaining:** all road values remain illustrative fixtures; mode formulas and live API/model data remain unconnected. This follow-up is ready for review, not a validated scoring release.
