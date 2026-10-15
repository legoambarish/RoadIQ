# RoadIQ API contract

## Status and conventions

Base URL for local development is `http://localhost:8000`; the versioned prefix is `/api/v1`. The currently implemented API is only `GET /api/v1/health` (plus the unversioned `/` informational route). Segment endpoints below are **planned and not implemented**. They specify the boundary for Task D; they are not a claim of working persistence or retrieval.

JSON field names follow the shared snake_case types in [SCORING_SPEC.md](./SCORING_SPEC.md), validated in `backend/app/schemas/road_segment.py` and mirrored in `frontend/src/types/road-segment.ts`. Dates are timezone-aware ISO-8601 strings. GeoJSON coordinates are `[longitude, latitude]` in WGS 84 decimal degrees.

## Implemented endpoint

### `GET /api/v1/health`

Returns HTTP 200 and:

```json
{ "status": "ok", "service": "RoadIQ API" }
```

The route is implemented without external-service dependencies.

## Planned segment retrieval endpoints

### `GET /api/v1/road-segments`

Returns segment records with their embedded `mode_suitability` (walking, cycling, two-wheeler, car, and bus), surface score, evidence, and explanations. An unrated segment remains in the result with null surface score/label and is never represented as good.

Planned query parameters:

| Name | Type | Validation |
| --- | --- | --- |
| `bbox` | optional string `west,south,east,north` | WGS 84 degrees; exactly four finite numbers; longitude bounds `[-180, 180]`, latitude `[-90, 90]`; south must not exceed north. Antimeridian-crossing behavior is unresolved. |
| `limit` | optional integer | 1-100; proposed default 50. |
| `offset` | optional integer | 0 or greater; proposed default 0. |

Success response (HTTP 200):

```json
{
  "items": [
    {
      "segment_id": "seg-demo-001",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-74.006, 40.7128], [-74.005, 40.7138]]
      },
      "survey_source": "RoadIQ demo fixture",
      "surveyed_at": "2026-10-15T12:00:00Z",
      "measurements": {
        "defect_count": {
          "value": null, "unit": "defects", "status": "unavailable", "source": null
        },
        "defect_density": {
          "value": null, "unit": "defects_per_km", "status": "unavailable", "source": null
        },
        "damaged_area_ratio": {
          "value": null, "unit": "ratio", "status": "unavailable", "source": null
        },
        "severity": {
          "value": null, "unit": "severity_index_0_100",
          "status": "unavailable", "source": null
        },
        "roughness_iri": {
          "value": null, "unit": "m_per_km", "status": "unavailable", "source": null
        },
        "longitudinal_grade": {
          "value": null, "unit": "percent", "status": "unavailable", "source": null
        },
        "crossfall": {
          "value": null, "unit": "percent", "status": "unavailable", "source": null
        }
      },
      "damage_components": {
        "damaged_area": null, "defect_density": null, "severity": null, "roughness": null
      },
      "surface_quality_score": null,
      "quality_label": null,
      "mode_suitability": {
        "walking": null, "cycling": null, "two_wheeler": null, "car": null, "bus": null
      },
      "pedestrian_context": {
        "footpath_present": null, "crossings_observed": null, "comfort_score": null
      },
      "confidence": null,
      "evidence_coverage": null,
      "assessment_status": "unrated",
      "explanation": "Demo geometry only; no measured evidence or quality rating is provided.",
      "data_provenance": [
        { "field_path": "geometry", "source": "demo_fixture" }
      ]
    }
  ],
  "count": 1
}
```

`count` is the number of returned records, not necessarily the total matching records. Pagination semantics and stable ordering must be agreed before implementation; offset is a provisional proposal.

### `GET /api/v1/road-segments/{segment_id}`

Returns one full segment using the same `RoadSegment` shape and includes the mode-specific scores in `mode_suitability`. A missing ID returns HTTP 404. IDs follow the schema's 1-64-character alphanumeric/underscore/dash rule.

## Validation and errors

The backend currently relies on FastAPI/Pydantic validation and has no custom error handler. Planned segment endpoints should preserve FastAPI's 422 validation response structure for malformed query or request values, and use a non-sensitive detail message for a missing segment (404). The route's precise error envelope is not yet customized.

Typical FastAPI validation response (actual input varies):

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "limit"],
      "msg": "Input should be greater than or equal to 1",
      "input": 0
    }
  ]
}
```

| Status | Meaning |
| --- | --- |
| 200 | Health or retrieval succeeded. |
| 404 | Planned detail route: segment ID does not exist. |
| 422 | FastAPI/Pydantic request or query validation failed. |
| 500 | Unexpected server error; do not expose stack traces, credentials, or internal details. |

Currently, requesting either planned segment route returns FastAPI's route-not-found 404 because those routes do not exist; it does **not** indicate a missing segment. No create, upload, persistence, or scoring endpoint is part of this contract.

## Shared schema validation

The segment model rejects extra fields, invalid IDs, invalid coordinates/units/ranges, timezone-naive survey timestamps, unavailable values represented as zero, and rated records missing any normalized damage component. It permits explicit nulls for unknown scores/evidence. Backend tests cover these validation boundaries; frontend uses matching TypeScript field names and unions. Generated OpenAPI types are not currently shared automatically, so changes to the contract require coordinated updates and tests.

## Decisions still open

- Persistence, stable ID issuance, pagination order/cursor semantics, data retention, and authorization.
- Whether list retrieval supports further filters or mode-specific response projection.
- Antimeridian bounding-box semantics and timestamp/freshness query behavior.
- Custom error envelope and operational handling.
- Contract versioning and generated cross-language types.
