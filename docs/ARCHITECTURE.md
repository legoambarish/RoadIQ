# RoadIQ architecture

## Current implementation

The owner-authorized India implementation extends the existing prototype with local trained detector/ROI adapters, actual readiness checks, source-coordinate observations, separate VDA, guarded image intake and live frontend reports. See the implementation section below, [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md), [MODEL_CARD.md](MODEL_CARD.md) and [VALIDATION_REPORT.md](VALIDATION_REPORT.md) for current behavior and measured limits. The original scoring and fixture map remain preserved. Model accuracy and missing field calibration prevent a production or engineering-certification claim.

### Preserved integration baseline

- **Frontend:** React + TypeScript + Vite under `frontend/`, with Leaflet/OpenStreetMap tiles, an OSM India-boundary mask, and selectable, color-coded GeoJSON lines that follow nine mapped central Bengaluru streets; Road Quality and five travel-profile overlays; filters, rankings, charts, Everyday/Engineer segment details; local image preview, manual Task C CLI report/annotation import, and image upload to the Task D API. Street geometry/name and RoadIQ scores have distinct sources: geometry references OSM ways; scores and profile values are illustrative fixtures, not street condition surveys. Segment retrieval remains unavailable.
- **Backend:** FastAPI + Pydantic under `backend/`. The API exposes `GET /api/v1/health` and `POST /api/v1/image-analyses`. The image route connects Task C observations to the Task A scorer but returns Unrated because supported component evidence and fixed normalization references are unavailable. `backend/app/schemas/road_segment.py` validates the shared road-segment shape. A deterministic demo fixture is isolated in `backend/app/fixtures/`.
- **Computer vision:** `backend/app/services/vision.py` validates JPEG/PNG/WebP input and reports heuristic image-quality observations, a named texture proxy, and an untrained texture-region candidate annotation. An optional experimental India-road semantic checkpoint can gate those candidates when explicitly configured; this does not provide validated pavement ROI, material classification, aggregate/metal segmentation, or physical measurements. The Task D route exposes this service over HTTP.
- **Scoring:** the provisional evidence-gated RSQI scorer exists in `backend/app/services/scoring.py`; no fixed default normalization profiles are configured, so its default result stays `unrated`. [SCORING_SPEC.md](./SCORING_SPEC.md) describes provisional rules and evidence limits.
- **Persistence and mapping:** no segment database or segment retrieval API exists. The map uses OSM street geometry for a central Bengaluru sample and masks tiles to the simplified OSM India relation; the boundary is a display aid, not a legal border reference or full road inventory. OSM tiles require network access. The RoadIQ scores/profile values are separate illustrative fixtures and have not been surveyed on the named streets. Data is attributed in the UI and source. Production basemap provider, licensing, caching, and availability remain open.

## Product objective and planned image-analysis pipeline

The primary product objective is image-based road-surface quality assessment. Aggregate structure—individual visible stone aggregates, their size/distribution, boundaries and gaps—plus visible aggregate loss, image texture, and deterioration are core evidence. Map and transport-mode dashboard features are secondary. Literal metal fragments are a separate analysis target from stone aggregates per project-owner direction. Asphalt/bituminous and cement-concrete surfaces are targets where validated; uncertain classification is `unknown`.

The following end-to-end pipeline is **partially implemented**:

1. **Image intake and quality gate (Task C):** the service validates JPEG, PNG, and WebP bytes, dimension/size bounds, decodability, and heuristic exposure/edge-detail indicators. Occlusion, perspective, and capture-specific gates are not yet implemented; heuristic thresholds are not labelled-data validated.
2. **Pavement ROI and surface type (Task C):** no validated pavement ROI or surface classifier is available by default. An explicitly configured experimental semantic road checkpoint can gate texture candidates and reports an uncalibrated predicted road-pixel fraction; surface type remains `unknown` and unavailable.
3. **Aggregate analysis (Task C):** not implemented; aggregate and physical measurements remain null. Literal metal-fragment count is represented separately and unavailable. Physical widths/counts require calibration and valid masks even after a model is added.
4. **Defect and texture analysis (Task C):** damage inference is unavailable without a reviewed India-only checkpoint; test-injected detectors exercise the adapter only. Raveling and mask-based area are unavailable. A named tile grayscale contrast proxy is emitted and is not physical roughness/IRI.
5. **Surface-quality index (Task A):** normalize supported feature components under a versioned, surface-type-aware configuration; calculate the provisional RSQI only with adequate evidence, else return Low Confidence or Unrated with contributions and explanation.
6. **Evaluation and integration (Task D):** validate payloads/routes, organize grouped data splits, run held-out evaluations against expert labels and field measures where available, and report actual metrics. Never substitute proposed metrics for evaluation results.
7. **Report UI (Task B):** display image, annotated overlay, score/status, component contributions, confidence, unavailable values, and limitations. An overlay is model output, not verified ground truth.

Image validation/quality observations, a named pixel-texture proxy, an untrained candidate-region annotation, and optional experimental ROI gating are implemented in Task C. The integrated dashboard supports browser upload through the HTTP image endpoint; it preserves unavailable features and returns Unrated until reviewed component extraction, usable-region evidence, and fixed scoring references are available. Validated pavement ROI/material classification, aggregate/metal instance segmentation, physical measurement, active trained RoadIQ model, configured default scoring references, and RoadIQ held-out evaluation remain unavailable. India-specific damage/segmentation datasets are under source, license, and split review; see [VISION_PIPELINE.md](./VISION_PIPELINE.md). See [SCORING_SPEC.md](./SCORING_SPEC.md) for feature definitions and the minimum dataset/evaluation plan.

## Shared contract

The canonical JSON contract is specified in [SCORING_SPEC.md](./SCORING_SPEC.md), validated by the backend Pydantic schema, and mirrored in `frontend/src/types/road-segment.ts`. Keep field names and units identical across the API and clients. `segment_id` is stable and opaque, while its generation/lifecycle are unresolved.

GeoJSON `LineString` coordinates are WGS 84 `[longitude, latitude]`. Each measurement explicitly declares its unit, status, and source. Unknowns use null and `unavailable`; they are never converted to zero. Provenance values distinguish `sensor`, `image_inference`, `user_input`, and `demo_fixture`.

Scores are nullable. Surface quality is distinct from mode-specific travel suitability. Pedestrian access/context (footpaths, crossings, comfort) is separately represented and must not be inferred from surface score or missing lane markings. Longitudinal grade is along the segment; crossfall is across it. Neither is derived from image pixels without calibration.

## Component boundaries

| Task | Responsibility | Owned implementation area |
| --- | --- | --- |
| A — scoring (`task/a-scoring-engine`) | Own the versioned image-feature normalization, provisional RSQI, evidence gates, contribution explanations, and scoring tests. | Dedicated backend scoring service/tests; consume C observations, not raw-image inference. |
| B — frontend/reporting (`task/b-map-dashboard`) | Own image/report presentation, annotated overlay, transparency/uncertainty states, and secondary map/mode dashboard UI. | `frontend/` and frontend tests; no scoring or inference implementation. |
| C — aggregate analysis (`task/c-computer-vision`) | Own image quality, pavement ROI, surface-type, aggregate instance/feature, defect, and texture-proxy inference with provenance and calibration metadata. | `backend/app/services/vision.py`, focused inference modules/tests, and model/annotation interfaces; do not invent A scoring. |
| D — integration/evaluation (`task/d-integration-release`) | Own API/runtime integration, image workflow boundaries, dataset/split protocol coordination, held-out evaluation runs/reporting, and release checks. | `backend/app/api/routes/`, `backend/app/main.py`, integration/evaluation tests and reports; do not replace A/B/C implementations. |

The shared schema is a cross-task interface. Changes to it require compatibility agreement among the affected owners and updates to backend tests, frontend types, examples, and API documentation. The `docs/` specifications establish shared assumptions; no task may silently convert missing evidence to zero or claim unsupported safety conclusions.

## Data flow (partially implemented)

1. The Task D image endpoint validates an uploaded image through the Task C service and returns explicit input/quality failures.
2. Task C currently emits quality observations, a named texture proxy, and an untrained texture-region candidate; validated surface type, aggregate/defect measurements, and adequate usable-region evidence remain unavailable.
3. Task A consumes only supported observations and emits Unrated when required evidence or fixed normalization references are missing; vehicle-mode suitability remains separate and unscored.
4. Task D exposes the current report through the image-analysis route. Grouped held-out evaluation and actual RoadIQ metrics remain pending.
5. The dashboard uploads images and displays the API response while retaining CLI report import. The HTTP response does not forward the annotated data URI; unavailable fields remain unavailable rather than implying a score or mask is ground truth.

The local image upload and scorer/API boundary are integrated into `main`, but do not currently produce a numeric score from a road image. No database, production model, segment API, or production map data is implied. The map dashboard remains based on OSM street geometry with illustrative RoadIQ scores.
The API integration does not currently produce a numeric score from a road image. No database, production model, segment API, or production map data is implied. The dashboard shows a fixed Bengaluru street sample with illustrative RoadIQ scores.

## Unresolved architecture decisions

- Data persistence, stable segment IDs, segment split/merge lifecycle, and survey version history.
- Authentication, authorization, retention, and external service requirements.
- Scoring calibration, confidence, evidence minimums, ranking comparability, and mode-specific definitions.
- Vision model/checkpoint, image collection and annotation protocol, acceptable image-quality thresholds, physical calibration, and deployment approach.
- Pretrained baseline choice, held-out dataset size/splits, and field validation availability.
- Map provider and handling of licensed basemaps/geocoding.
- API pagination/error envelope and generated frontend contract strategy.
# India implementation update — 2026-10-16

The existing upload boundary now runs `vision.py` in a bounded worker thread, loads provenance-checked local detector/semantic checkpoints, and returns observations plus a separate versioned VDA. `india_detector.py` owns letterbox/tile reconstruction and NMS; `mask_geometry.py` computes image-projected quantities only from semantic masks; the preserved scorer still receives no fabricated component inputs. React draws actual source-coordinate predictions and optional experimental masks and exposes model/timing/calibration evidence in Engineer view. The frozen road-segment contract and illustrative Bengaluru network remain separate.

Offline scripts acquire two rights-recorded India corpora, freeze duplicate-aware splits, train from random initialization, and evaluate actual heldouts. Local raw assets/weights/runs are ignored by Git; compact manifests, hashes, source ledgers and actual benchmark summaries are retained for review. A one-origin source launcher and optional CPU model-enabled Windows package use these same services. See TRAINING_AND_DEMO.md and MEASUREMENT_AND_SCORING_SPEC.md. No physical-depth, aggregate-instance, percentile or measured-map capability is implied by these layers.
