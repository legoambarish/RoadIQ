# RoadIQ task tracker

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the initial coordination freeze, only `main` existed locally/remotely. Task B is now assigned to the project owner on `task/b-map-dashboard`; remaining task branches follow the ownership table below.
- Human owners are still to be confirmed for Tasks A, C, and D. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Core product objective

RoadIQ is primarily an image-based road-surface quality assessment prototype. Its core image engine should analyze pavement region/quality, individual visible stone aggregates and their boundaries/gaps/coverage/loss, literal metal fragments as a separate target, image texture, and visible deterioration. Map and travel-mode dashboard features are secondary. Support asphalt/bituminous and cement-concrete when evidence supports them; otherwise return unknown. Task A’s provisional RSQI scorer was merged by PR #1. The fixture-backed Task B dashboard was merged by PR #2 and its Everyday/Engineer distinction by PR #5; this branch adds persistent controls and a visual usability refinement. Task C’s India-only branch has a manifest validator, experimental untrained texture-region baseline, and evaluation scaffold, but no trained/active checkpoint, image API, or held-out RoadIQ evaluation. Task D’s integration checklist is merged; no end-to-end flow is implemented.

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
| A — Scoring | Human owner/reviewer not assigned; implementation merged in PR #1; calibration dependencies remain | `task/a-scoring-engine` |
| B — Frontend/reporting | Project owner confirmed; dashboard merged in PR #2 and Everyday/Engineer distinction in PR #5; current sticky-control refinement on branch | `task/b-map-dashboard` |
| C — Aggregate/image analysis | Human owner not recorded; India-only experimental baseline and evaluation scaffold on remote branch; no trained checkpoint or PR | `task/c-computer-vision` |
| D — Integration/evaluation | Human owner not recorded; integration checklist merged in PR #3; runtime integration remains pending | `task/d-integration-release` |

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

### Task A — scoring (merged in PR #1; calibration dependencies remain)

- [x] Implements configurable, versioned candidate image-feature index and exposes every component contribution; initial weights remain hypotheses pending evaluation.
- [x] Selects fixed normalization profiles by surface type and capture profile; never normalizes per image/test cohort. RoadIQ training-derived ranges remain unavailable until a labelled dataset is prepared and reviewed.
- [x] Returns `unrated` with null score when required image quality, usable ROI, material-specific references, resolution, or component evidence is absent; never fills missing values with zero or renormalizes weights silently.
- [x] Separates surface condition from vehicle/pedestrian suitability; mode scores remain null because formulas/evidence rules are unresolved. Confidence and evidence coverage remain null until calibrated.
- [x] Tests formula, normalization boundaries, configuration/version, missing evidence, unknown surface type, confidence/status, mode outputs, and label cutoffs.
- [ ] Supply and validate frozen RoadIQ normalization ranges and confidence/coverage calibration against a labelled dataset; no such dataset currently exists.

Task A implementation is on `task/a-scoring-engine` in `backend/app/services/scoring.py` with focused tests in `backend/tests/test_scoring.py`; PR #1 is merged into `main` at `7995ff4`. It provides a scorer/API boundary only and does not implement Task C feature extraction or Task D API routes/evaluation.

### Task B — dashboard (core merged in PR #2 and view follow-up in PR #5; current UI refinement on branch)

- [x] Renders an interactive schematic map from typed GeoJSON fixtures, with selectable, zoomable segments and a color-coded Road Quality overlay. No live basemap is claimed while provider choice is unresolved.
- [x] Offers five separate travel-profile overlays (walking, cycling, two-wheeler, car, bus), ranked segment lists, quality/search/minimum-score filters, and quality/profile charts.
- [x] Provides materially distinct Everyday traveler briefs and Engineer evidence/provenance audits, with unknown-value gates and score explanations in segment details.
- [x] Keeps all five full travel-profile choices and the Everyday/Engineer switch visible in a sticky control dock while scrolling; controls adapt to narrow screens.
- [x] Uses a calmer sage/forest Everyday palette, a distinct high-contrast Engineer palette, clearer spacing, and larger rounded panels.
- [x] Keeps pedestrian infrastructure and comfort separate; lane markings are not treated as a walkability proxy, and unknown observations remain distinct from observed absence.
- [x] Keeps unrated values null/Unrated and separates surface condition from mode suitability and pedestrian context.
- [x] Clearly marks all sample values as illustrative `demo_fixture` data; retains the health-only API honestly and does not claim segment retrieval or image analysis is connected.
- [x] Provides a local-only image preview and Unrated/unavailable report shell. It does not upload files or imply inference/annotation occurred.
- [ ] Displays real reviewed image-analysis outputs and annotated images after Task C/Task D finalize the compatible API response and endpoint.
- [x] Passes frontend TypeScript checks, lint, and Vite production build.

### Task C — computer vision (partial branch implementation; no PR; not ready for integration)

- [ ] Implements testable image validation/quality gating, usable pavement ROI, and surface-type output (`asphalt_bituminous`, `cement_concrete`, or `unknown`).
- [ ] Segments/counts individual stone aggregates only where resolution permits and reports count, pixel size distribution, visible coverage, boundary/gap statistics, and aggregate-loss proxy with explicit provenance/confidence.
- [ ] Emits counts/m² or physical widths only with ground scale, usable physical area, and sufficient resolution; otherwise returns null physical values and retains valid pixel-space estimates.
- [ ] Detects visible cracks, potholes, raveling, and deterioration; emits named image texture proxies and never calls 2D image texture true 3D roughness/IRI.
- [ ] Preserves unavailable values as null and documents model/checkpoint, preprocessing, calibration method, and limitations.
- [ ] Tests malformed/low-quality inputs, unsupported material/resolution, unit/calibration gates, masks, and unavailable outputs without requiring production weights.

The latest Task C remote branch is `task/c-computer-vision` at `3e5f791`. Its handoff records India-only dataset manifest validation, an untrained texture-region heuristic, and evaluation scaffolding; this is experimental plumbing, not an active trained detector. No trained/active checkpoint or held-out model-quality result is available; aggregate-instance and metal-fragment labels remain unavailable, and no image API is integrated. The multi-country RDD2022 detector remains disabled under the India-only data policy; that is a dataset-policy choice, not a technical incompatibility with Indian roads. C response/dependency changes still need A/D review. This branch has no PR.

### Task D — integration and release (integration checklist merged; runtime integration blocked on dependencies)

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

- Task A’s provisional RSQI scorer was merged into `main` by PR #1 at `7995ff4`; its RoadIQ normalization and confidence calibration still lack labelled data.
- The fixture-backed dashboard was merged by PR #2 and the Everyday/Engineer distinction by PR #5. This branch carries a new sticky selector and presentation refinement, pending publication/review.
- Task C’s latest remote work is `3e5f791`; its India-only experimental baseline is not a trained active detector and no aggregate/metal labels, image API, or held-out RoadIQ evaluation are available.
- Task D’s docs-only integration checklist was merged in PR #3; runtime integration remains blocked on reviewed A/B/C mappings and dependencies.

## Four-owner kickoff checklist

- [ ] **Task A owner/reviewer:** still not recorded; PR #1 is merged. Resolve the remaining labelled-data normalization and confidence-calibration dependency before claiming a validated score.
- [x] **Task B owner/reviewer:** project owner confirmed; dashboard PR #2 and view follow-up PR #5 merged. Publish the current sticky-control/presentation refinement for review. Current fixtures and image preview are not live segment or image API integration.
- [ ] **Task C owner:** not recorded; continue the India-only experimental baseline on `task/c-computer-vision`, obtain appropriate India-only aggregate/metal labels, validate the output contract and held-out evaluation, then open a PR. No C PR is currently open.
- [ ] **Task D owner:** not recorded; PR #3 integration checklist is merged. Keep shared-contract mappings proposed until affected owners agree, then integrate only approved outputs and add tests.
