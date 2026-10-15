# RoadIQ task tracker

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the initial coordination freeze, only `main` existed locally/remotely. Task B is now assigned to the project owner on `task/b-map-dashboard`; remaining task branches follow the ownership table below.
- Human owners are still to be confirmed for Tasks A, C, and D. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Core product objective

RoadIQ is primarily an image-based road-surface quality assessment prototype. Its core image engine should analyze pavement region/quality, individual visible stone aggregates (provisionally interpreting “metal chips” as aggregates, pending owner confirmation), aggregate boundaries/gaps/coverage/loss, image texture, and visible deterioration. Map and travel-mode dashboard features are secondary. Support asphalt/bituminous and cement-concrete when evidence supports them; otherwise return unknown. A provisional RSQI scoring service is implemented on `task/a-scoring-engine` and is under review in PR #1. Image analysis, report UI, image API, and held-out model evaluation are not implemented.

## Contract baseline

- Current agreed working branch: `main` (also the branch at task start).
- Shared contract: [SCORING_SPEC.md](docs/SCORING_SPEC.md), [API_CONTRACT.md](docs/API_CONTRACT.md), and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- The backend Pydantic schema and frontend TypeScript types are aligned. Changes require coordination across owners and matching tests/docs.
- Segment retrieval routes, persistence, scoring, dashboard, and computer-vision inference are not implemented by this contract-freeze task.
- Score weights, normalization and labels are provisional hackathon assumptions. Open choices are listed in [DECISIONS.md](docs/DECISIONS.md); do not treat them as silently approved engineering thresholds.

## Cross-task boundaries and ownership

| Task | Scope and file ownership | Explicitly out of scope | Dependencies |
| --- | --- | --- | --- |
| A — Scoring | Own versioned image-feature normalization, provisional RoadIQ Surface Quality Index (RSQI), evidence sufficiency, transparent contributions/explanations, confidence policy, and scorer tests in a dedicated backend scoring service. Consume Task C outputs and the shared contract. | Image inference/annotations, frontend/reporting, API integration, unilateral shared schema changes. No safety/engineering certification. | Written candidate feature/weight proposal in `docs/SCORING_SPEC.md`; C output shape and adequate labelled evidence. |
| B — Map and dashboard | Own the interactive road map and overlays, five travel profiles, Everyday/Engineer views, filters, rankings, charts, segment details, and image-report presentation in `frontend/`. | Scoring or inference logic; portraying masks as truth; implying missing data means good; claiming a live basemap, segment API, or image-analysis API exists. | Frozen road-segment contract and clearly marked typed fixtures; reviewed A/C result interfaces and Task D API integration before displaying live analysis. |
| C — Aggregate analysis | Own image quality gate, pavement ROI, asphalt/concrete/unknown classification, aggregate instance segmentation/features, defect detection, texture proxies, calibration handling, provenance, and inference tests in `backend/app/services/vision.py` and dedicated modules/tests. | RSQI weighting/score decisions, dashboard, map API; no ground dimensions from pixels without calibration. | Confirm “metal chips” means stone aggregates; shared field/unit contract and annotated-label protocol. |
| D — Integration/evaluation | Own API integration and release checks; coordinate dataset versioning/split hygiene and held-out end-to-end/model evaluation reporting with actual metrics. Own `backend/app/api/routes/`, `backend/app/main.py`, integration/evaluation tests and reports. | Replacing A scoring, B UI, or C inference; claiming planned API/model/results exist. | Integrates A/B/C reviewed outputs; dataset/label availability and a frozen held-out test set for evaluation. |

### Branch assignment and human owner

| Task | Human owner | Assigned branch |
| --- | --- | --- |
| A — Scoring | TBD; assign before implementation | `task/a-scoring-engine` |
| B — Map and dashboard | Project owner (confirmed 2026-10-15) | `task/b-map-dashboard` |
| C — Aggregate/image analysis | TBD; assign before implementation | `task/c-computer-vision` |
| D — Integration/evaluation | TBD; assign before implementation | `task/d-integration-release` |

`main` is the shared integration branch. At this workflow freeze no task branches existed locally or remotely. Create task branches from up-to-date `main`; send completed task work through reviewed pull requests. Task D coordinates integration, but does not take over A/B/C modules. Dependency manifests and lockfiles are shared-impact files and require review from affected owners.

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

### Task A — scoring (implemented; PR #1 open; calibration dependencies remain)

- [x] Implements configurable, versioned candidate image-feature index and exposes every component contribution; initial weights remain hypotheses pending evaluation.
- [x] Selects fixed normalization profiles by surface type and capture profile; never normalizes per image/test cohort. RoadIQ training-derived ranges remain unavailable until a labelled dataset is prepared and reviewed.
- [x] Returns `unrated` with null score when required image quality, usable ROI, material-specific references, resolution, or component evidence is absent; never fills missing values with zero or renormalizes weights silently.
- [x] Separates surface condition from vehicle/pedestrian suitability; mode scores remain null because formulas/evidence rules are unresolved. Confidence and evidence coverage remain null until calibrated.
- [x] Tests formula, normalization boundaries, configuration/version, missing evidence, unknown surface type, confidence/status, mode outputs, and label cutoffs.
- [ ] Supply and validate frozen RoadIQ normalization ranges and confidence/coverage calibration against a labelled dataset; no such dataset currently exists.

Task A implementation is on `task/a-scoring-engine` in `backend/app/services/scoring.py` with focused tests in `backend/tests/test_scoring.py`. PR #1 is open against `main`. It provides a scorer/API boundary only and does not implement Task C feature extraction or Task D API routes/evaluation.

### Task B — map and dashboard (in progress)

- [x] Renders an interactive schematic map from typed GeoJSON fixtures, with selectable, zoomable segments and a color-coded Road Quality overlay. No live basemap is claimed while provider choice is unresolved.
- [x] Offers five separate travel-profile overlays (walking, cycling, two-wheeler, car, bus), ranked segment lists, quality/search/minimum-score filters, and quality/profile charts.
- [x] Provides Everyday and Engineer views, with contract-field evidence, units/status, provenance, unknown values, and score explanations in segment details.
- [x] Keeps unrated values null/Unrated and separates surface condition from mode suitability and pedestrian context.
- [x] Clearly marks all sample values as illustrative `demo_fixture` data; retains the health-only API honestly and does not claim segment retrieval or image analysis is connected.
- [x] Provides a local-only image preview and Unrated/unavailable report shell. It does not upload files or imply inference/annotation occurred.
- [ ] Displays real reviewed image-analysis outputs and annotated images after Task C/Task D finalize the compatible API response and endpoint.
- [x] Passes frontend TypeScript checks, lint, and Vite production build.

### Task C — computer vision (planned)

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

- Core requirements alignment: Task B now has an interactive fixture-backed map/dashboard and local-only image-report shell; image API integration remains unimplemented.
- Task A scoring and Task D API integration/evaluation remain planned. Task B is in progress with the map/dashboard criteria above implemented. Task C has separate remote work that is not integrated into this branch.

## Four-owner kickoff checklist

- [ ] **Task A owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/a-scoring-engine`; implement only scoring scope; test, update status/changelog/handoff, push, and open/update a PR.
- [x] **Task B owner:** Project owner confirmed ownership on 2026-10-15. Work on `task/b-map-dashboard`; map/dashboard implementation and frontend checks are recorded in `HANDOFF.md`. Live image-analysis response/annotation display still depends on A/C interface agreement and Task D API integration.
- [ ] **Task C owner:** confirm human owner and confirm “metal chips” means stone aggregates; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/c-computer-vision`; implement only image/aggregate-analysis scope; test, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task D owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/d-integration-release`; coordinate dependencies, dataset hygiene, held-out evaluation, and reviewed PR integration; run release checks, update status/changelog/handoff, and open/update a PR.
