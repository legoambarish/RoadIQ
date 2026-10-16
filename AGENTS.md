# RoadIQ agent instructions

## Mission
The owner authorized the 2026-10-16 implementation handoff: extend the existing prototype with genuine India-only model training, evaluation, and integrated image assessment. The former scaffold-only restriction is superseded for this assignment. Preserve useful implementations and explicit unknowns. Do not claim production readiness or engineering certification.

## Required boundaries
- Frontend application lives under `frontend/`.
- Backend application lives under `backend/`.
- Shared project documentation lives under `docs/` and the repository root.
- Do not invent completed features or claim production readiness. Clearly distinguish implemented code from proposed architecture.

## Coding conventions
- Prefer small, single-purpose modules over a monolithic implementation.
- Use TypeScript strictness for the frontend and Python type hints for the backend.
- Keep API routes separated from validation models and business logic.
- Keep demo data clearly isolated from production assumptions.
- Document assumptions in the docs and label unresolved decisions.

## Testing expectations
- Backend: use pytest for validation scenarios and health checks.
- Frontend: use the Vite app build and TypeScript checks as the verification path.
- Add integration tests only when they validate a real contract boundary and are lightweight.

## Security rules
- Never expose API keys, tokens, or secrets in source code, logs, or documentation.
- Keep local environment files untracked and use `.env.example` as the template.
- Use environment variables for configuration and document required external services without adding real credentials.

## Repository workflow
- Preserve useful existing work and avoid destructive resets.
- Record in `HANDOFF.md` the current branch, latest commit, tests run, and known issues before finishing.
- Keep the project ready for review and avoid implementation outside the owner-authorized scope recorded in TASKS.md.

## Mandatory collaboration workflow

These steps apply to every human or AI agent, regardless of model, account, or chat history. The GitHub repository and its committed documents are the source of truth.

### Before editing

1. Read this `AGENTS.md`, `TASKS.md`, the relevant technical specifications under `docs/`, and `HANDOFF.md`.
2. Inspect `git branch --show-current`, `git status`, recent commits, and configured remotes. Fetch the latest remote changes before starting a work session. Reconcile fetched changes deliberately; do not discard local work or blindly choose one side in a conflict. If an uncommitted change or conflict may belong to someone else, stop and coordinate rather than overwrite it.
3. Confirm the assigned task, its branch, file ownership, dependencies, and acceptance criteria in `TASKS.md`. Work only on that task's assigned branch. Do not work directly on `main` for Tasks A-D.

### While working

4. Keep changes limited to the assigned task; avoid unrelated refactoring and preserve others' work.
5. Follow the shared schema and API contract. Propose contract changes in writing and obtain affected owners' review before making incompatible changes. Update all affected backend/frontend types, tests, examples, and specifications together after agreement.
6. Add or update tests for changed behavior. Do not claim planned features or unrun checks as implemented or verified.

### Before handing off

7. Run relevant tests, type checks, builds, and lint checks. Report exact commands and actual outcomes, and explicitly list checks not run.
8. For meaningful completed work, update `TASKS.md`, `CHANGELOG.md`, and `HANDOFF.md`; keep status and known issues accurate.
9. Commit and push changes to the assigned task branch, then open or update a pull request against `main` for review. Do not bypass review by merging your own task branch unless the team has explicitly agreed to a different process.
10. Report the commit hash, changed files, tests run and not run, known issues/blockers, contract/dependency changes, and the exact next recommended action.

### Branch and merge policy

The agreed branches are:

- `main` — shared integration/release branch.
- `task/a-scoring-engine` — Task A.
- `task/b-map-dashboard` — Task B.
- `task/c-computer-vision` — Task C.
- `task/d-integration-release` — Task D.

No task branches existed at the coordination workflow freeze; create/use the named branch for the assigned task. If the team establishes different branch names later, record those actual names in `TASKS.md` before work begins. Fetch before each new work session. Never reset, force-push, or rewrite shared history without explicit team approval. Resolve conflicts deliberately with the affected owners; do not blindly accept ours/theirs.

### Ownership and contracts

`TASKS.md` is authoritative for task boundaries, human owner assignment, dependencies, and file ownership. Each task owner changes their own modules. Shared contracts, dependency manifests, and integration files require review by affected owners. Task D coordinates integration and release checks; it must not replace Task A, B, or C implementations.

Never put credentials, private tokens, or secrets in code, commits, issues, pull requests, logs, or documentation.
