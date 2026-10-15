# RoadIQ task tracker

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the coordination workflow freeze, only `main` existed locally/remotely; create each task branch from an up-to-date `main` when its owner begins work.
- Human owner names have not been supplied; assign one human owner to each task before implementation. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Core product objective

RoadIQ is primarily an image-based road-surface quality assessment prototype. Its core image engine should analyze pavement region/quality, individual visible stone aggregates and their boundaries/gaps/coverage/loss, literal metal fragments as a separate class per the project owner’s direction, image texture, and visible deterioration. Map and travel-mode dashboard features are secondary. Support asphalt/bituminous and cement-concrete when evidence supports them; otherwise return unknown. The Task C service now validates images and supports optional crack/pothole inference, but aggregate/metal segmentation, ROI/material models, RSQI scorer, report UI, image API, and held-out RoadIQ evaluation are not implemented.

## Contract baseline

- Historical contract-freeze branch: `main`. Task C started on `task/c-computer-vision`, which was clean and matched fetched `origin/main` at `8b0df94`.
- Shared contract: [SCORING_SPEC.md](docs/SCORING_SPEC.md), [API_CONTRACT.md](docs/API_CONTRACT.md), and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- The backend Pydantic schema and frontend TypeScript types are aligned. Changes require coordination across owners and matching tests/docs.
- Segment retrieval routes, persistence, scoring, dashboard, and HTTP image-analysis integration are not implemented by this contract-freeze task. Task C now has a local image-analysis service with optional crack/pothole inference.
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
| A — Scoring | TBD; assign before implementation | `task/a-scoring-engine` |
| B — Frontend/reporting | TBD; assign before implementation | `task/b-map-dashboard` |
| C — Aggregate/image analysis | TBD; assign before implementation | `task/c-computer-vision` |
| D — Integration/evaluation | TBD; assign before implementation | `task/d-integration-release` |

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

### Task A — scoring (planned)

- [ ] Implements configurable, versioned candidate image-feature index and exposes every component contribution; initial weights remain hypotheses pending evaluation.
- [ ] Uses surface-type/capture-aware normalization, with frozen training references and no per-image/test-cohort normalization.
- [ ] Returns `unrated` with null score when required image quality, usable ROI, material-specific features, or component evidence is absent; never fills missing values with zero or renormalizes weights silently.
- [ ] Separates surface condition from vehicle/pedestrian suitability; produces transparent score reasons and calibrated confidence only.
- [ ] Tests formula, normalization boundaries, configuration/version, missing evidence, unknown surface type, confidence/status, and label cutoffs.

### Task B — dashboard (planned)

- [ ] Supports the future image-analysis workflow and renders the submitted image with an annotated overlay and explanatory report.
- [ ] Shows image-quality/ROI status, surface type or unknown, aggregate/defect/texture evidence and units, index contributions, confidence, unavailable values, and limitations.
- [ ] Clearly renders Low Confidence or Unrated and never presents unrated as good; distinguishes image-derived texture proxies from physical roughness.
- [ ] Keeps surface condition separate from mode suitability and pedestrian access/context; does not infer pedestrian-friendliness from missing lane markings.
- [ ] Handles the currently implemented health-only API honestly; no claim that planned image/segment APIs exist.
- [ ] Passes frontend TypeScript checks, lint, and Vite production build.

### Task C — computer vision (in progress)

- [ ] Implements testable image validation/quality gating, usable pavement ROI, and surface-type output (`asphalt_bituminous`, `cement_concrete`, or `unknown`).
- [ ] Segments/counts individual stone aggregates only where resolution permits and reports count, pixel size distribution, visible coverage, boundary/gap statistics, and aggregate-loss proxy with explicit provenance/confidence.
- [ ] Emits counts/m² or physical widths only with ground scale, usable physical area, and sufficient resolution; otherwise returns null physical values and retains valid pixel-space estimates.
- [ ] Detects visible cracks, potholes, raveling, and deterioration; emits named image texture proxies and never calls 2D image texture true 3D roughness/IRI.
- [ ] Preserves unavailable values as null and documents model/checkpoint, preprocessing, calibration method, and limitations.
- [ ] Tests malformed/low-quality inputs, unsupported material/resolution, unit/calibration gates, masks, and unavailable outputs without requiring production weights.

### Task D — integration and release (planned)

- [ ] Implements reviewed image-analysis request/response contract and validation/error behavior; keeps current health route working and marks segment/image routes planned until implemented.
- [ ] Defines dataset manifest/annotation protocol and grouped train/validation/test split; prevents road-segment and feasible near-duplicate leakage across splits.
- [ ] Runs evaluation on a held-out, labelled test set and reports actual counts/metrics by surface class and task (detection/segmentation, aggregate measures, surface index, confidence); never fabricates metrics.
- [ ] Distinguishes untouched pretrained baseline from frozen/finetuned/RoadIQ-trained models and records training data/split/version.
- [ ] Runs backend pytest and frontend build/type/lint checks; records actual commands/results and unresolved issues in `HANDOFF.md`.
- [ ] Confirms configuration/secrets safety and release readiness without claiming production algorithm/model validation.

## Current status

- Core requirements alignment: image-analysis objectives and ownership are documented. Task C's partial service is implemented locally; RSQI, report UI, project-labeled dataset/evaluation, and image API remain unimplemented.
- Tasks A, B, and D remain planned. Task C is in progress: image validation/quality heuristics, a named texture proxy, structured observations, and an optional pretrained crack/pothole wrapper exist. ROI, surface classification, stone/metal segmentation, raveling, and physical measures remain unavailable; see `docs/VISION_PIPELINE.md`.

## Four-owner kickoff checklist

- [ ] **Task A owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/a-scoring-engine`; implement only scoring scope; test, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task B owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/b-map-dashboard`; implement only frontend/image report scope; test/build/lint, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task C owner:** human name remains unrecorded; implementation is in progress on `task/c-computer-vision`. The project owner confirmed stone aggregates and literal metal fragments are separate targets. Remaining: obtain A/D review of output/dependency changes, add reviewed aggregate/metal/ROI/material models and labelled evaluation data, then complete the acceptance list.
- [ ] **Task D owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/d-integration-release`; coordinate dependencies, dataset hygiene, held-out evaluation, and reviewed PR integration; run release checks, update status/changelog/handoff, and open/update a PR.
