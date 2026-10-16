# Changelog

## 2026-10-16 — Task B Leaflet/OpenStreetMap map and dashboard tests

- Replaced the drawn SVG street schematic with an interactive Leaflet map using OpenStreetMap tiles, attribution, accessible selectable fixture polylines, and map zoom controls. Tile failures show a notice while fixture routes remain available.
- Kept the fixture routes, scores, overlays, ranking, and score legend explicitly identified as illustrative RoadIQ data; the basemap is not evidence that those segments were surveyed.
- Added survey source and timestamp to the Engineer record audit, labeled the values as fixture metadata, and clarified that the demo timestamps are not actual surveys.
- Extracted dashboard filter/ranking/selection helpers and added tests for all five profile overlays, surface overlay, quality tone boundaries, null/unrated behavior, active-overlay minimum filters, ranking order, and visible segment selection.
- Added pinned Leaflet/TypeScript definitions and Vitest dependencies. TypeScript build, Vite production build, Oxlint, and six frontend unit tests passed. Implementation commit: `8a06f0c6bf5d2f14637e5a4d52db52d6272f4066` on `task/b-map-dashboard`; see `docs/HANDOFF.md` for exact commands, browser verification, and final branch status.

## 2026-10-16 — Task B traveler brief and report-import clarity

- Reflowed Everyday traveler profile checklists into a responsive layout with the label above the items; verified all five profiles in the browser.
- Labeled Insights as summaries of currently filtered demo records, distinct from the selected map segment and uploaded image.
- Explained the Task C JSON and annotated-image imports and made an imported annotation preview visible even when no original road image is selected.
- Frontend TypeScript/Vite build and Oxlint passed; see `HANDOFF.md` for browser verification and limitations.

## 2026-10-16 — Task B alignment with latest Task C report output

- Audited the latest merged Task C, Task A, and Task D state. B can continue importing saved C reports; there is still no browser image endpoint and A's default scorer references remain empty.
- Added report-backed candidate method, analysis path, optional road-ROI-gate status, confidence calibration state, and inference runtime to the Task B report view.
- Corrected frontend/root README and architecture text to distinguish local report import from browser-triggered image upload/inference, and to describe the optional experimental ROI gate accurately.
- Frontend TypeScript/Vite build, Oxlint, and diff checks are recorded in `HANDOFF.md`.

## 2026-10-16 — Task B Surface Quality overlay selection

- Made travel-profile and Surface Quality overlay selection mutually exclusive in both pressed state and selected styling. The previous travel profile no longer remains highlighted when the map is displaying Surface Quality.
- Renamed the overlay control group and verified both directions of selection in the built local site. TypeScript/Vite build and Oxlint passed.

## 2026-10-16 — Task B local Task C report import

- Added local JSON report import and optional annotated-image import to the image analysis workspace. Available Task C image quality, metadata, texture proxy, and texture-candidate area values are displayed from the saved report; missing evidence remains unavailable and RSQI stays Unrated.
- Kept CLI execution local and manual. The browser does not upload images, run analysis, or call a new API. The CLI report's annotation path requires selecting the accompanying preview file.
- Frontend TypeScript/Vite production build and Oxlint passed; see `HANDOFF.md` for exact commands and current branch state.

## 2026-10-16 — Task B cross-task UI refresh

- Updated the image-report workspace with the current Task A scorer evidence/reference gates, Task C local-only untrained texture-region MVP and limitations, and Task D desktop package scope. The browser image preview remains local and does not claim inference.
- Made the production health client use the same-origin `/api/v1` by default, matching Task D's packaged-dashboard build; development still targets the local backend and explicit `VITE_API_BASE_URL` overrides remain supported.
- TypeScript build, Vite production build, and Oxlint passed. No shared contract, inference behavior, or scoring logic changed.

## 2026-10-16 — Task B continuation audit

- Audited the assigned `task/b-map-dashboard` branch and confirmed the existing frontend acceptance items are complete except for image-analysis report integration, which remains dependent on Task C/Task D API agreement and endpoint work.
- Verified frontend TypeScript, Vite production build, and Oxlint using the bundled Node runtime. No product code or shared API contract changed.
- Recorded the repository documentation-path mismatch: the requested `docs/HANDOFF.md` is absent; the repository instructions designate root `HANDOFF.md` as the handoff record.

## 2026-10-16 — Task C MVP status and evaluation clarification

- Clarified that the local Task C image-analysis demo is runnable today while browser upload and HTTP API integration remain pending Tasks B/D.
- Recorded the synthetic ACAD pixel-region result as supplemental evidence only; it does not establish India-road performance, instance counting, or training accuracy.
- Documented that aggregate/material/metal detections and calibrated physical values remain unavailable rather than presenting texture candidates as those outputs.

## 2026-10-16 — Optional Task C road-ROI gating

- When an India-road semantic segmentation checkpoint is explicitly configured, constrain high-frequency texture candidates and their preview to the predicted road region. The default remains the existing ungated texture baseline.
- Label ROI-gated previews and structured results as experimental, uncalibrated road-gated texture candidates; aggregate counts, confidence, and physical measurements remain unavailable.
- Added focused tests for mask intersection, default behavior, and integration through the existing image-analysis service.

## 2026-10-16 — Supplemental synthetic aggregate evaluation

- Evaluated the existing texture-region baseline on 20 visually reviewed images sampled evenly from ACAD's published low-occlusion synthetic-concrete test split. Recorded CC BY 4.0 attribution, subset construction, manifest digest, and limitations in `docs/DATASET_MANIFEST.md`.
- Measured pixel IoU 0.487652, precision 0.822176, and recall 0.545149 against aggregate polygon unions; individual-instance count MAE remains null. These controlled synthetic results are not RoadIQ road performance or training evidence.

## 2026-10-16 — Task C demonstrable baseline

- Fixed annotated-preview mask scaling when the source image exceeds the 512-pixel analysis resolution; larger valid images now produce previews instead of failing during alpha composition.
- Added deterministic synthetic road-texture sample generation and CLI flags to export the annotation and structured JSON report separately.
- Added a one-command Task C demo runner for either a generated sample or a local image, saving the annotation and structured report together.
- Added an end-to-end regression test for the synthetic 640×480 image. It validates baseline plumbing only; no real-world model performance is claimed.

## 2026-10-16 — Task D Windows desktop package

- Added a Windows one-file build that bundles the FastAPI health service and compiled dashboard; the launcher binds only to loopback, checks readiness, opens the browser, and safely restarts a verified existing RoadIQ instance.
- Added desktop runtime tests and build instructions. Backend tests, frontend build/lint, Windows packaging, browser startup, health, and graceful second-launch restart passed on the development host.
- The desktop package still exposes only health at runtime. The map and scores are fixtures; there is no live image/segment API, C-to-A scoring, active model, or RoadIQ-held-out evaluation.
- Current integration status: Task B PR #13 at `86f397c` (12 commits ahead of main) supports local Task C CLI report/annotation import and displays report-backed candidate method, analysis path, optional experimental ROI-gate state, candidate confidence calibration status, and runtime. It still does not upload an image or call an API. Its latest handoff reports frontend build/lint and label/overlay browser checks, but no saved report import; GitHub has no submitted reviews or CI checks.
- With explicit user approval, fast-forwarded remote `task/a-scoring-engine` (`18326f4`) and `task/c-computer-vision` (`ba2d98a`) to `origin/main` (`f83b4d7`) using a normal push after confirming neither had unique commits. PR #12 and PR #13 remain open with no submitted reviews or CI check runs.
- Re-ran current Task D checkout verification: backend pytest 93 passed/2 skipped; frontend TypeScript/Vite production build and Oxlint passed. Windows packaging and startup/restart smoke were not rerun because application code is unchanged.

## Unreleased
- Added a sticky, responsive dashboard control dock with all five full travel-profile names and the Everyday/Engineer switch visible while scrolling; refined spacing and a comfortable sage/forest palette while preserving a distinct Engineer theme.
- Reworked Everyday and Engineer into distinct assessment experiences: Everyday gets profile-specific plain-language briefs; Engineer gets evidence/status/provenance tables and record-readiness audits. Surface condition, mode suitability, and pedestrian infrastructure remain separate, with all fixture values identified as illustrative.
- Updated the Task B branch against the latest `main` integration checklist and refreshed the Task B/C/D status from their current branches. No score formula, API contract, backend scorer, or Task C inference code changed.
- Added Task D integration preparation with a cross-task field audit, unresolved mapping proposals, end-to-end failure scenarios, and verified environment requirements. The desktop package serves the bundled dashboard and health route; no image-analysis route, shared image contract, or full end-to-end integration is claimed.
- Updated live task status: Task A PR #1, Task B dashboard PRs #2, #5, and #6, Task D checklist PR #3, and Task C PRs #4, #7, #8, #10, and #11 are merged. Task C has no active trained checkpoint. The RDD2022 detector remains disabled under the India-only policy, not for technical incompatibility.

- Added the Task A deterministic candidate RSQI scoring service with configurable weights and labels, fixed surface/capture-specific reference normalization, strict evidence gates, auditable component contributions, null confidence/coverage, and null mode-suitability outputs. No RoadIQ normalization references, inference, API route, or calibrated evaluation are claimed.
- Added focused scoring tests for the formula, thresholds, normalization, evidence gates, units/provenance, deterministic output, mode outputs, and proposed API object shape.
- Aligned the product objective around image-based pavement analysis, with aggregate structure, visible defects, and texture proxies as core evidence.
- Added a provisional image-feature RSQI proposal, measurement/calibration constraints, dataset annotation/split requirements, and held-out evaluation metrics; no metrics or model results are claimed.
- Updated Task A-D ownership/acceptance criteria and the proposed image-analysis API payload. Task C provides image validation, heuristic quality observations, and a named texture proxy; active damage inference, aggregate/material/ROI analysis, scoring, UI, HTTP upload route, and RoadIQ evaluation remain unimplemented.
- Added a mandatory model-agnostic agent workflow covering repository inspection, task branches, ownership, contract coordination, verification, handoff, commits, and pull requests.
- Recorded the four agreed task branch names, ownership boundaries, owner-assignment placeholders, and kickoff checklist.
- Standardized the handoff template; no feature task implementation or runtime contract change was made.
- Froze a shared, unit-explicit road-segment contract with GeoJSON geometry, explicit unknown values, status, confidence, coverage, suitability, and provenance.
- Aligned backend Pydantic validation and frontend TypeScript types; updated the demo fixture to remain unrated when evidence is absent.
- Documented provisional damage scoring, ranking constraints, planned (not implemented) segment API routes, task boundaries, and unresolved decisions.
- Added backend contract validation tests; no scoring engine, segment retrieval routes, dashboard, or computer-vision inference was implemented.

## 0.1.0 - 2026-10-15
- Created a minimal FastAPI backend with a versioned health endpoint at `/api/v1/health`.
- Created a minimal React + TypeScript + Vite frontend landing page.
- Added a validated road-segment schema and deterministic sample fixture.
- Documented architecture, API contract, scoring assumptions, and key tooling decisions.
- Added baseline backend tests for health and schema validation.
- Established repository-level instructions and handoff notes for future agents.

## 2026-10-15 — Task C India-only segmentation experiment

- Added a compact PyTorch U-Net training/inference path for the one selected free India-only e-Yantra/IIT Bombay road semantic segmentation dataset. It supports road ROI and semantic pothole pixels, not aggregate instances or metal fragments.
- Added optional row-major binary RLE masks to pavement ROI and defect observations. Semantic pothole masks leave instance count unavailable; image-space ratios are not physical measurements.
- Added safe extraction of only the primary raw-image and mask files, sequence split checks, metadata-bearing checkpoints, and CPU/CUDA selection. Sample/batch-limited runs never save checkpoints.
- Audited and extracted 3,227 paired images/masks; source archive SHA-256: `a25aa4922fa4b7af7098832fad3f31f226721d4638abca1970081c0fe35a09af`.
- Verification: full backend suite 26 passed; Python compileall and `git diff --check` passed. A one-batch CPU smoke run verified the loader/model/metrics path but produced plumbing-only metrics and no checkpoint. No CUDA device was visible in the runner, so full training and quality evaluation were not run.

## 2026-10-15 — Task C PR handoff snapshot

- Recorded actual Task C implementation and remaining work in `TASKS.md` and `HANDOFF.md`. Branch `task/c-computer-vision` is at `023da26f3a23b63ed75b3cdce580be1ef326598d`, pushed and clean before this documentation update.
- PR #4 targets `main`; it was subsequently updated with merge commit `b6f23a33777ecae88d1c52ebbe3499d5f2927740` to bring in newer main work. A live GitHub check then showed the PR open with 15 commits, 19 changed files, and no conflicts with the base branch. It was not merged.
- Handoff docs were committed as `65ee031`, rebased onto `b6f23a3` to preserve newer remote work, and pushed successfully using a normal fast-forward update. A final documentation correction may advance the branch tip; confirm the exact final hash with `git log -1`.
- Tests actually run for implementation: backend suite 26 passed; compileall and `git diff --check` passed; one-batch CPU smoke run completed with plumbing-only macro IoU 0.0148, no checkpoint. These are historical results, not rerun for this documentation-only handoff. No full model training/evaluation was completed.
