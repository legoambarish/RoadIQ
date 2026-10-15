# RoadIQ handoff

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

- Date/time: 2026-10-15 15:49 UTC
- Task owner: Project owner (confirmed in chat; account name not recorded here)

### Branch and commits

- Branch: `task/b-map-dashboard`
- Base: `8b0df94` (`Record RoadIQ push limitation`), the fetched `origin/main` at task start.
- Implementation commit: `4272539c3d678f8c7c8bdc77f57d60bef6f6d0da` (`Build fixture-backed RoadIQ map dashboard`).
- Handoff metadata commit: recorded by the commit containing this section.
- Push: attempted three times with `git push -u origin task/b-map-dashboard`; each attempt was blocked because the Git Credential Manager helper could not start and Git could not obtain GitHub credentials. Network permission was granted before the second attempt. No remote branch or PR was created.

### Completed work

- Replaced the landing page with a responsive dashboard featuring an interactive schematic SVG map, clickable/keyboard-selectable segments, zoom, Road Quality and five travel-profile overlays, filters, ranked segments, summary cards, charts, and Everyday/Engineer segment details.
- Added nine typed illustrative `demo_fixture` road records, including an unrated record. No production scores or safety claims are made.
- Added local-only image preview and an Unrated report shell. Files are not uploaded and no inference or annotated output is claimed.
- Updated the root/frontend README, architecture, changelog, and Task B ownership/status/acceptance notes. No shared API contract, dependency manifest, or lockfile changed.

### Verification performed

- From `frontend/`: `node_modules/.bin/tsc.CMD -b` — passed.
- From `frontend/`: `node_modules/.bin/oxlint.CMD` — passed with no warnings.
- From `frontend/`: `node_modules/.bin/vite.CMD build` — passed.
- `git diff --check` — passed.
- Browser accessibility snapshot confirmed dashboard overlays, rankings, image-report shell, segment details, and charts render. Interactive browser inspection also exercised overlay/view switching earlier in the work session.
- No backend tests were run because Task B changed no backend files. No frontend unit-test suite exists in this scaffold.

### Remaining issues and next action

- Real image analysis, annotated images, and segment data remain unavailable until Task C/Task A outputs and the Task D API interface are reviewed and integrated.
- Map provider, live segment retrieval, and score production remain unimplemented. Demo measurements are illustrative only.
- Push the branch using an authenticated GitHub account, open a PR against `main`, and request the required review. Do not force-push.
- Readiness: implementation is ready for review on the local branch; integration is pending remote push and PR review.

### Task B presentation follow-up — 2026-10-15

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
