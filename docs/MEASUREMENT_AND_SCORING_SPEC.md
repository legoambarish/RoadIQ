# Measurement and scoring contract — image-analysis-v1.1

The frozen road-segment contract and the existing five-component RSQI implementation are unchanged. Image responses add a separate `visual_distress` object (`vda-observations-v1`), model provenance/readiness, calibration status, actual timings, and mask geometry where a genuine semantic model supplied a mask. Backend findings are authoritative for the live UI; the frontend draws them without computing a condition score.

## Geometry and transforms

1. Decode JPEG/PNG/WebP, verify size limits, apply EXIF orientation, preserve stored size/orientation and original file SHA-256. All geometry uses **EXIF-oriented source image pixels**, origin top-left, x right/y down. Browser previews use the same orientation.
2. VOC source annotation conversion is 1-based inclusive to zero-based half-open: xmin/ymin minus one, xmax/ymax unchanged, clipped to actual dimensions. Invalid/reversed boxes and source dimension mismatches fail preparation.
3. YOLO letterbox padding/resize is reversed by its original-shape output. The adapter verifies that shape. Optional tiles add their source offsets and run class-wise NMS (IoU .5), with overlapping edge-complete windows and a 16-tile resource limit. This optional mode has geometry unit tests; the benchmark uses the untiled 640-pixel path. It has not established a small-defect accuracy improvement.
4. `box_extent_width_px`/height are rectangle extents. Counts are detector candidate counts after NMS, not confirmed physical defects. A box cannot supply damaged area, crack width/length, pothole volume or depth. Edge clipping and extents smaller than four source pixels get explicit flags. The four-pixel rule is a resolution warning heuristic, not a validated defect-size threshold.
5. The corrected v4 U-Net uses aspect-preserving letterboxing for training and inference. Metadata records source/input/resized dimensions, actual x/y scale and four padding edges. Synthetic mask padding maps to ignore 255; real source 255 maps to learned background. Inference crops padding, takes model-grid argmax and projects labels by nearest-neighbor to the source frame; boundaries therefore retain model-grid quantization. Raw class confidence is measured on the unpadded model grid. Older v2/v3 stretch runs are retained as baseline evidence and are not the corrected application checkpoint. Road and pothole masks use validated row-major binary RLE: alternating zero/one runs beginning with zero; `[height,width]`; nonnegative integer runs sum to exactly all pixels. They are predictions, visually distinct from source labels. No source-sized softmax tensor is needed in v4.

`segmented_area_px` is mask foreground count. `image_projected_fraction = foreground/(image_width*image_height)`. `grid_boundary_length_px` counts horizontal/vertical exposed pixel-cell edges (four-neighbor lattice perimeter), not Euclidean contour length or crack centerline. Eight-connected component count is explicitly **not** a validated instance count. Geometry reports touching-frame clipping and missing uncertainty calibration.

For the additive affected-pavement pixel fraction, the denominator is the predicted union of road and pothole source classes. Footpath, ambiguous shallow paths and source background are excluded; the shallow class is not independently established as drivable pavement. Numerator is pothole mask intersected with that union. A zero denominator returns null. This is an experimental image-projected prediction affected by perspective, model error, shadows/occlusion and capture framing; it is not ground area. `measurement_status=experimental_model_prediction` and `physical_measurement_validated=false` accompany the geometry. The older `usable_area_ratio`/road mask retain their original road-class-only semantics for compatibility. Semantic and detector results are separate models: there is no invented one-to-one correspondence between a semantic component and a detector instance.

## Quality and reliability

Intake: maximum 10 MiB image bytes, 40 megapixels and 10,000-pixel edge; declared/decoded MIME must match. Animated/multiframe files are rejected, so a moving browser preview cannot misrepresent first-frame geometry. A raw multipart ceiling of 10 MiB +64 KiB also bounds streams without Content-Length before file parsing. Decode failure is an HTTP error. Extreme exposure or resolution below 320x240 makes the image unusable. Existing edge-detail/exposure heuristics are disclosed; the edge calculation excludes artificial image borders. Saturation (>15% pixels >=250) and deep shadow (>50% <6) add warnings. These are heuristic capture warnings, not a validated classifier for wetness, blur, material or road presence.

Inference is offloaded from the async event loop and bounded to two simultaneous analyses; excess receives HTTP 503 with Retry-After. Model-load/inference failures are explicit structured errors. Liveness `/health` is independent from actual configured-model load checks at `/vision-readiness`. Readiness is not an accuracy certification.

Raw detector scores and mean semantic softmax values are **uncalibrated**. They are not assessment reliability or physical-measurement confidence. No ECE/temperature calibration has been fitted. Reliability is qualitative `limited` or `unavailable`, with reasons, rather than an unsupported 0–1 probability. There is no validated material/viewpoint/occlusion classifier; material remains unknown. ROI and quality limitations remain visible even when model predictions exist.

Predicted road-class coverage below 10% triggers a disclosed, unvalidated visibility warning and VDA `low_confidence`; it does not suppress otherwise valid candidate counts or establish absence of road. Higher coverage does not validate material, occlusion, viewpoint, geometry or a condition score.

## Visual Distress Assessment

| State | Trigger | Interpretation |
| --- | --- | --- |
| unavailable | Model missing/load/inference failed | Counts null, no inferred condition |
| unusable | Image quality gate failed | Counts null, request a supported capture |
| low_confidence | Loaded detector, heuristic capture warnings | Candidate observations with limited evidence |
| defects_detected | Supported candidate(s), no capture warning | Inspect localized candidates; severity unknown |
| no_defect_detected | Loaded detector returns zero at threshold .25 | No supported detection at this threshold; not healthy pavement |

A pothole candidate always produces a localized inspection flag, regardless of average area. Alligator-crack candidates, clipping and tiny extents have additional flags. Neither a tiny affected ratio nor many clear pixels can erase a localized hazard candidate. Flags are inspection prompts; no safe/unsafe or operational-severity claim is made.

VDA has **no numeric index or Good/Medium/Bad grade**. `score_eligible=false`, score/grade/confidence=null. Source class labels have no validated severity/grade labels, and visual appearance alone cannot establish structural condition. This is consistent with keeping distress observations separate from standardized pavement inspection; see [FHWA distress manual](https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/ltpp/13092/001.cfm). No ASTM PCI/IRI compliance is claimed.

## Legacy RSQI, physical measurements and percentile

The original V/L/G/T/M evidence gates, weights, caps and scoring-version identity are preserved. Default normalization references are empty; aggregate loss, gaps, individual distribution, material/capture support and validated normalization are missing. The live API supplies no fabricated component values, so RSQI and travel-mode scores remain **Unrated/null**. The historical texture candidate heuristic is retained as experimental and never substituted for individual stones or a required scoring component.

Calibration status is explicit and bound to the image hash where supplied by an existing local caller. This release's HTTP workflow does not accept a validated fiducial/homography or operator scale. A `verified` flag in old metadata is not independent physical validation. No physical measurement is computed from it. Crack widths in mm, affected ground m², depths, IRI, PCI, friction and load capacity stay null. Box pixels are never converted to cm by a universal scale.

No genuinely scored, eligible, version-compatible fixed RSQI cohort exists; therefore reference percentile is null with a reason. There is no percentile over raw confidence, no rank over Unrated values, and no fabricated 20/20/20 distribution. P1 physical dimensions need measured references and error assessment; P1 percentile needs valid scores and a frozen compatible cohort. Those are real evidence gates, not scaffolding to call complete.
