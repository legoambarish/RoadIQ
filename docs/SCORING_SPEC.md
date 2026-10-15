# RoadIQ scoring specification

## Status and scope

This is the provisional hackathon contract, not a validated engineering standard or an implemented production scorer. The backend currently validates the data shape; it does not calculate a score. All weights, normalizations, and label thresholds below are configurable assumptions that require team/domain review before use beyond a clearly identified demo.

The shared segment contract is implemented in `backend/app/schemas/road_segment.py` and mirrored by `frontend/src/types/road-segment.ts`. API retrieval remains planned; see [API_CONTRACT.md](./API_CONTRACT.md).

## Road-segment data contract

The JSON field names below are canonical in both Python and TypeScript. Coordinates use GeoJSON RFC 7946 order: `[longitude, latitude]` in WGS 84 decimal degrees; a geometry is a `LineString` with at least two valid positions. `segment_id` is a stable, opaque identifier, 1-64 characters matching `[A-Za-z0-9_-]+`. Its generation and persistence strategy is unresolved.

Every segment includes:

| Field | Type / unit | Validation and meaning |
| --- | --- | --- |
| `segment_id` | string | Stable identifier; unique within the RoadIQ dataset. |
| `geometry` | GeoJSON `LineString` | At least two `[longitude, latitude]` positions; longitude `[-180, 180]`, latitude `[-90, 90]`. |
| `survey_source` | string | Non-empty, at most 128 characters; identifies the survey/device/import. |
| `surveyed_at` | ISO-8601 timestamp | Required and timezone-aware. |
| `measurements` | object | Raw measurement fields below. Missing evidence uses `status: "unavailable"`, `value: null`, `source: null`, never a zero substitute. |
| `damage_components` | four nullable numbers, 0-100 | Normalized damage inputs A, D, S, R. These are not the raw measurement values. |
| `surface_quality_score` | nullable number, 0-100 | Higher means better surface condition; null when unrated. |
| `quality_label` | nullable enum | Provisional `Good`, `Fair`, `Poor`, `Very Poor`; null when unrated. |
| `mode_suitability` | nullable numbers, 0-100 | Separate `walking`, `cycling`, `two_wheeler`, `car`, `bus` values. Null means unsupported/unknown, not unsuitable. |
| `pedestrian_context` | nullable fields | `footpath_present` and `crossings_observed` are booleans or unknown; `comfort_score` is 0-100 or unknown. These are separate from surface condition. |
| `confidence` | nullable number, 0-1 | Calibrated confidence, not a quality score. Null until a defensible method exists. |
| `evidence_coverage` | nullable number, 0-1 | Fraction under a defined coverage protocol; null when unavailable or not defined. |
| `assessment_status` | `rated` or `unrated` | An unrated segment has null surface score and label. A rated segment requires all four normalized damage inputs and a score and label. |
| `explanation` | non-empty string | Human-readable basis and uncertainty; do not present unsupported claims. |
| `data_provenance` | array | Each item maps `field_path` to `sensor`, `image_inference`, `user_input`, or `demo_fixture`. |

Each item under `measurements` has `{ "value": number | null, "unit": string, "status": "observed" | "estimated" | "unavailable", "source": source | null }`. Observed and estimated values require a value and source. Unavailable measurements require null value and source. Units and validation:

| Measurement | Unit | Validation |
| --- | --- | --- |
| `defect_count` | `defects` | Non-negative whole number. |
| `defect_density` | `defects_per_km` | Non-negative; count per surveyed kilometre. |
| `damaged_area_ratio` | `ratio` | Fraction `[0, 1]`, not percent. |
| `severity` | `severity_index_0_100` | Index `[0, 100]`; severity rubric remains unresolved. |
| `roughness_iri` | `m_per_km` | Non-negative International Roughness Index (IRI). |
| `longitudinal_grade` | `percent` | Signed rise/run along the road. |
| `crossfall` | `percent` | Signed slope across the road. Its direction/sign convention remains unresolved. |

All numeric values must be finite. A measurement's unit must match its field. The schema does not infer a measurement from geometry or imagery. For example, do not report real-world longitudinal grade from pixels without a documented calibration method and scale.

`mode_suitability` is not interchangeable with `surface_quality_score`. A smooth surface alone does not establish that walking is safe or suitable. A walking assessment needs relevant access, comfort, footpath, and crossing evidence; pedestrian attributes remain distinct from pavement condition. Missing lane markings are not evidence of pedestrian-friendliness.

### Illustrative unrated JSON

```json
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
      "value": null, "unit": "severity_index_0_100", "status": "unavailable", "source": null
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
```

## Provisional surface scoring

If (and only if) the four components have supportable, comparable normalized inputs:

```text
Damage = 0.35A + 0.25D + 0.25S + 0.15R
Surface Quality = 100 - Damage
```

`A`, `D`, `S`, and `R` mean normalized damaged area, defect density, severity, and roughness on `[0, 100]`; larger values mean more damage. Weights sum to 1. The four values are provided as `damage_components.damaged_area`, `.defect_density`, `.severity`, and `.roughness`.

Normalization contract (the formulas are candidates, not yet calibrated):

- `A`: damaged-area ratio mapped to a 0-100 damage index using a configurable reference ratio.
- `D`: defects/km mapped to a 0-100 index using a configurable reference density. Counts may be divided by segment length only when that surveyed length and count cover the same interval.
- `S`: severity converted using an agreed defect severity rubric to 0-100.
- `R`: IRI in m/km mapped to a 0-100 damage index using a configurable reference IRI.
- Clamp normalized inputs to `[0, 100]`; do not clamp or fill missing raw measurements into an apparent observation.
- Reference values, severity rubric, and configuration version are not yet agreed. Until they are fixed and justified, a component without an approved mapping is null.

Do not renormalize weights across available components. If any one of A/D/S/R is missing, evidence is insufficient, or inputs are not reasonably comparable, return `assessment_status: "unrated"` and null surface score/label. Missing evidence is not zero damage. The schema enforces the rated/unrated shape but deliberately does not calculate or validate the formula; Task A owns scoring implementation.

### Provisional labels

| Surface Quality | Label |
| --- | --- |
| 80 to 100 inclusive | `Good` |
| 60 to less than 80 | `Fair` |
| 40 to less than 60 | `Poor` |
| 0 to less than 40 | `Very Poor` |

Thresholds are configurable hackathon assumptions, not validated engineering thresholds. Label every display as provisional until validated.

## Confidence, evidence, and explanations

Confidence (0-1) must describe confidence in the assessment, not be conflated with evidence coverage or quality. Evidence coverage (0-1) needs a documented denominator (e.g., surveyed length/area or required evidence fields) and sampling protocol. Both are nullable; do not invent precision. There is not yet an agreed confidence calibration, coverage denominator, minimum coverage, or age/freshness limit. Task A must expose these limitations and explain which components and sources informed any score.

## Mode-specific suitability

Mode scores are independent 0-100 indices (higher is more suitable under the documented evidence), not safety certification, legal access, travel-time prediction, or a probability. No mode-specific formula or minimum evidence threshold is agreed or implemented. Return null rather than a numeric rating where relevant mode evidence is inadequate. Explain evidence and uncertainty.

Walking must not be derived from pavement condition alone: access, comfort, footpaths, and crossings require separate evidence. A missing lane marking must not increase or imply pedestrian suitability. Other mode assessments need mode-relevant constraints and evidence; do not copy surface quality into all five scores.

## Ranking and comparison

- Keep absolute score (0-100) distinct from a relative percentile (position within an explicitly described comparison cohort); never label one as the other.
- Compare/rank only rated segments with sufficient, reasonably comparable evidence, same scoring/normalization version, and compatible survey periods. Do not rank unrated segments as good or include them as zero.
- Surface evidence date, sample count and/or coverage, confidence, and score explanation where available. A percentile must name the cohort and reference period.
- Do not publish rankings until the evidence sufficiency, comparability, freshness, tie handling, and cohort rules are agreed. Those decisions remain open.

## Limitations and unresolved decisions

- Calibration data, validation process, reference values, severity rubric, and formula/threshold approval.
- Minimum evidence and freshness thresholds; confidence calibration and evidence-coverage denominator.
- Mode-specific formulas, required evidence, and suitable interpretation.
- Stable ID generation, segment splitting/merging, directionality, and grade/crossfall sign convention.
- Ranking cohorts, percentile method, tie handling, and sample-size disclosure.

This specification does not claim that a prototype rating reflects a transport authority standard or real-world safety.
