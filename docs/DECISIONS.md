# RoadIQ decisions and open questions

This log records scaffold decisions and provisional contract choices. A provisional choice is not evidence of a validated road-engineering standard or production approval.

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
| Task B prototype map | Leaflet 1.9.4 with OpenStreetMap standard tiles and visible attribution | No API key or paid provider; tiles need network access. Fixture geometries/scores are independent of OSM and are not surveyed observations. Use the exact tile URL, honor browser caching, avoid prefetch, and follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/). A provider override must also configure its attribution. Production provider, licensing, caching, and availability remain open. |
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
