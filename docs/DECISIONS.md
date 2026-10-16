# RoadIQ decisions and open questions

This log records scaffold decisions and provisional contract choices. A provisional choice is not evidence of a validated road-engineering standard or production approval.

## India implementation decisions — 2026-10-16

| Decision | Reason and evidence boundary |
| --- | --- |
| Extend the existing modules and additive `image-analysis-v1.1` | Preserve the functioning upload/import/map/scorer and all original task branches; combined owner authorization is recorded in TASKS.md. No new application framework or frozen segment schema rewrite. |
| India road fine-tuning with an explicitly approved COCO YOLO11n initialization | The owner approved official Ultralytics YOLO11n COCO weights at `https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt` with SHA-256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`. Fine-tuning, validation and evaluation imagery remain India-only; the checkpoint is not described as India-only pretrained. The compact U-Net remains randomly initialized. The trainer and runtime provenance guard require the pinned hash and record the checkpoint/license. |
| Fixed source grouping plus complete exact/dHash audit | Verified route/session metadata is absent in RDD. Numeric blocks are only capture-order proxies. Exclude later-split neighbors and disclose residual dependence/selection bias instead of calling them independent routes. |
| Report observations and localized cautions without a numeric VDA | Available labels are detection classes, not condition/severity grades. No defensible Good/Medium/Bad calibration or complete RSQI component/reference set exists. |
| Separate boxes, semantic pixels and physical measurements | Only supervised masks generate experimental pixel geometry. Boxes supply extents/counts; physical depth/area/width stay null. Unknown material and capture support remain visible. |
| Train a new U-Net with an aspect-preserving input and source-resolution final metric | Keep the previously evaluated v3/v4 evidence immutable. The new version selects and early-stops on validation road/pothole mean IoU; its test pass also measures the actual nearest-neighbor source projection used in inference. |
| Disclose failed mask quality beside its outputs | Heldout pothole IoU is zero. Pixel areas are experimental predictions and cannot support trustworthy damage measurement. Never hide a failure behind an aggregate overlap or a small average area error. |
| CPU runtime and separate clean CPU package environment | CUDA trains on the local GPU; CPU inference and the standalone Windows package use pinned CPU Torch/torchvision to avoid bundling CUDA DLLs. Package tests must exercise the fresh executable outside the checkout. |
| Hold P1 physical dimensions, percentile and survey map at their evidence gates | No measured scale references, eligible RSQI scores/cohort or legitimate survey GPS/time exists. JSON observation export is available; future features must not silently manufacture these inputs. |

Current scientific contract and benchmark identities: [MEASUREMENT_AND_SCORING_SPEC.md](MEASUREMENT_AND_SCORING_SPEC.md), [DATASET_AND_RIGHTS_REGISTER.md](DATASET_AND_RIGHTS_REGISTER.md), [MODEL_CARD.md](MODEL_CARD.md). The remaining earlier rows preserve coordination history; their initial endpoint/formula proposals do not supersede current code/specifications.

## Recorded decisions

| Decision | Current choice | Rationale / limit |
| --- | --- | --- |
| Frontend | React + TypeScript + Vite | Small, typed prototype boundary. |
| Backend | FastAPI + Pydantic | Python API and validation scaffold. |
| API prefix | `/api/v1` | Current health endpoint is versioned here. |
| Shared segment geometry | GeoJSON `LineString`, WGS 84 `[longitude, latitude]` | Standard interoperable coordinate order; coordinate reference assumes RFC 7946. |
| Unknown data | Explicit null with `status: "unavailable"` for measurements | Missing data is not zero and must not imply good condition. |
| Data provenance | `sensor`, `image_inference`, `user_input`, `demo_fixture` | Makes the origin distinguishable at field level. |
| Surface score proposal | `Damage = 0.35A + 0.25D + 0.25S + 0.15R`; `Surface Quality = 100 - Damage` | Hackathon assumption only; no scoring implementation or calibration is included in this contract freeze. |
| Surface labels proposal | Good 80-100, Fair 60-<80, Poor 40-<60, Very Poor 0-<40 | Configurable, provisional thresholds; not an engineering standard. |
| Mode suitability | Separate nullable scores from surface quality | Surface condition alone cannot establish suitability or safety for any travel mode. |
| Grade fields | Longitudinal grade along the road; crossfall across the road | Distinct measurements. No real-world grade from pixels without calibration. |
| Current API scope | Health endpoint only | Segment endpoints are specified as planned and do not exist yet. |
| Task B prototype map | Leaflet 1.9.4 with OpenStreetMap standard tiles; viewport opens on OSM street geometry in central Bengaluru and tiles are masked to simplified OSM India relation 304716 | OSM way geometry/name is separate from illustrative RoadIQ scores/profile fixtures; no condition survey is implied. The India mask is for display, not legal-boundary authority or full India coverage. Keep visible OSM attribution, tiles need network access, use the exact tile URL, honor browser caching, avoid prefetch, and follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/). A provider override must also configure its attribution. Production provider, licensing, caching, and availability remain open. |
| Demo records | Isolated fixture; unrated absent evidence | Prevents fixture values from being mistaken for sensor/model results. |

## Unresolved decisions (must not be silently assumed)

### Data and surveying

- Who issues stable segment IDs; how roads are split, merged, directed, and versioned.
- Survey boundary and aggregation method; method to compute segment length and defect density.
- Provenance reference format, sensor calibration metadata, and evidence retention.
- Crossfall sign/direction convention and acceptable grade ranges/precision.
- Which data source is authoritative when sources conflict.

### Scoring and rankings

- Reference normalization anchors for damaged-area ratio, defect density, and IRI; severity rubric.
- Whether formula weights and provisional label thresholds are accepted, and who can change/version them.
- Minimum evidence sufficiency, comparability, and freshness rules.
- Confidence calibration, evidence-coverage denominator, and how samples are counted.
- Mode-specific scoring rules, required evidence, and disclosure language; walking/access/crossings require separate evidence.
- Ranking cohort, percentile method, ties, sample size, survey period, and handling of unrated records.
- Ground-truth data, validation design, error bounds, and owner for engineering review.

### API and operations

- Persistence, pagination semantics and stable ordering, query filters, contract generation/versioning.
- Authentication/authorization, privacy, data deletion, monitoring, and operational error envelope.
- Production map provider, basemap licensing/caching, and geocoding (the Task B prototype uses OSM tiles).
- Image upload, storage, and supported image/model execution environments.

## Review rule

Changes to the shared road-segment schema must update both backend Pydantic and frontend TypeScript types, contract tests, API examples, and this decision log as appropriate. A score must not be treated as calibrated or safety-certified until the relevant open decisions are resolved and validated.
