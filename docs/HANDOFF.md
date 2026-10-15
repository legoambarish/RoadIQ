# Task B — Leaflet/OpenStreetMap dashboard handoff (2026-10-16)

## Assignment and repository state

- Assignment: Task B frontend/dashboard on `task/b-map-dashboard`; work is limited to `frontend/` and coordinated project documentation.
- Before this continuation, `git fetch --all --prune` completed and the checkout was clean at `6ddcc117e72d4522009ba3ee4766f7c80d4dc01e`, tracking `origin/task/b-map-dashboard`. No local user changes were present.
- After fetching, Task A and Task C branches both point at `f83b4d7`, the current `origin/main` commit. Task D is at `0431d64`; its latest commit changes only `CHANGELOG.md`, `HANDOFF.md`, and `TASKS.md`. Its branch still contains the Windows package work, not an image-analysis endpoint. The Task D integration checklist says image analysis remains unimplemented and its field-mapping differences are unresolved. No Task A/C/D backend or shared API code was changed here.
- `docs/HANDOFF.md` did not exist before this work; it is created to carry the requested concise Task B handoff. Root `HANDOFF.md` remains the repository workflow handoff.

## What was completed

- Replaced the drawn SVG street schematic with Leaflet 1.9.4 over the OpenStreetMap standard raster tile endpoint. GeoJSON fixture polylines remain selectable, keyboard accessible, zoomable, and recolored by Road Quality or each travel profile.
- Added the fixture survey source and timestamp to Engineer details; the timestamp is explicitly identified as demo metadata rather than a real survey.
- Kept the score legend, filters, rankings, segment details, Everyday and Engineer views, and existing local Task C report import behavior. Route names, geometries, and scores are explicitly identified as RoadIQ fixture data, independent of OSM.
- Added a tile-load error notice; fixture routes remain usable when the basemap cannot load. Kept visible OSM attribution and added `VITE_MAP_TILE_URL` / `VITE_MAP_TILE_ATTRIBUTION` provider overrides. The default browser tile cache is unchanged and the app does not prefetch tiles. See the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/).
- Extracted filter, ranking, and visible-record selection helpers; added six unit tests for mode-overlay lookup, score-band/status mapping, minimum/search filters, null/unrated handling, ranking order, and visible-segment selection.

## Files changed

- `frontend/src/components/SegmentMap.tsx`
- `frontend/src/components/ModeAssessmentPanel.tsx`
- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/lib/roadSegments.ts`
- `frontend/src/lib/roadSegments.test.ts`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/README.md`
- `README.md`
- `TASKS.md`
- `CHANGELOG.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `HANDOFF.md`
- `docs/HANDOFF.md`

## Checks actually run

All frontend commands below ran from `frontend/` with the locally installed project executables because the default `pnpm run` wrapper tried to reinstall modules and aborted without a TTY.

- `node_modules/.bin/tsc.CMD -b` — passed on the final source state.
- `node_modules/.bin/vite.CMD build` — passed; 27 modules transformed.
- `node_modules/.bin/oxlint.CMD src` — passed.
- `node_modules/.bin/vitest.CMD run` — passed, 1 test file / 6 tests.
- `git diff --check` — passed after source/docs edits.
- Browser on `http://127.0.0.1:4173/#network` — verified OSM tiles/attribution and fixture lines render; Walking, Cycling, Two-wheeler, Car, Bus, and Surface quality switch the map overlay and ranking; Engineer view displays survey source and timestamp labeled fixture metadata; `80+` active-overlay filter leaves two matching surface-quality fixtures; a text query with no results displays the empty state; selecting a route updates segment details and leaves one selected-route label. Browser check is manual, not an automated browser test.
- Dependency install/audit via `pnpm dlx npm@10.9.2 install --save-dev vitest --ignore-scripts` and `pnpm dlx npm@10.9.2 install --ignore-scripts` — both completed; each reported zero vulnerabilities.
- Backend pytest was not run because this change did not touch backend code.
- Two initial tool invocations did not run checks: an unsupported `--no-frozen-lockfile` flag and a `pnpm run` auto-install that aborted because it could not remove `node_modules` without a TTY. A `pnpm dlx npm --prefix frontend` attempt also used the wrong working directory and failed to find a root `package.json`. These did not alter project source or the final package lock.

## Current status, limitations, and next task

- At the start: clean `task/b-map-dashboard`, commit `6ddcc117e72d4522009ba3ee4766f7c80d4dc01e`. The verified implementation and documentation changes are currently uncommitted on the assigned branch; commit identifiers and post-push status will be recorded in the follow-up handoff commit and completion message.
- Known limitations: map segments and every displayed road value remain illustrative fixtures; they are not OSM road observations or validated measurements. Public OSM tiles require a connection and are best-effort. Production tile-provider/caching policy remains open. There is still no live segment API, no browser-triggered image analysis endpoint, and no connection to Task A scoring; image report import remains manual. Task C's report schema and the proposed API/scorer mappings remain unresolved by Task D.
- Readiness: frontend changes are locally verified; integration still requires review of the new dependency and map provider choice. No backend/API contract changes are included.
- Single most useful next task: Task D should finish and obtain affected-owner review for the Task C-to-Task A response mapping and image-analysis endpoint, then Task B can replace manual report import with live, contract-backed results.
