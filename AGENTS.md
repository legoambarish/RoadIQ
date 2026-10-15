# RoadIQ agent instructions

## Mission
The repository is in its initial scaffold phase. Build only the minimum viable structure for a full-stack RoadIQ prototype, leaving the production road-quality algorithm, dashboard UI, and computer-vision pipeline intentionally unimplemented.

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
- Keep the project ready for review and avoid full feature implementation outside the approved scaffold.
