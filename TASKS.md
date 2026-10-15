# RoadIQ task tracker

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the initial coordination freeze, only `main` existed locally/remotely. Task B is now assigned to the project owner on `task/b-map-dashboard`; remaining task branches follow the ownership table below.
- Human owners are still to be confirmed for Tasks A, C, and D. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Core product objective

RoadIQ is primarily an image-based road-surface quality assessment prototype. Its core image engine should analyze pavement region/quality, individual visible stone aggregates and their boundaries/gaps/coverage/loss, literal metal fragments as a separate class per the project owner’s direction, image texture, and visible deterioration. Map and travel-mode dashboard features are secondary. Support asphalt/bituminous and cement-concrete when evidence supports them; otherwise return unknown. The Task C service validates images and emits a texture proxy, but active damage inference, aggregate/metal segmentation, ROI/material models, RSQI scorer, report UI, image API, and held-out RoadIQ evaluation are not implemented. The owner has directed that all datasets/model training/evaluation use Indian road data only.

## Contract baseline

- Historical contract-freeze branch: `main`. Task C started on `task/c-computer-vision`, which was clean and matched fetched `origin/main` at `8b0df94`.
- Shared contract: [SCORING_SPEC.md](docs/SCORING_SPEC.md), [API_CONTRACT.md](docs/API_CONTRACT.md), and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- The backend Pydantic schema and frontend TypeScript types are aligned. Changes require coordination across owners and matching tests/docs.
- Segment retrieval routes, persistence, scoring, dashboard, and HTTP image-analysis integration are not implemented by this contract-freeze task. Task C has a local image-analysis service; its previous multinational checkpoint is blocked under the India-only data policy.
- Score weights, normalization and labels are provisional hackathon assumptions. Open choices are listed in [DECISIONS.md](docs/DECISIONS.md); do not treat them as silently approved engineering thresholds.

## Cross-task boundaries and ownership

| Task | Scope and file ownership | Explicitly out of scope | Dependencies |
| --- | --- | --- | --- |
| A — Scoring | Own versioned image-feature normalization, provisional RoadIQ Surface Quality Index (RSQI), evidence sufficiency, transparent contributions/explanations, confidence policy, and scorer tests in a dedicated backend scoring service. Consume Task C outputs and the shared contract. | Image inference/annotations, frontend/reporting, API integration, unilateral shared schema changes. No safety/engineering certification. | Written candidate feature/weight proposal in `docs/SCORING_SPEC.md`; C output shape and adequate labelled evidence. |
| B — Frontend/reporting | Own image upload/report experience, annotated-image display, RSQI contribution/evidence/uncertainty presentation, unrated/error states, and secondary map/mode UI in `frontend/`. | Scoring or inference logic; portraying masks as truth; implying missing data means good. | Shared proposed image-analysis response/API contract; can use clearly marked typed fixtures until API exists. |
| C — Aggregate/image analysis | Own image quality gate, pavement ROI, asphalt/concrete/unknown classification, stone-aggregate instance segmentation/features, separate metal-fragment detection, visible defect detection, texture proxies, calibration handling, provenance, and inference tests in the Task C service and focused modules/tests. | RSQI weighting/score decisions, dashboard, map API; no ground dimensions from pixels without calibration. | Task A observation requirements; Task D review of the exact service/HTTP mapping; labelled aggregate/metal annotations and a held-out evaluation set. |
| D — Integration/evaluation | Own API integration and release checks; coordinate dataset versioning/split hygiene and held-out end-to-end/model evaluation reporting with actual metrics. Own `backend/app/api/routes/`, `backend/app/main.py`, integration/evaluation tests and reports. | Replacing A scoring, B UI, or C inference; claiming planned API/model/results exist. | Integrates A/B/C reviewed outputs; dataset/label availability and a frozen held-out test set for evaluation. |

### Branch assignment and human owner

| Task | Human owner | Assigned branch |
| --- | --- | --- |
| A — Scoring | Human owner/reviewer not assigned; implementation merged in PR #1; calibration dependencies remain | `task/a-scoring-engine` |
| B — Frontend/reporting | Human owner/reviewer not recorded; dashboard implementation is in open PR #2 | `task/b-map-dashboard` |
| C — Aggregate/image analysis | Human owner not recorded; partial branch implementation, no PR, not ready for integration | `task/c-computer-vision` |
| D — Integration/evaluation | Human owner not recorded; Task D preparation underway | `task/d-integration-release` |

`main` is the shared integration branch. At this workflow freeze no task branches existed locally or remotely. Each task branch must be based on fetched `main`; send completed task work through reviewed pull requests. Task D coordinates integration, but does not take over A/B/C modules. Dependency manifests and lockfiles are shared-impact files and require review from affected owners.

### Shared file ownership

- `backend/app/schemas/road_segment.py` and `frontend/src/types/road-segment.ts` are frozen cross-task contract files, not owned for unilateral redesign. The task implementing a compatible contract update must coordinate with affected owners and update tests, examples, and documentation.
- `docs/SCORING_SPEC.md`, `docs/API_CONTRACT.md`, `docs/ARCHITECTURE.md`, and `docs/DECISIONS.md` are shared specifications. Task A proposes scoring changes; Task D owns API runtime alignment; any owner may propose amendments through coordinated review.
- Keep demo data under `backend/app/fixtures/` and clearly mark it as a fixture. Do not treat fixture values as production telemetry.

## Acceptance criteria

### Shared segment-contract freeze — completed previously

- [x] One schema defines stable ID, GeoJSON line geometry, survey source/time, typed measurements and units, unknowns, damage fields, surface and mode scores, confidence/coverage, status, explanation, and provenance.
- [x] Backend validation and frontend TypeScript field names/types agree; schema tests cover key valid/invalid boundaries.
- [x] Scoring assumptions, no-imputation/missing-data behavior, limitations, rankings, and unresolved calibration decisions are documented.
- [x] Actual health endpoint is distinguished from planned segment retrieval endpoints.
- [x] Task boundaries, file ownership, dependencies, and outcomes are specified without implementing all four tasks.

### Task A — scoring (merged in PR #1; calibration dependencies remain)

- [x] Implements configurable, versioned candidate image-feature index and exposes every component contribution; initial weights remain hypotheses pending evaluation.
- [x] Selects fixed normalization profiles by surface type and capture profile; never normalizes per image/test cohort. RoadIQ training-derived ranges remain unavailable until a labelled dataset is prepared and reviewed.
- [x] Returns `unrated` with null score when required image quality, usable ROI, material-specific references, resolution, or component evidence is absent; never fills missing values with zero or renormalizes weights silently.
- [x] Separates surface condition from vehicle/pedestrian suitability; mode scores remain null because formulas/evidence rules are unresolved. Confidence and evidence coverage remain null until calibrated.
- [x] Tests formula, normalization boundaries, configuration/version, missing evidence, unknown surface type, confidence/status, mode outputs, and label cutoffs.
- [ ] Supply and validate frozen RoadIQ normalization ranges and confidence/coverage calibration against a labelled dataset; no such dataset currently exists.

Task A implementation is on `task/a-scoring-engine` in `backend/app/services/scoring.py` with focused tests in `backend/tests/test_scoring.py`; PR #1 is merged into `main` at `7995ff4`. It provides a scorer/API boundary only and does not implement Task C feature extraction or Task D API routes/evaluation.

### Task B — dashboard (implementation on branch; PR #2 open; integration pending review)

### Task C — computer vision (in progress)

- [ ] Implements testable image validation/quality gating, usable pavement ROI, and surface-type output (`asphalt_bituminous`, `cement_concrete`, or `unknown`).
- [ ] Segments/counts individual stone aggregates only where resolution permits and reports count, pixel size distribution, visible coverage, boundary/gap statistics, and aggregate-loss proxy with explicit provenance/confidence.
- [ ] Emits counts/m² or physical widths only with ground scale, usable physical area, and sufficient resolution; otherwise returns null physical values and retains valid pixel-space estimates.
- [ ] Detects visible cracks, potholes, raveling, and deterioration; emits named image texture proxies and never calls 2D image texture true 3D roughness/IRI.
- [ ] Preserves unavailable values as null and documents model/checkpoint, preprocessing, calibration method, and limitations.
- [ ] Tests malformed/low-quality inputs, unsupported material/resolution, unit/calibration gates, masks, and unavailable outputs without requiring production weights.

### Task D — integration and release (preparation in progress; integration blocked on dependencies)

- [ ] Implements reviewed image-analysis request/response contract and validation/error behavior; keeps current health route working and marks segment/image routes planned until implemented.
- [ ] Defines dataset manifest/annotation protocol and grouped train/validation/test split; prevents road-segment and feasible near-duplicate leakage across splits.
- [ ] Runs evaluation on a held-out, labelled test set and reports actual counts/metrics by surface class and task (detection/segmentation, aggregate measures, surface index, confidence); never fabricates metrics.
- [ ] Distinguishes untouched pretrained baseline from frozen/finetuned/RoadIQ-trained models and records training data/split/version.
- [ ] Runs backend pytest and frontend build/type/lint checks; records actual commands/results and unresolved issues in `HANDOFF.md`.
- [ ] Confirms configuration/secrets safety and release readiness without claiming production algorithm/model validation.

#### Task D integration checklist

- [ ] Compare frontend fixtures, Task A scorer input/output, Task C observations, and the proposed API field by field; record exact names, units, statuses, provenance, and null rules. Keep mismatches as proposals until affected owners agree.
- [ ] Define tests for valid image analysis; malformed/unsupported/invalid images; failed quality, pavement-region, and resolution gates; unknown surface type; missing/null/unavailable/invalid measurements; unit/status/provenance mismatches; incomplete scorer input and `unrated`; and unavailable model, backend, or API.
- [ ] Verify the frontend shows backend explanations and unavailable fields, keeps mode suitability separate from surface quality, and never presents missing or unrated evidence as a good road.
- [ ] Use clearly labeled fixtures; once an agreed end-to-end flow exists, verify explanations, unavailable values, map colors, mode changes, and details against backend values.
- [ ] Verify repository-documented backend/frontend startup, test, build, and lint commands; record only commands and results confirmed in this environment.
- [ ] Inspect environment variables, secrets handling, model/download requirements, map-provider keys, storage, and network needs without exposing secrets.
- [ ] Add Task D integration tests and attempt release checks only after dependency outputs and the shared mapping are reviewed and agreed.

## Current status

- Core requirements alignment: image-analysis objectives and ownership are documented. Task C's partial service is implemented locally; RSQI, report UI, project-labeled dataset/evaluation, and image API remain unimplemented.
- Tasks A, B, and D remain planned. Task C is in progress: image validation/quality heuristics, a named texture proxy, structured observations, mockable detection, and an optional binary-RLE mask contract exist. One free India-only road/pothole semantic dataset (3,227 images) has been downloaded and audited; an experimental U-Net trainer and checkpoint loader are implemented. Only CPU smoke plumbing was verified; no trained checkpoint or held-out quality result exists, and this runner currently cannot access CUDA. The dataset has no stone-aggregate-instance or metal-fragment labels. Pavement ROI/pothole inference is inactive until a checkpoint is trained/configured; material classification, aggregates, metal, broader damage, raveling, and physical measures remain unavailable; see `docs/VISION_PIPELINE.md`.
- **Handoff snapshot (2026-10-15):** Task C branch includes merge commit `b6f23a33777ecae88d1c52ebbe3499d5f2927740` (`Merge branch 'main' into task/c-computer-vision`), which brought in newer main work and addressed the six previously reported conflicts. PR #4 (`https://github.com/Sine-Ads/RoadIQ/pull/4`) is still open against `main`; the latest live GitHub check showed 15 commits, 19 changed files, and “No conflicts with base branch.” It was not merged. Documentation handoff commit is `01cf01a5a5df56d90b3f45e5f11a2aca889c8bd2`; push status is pending verification. This session's initial `git ls-remote` failed due to DNS, but a later authenticated SSH fetch succeeded and PR #4 was checked in the signed-in browser.
- **Next Task C steps:** (1) fetch current `main` and PR head; inspect every conflict and preserve both branches' intended documentation, then commit/push the conflict resolution to `task/c-computer-vision` only after review; (2) recheck CUDA from the actual trainer runtime before full training; (3) request/prepare India-only close-up imagery with license/permission and reviewed separate aggregate/metal instance annotations; (4) implement and test the corresponding instance-data/model path and held-out evaluation; (5) coordinate the exact output mapping with Task A and Task D, then update PR and handoff. Do not merge PR #4 or claim full Task C completion until the acceptance criteria are met.

## Four-owner kickoff checklist

- [ ] **Task A owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/a-scoring-engine`; implement only scoring scope; test, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task B owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/b-map-dashboard`; implement only frontend/image report scope; test/build/lint, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task C owner:** human name remains unrecorded; implementation is in progress on `task/c-computer-vision`. PR #4 is open and has no conflicts with `main` following merge commit `b6f23a3` (per live GitHub check). The project owner confirmed stone aggregates and literal metal fragments are separate targets. Remaining: obtain A/D review of output/dependency changes, add reviewed aggregate/metal/ROI/material models and labelled evaluation data, then complete the acceptance list.
- [ ] **Task D owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/d-integration-release`; coordinate dependencies, dataset hygiene, held-out evaluation, and reviewed PR integration; run release checks, update status/changelog/handoff, and open/update a PR.
