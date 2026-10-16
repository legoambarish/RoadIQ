# RoadIQ API contract

## Status and conventions

Base URL for local development is `http://localhost:8000`; the versioned prefix is `/api/v1`. The implemented API includes `GET /api/v1/health` and `POST /api/v1/image-analyses` (plus the unversioned `/` informational route). Segment endpoints below are **planned and not implemented**. Image analysis is synchronous and local to the backend process; there is no image persistence.

JSON field names follow the shared snake_case types in [SCORING_SPEC.md](./SCORING_SPEC.md), validated in `backend/app/schemas/road_segment.py` and mirrored in `frontend/src/types/road-segment.ts`. Dates are timezone-aware ISO-8601 strings. GeoJSON coordinates are `[longitude, latitude]` in WGS 84 decimal degrees.

## Implemented endpoint

### `GET /api/v1/health`

Returns HTTP 200 and:

```json
{ "status": "ok", "service": "RoadIQ API" }
```

The route is implemented without external-service dependencies.

## Implemented image-analysis endpoint

Image analysis is the primary product workflow. The endpoint integrates Task C observations with the Task A scorer and is displayed in the local dashboard. Upload limits and supported formats follow the Task C image service. The route currently accepts only an image file; calibration input, storage, and retention are not implemented.

Task C exposes `app.services.vision.analyze_road_image(image_bytes, *, source_name="unknown", calibration=None, detector=None, segmentation_model=None, confidence_threshold=0.25)`. It returns observations and does not score. A configured India-road semantic segmentation checkpoint can populate a road ROI mask and pothole pixel mask; these use optional `mask_rle` fields encoded as `row_major_binary_rle_v1`. The service also returns image metadata, unavailable-value reasons, detector boxes, and a separate `metal_fragments` observation. The HTTP route passes explicit image-quality and resolution gates to Task A, retains unknown surface type, and does not invent missing component values or normalization references.

### `POST /api/v1/image-analyses`

The optional `pavement_region.mask_rle` and `defects[].mask_rle` fields use `row_major_binary_rle_v1`. `size_px` is `[height, width]`; `counts` begins with the background run (which may be zero), then alternates foreground/background. The counts must sum to `height * width`. A semantic pothole mask does not imply an instance count: keep `count.value` null unless instances are separately detected.

Request: `multipart/form-data` with a required `image` file. The current route does not accept a calibration part. Do not accept remote image URLs unless a separately reviewed SSRF-safe design is adopted.

The response includes Task C observations, an `rsqi` object from Task A, adjacent `quality_label` and `scoring_version` metadata, and nullable mode-suitability fields. Processing/validation errors use HTTP error responses rather than a success-shaped scored result. The Task C inline annotation is not returned over HTTP; `annotated_image` remains unavailable until safe storage/serving is reviewed.

**Current scoring behavior:** the integrated scorer uses its default configuration, which has no fixed normalization profiles. Task C currently reports unknown surface type, no adequate pavement-region decision, and no supported RSQI component observations. Consequently, a valid image currently returns `analysis_status: "unrated"` and a null RSQI value; all mode-suitability values remain null. The API is wired, but this is not a numeric image-quality scorer. A score and visible-defect cap are only produced when all required, properly normalized component evidence and gates are supplied under a reviewed scoring configuration.

Example response shape for a valid upload:

```json
{
  "analysis_id": "img-analysis-opaque-id",
  "analysis_status": "unrated",
  "image_quality": {
    "status": "observed",
    "issues": [],
    "usable": true,
    "source": "image_inference"
  },
  "pavement_region": {
    "usable_area_ratio": {
      "value": null, "unit": "ratio", "status": "unavailable",
      "source": null
    },
    "annotation": { "value": null, "unit": "uri", "status": "unavailable", "source": null },
    "mask_rle": null
  },
  "surface_type": {
    "value": "unknown",
    "unit": "category",
    "status": "estimated",
    "source": "image_inference",
    "confidence": null
  },
  "aggregate_analysis": {
    "aggregate_count": {
      "value": null, "unit": "aggregates_per_image", "status": "unavailable", "source": null
    },
    "aggregate_count_per_m2": {
      "value": null, "unit": "aggregates_per_m2", "status": "unavailable", "source": null
    },
    "size_distribution": {
      "value": null, "unit": "pixel_distribution", "status": "unavailable", "source": null
    },
    "physical_size_distribution": {
      "value": null, "unit": "mm_distribution", "status": "unavailable", "source": null
    },
    "visible_coverage_ratio": {
      "value": null, "unit": "ratio", "status": "unavailable", "source": null
    },
    "boundary_gap_statistics": {
      "value": null, "unit": "pixel_statistics", "status": "unavailable", "source": null
    },
    "physical_boundary_gap_statistics": {
      "value": null, "unit": "mm_statistics", "status": "unavailable", "source": null
    },
    "aggregate_loss_indicator": {
      "value": null, "unit": "damage_index_0_100", "status": "unavailable", "source": null
    }
  },
  "defects": [
    {
      "class": "crack",
      "count": {
        "value": null, "unit": "defects_per_image", "status": "unavailable", "source": null
      },
      "visible_area_ratio": {
        "value": null, "unit": "ratio", "status": "unavailable", "source": null
      },
      "confidence": null,
      "annotation": null,
      "detections": [],
      "mask_rle": null
    }
  ],
  "texture_features": {
    "features": [
      {
        "name": "local_contrast",
        "value": null,
        "unit": "algorithm_defined_proxy",
        "status": "unavailable",
        "source": null
      }
    ],
    "is_physical_roughness": false
  },
  "rsqi": {
    "value": null,
    "unit": "index_0_100",
    "status": "unrated",
    "confidence": null,
    "confidence_band": "unrated",
    "components": {
      "visible_defect_burden": {
        "value": null, "unit": "damage_index_0_100",
        "status": "unavailable", "source": null, "weight": 0.35,
        "weighted_contribution": null
      },
      "aggregate_loss": {
        "value": null, "unit": "damage_index_0_100",
        "status": "unavailable", "source": null, "weight": 0.20,
        "weighted_contribution": null
      },
      "gap_anomaly": {
        "value": null, "unit": "damage_index_0_100",
        "status": "unavailable", "source": null, "weight": 0.15,
        "weighted_contribution": null
      },
      "texture_anomaly": {
        "value": null, "unit": "damage_index_0_100",
        "status": "unavailable", "source": null, "weight": 0.15,
        "weighted_contribution": null
      },
      "aggregate_distribution_anomaly": {
        "value": null, "unit": "damage_index_0_100",
        "status": "unavailable", "source": null, "weight": 0.15,
        "weighted_contribution": null
      }
    },
    "explanation": "Surface type and required image evidence are unavailable; no index is assigned.",
    "limitations": ["No reliable image-derived feature values are available."]
  },
  "quality_label": null,
  "scoring_version": "image-rsqi-candidate-v1",
  "mode_suitability": {
    "walking": null,
    "cycling": null,
    "two_wheeler": null,
    "car": null,
    "bus": null
  },
  "data_provenance": [
    { "field_path": "image_quality", "source": "image_inference" }
  ],
  "annotated_image": {
    "value": null, "unit": "uri", "status": "unavailable", "source": null
  },
  "model": {
    "name": null,
    "version": null,
    "training_status": "not_reported"
  },
  "processing_errors": []
}
```

This is a shape example, not a result from a running model. All values shown unavailable/null must remain null unless a valid measurement method produced a value. A result's provenance should include image/model/version references without exposing secrets or unsafe storage locations. `training_status` must distinguish `pretrained_baseline`, `roadIQ_trained`, `roadIQ_fine_tuned`, and `not_reported`; do not claim RoadIQ training unless it occurred and its split/data version are recorded.

The current Task C Python service has an additional local-only observation under `aggregate_analysis.surface_region`: an untrained Pillow high-frequency texture candidate mask in the existing `row_major_binary_rle_v1` format, a bounding box and pixel-area statistics, uncalibrated confidence (`null`), and a measured heuristic runtime. It explicitly sets `individual_particles_segmented` false and keeps aggregate count, coverage, size/gap statistics, and physical values unavailable. The local CLI may return an annotated JPEG data URI; the HTTP endpoint deliberately returns `annotated_image` as unavailable until payload size, content handling, retention, and response mapping are reviewed. Dataset-manifest fields and split/dedup validation are documented in [`DATASET_MANIFEST.md`](DATASET_MANIFEST.md).

### Proposed measurement conventions and validation

- Every measurement object uses `{value, unit, status, source}`. `status` is `observed`, `estimated`, or `unavailable`; an observed/estimated value requires a source, while unavailable requires `value: null` and `source: null`. Source is one of `sensor`, `image_inference`, `user_input`, `demo_fixture`.
- Ratios are finite numbers in `[0,1]`; confidence is nullable `[0,1]`; index values are nullable `[0,100]`. Counts are non-negative integers. Physical widths/sizes are non-negative and only returned in `mm` when calibration and resolution justify them.
- Image-analysis `analysis_status` is `completed`, `low_confidence`, `unrated`, or `failed`; `rsqi.status` is `rated`, `low_confidence`, or `unrated`. `unrated` requires null RSQI value and confidence band `unrated`. `low_confidence` may carry a tentative numeric estimate only when all required evidence exists; it must be visibly labelled and use a validated confidence policy. `failed` is a processing error, not a successful empty analysis.
- Every defect count/extent and every named texture feature is individually represented with value, unit, availability status, and source. RSQI components carry normalized damage value, unit, status/source, configured weight, and weighted contribution so the explanation is auditable.
- `aggregates_per_m2` requires known ground scale, established usable physical pavement area, and count over that same area. Otherwise it is unavailable; `aggregates_per_image` may be reported when countable.
- Pixel measurements (pixel count/size/gap statistics) must not be described as physical dimensions. Texture feature names/method/version must be included; texture is not IRI or 3D roughness.
- Surface type is `asphalt_bituminous`, `cement_concrete`, or `unknown`; uncertainty must be retained. An unknown surface type prevents scoring components that require material-specific references.
- Missing/unreliable feature inputs are null, not zero. If required quality/evidence gates fail, `rsqi.status` is `unrated`, `value` and confidence band are null/`unrated`, and explanation includes reasons. A tentative numeric score may be labelled `low_confidence` only under a validated confidence policy; numeric cutoffs remain unresolved.
- The `annotated_image` reference can be absent. When present, API access control, expiry, safe content types, and retention must be defined before implementation.
- Surface index is distinct from travel-mode suitability and does not establish structural strength, skid resistance, weather resistance, or safety.

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
| 200 | Health or image analysis succeeded; image analysis may legitimately be `unrated`. |
| 404 | Planned detail route: segment ID does not exist. |
| 422 | FastAPI/Pydantic request or query validation failed, including an unsupported or corrupt image. |
| 500 | Unexpected server error; do not expose stack traces, credentials, or internal details. |

Currently, requesting either planned segment route returns FastAPI's route-not-found 404 because those routes do not exist; it does **not** indicate a missing segment. The image endpoint is synchronous and does not persist uploads.

The image endpoint returns 400 for an empty upload, 422 for invalid image data, and propagates unexpected processing failures as server errors. Quality/model limitations are represented as unavailable observations and an Unrated result, not as a successful zero-valued score.

## Shared schema validation

The segment model rejects extra fields, invalid IDs, invalid coordinates/units/ranges, timezone-naive survey timestamps, unavailable values represented as zero, and rated records missing any normalized damage component. It permits explicit nulls for unknown scores/evidence. Backend tests cover these validation boundaries; frontend uses matching TypeScript field names and unions. Generated OpenAPI types are not currently shared automatically, so changes to the contract require coordinated updates and tests.

## Decisions still open

- Persistence, stable ID issuance, pagination order/cursor semantics, data retention, and authorization.
- Whether list retrieval supports further filters or mode-specific response projection.
- Antimeridian bounding-box semantics and timestamp/freshness query behavior.
- Custom error envelope and operational handling.
- Contract versioning and generated cross-language types.
- Calibration format, annotated-image storage/access/retention, and any future asynchronous processing.
- Compatibility/mapping of image-analysis outputs into road-segment records; current Pydantic/TypeScript segment types do not yet implement the proposed image-specific fields.
- Dataset/label version references and safe exposure of model provenance.
