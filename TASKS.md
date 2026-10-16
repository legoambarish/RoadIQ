# RoadIQ task tracker

## Task B Leaflet/OpenStreetMap map implementation — 2026-10-16

Replaced the hand-drawn SVG schematic with a Leaflet map using OpenStreetMap tiles and the existing typed GeoJSON fixture lines. Routes remain selectable, keyboard accessible, zoomable, and recolored by Road Quality or any of the five travel-profile overlays; existing filters, rankings, legend, details, and fixture warnings remain in place. The Engineer panel now surfaces survey source and timestamp, explicitly labeled fixture metadata. Added frontend tests for overlay lookup, status bands, unrated/null handling, filtering/ranking, and visible-segment selection. The map’s route names/scores are still fixture data, distinct from the OSM basemap; map tiles require an internet connection. Implementation commit: `8a06f0c6bf5d2f14637e5a4d52db52d6272f4066` on `task/b-map-dashboard`; pushed branch status and checks are recorded in `docs/HANDOFF.md` and root `HANDOFF.md`.

## Task B Everyday brief layout and explainer clarity — 2026-10-16

Fixed traveler checklist layout so “What matters for this profile” sits above wrapped, responsive items rather than sharing a cramped row; checked the Everyday state for all five profiles in the built site. Clarified in Insights that charts summarize the currently filtered demo network, not the selected map segment or imported image. Expanded image-import help: JSON loads saved report data; optional annotated preview displays the CLI visualization, and the CLI JSON stores its preview as a local path. An annotation can now display on its own or overlay the selected road image. See root `HANDOFF.md` for verification and branch status.

## Task B alignment with latest Task A/C/D updates — 2026-10-16

Reviewed the merged Task C report fields, current Task A scorer defaults, and the latest Task D branch. The B frontend remains API-compatible: Task D's latest changes are docs-only for dependency status, the desktop package still has no image-analysis route, and Task A's scorer defaults remain unrated without configured references. Updated local Task C report rendering to expose the candidate method, analysis path, experimental ROI-gate state, uncalibrated confidence, and measured runtime when present. Refreshed README and architecture status text that still described report import as unavailable. No shared API contract or backend code changed. See root `HANDOFF.md` for branch, changed files, and checks.

## Task B cross-task UI refresh — 2026-10-16

Updated the image-report workspace to reflect the current Task A scorer, Task C local CLI baseline, and Task D Windows package branch. The panel now explains that Task C's untrained texture-region output is CLI-only and not individual aggregate/defect segmentation, that Task A's scorer remains Unrated without evidence and fixed normalization references, and that Task D's package serves the dashboard/health service without an image-analysis route. Production health checks now default to the same-origin `/api/v1`, as used by the Task D package build; `VITE_API_BASE_URL` remains configurable and development retains `http://localhost:8000/api/v1`. Image selection was preview-only at this point; the follow-up below adds manual import of Task C's local JSON report and annotated image without claiming browser-triggered inference.

## Task B Surface Quality selection clarification — 2026-10-16

Made dashboard overlay selection exclusive: travel-profile buttons now reflect the active map overlay instead of retaining a separate highlighted profile, and the Surface Quality overlay uses the same high-contrast selected styling. Renamed the control group for clarity. Verified cycling-to-surface and surface-to-cycling transitions in the built local site; map label/ranking and pressed state update. Frontend typecheck/build, lint, and browser verification passed; see root `HANDOFF.md`.

## Task B local Task C report import — 2026-10-16

Added a browser-local import flow for the existing Task C `analysis-report.json` and optional `annotated-preview.jpg`. The UI validates the report's key structure, renders available image metadata, image quality, texture proxy, and texture-candidate area observations, and keeps absent values unavailable and RSQI Unrated. The CLI report stores its annotation as a local path, so the user must select the companion preview image; data URIs from direct analyzer output are accepted only for supported image types. No image API, backend, scoring, or shared contract was changed. Frontend build and lint passed; exact commands and commit/push state are recorded in root `HANDOFF.md`.

## Task B continuation audit — 2026-10-16

The active checkout is the clean `task/b-map-dashboard` branch at `f83b4d7`, tracking `origin/task/b-map-dashboard`; `git fetch --all --prune` completed and found no newer Task B commit. The assigned Task B UI acceptance items are complete. Its only unchecked acceptance item—displaying reviewed image-analysis output and annotations—depends on Task C/Task D finalizing the response mapping and implementing the image endpoint. Those dependencies remain unresolved, and `docs/API_CONTRACT.md` confirms the endpoint is not implemented. No new UI behavior was added or represented as integrated in this continuation. Frontend typecheck, Vite build, and Oxlint were run directly with the bundled Node runtime and all passed; see root `HANDOFF.md` for exact commands and the npm/pnpm environment limitations.

## Task C MVP continuation — 2026-10-16

The Task C local hackathon MVP is demonstrable on the assigned `task/c-computer-vision` branch. It analyzes a deterministic synthetic texture or a local road image, applies quality checks, produces an untrained texture-candidate mask and annotated JPEG, and writes a structured JSON report. An explicitly configured experimental India-road semantic checkpoint can optionally gate candidates to a predicted road ROI. API and frontend integration remain owned by Task D and Task B.

Verified demo: a 640×480 synthetic image generated with seed 42 completes analysis, reports `unrated`, identifies method `pillow_high_frequency_texture_regions_v1` as `untrained_baseline`, returns a candidate area ratio (not aggregate coverage), keeps individual particle count null, and writes an annotated preview and JSON report with one command. A local image path uses the same runner. Focused Task C suite: 28 passed, 2 skipped; backend suite excluding the unrelated health TestClient case: 87 passed, 2 skipped, 1 deselected. Supplemental ACAD synthetic-concrete sample (20 visually reviewed published test images) measured texture-region pixel IoU 0.488, precision 0.822, recall 0.545; this is not RoadIQ road performance or instance-count evidence. No India-only aggregate-instance labels or active trained checkpoint are present; RoadIQ model metrics remain pending. See `HANDOFF.md` and `README.md` for commands and caveats.

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the initial coordination freeze, only `main` existed locally/remotely. Task B is now assigned to the project owner on `task/b-map-dashboard`; remaining task branches follow the ownership table below.
- Human owners are still to be confirmed for Tasks A, C, and D. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Core product objective

RoadIQ is primarily an image-based road-surface quality assessment prototype. Its core image engine should analyze pavement region/quality, individual visible stone aggregates and their boundaries/gaps/coverage/loss, literal metal fragments as a separate target, image texture, and visible deterioration. Map and travel-mode dashboard features are secondary. Support asphalt/bituminous and cement-concrete when evidence supports them; otherwise return unknown. Task A’s provisional RSQI scorer was merged by PR #1. The fixture-backed Task B dashboard was merged by PR #2; the Everyday/Engineer distinction and sticky-control refinement were merged by PRs #5 and #6. Task C’s India-only branch has a manifest validator, experimental untrained texture-region baseline, and evaluation scaffold, but no trained/active checkpoint, image API, or held-out RoadIQ evaluation. Task D’s integration checklist is merged; no end-to-end flow is implemented.

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
| A — Scoring | Human owner/reviewer not assigned; scorer merged in PR #1 and visible-defect caps in PR #15; calibration dependencies remain | `task/a-scoring-engine` |
| B — Frontend/reporting | Project owner confirmed; dashboard merged in PR #2, view distinction in PR #5, and sticky-control refinement in PR #6 | `task/b-map-dashboard` |
| C — Aggregate/image analysis | Human owner not recorded; Task C PRs #4, #7, #8, #10, and #11 are merged; no active trained checkpoint or held-out RoadIQ evaluation | `task/c-computer-vision` |
| D — Integration/evaluation | Human owner not recorded; integration checklist and Windows package merged in PRs #3 and #12; image upload/scorer integration is under Task D review | `task/d-integration-release` |

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
- [x] Caps RSQI at 55 when normalized visible-defect burden is at least 15, and at 30 when it is at least 25; derives the quality label from the capped score.
- [ ] Supply and validate frozen RoadIQ normalization ranges and confidence/coverage calibration against a labelled dataset; no such dataset currently exists.

Task A implementation is on `task/a-scoring-engine` in `backend/app/services/scoring.py` with focused tests in `backend/tests/test_scoring.py`; PR #1 is merged into `main` at `7995ff4`. It provides a scorer/API boundary only and does not implement Task C feature extraction or Task D API routes/evaluation.

### Task B — dashboard (core and view follow-ups merged in PRs #2, #5, and #6; current remote branch adds handoff documentation only)

- [x] Renders an interactive Leaflet map with OpenStreetMap tiles and selectable, zoomable polylines from the typed GeoJSON schema; color-codes the selected Road Quality or travel-profile overlay. Clearly separates illustrative RoadIQ fixture routes and scores from OSM basemap data.
- [x] Offers five separate travel-profile overlays (walking, cycling, two-wheeler, car, bus), ranked segment lists, quality/search/minimum-score filters, and quality/profile charts.
- [x] Provides materially distinct Everyday traveler briefs and Engineer evidence/provenance audits, including source, survey timestamp, underlying fields, confidence, limitations, unknown-value gates, and score explanations in segment details.
- [x] Keeps all five full travel-profile choices and the Everyday/Engineer switch visible in a sticky control dock while scrolling; controls adapt to narrow screens.
- [x] Uses a calmer sage/forest Everyday palette, a distinct high-contrast Engineer palette, clearer spacing, and larger rounded panels.
- [x] Keeps pedestrian infrastructure and comfort separate; lane markings are not treated as a walkability proxy, and unknown observations remain distinct from observed absence.
- [x] Keeps unrated values null/Unrated and separates surface condition from mode suitability and pedestrian context.
- [x] Clearly marks all sample values as illustrative `demo_fixture` data; main retains health-only API status without claiming segment retrieval. The Task D integration branch adds image analysis but no segment endpoint.
- [x] Provides local image preview and an Unrated/unavailable report state; Task D's branch adds image upload through its API without implying unavailable model evidence.
- [x] Imports and displays available fields from a Task C local CLI JSON report and optional annotated image; the Task D branch additionally connects browser upload to the HTTP image-analysis endpoint.
- [x] Passes frontend TypeScript checks, lint, and Vite production build.

### Task C — computer vision (local hackathon MVP demonstrated; learned inference remains data-limited)

- [x] Validates JPEG/PNG/WebP inputs, applies tested image-quality heuristics, and returns a named image-texture proxy; quality thresholds remain unvalidated on RoadIQ data.
- [ ] Segments a usable pavement ROI and classifies asphalt/concrete/unknown with validated model evidence.
- [x] Provides a transparent untrained high-frequency texture-region baseline, RLE candidate mask, bounding box, image-space area/boundary features, preview annotation, and measured runtime; optionally gates candidates with the experimental India road ROI when a checkpoint is explicitly configured. Labels output as a region candidate only, not particle segmentation.
- [x] Provides a reproducible held-out evaluator for reviewed COCO polygon/uncompressed-RLE or PNG instance masks, reporting pixel IoU/precision/recall and exact manifest/image/label hashes; individual-count MAE remains unavailable.
- [ ] Segments/counts individual stone aggregates only where resolution permits and reports count, pixel size distribution, visible coverage, boundary/gap statistics, and aggregate-loss proxy with explicit provenance/confidence.
- [ ] Emits counts/m² or physical widths only with ground scale, usable physical area, and sufficient resolution; otherwise returns null physical values and retains valid pixel-space estimates.
- [ ] Detects visible cracks, potholes, raveling, and deterioration; emits named image texture proxies and never calls 2D image texture true 3D roughness/IRI.
- [x] Documents and validates JSONL dataset manifests, including labels, provenance, annotation state, scene-group splits, exact duplicates, and perceptual near-duplicates. No aggregate dataset is included.
- [x] Preserves unavailable values as null and documents model/checkpoint, preprocessing, calibration method, and limitations.
- [x] Tests image validation, low-quality gates, manifest/label parsing, missing labels, exact and near duplicates, aggregate-versus-defect separation, RLE mask formats, evaluator test-split gates, and response compatibility without production weights.

The local synthetic/local-image demo and optional experimental ROI-gated texture preview are implemented and tested; Task C PRs #7, #8, #10, and #11 have merged into `main`. The one-command demo writes an annotated JPEG and structured JSON report without network access. The texture overlay is only an untrained high-frequency candidate, not a pavement, aggregate, or defect segmentation. The 20-image ACAD result is supplemental synthetic-concrete region-overlap evidence only (IoU 0.488, precision 0.822, recall 0.545); it is not India-road performance, training evidence, or instance-count validation. No India-only aggregate-instance or metal-fragment labels, active trained checkpoint, calibrated confidence, or held-out RoadIQ road evaluation are available. Browser upload/report and the HTTP image API remain owned by Tasks B/D. The multi-country RDD2022 detector remains disabled under the India-only data policy; that is a dataset-policy choice, not a technical incompatibility with Indian roads.

### Task D — integration and release (Windows package merged; image API/scorer boundary implemented on branch)

- [x] Implements `POST /api/v1/image-analyses` using the existing draft response contract, validation/error behavior, Task C observations, and Task A scorer. Current evidence is insufficient, so valid uploads return Unrated rather than a synthetic score.
- [ ] Defines dataset manifest/annotation protocol and grouped train/validation/test split; prevents road-segment and feasible near-duplicate leakage across splits.
- [ ] Runs evaluation on a held-out, labelled test set and reports actual counts/metrics by surface class and task (detection/segmentation, aggregate measures, surface index, confidence); never fabricates metrics.
- [ ] Distinguishes untouched pretrained baseline from frozen/finetuned/RoadIQ-trained models and records training data/split/version.
- [x] Runs focused image-route/scorer tests and frontend TypeScript/Vite build for the integration; records exact commands/results and unresolved issues in `HANDOFF.md`. Full backend suite and Windows package rebuild remain pending.
- [x] Records configuration/secrets, model/download, map-provider, storage, and network requirements; distinguishes the runnable desktop demo from production analysis/release readiness.
- [x] Builds a one-file Windows desktop package and verifies bundled dashboard/health startup, token-gated restart, and safe replacement of a verified RoadIQ process.

#### Task D integration checklist

- [x] Add desktop-runtime tests for dashboard asset serving and authenticated restart, plus image-route tests for unavailable evidence and the scorer cap boundary.
- [x] Verify the Windows build, startup and second-launch graceful restart on the available Windows 11 host; record the clean-VM limitation.

- [x] Compare frontend fixtures, Task A scorer input/output, Task C observations, and the API field by field; record exact names, units, statuses, provenance, and null rules. Keep unresolved mappings unavailable.
- [x] Specify and test valid uploads, empty/invalid images, unknown surface type, missing component evidence, `unrated`, and the visible-defect cap through the HTTP response.
- [ ] Complete browser-level validation that the API-connected frontend shows backend explanations and unavailable fields without presenting missing or unrated evidence as a good road.
- [x] Keep dashboard fixture values tagged demo_fixture; they are illustrative, not RoadIQ observations or model predictions.
- [ ] After the shared evidence mapping is reviewed, verify explanations and unavailable values against backend values; mode suitability remains unscored.
- [x] Verify repository-documented backend/frontend startup, test, build, and lint commands; record only commands and results confirmed in this environment.
- [x] Inspect environment variables, secrets handling, model/download requirements, map-provider keys, storage, and network needs without exposing secrets. The .env.example file contains development settings and URLs only; the packaged app needs no runtime credentials, map key, model download, storage service, or internet connection. No real credential is required or present in .env.example; no tracked .env, key, or certificate file was found.
- [x] Add Task D integration tests for the current API/scorer boundary; Windows release checks remain pending.

## Current status

- Task A's scorer is merged by PR #1 and the visible-defect caps by PR #15. RoadIQ normalization and confidence calibration still lack labelled data.
- The Task B dashboard is merged in PRs #2, #5, #6, and #13. Its map/fixture UI and local CLI report import remain distinct from the current Task D branch's local image upload integration.
- Task C's local image-analysis demo, evaluation scaffold, and optional experimental India-road ROI gating are merged into `main` by PRs #4, #7, #8, #10, and #11. No India-road aggregate labels or held-out RoadIQ road metrics exist. Physical measurements, material classification, aggregate/metal instance analysis, and broad validated damage detection remain unavailable.
- Task D's checklist and Windows package are merged by PRs #3 and #12. Its current branch adds a local image API and dashboard upload integration; the integration returns Unrated with current evidence and has not been reviewed/merged or packaged as a new `.exe`.
- Branch alignment (2026-10-16): Task D was fast-forwarded to latest `origin/main` at `4107965` before the integration update. The working integration changes are local and unpushed.
- Current Task D verification (2026-10-16): focused image-route/scorer tests passed (59 passed); `cd frontend && npm run build` and `cd frontend && npm run lint` passed; `git diff --check` passed. Full backend tests, browser validation, and Windows build/runtime checks were not run for this change.

## Four-owner kickoff checklist

- [ ] **Task A owner/reviewer:** still not recorded; PR #1 is merged. Resolve the remaining labelled-data normalization and confidence-calibration dependency before claiming a validated score.
- [x] **Task B owner/reviewer:** project owner confirmed; dashboard PR #2 and view follow-ups PRs #5 and #6 merged. Current fixtures and image preview are not live segment or image API integration.
- [ ] **Task C owner:** not recorded; the local demo and optional ROI-gated preview are merged. Obtain appropriate India-only aggregate/metal labels and a held-out road evaluation set before implementing or claiming learned instance/model quality. Coordinate any service/API contract changes with Tasks A and D.
- [ ] **Task D owner:** not recorded; PR #3 integration checklist is merged. Keep shared-contract mappings proposed until affected owners agree, then integrate only approved outputs and add tests.
