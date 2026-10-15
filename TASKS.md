# RoadIQ task tracker

## Coordination baseline

- Current integration branch: `main`.
- Agreed task branches: `task/a-scoring-engine`, `task/b-map-dashboard`, `task/c-computer-vision`, and `task/d-integration-release`.
- At the coordination workflow freeze, only `main` existed locally/remotely; create each task branch from an up-to-date `main` when its owner begins work.
- Human owner names have not been supplied; assign one human owner to each task before implementation. Task labels identify scope, not a person.
- Follow the mandatory read/inspect/branch/test/handoff/PR workflow in `AGENTS.md`. GitHub's committed repository state is authoritative, independent of any agent's memory.

## Contract baseline

- Current agreed working branch: `main` (also the branch at task start).
- Shared contract: [SCORING_SPEC.md](docs/SCORING_SPEC.md), [API_CONTRACT.md](docs/API_CONTRACT.md), and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- The backend Pydantic schema and frontend TypeScript types are aligned. Changes require coordination across owners and matching tests/docs.
- Segment retrieval routes, persistence, scoring, dashboard, and computer-vision inference are not implemented by this contract-freeze task.
- Score weights, normalization and labels are provisional hackathon assumptions. Open choices are listed in [DECISIONS.md](docs/DECISIONS.md); do not treat them as silently approved engineering thresholds.

## Cross-task boundaries and ownership

| Task | Scope and file ownership | Explicitly out of scope | Dependencies |
| --- | --- | --- | --- |
| A — Scoring | Implement configurable normalization/scoring, evidence sufficiency, confidence/explanation production, and scoring tests in a dedicated backend scoring service and its tests. Consume `backend/app/schemas/road_segment.py`; own scoring-service files only. | API routes, dashboard, image inference, changing shared schema without coordination. No safety certification. | Frozen shared schema and written scoring assumptions; may develop independently of B/C. |
| B — Dashboard | Implement frontend UX, data display, unrated/error states, accessible explanations, and API integration in `frontend/`. Own frontend UI/API modules; use `frontend/src/types/road-segment.ts`. | Scoring or inference logic; implying missing data means good. | Frozen shared schema and API contract; may develop independently of A/C against typed fixtures. |
| C — Computer vision | Implement image inference, supported measurement extraction, source attribution, uncertainty, and image/calibration tests in `backend/app/services/vision.py` and dedicated vision modules/tests. | Segment API, dashboard, claiming ground dimensions/grade from pixels without calibration. | Frozen measurement/provenance schema; may develop independently of A/B. |
| D — Integration/release | Implement planned retrieval routes, service wiring, persistence boundary only if approved, contract/integration tests, release checks, and API runtime behavior. Own `backend/app/api/routes/`, `backend/app/main.py`, integration tests, and release configuration. | Taking over A scoring, B UI, or C inference implementations; claiming planned routes already exist. | Depends on A, B, and C outputs for end-to-end integration; API routes may be scaffolded against the frozen contract before all implementations are complete. |

### Branch assignment and human owner

| Task | Human owner | Assigned branch |
| --- | --- | --- |
| A — Scoring | TBD; assign before implementation | `task/a-scoring-engine` |
| B — Dashboard | TBD; assign before implementation | `task/b-map-dashboard` |
| C — Computer vision | TBD; assign before implementation | `task/c-computer-vision` |
| D — Integration/release | TBD; assign before implementation | `task/d-integration-release` |

`main` is the shared integration branch. At this workflow freeze no task branches existed locally or remotely. Create task branches from up-to-date `main`; send completed task work through reviewed pull requests. Task D coordinates integration, but does not take over A/B/C modules. Dependency manifests and lockfiles are shared-impact files and require review from affected owners.

### Shared file ownership

- `backend/app/schemas/road_segment.py` and `frontend/src/types/road-segment.ts` are frozen cross-task contract files, not owned for unilateral redesign. The task implementing a compatible contract update must coordinate with affected owners and update tests, examples, and documentation.
- `docs/SCORING_SPEC.md`, `docs/API_CONTRACT.md`, `docs/ARCHITECTURE.md`, and `docs/DECISIONS.md` are shared specifications. Task A proposes scoring changes; Task D owns API runtime alignment; any owner may propose amendments through coordinated review.
- Keep demo data under `backend/app/fixtures/` and clearly mark it as a fixture. Do not treat fixture values as production telemetry.

## Acceptance criteria

### Contract freeze — completed in this change

- [x] One schema defines stable ID, GeoJSON line geometry, survey source/time, typed measurements and units, unknowns, damage fields, surface and mode scores, confidence/coverage, status, explanation, and provenance.
- [x] Backend validation and frontend TypeScript field names/types agree; schema tests cover key valid/invalid boundaries.
- [x] Scoring assumptions, no-imputation/missing-data behavior, limitations, rankings, and unresolved calibration decisions are documented.
- [x] Actual health endpoint is distinguished from planned segment retrieval endpoints.
- [x] Task boundaries, file ownership, dependencies, and outcomes are specified without implementing all four tasks.

### Task A — scoring (planned)

- [ ] Implements formula only with approved, versioned normalizations and all four supported inputs; no partial weight renormalization.
- [ ] Returns `unrated` and null surface score/label if evidence is insufficient; never maps unknown to zero.
- [ ] Keeps surface quality separate from every mode score; emits reproducible explanations and reports confidence/coverage only with documented methods.
- [ ] Tests normalization boundaries, exact formula behavior, missing inputs, version/config selection, and score labels.

### Task B — dashboard (planned)

- [ ] Consumes the shared types and planned API contract, while handling the currently implemented health-only API honestly.
- [ ] Distinguishes absolute score from relative percentile and never presents unrated as good.
- [ ] Displays survey date, available sample/coverage, confidence, provenance/explanation, and uncertainty.
- [ ] Separates surface quality from mode suitability and pedestrian access/context; does not infer pedestrian-friendliness from missing lane markings.
- [ ] Passes frontend TypeScript checks, lint, and Vite production build.

### Task C — computer vision (planned)

- [ ] Keeps inference behind a replaceable service boundary; preserves source=`image_inference`, nulls, and uncertainty in outputs.
- [ ] Does not emit calibrated physical grade/roughness/area from pixels without documented calibration.
- [ ] Tests supported/unsupported inputs and malformed/unavailable inference results without requiring production model weights.

### Task D — integration and release (planned)

- [ ] Implements only the documented routes and response/error shapes, including mode scores in segment retrieval.
- [ ] Validates contract boundaries and service integrations; protects health route behavior.
- [ ] Runs backend pytest and frontend build/type/lint checks; records actual commands/results and unresolved issues in `HANDOFF.md`.
- [ ] Confirms configuration/secrets safety and release readiness without claiming production algorithm/model validation.

## Current status

- Contract freeze: complete for the prototype baseline; this does not approve the provisional scoring assumptions as engineering standards.
- Tasks A-D: planned; none of their end-user features is claimed as complete here.

## Four-owner kickoff checklist

- [ ] **Task A owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/a-scoring-engine`; implement only scoring scope; test, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task B owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/b-map-dashboard`; implement only frontend scope; test/build/lint, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task C owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/c-computer-vision`; implement only inference scope; test, update status/changelog/handoff, push, and open/update a PR.
- [ ] **Task D owner:** confirm human owner; read `AGENTS.md`, relevant docs, and `HANDOFF.md`; fetch latest remote; use `task/d-integration-release`; coordinate dependencies and integrate through reviewed PRs; run release checks, update status/changelog/handoff, and open/update a PR.
