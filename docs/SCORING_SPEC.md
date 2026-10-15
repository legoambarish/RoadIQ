# RoadIQ scoring specification

## Status and scope

This is a provisional hackathon contract, not a validated engineering standard or production scorer. The backend includes a standalone candidate scorer, but the HTTP API does not accept or analyse images and no vision pipeline supplies it with measurements. Image-based pavement structure and visible distress—especially stone aggregates, their boundaries and gaps, texture, aggregate loss, and defects—are the primary product objective. Mapping and mode dashboards are secondary.

The existing segment contract is implemented in `backend/app/schemas/road_segment.py` and mirrored by `frontend/src/types/road-segment.ts`. The richer image-analysis result below is proposed and requires coordinated schema/API implementation; no image-analysis endpoint currently exists. See [API_CONTRACT.md](./API_CONTRACT.md).

The phrase “metal chips” is interpreted provisionally as visible **stone aggregates**. Confirm this with the project owner before model or annotation work. Target surfaces are asphalt/bituminous and cement concrete where evidence permits; return surface type `unknown` when uncertain.

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

The candidate RoadIQ Surface Quality Index (RSQI) is a surface-condition index, not travel suitability, structural strength, skid resistance, or a safety certification. Candidate component scores below are **damage-oriented**: 0 means no detected damage signal under that feature definition, and 100 means the reference maximum damage signal. The overall index is higher-is-better:

```text
Damage = 0.35V + 0.20L + 0.15G + 0.15T + 0.15M
RSQI = 100 - Damage
```

Weights sum to 1. These are initial hypotheses only and must be configurable/versioned and validated before reporting as a meaningful quality index:

| Component | Weight | Candidate evidence and direction |
| --- | ---: | --- |
| `V` — visible defect burden | 0.35 | Area fraction and/or severity of visible cracks, potholes, raveling, and deterioration in usable pavement; more visible deterioration increases damage. |
| `L` — aggregate-loss indicator | 0.20 | Image-inferred loss/displacement of expected surface aggregate, conditioned on surface type and validated reference examples; stronger loss signal increases damage. This is a visual indicator, not proof of material loss below the visible surface. |
| `G` — aggregate boundary/gap anomaly | 0.15 | Gap/void and boundary statistics relative to surface-type-specific, scale/resolution-appropriate references; larger anomalous gaps increase damage. Ordinary aggregate boundaries are not defects by themselves. |
| `T` — image texture anomaly | 0.15 | Surface-type- and capture-condition-adjusted image texture proxy (e.g. local contrast, entropy, or spatial-frequency features); larger validated deterioration-associated anomaly increases damage. This is not physical roughness. |
| `M` — aggregate size/coverage anomaly | 0.15 | Aggregate size-distribution and visible aggregate-coverage deviation from a validated, surface-type-specific reference; greater deterioration-associated deviation increases damage. |

### Candidate image features and measurement integrity

The image-analysis report should expose raw estimates, units, method/provenance, and availability separately from normalized scoring components:

- **Image quality:** blur/focus, exposure, occlusion, perspective, minimum usable pixel dimensions, and whether analysis is supported. Failed quality gates produce `unrated`, not zero defects.
- **Pavement region:** mask/region of interest and usable-area fraction. Exclude non-pavement/occlusion from denominators and disclose the usable fraction.
- **Surface type:** `asphalt_bituminous`, `cement_concrete`, or `unknown`, with confidence. Do not force uncertain classification.
- **Aggregates:** instance count per image; size distribution in pixels; visible aggregate coverage ratio `[0,1]`; boundary/gap statistics in pixels; aggregate-loss indicator as an image inference/proxy. Individual aggregates are reported only when resolution supports separation.
- **Physical aggregates per square metre:** nullable. Report only when ground scale and usable pavement area are established for that image; otherwise report count per image and pixel-space features only.
- **Boundary/gap widths:** report pixels by default. Physical units (e.g. mm) require appropriate per-image scale calibration and enough resolved pixels for meaningful precision.
- **Defects:** visible classes include cracks, potholes, raveling, and other visible deterioration. Preserve class, count/area extent, confidence, and mask/detection provenance. Counts do not imply length/km or area/m² without a surveyed denominator.
- **Texture:** image-derived feature values must be named and versioned; identify them as image texture proxies. Do not label them IRI, physical roughness, or 3D topography.
- **Unknowns:** every unavailable/unreliable measurement is null with an unavailable status/reason, not zero. A numeric zero is permitted only for a valid measurement process that observed zero.

For each feature, normalization must be defined against versioned, labelled references stratified or otherwise validated for surface type and capture conditions (camera, distance, lighting, resolution, perspective). Candidate approaches are monotonic reference ranges/percentiles fitted on training data and frozen before validation/test evaluation; clamp normalized values to `[0,100]` only after the reference mapping is fixed. Avoid normalizing independently per submitted image or test cohort, which would destroy absolute comparability.

The reference ranges, class-specific handling, feature extractors, annotation rubric, and configuration version are not yet agreed. A feature that cannot be extracted reliably or normalized comparably is null. Do not adjust or renormalize weights around missing features. The candidate full index is `unrated` if any required component `V/L/G/T/M` is unavailable, the surface type is unknown where the component depends on it, the image-quality gate fails, or usable area/resolution is inadequate. A future, explicitly versioned alternative may be proposed, but cannot silently treat absent evidence as no damage.

No values for `V/L/G/T/M`, weights, normalizations, thresholds, or confidence are validated today. Task A owns index implementation and must version the weights/normalization; Task C owns extracting image observations and documenting model/output provenance; Task D coordinates held-out evaluation. The existing `damage_components` fields are the current generic scaffold, not a complete image-analysis response contract.

### Task A scorer implementation boundary

`backend/app/services/scoring.py` implements the candidate weighting and label formula as a deterministic service. `score_surface_quality` accepts one explicitly-unit-tagged component measurement for each of `visible_defect_burden`, `aggregate_loss`, `gap_anomaly`, `texture_anomaly`, and `aggregate_distribution_anomaly`, together with upstream image-quality, usable-region, resolution, surface-type, and capture-profile gate decisions. A caller-supplied `ScoringConfig` must provide fixed normalization profiles keyed by surface type and capture profile; each profile contains component-specific units and reference intervals plus a reference-set identifier. Normalization clamps to `[0,100]` and follows the configured damage direction. The service never fits ranges per image/cohort and never renormalizes weights.

The default configuration deliberately contains no normalization references. The scorer therefore returns `unrated` unless a complete applicable profile and all required evidence are supplied. The current repository has no labelled dataset from which to supply or validate RoadIQ reference ranges. Confidence and spatial evidence coverage remain null because their calibration method and denominator are unresolved. Mode suitability for walking, cycling, two-wheeler, car, and bus remains null because no mode-specific formulas/evidence requirements have been agreed. The `rsqi` model serializes to the proposed `API_CONTRACT.md` RSQI object; labels, scoring-config version, and nullable mode outputs are returned as adjacent service metadata for callers that also consume the segment contract.

### Provisional labels

| Surface Quality | Label |
| --- | --- |
| 80 to 100 inclusive | `Good` |
| 60 to less than 80 | `Fair` |
| 40 to less than 60 | `Poor` |
| 0 to less than 40 | `Very Poor` |

Thresholds are configurable hackathon assumptions, not validated engineering thresholds. Label every display as provisional until validated.

An implementation must be able to report **Low Confidence** when a tentative estimate is emitted with calibrated low confidence, or **Unrated** when input/evidence gates fail. Numeric score without adequate evidence is not allowed. Numeric confidence and any low/medium/high bands require calibration on held-out data; cutoffs remain unresolved.

## Confidence, evidence, and explanations

Confidence (0-1) must describe confidence in the assessment, not be conflated with score or coverage. It should account for image quality, usable region, effective resolution, surface-type uncertainty, component availability, model calibration, and disagreement/uncertainty where supportable. Evidence coverage (0-1) needs a documented denominator such as usable pavement area over image area and must not mean model confidence. Both are nullable; do not invent precision. There is not yet an agreed calibration, coverage denominator, quality/resolution threshold, or Low Confidence cutoff. The report must give score contributions, salient detected evidence, unavailable features, caveats, and a human-readable explanation. The frontend displays these and the annotated image without implying annotation is ground truth.

## Dataset and evaluation contract

No RoadIQ-labelled dataset, trained model, or evaluation result is currently present. Dataset creation and evaluation are planned, not completed. Do not state or imply metrics until the held-out evaluation has actually run and been recorded.

### Minimum labelled example

Each image needs a stable `image_id`, `road_segment_id` grouping key (or an explicit `unknown` group), image file/checksum, capture metadata where available (camera/device, timestamp, view/distance, lighting/weather if known), surface type (`asphalt_bituminous`, `cement_concrete`, or `unknown`) and annotator confidence, image-quality/usability label, usable pavement-region mask, annotation protocol/version, and split/group assignment. Annotations should include:

- Aggregate instance masks/IDs and visible aggregate boundaries where resolvable; unresolved aggregate labels must be explicitly marked, not omitted as zero.
- Pixel-space aggregate size measurements and visible coverage; ground scale/calibration metadata and physical measurements only for calibrated images.
- Defect masks/boxes and class labels for cracks, potholes, raveling, and visible deterioration, plus severity/extent according to a written rubric.
- Expert image-based surface-condition label/score and rationale, with independent annotator identity/review status. Field measurements (e.g. calibrated profile/roughness or condition survey) may be linked by segment/time but kept as separate targets with method/unit.
- Image-quality labels and reasons for excluded/unratable images; data provenance/licensing/consent and annotation version.

Keep train/validation/test assignments grouped by road segment and, where feasible, location/session/capture burst. Deduplicate exact files by checksum and detect near-duplicates (perceptual hash/embedding/manual review); all near-duplicates must remain in one split. Freeze test labels and references before tuning. Report dataset counts by split, segment, surface class, defect class, and excluded/unrated cases. A small dataset may support a baseline experiment only; it does not establish generalization.

### Evaluation

Report actual held-out metrics with sample counts, split/dataset version, confidence intervals or resampling method where feasible, and stratification by surface type and relevant image-quality strata:

- Aggregate and defect detection: precision, recall, F1, and AP/mAP where the annotation/task supports it.
- Instance/semantic segmentation and pavement ROI: IoU and Dice; report per-class results.
- Aggregate count: MAE and bias; size distribution: distributional error with the chosen statistic documented; visible coverage/gap metrics: error against expert masks/measurements.
- Surface-type classification: confusion matrix and per-class precision/recall/F1, including `unknown`.
- RSQI versus expert image labels: MAE/RMSE for numeric labels, rank correlation, and weighted kappa for ordinal labels; document adjudication and inter-rater agreement.
- Where field measurements exist: evaluate separately against those measurement protocols; image ratings are not a substitute or proof of physical roughness.
- Confidence: calibration (e.g. reliability curve/ECE or Brier score where applicable) and performance versus coverage/selective risk.

Name pretrained checkpoints, source/license, preprocessing, and whether inference is an untouched pretrained baseline, a frozen feature extractor, or trained/fine-tuned on RoadIQ data. Report all training data and split boundaries. Never describe a pretrained-only baseline as trained on RoadIQ.

## Image-based limitations

- A 2D image cannot establish true 3D roughness, subsurface structure/strength, weather resistance, or skid resistance.
- Shadows, glare, water, dirt, paint, viewpoint, scale, compression, and camera differences can mimic/obscure aggregate gaps, cracks, or texture. Annotated pixels and inferred masks are estimates.
- Aggregate appearance and visible coverage vary by material, construction, age, lighting, and image scale. Do not treat expected ordinary stone texture as deterioration.
- Physical dimensions and counts per square metre require defensible calibration and a valid usable-area denominator.
- Surface type and component-specific model performance may vary; unknown surface type or unsupported image conditions must reduce confidence or make the index unrated.
- Mode-specific suitability remains separate from the RSQI. Surface condition alone does not establish walking or vehicle suitability.

## Mode-specific suitability

Mode scores are independent 0-100 indices (higher is more suitable under the documented evidence), not safety certification, legal access, travel-time prediction, or a probability. No mode-specific formula or minimum evidence threshold is agreed or implemented. Return null rather than a numeric rating where relevant mode evidence is inadequate. Explain evidence and uncertainty.

Walking must not be derived from pavement condition alone: access, comfort, footpaths, and crossings require separate evidence. A missing lane marking must not increase or imply pedestrian suitability. Other mode assessments need mode-relevant constraints and evidence; do not copy surface quality into all five scores.

## Ranking and comparison

- Keep absolute score (0-100) distinct from a relative percentile (position within an explicitly described comparison cohort); never label one as the other.
- Compare/rank only rated segments with sufficient, reasonably comparable evidence, same scoring/normalization version, and compatible survey periods. Do not rank unrated segments as good or include them as zero.
- Surface evidence date, sample count and/or coverage, confidence, and score explanation where available. A percentile must name the cohort and reference period.
- Do not publish rankings until the evidence sufficiency, comparability, freshness, tie handling, and cohort rules are agreed. Those decisions remain open.

## Limitations and unresolved decisions

- Owner confirmation that “metal chips” means stone aggregates.
- Annotation protocol, dataset availability/licensing, image-quality/resolution gate, and surface-specific aggregate references.
- Calibration data, validation process, feature normalization references, component definitions, RSQI formula/threshold approval.
- Minimum image evidence and calibration requirements; confidence calibration, Low Confidence cutoff, and usable-area denominator.
- Expert-label adjudication, inter-rater agreement, field-measurement availability, held-out dataset size, and acceptable performance criteria.
- Pretrained baseline/checkpoint/license and whether/when RoadIQ-specific training is feasible.
- Mode-specific formulas, required evidence, and suitable interpretation.
- Stable ID generation, segment splitting/merging, directionality, and grade/crossfall sign convention.
- Ranking cohorts, percentile method, tie handling, and sample-size disclosure.

This specification does not claim that a prototype rating reflects a transport authority standard or real-world safety.
