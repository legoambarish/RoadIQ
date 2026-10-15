# Architecture and tooling decisions

## Frontend stack
The initial frontend uses React + TypeScript + Vite because it is a streamlined, well-supported combination for a small project that needs a low-friction developer experience and a clean production build.

## Backend stack
FastAPI and Pydantic were chosen for the backend because the project requires a Python-based API with strict validation and a simple path to health checks and future typed endpoints.

## Mapping provider
The initial scaffold avoids a hard dependence on Google Maps for two reasons: it requires a valid key and license management, and the repository does not yet have a guaranteed integration environment. Leaflet with OpenStreetMap is the safer default for early prototype work and is easy to replace with a provider abstraction later.

## Computer-vision boundary
The placeholder vision module keeps the model boundary separate from the API so future integration can be added without rewriting routes or schemas. This avoids downloading or shipping unsupported model weights during the initial scaffold.

## Data model approach
The road-segment schema is intentionally small and deterministic. It is designed for incremental extension without implying that the sample output represents a production scoring system.

## Security
The repository does not permit secrets in source control. Each service-specific configuration value is kept in environment variables, with `.env.example` acting as the only template checked into the repo.

## Scope guardrail
The scaffold is intentionally limited to documentation, health checks, sample validation, and buildability. It excludes the final dashboard, real scoring logic, and production-grade infra to stay aligned with the hackathon scope.
