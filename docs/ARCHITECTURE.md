# RoadIQ architecture

## Current implementation

RoadIQ remains an initial prototype scaffold; it is not production-ready.

- **Frontend:** React + TypeScript + Vite under `frontend/`, with a fixture-backed interactive schematic map, Road Quality and five travel-profile overlays, filters, rankings, charts, Everyday/Engineer segment details, a health-only API badge, local image preview, and manual Task C CLI JSON/annotation import. It uses illustrative typed segment fixtures; there is no live basemap, segment API, browser-triggered image upload/inference, or scoring connection.
- **Backend:** FastAPI + Pydantic under `backend/`. The implemented HTTP API exposes `GET /api/v1/health` and `/`. `backend/app/schemas/road_segment.py` validates the shared road-segment shape. A deterministic demo fixture is isolated in `backend/app/fixtures/`.
- **Computer vision:** `backend/app/services/vision.py` validates JPEG/PNG/WebP input and reports heuristic image-quality observations, a named texture proxy, and an untrained texture-region candidate annotation. An optional experimental India-road semantic checkpoint can gate those candidates when explicitly configured; this does not provide validated pavement ROI, material classification, aggregate/metal segmentation, or physical measurements. No image HTTP route is implemented.
- **Scoring:** the provisional evidence-gated RSQI scorer exists in `backend/app/services/scoring.py`; no fixed default normalization profiles are configured, so its default result stays `unrated`. [SCORING_SPEC.md](./SCORING_SPEC.md) describes provisional rules and evidence limits.
- **Persistence and mapping:** no segment database, segment retrieval API, or live basemap exists. The current schematic map plots illustrative fixture geometry; mapping provider choice remains open.

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

Image validation/quality observations, a named pixel-texture proxy, an untrained candidate-region annotation, and optional experimental ROI gating are implemented in Task C. The dashboard can import the saved CLI report and annotated image, but no browser-triggered inference or HTTP image endpoint exists. Validated pavement ROI/material classification, aggregate/metal instance segmentation, physical measurement, active trained RoadIQ model, configured default scoring references, and RoadIQ held-out evaluation remain unavailable. India-specific damage/segmentation datasets are under source, license, and split review; see [VISION_PIPELINE.md](./VISION_PIPELINE.md). See [SCORING_SPEC.md](./SCORING_SPEC.md) for feature definitions and the minimum dataset/evaluation plan.

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

## Planned data flow (not implemented end-to-end)

1. A future image intake validates format/quality and returns explicit quality failures.
2. Task C emits ROI, surface type, aggregate/defect/texture observations with units, source=`image_inference`, availability, and calibration/evidence metadata.
3. Task A consumes supported observations, computes a versioned RSQI only when evidence is adequate, and otherwise emits Low Confidence or Unrated; vehicle-mode suitability remains separate.
4. Task D exposes validated analysis reports through planned routes and evaluates predictions on grouped held-out images; actual metrics and data splits are recorded.
5. Task B renders the annotated image/report, score contributions, evidence, confidence, and unavailable fields without implying a score or mask is ground truth.

No database, inference execution, scoring execution, segment API, or production map data is implied by this proposed flow. The existing dashboard remains a demo fixture interface.

## Unresolved architecture decisions

- Data persistence, stable segment IDs, segment split/merge lifecycle, and survey version history.
- Authentication, authorization, retention, and external service requirements.
- Scoring calibration, confidence, evidence minimums, ranking comparability, and mode-specific definitions.
- Vision model/checkpoint, image collection and annotation protocol, acceptable image-quality thresholds, physical calibration, and deployment approach.
- Pretrained baseline choice, held-out dataset size/splits, and field validation availability.
- Map provider and handling of licensed basemaps/geocoding.
- API pagination/error envelope and generated frontend contract strategy.
