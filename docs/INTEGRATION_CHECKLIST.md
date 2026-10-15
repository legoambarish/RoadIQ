# Task D integration preparation and contract audit

**Status recorded 2026-10-16:** Task D has packaged and exercised a Windows desktop build on the available host. Live image-analysis integration is still unimplemented. This file records current merged dependencies and proposed field mappings; it does not approve a new shared API contract.

## Dependency readiness

- **Task A:** PR #1 is merged into main at commit 7995ff4. The provisional scorer and its tests are present. Its default normalization profiles are empty, so it returns an unrated result unless a caller supplies a complete fixed profile and all required evidence. No RoadIQ-labelled calibration set exists.
- **Task B:** PRs #2, #5, and #6 are merged into main. PR #13 is open from task/b-map-dashboard (six commits ahead of main at e9d3b70) and refreshes the preview-only image-report copy/state plus production health URL default. Its PR description records passing TypeScript, Vite build, Oxlint, and git diff checks; the GitHub Checks tab has no CI runs. No backend/API contract changed, and the image panel still does not upload or analyze images.
- **Task C:** PRs #4, #7, #8, #10, and #11 are merged into main. The local observation/demo service and tests exist, but there is no image HTTP route or active trained checkpoint. Usable-pavement/material classification, individual aggregate/metal analysis, calibrated physical measurements, and held-out RoadIQ evaluation remain unavailable; Task C is not ready as a complete production analysis dependency.
- **Task D:** checklist PR #3 is merged. This package branch is task/d-integration-release, based on current origin/main at f83b4d7. Windows packaging and desktop-runtime tests are published for review in [PR #12](https://github.com/Sine-Ads/RoadIQ/pull/12) against main. The PR is open and unmerged.

## Field crosswalk

### Shared proposed image API

The only live backend endpoint on main is GET /api/v1/health. The image-analysis request/response in docs/API_CONTRACT.md is proposed, not implemented. It proposes POST /api/v1/image-analyses with an image part and optional calibration part.

The proposed response names analysis_id, analysis_status, image_quality, pavement_region, surface_type, aggregate_analysis, defects, texture_features, rsqi, data_provenance, annotated_image, and model. analysis_status is completed, low_confidence, unrated, or failed. Each measurement object has value, unit, status, and source; status is observed, estimated, or unavailable. Available values require a source; unavailable requires value=null and source=null. Proposed source values are sensor, image_inference, user_input, and demo_fixture. Ratios use unit ratio, score uses index_0_100, and the example component values use damage_index_0_100. Unavailable values must not be converted to zero.

### Task A scorer input and output

ScoringEvidence has surface_type (asphalt_bituminous, cement_concrete, or unknown), capture_profile (nullable string), image_quality_usable, usable_region_adequate, and resolution_adequate (nullable booleans), and components keyed by:

- visible_defect_burden
- aggregate_loss
- gap_anomaly
- texture_anomaly
- aggregate_distribution_anomaly

Each FeatureObservation has numeric value or null, a unit string, status observed/estimated/unavailable, and source. Available observations require a value and source; unavailable observations require both to be null. The selected ScoringConfig profile is keyed by surface type and capture profile and defines the expected unit and fixed normalization interval for every component. The default config contains no reference profiles.

RSQIResponse has value (nullable, unit index_0_100), status rated/low_confidence/unrated, confidence (always null today), confidence_band (unrated or null), components, explanation, and limitations. Each normalized ComponentScore has value (nullable, unit damage_index_0_100), status/source, weight, and weighted_contribution; unavailable components require null value, source, and contribution. ScoringResult also exposes quality_label, scoring_version, mode_suitability, evidence_coverage, and suitability_explanation. Mode suitability and evidence coverage remain null under the current policy.

### Task C observation service

The branch schema ImageAnalysisResponse currently declares analysis_status, image, image_quality, pavement_region, surface_type, aggregate_analysis, defects, metal_fragments, texture_features, calibration, processing_errors, model, and data_provenance. It does not declare the proposed analysis_id, rsqi, or annotated_image fields. It adds image, metal_fragments, calibration, and processing_errors. The C schema comment says Task D may wrap this service payload.

C ImageMeasurement has value (Any or null), unit (string), status observed/estimated/unavailable, source limited to image_inference or user_input (or null), and an optional reason. Available values require value and source; unavailable values require value=null and source=null. This differs from the proposed source union, does not type-check measurement values/units narrowly, and includes reason which the proposal does not include in the measurement object.

Current C output uses these exact measurement unit strings:

- Aggregate fields: aggregate_count / aggregates_per_image; aggregate_count_per_m2 / aggregates_per_m2; size_distribution / pixel_distribution; physical_size_distribution / mm_distribution; visible_coverage_ratio / ratio; boundary_gap_statistics / pixel_statistics; physical_boundary_gap_statistics / mm_statistics; aggregate_loss_indicator / damage_index_0_100.
- Pavement region: usable_area_ratio / ratio; annotation / uri.
- Defects: count / defects_per_image; visible_area_ratio / ratio; annotation / uri. Detection boxes use bbox_xyxy_px and bbox_xyxy_normalized; these are not proposed image-analysis measurement fields.
- Metal fragments: count / fragments_per_image; visible_area_ratio / ratio; annotation / uri.
- Texture: feature name tile_grayscale_contrast_v1, unit grayscale_intensity_std_0_255, method_version 1, and is_physical_roughness=false.

Unavailable measurements currently carry null value and source, plus a reason. The default C result reports surface_type.value=unknown with unit category and unavailable status; aggregate/metal counts, physical measurements, annotations, and ROI are unavailable. The service sets analysis_status to unrated and does not attach an RSQI. Its India-only policy rejects the legacy multi-country checkpoint; no active checkpoint or labelled aggregate/metal set is configured.

### Task B frontend fixtures

The B fixture type is RoadSegment with these exact fields: segment_id, geometry, survey_source, surveyed_at, measurements, damage_components, surface_quality_score, quality_label, mode_suitability, pedestrian_context, confidence, evidence_coverage, assessment_status, explanation, and data_provenance.

Its measurement fields and units are defect_count/defects, defect_density/defects_per_km, damaged_area_ratio/ratio, severity/severity_index_0_100, roughness_iri/m_per_km, longitudinal_grade/percent, and crossfall/percent. Measurement status is observed/estimated/unavailable; source is sensor/image_inference/user_input/demo_fixture or null. B marks available fixture measurements with estimated status and demo_fixture source; unavailable measurements have null value and source. Record scores and mode suitability are raw nullable numbers rather than Measurement objects; provenance is attached by field_path at the record level. The nine records, including their map geometry and scores, are illustrative fixtures. The image panel has no typed image-analysis response and shows an Unrated placeholder until a future API exists.

### Unresolved mapping proposals — not agreed

Potential input mappings from Task C to Task A are candidates only:

- defects counts/visible area to visible_defect_burden;
- aggregate_loss_indicator to aggregate_loss;
- boundary_gap_statistics to gap_anomaly;
- named texture feature values to texture_anomaly;
- size_distribution and/or visible_coverage_ratio to aggregate_distribution_anomaly.

These mappings cannot be implemented by copying raw values. Task A requires a unit that exactly matches a fixed surface/capture profile and a normalized damage value for the RSQI. Task C currently has no validated aggregate or ROI measurements, and the default scorer profile is empty. Task C’s source enum also excludes demo_fixture and sensor. Affected owners must agree on raw inputs, unit conversion, source/status handling, profile version, and missing-evidence behavior before Task D connects them.

## End-to-end scenario checklist

| Scenario | Required behavior before release | Current status |
| --- | --- | --- |
| Valid supported image with successful analysis | Return a real analysis result; only rate when all required measurements, gates, and fixed scorer references are present. | No image route or active model. |
| Malformed, unsupported, or invalid image | Return a safe request/processing error; do not return a successful empty report. Agree exact HTTP mapping before implementation. | C service raises validation errors; no route mapping. |
| Image-quality gate fails | Preserve failure reason and return unrated with null score; do not render green/good. | C has heuristic quality checks; route and frontend flow absent. |
| Pavement ROI or resolution gate fails | Mark analysis unrated and required observations unavailable; never infer zero defects. | No validated ROI model; integration behavior unimplemented. |
| Unknown surface type | Preserve unknown; no material-specific profile means unrated. | C currently emits unknown/unavailable. |
| Missing, null, unavailable, or invalid measurement | Preserve unavailable as null with reason; reject invalid non-finite, boolean, out-of-range, or mismatched-unit evidence; never impute zero. | A validates scorer observations; API boundary absent. |
| Unit, provenance, or status mismatch | Do not coerce or silently map; agree the conversion/status policy and test it at the route boundary. | C and API source sets differ; mapping is unresolved. |
| Incomplete scorer input | Return unrated with null RSQI and explicit explanation; weights are not renormalized. | A implements this; no route invokes it. |
| Model, backend, or API unavailable | Expose an unavailable/error state, keep health separate from analysis readiness, and do not substitute fixture predictions. | Health endpoint only; B displays health-only/offline demo labels. |
| Frontend report and suitability | Display backend explanations and unavailable values; show mode values separately from surface quality; map colors, mode changes, rankings, and details must reflect backend values. | B has fixture dashboard and local image preview only; not connected to segment or image APIs. |

## Commands, configuration, and demo limits

The repository documents the development backend as `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`, from `backend/` after activating the root virtual environment. It documents the frontend as `npm run dev -- --host 0.0.0.0` from `frontend/`, backend tests as `pytest backend/tests -q` from the root, and frontend checks as `npm run build` and `npm run lint` from `frontend/`.

The verified Windows package commands, from the repository root, were:

~~~powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\scripts\build_windows.ps1
.\dist\RoadIQ.exe
~~~

Backend tests passed with 93 passed and 2 skipped, plus one existing Starlette deprecation warning. The build script ran `npm install`, built the frontend with `VITE_API_BASE_URL=/api/v1`, and produced `dist\RoadIQ.exe` (24,040,596 bytes). `npm run lint` and the Vite/TypeScript build passed. The runtime smoke check used a reduced inherited `PATH` containing only Windows system binaries; the app returned health JSON, served the dashboard, opened the default browser, rejected an unauthenticated restart request with 403, and gracefully restarted when the same executable was launched again. This was not a clean-VM test.

The exact manual frontend commands used were `npm run build -- --outDir ../build/windows-frontend --emptyOutDir` with `VITE_API_BASE_URL=/api/v1`, then `npm run lint`, from `frontend/`. The packaged app command is `dist\RoadIQ.exe`; its single-file bundle does not need Python or Node at runtime. Logs are written to `%LOCALAPPDATA%\RoadIQ\logs\RoadIQ.log`. Starting the executable a second time replaces only a live process whose executable path matches the recorded `RoadIQ.exe`. Closing the browser leaves the local service running; stopping it currently requires ending RoadIQ from Task Manager or shutting down Windows.

The host provided Python 3.12.14, Node 24.16.0, npm 11.13.0, and PyInstaller 6.22.3. The build environment was a local `.venv`; the output package was built on Windows 11. Generated `build/` and `dist/` outputs are ignored.

The only `.env.example` settings are `FASTAPI_ENV`, `API_PREFIX`, `CORS_ORIGINS`, and `VITE_API_BASE_URL`; the inspected values are development defaults, not credentials. The packaged app overrides API prefix/environment and uses loopback. No secret, model download, map-provider key, database, image storage, or external service is required for runtime. The dashboard uses local fixtures and a browser-only image preview. Task C has optional vision requirements and experimental code, but no approved active India-only checkpoint is bundled or downloaded by the app.

The demo may show B’s numeric RoadSegment values only when clearly labeled fixture/demo values. It must not describe them as RoadIQ observations, scorer outputs, model predictions, validated scores, or safety ratings. No end-to-end image-analysis demo or production release readiness is claimed.
