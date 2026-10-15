# Task C image-analysis service

## Status and interface

Task C provides a synchronous backend service. Task D owns the HTTP upload route and should pass the uploaded image bytes to:

```python
from app.services.vision import analyze_road_image

report = analyze_road_image(
    image_bytes,
    source_name="road.jpg",  # display/provenance label only; never treated as a path
    calibration=None,         # optional ImageCalibration or matching dictionary
)
```

The function returns a JSON-ready dictionary validated by `ImageAnalysisResponse`. It accepts JPEG, PNG, and WebP bytes; it does not accept a path or remote URL. `ImageValidationError` carries a stable `code` and user-safe `message` for empty, unsupported, oversized, or corrupt images. The service limits uploads to 10 MiB, dimensions to 10,000 pixels per edge and 40 megapixels total, and rejects images below 320×240 for inference. Task D should enforce the byte limit while streaming uploads as well, before buffering the full request.

The service is observation-only. It does not implement an API route or RSQI. `analysis_status` remains `unrated` while the required pavement ROI, material, and aggregate evidence is unavailable. Detected boxes include pixel and normalized coordinates; confidence values are raw model scores and are not calibrated probabilities.

## India-only model policy

The project owner directed that model data remain India-only. Therefore no non-Indian road imagery may be used for training, fine-tuning, validation, or evaluation. The previously wired DetectionBench RF-DETR checkpoint was fine-tuned on the six-country RDD2022 corpus, so the service now refuses to load it. No India-only damage checkpoint is currently active; without an injected test detector, damage outputs remain unavailable. The RF-DETR smoke test from the earlier implementation is historical plumbing evidence only and is not a current India-focused quality result.

India-only damage candidates have improved, but data are not downloaded or pinned yet:

- The official [RDD2022 release](https://github.com/sekilab/RoadDamageDetector) documents an India-specific partition with 7,706 labelled training images and 1,959 unlabelled test images. Its archive returned HTTP 403 in this environment.
- The user-provided [Siddhesh Roboflow project](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2) advertises 7,706 images, CC BY 4.0, and object-detection exports. The opened v2 page reports 5,394/1,541/771 train/validation/test images, Auto-Orient and stretch-resize to 720×720. The dataset page does not establish that every source image or split is independent, and its taxonomy/source relationship must be checked against the original RDD2022 India annotations before use. Do not train or claim metrics from it until a local export is reviewed, split leakage is checked, labels are mapped, and a checksum is recorded.
- A separate [Roboflow RDD2022-India copy](https://universe.roboflow.com/prakhar-kpb1v/rdd2022-india-il8ju/dataset/5) advertises different split sizes and a ten-class taxonomy. Its export was inaccessible here. Treat it as a separate copy/version, not interchangeable with the Siddhesh project.

India-specific adjacent segmentation data are candidates, not replacements for road pavement data:

- The [Indian Roads semantic segmentation dataset](https://platform.ultralytics.com/ultralytics/datasets/indian-roads-semantic-segmentation) corresponds to the e-Yantra/IIT Bombay Indian Roads dataset. The dataset listing describes road/footpath/pothole-related pixel annotations; a public catalog reports 3,227 images and GPL-2.0. It may inform pavement ROI/pothole masks after the original files and license are verified, but does not annotate individual aggregate instances or metal fragments. The Ultralytics platform page itself could not be fetched in this review.
- The peer-reviewed [Indian Footpath Damage Segmentation dataset](https://www.nature.com/articles/s41597-025-06207-x) and [Zenodo record](https://zenodo.org/records/17154852) provide 583 India-collected footpath images with pixel masks; the archive is 4.5 GB. The paper describes Pune pedestrian footpaths (not carriageway pavement), so it is adjacent-domain data only and must not be presented as validation of the road-surface model. Review the record's license and mask schema before any use.
- [iWatchRoadv2](https://arxiv.org/html/2510.16375v1) describes 7,000+ manually box-annotated pothole frames from Indian dashcam footage and links a Kaggle dataset. The paper is licensed CC BY-NC-SA 4.0; separately verify the dataset's license and files. It reports pothole boxes, not aggregate or metal labels, and is a preprint rather than an independently reproduced RoadIQ result.
- [DriveIndia](https://arxiv.org/html/2507.19912v1) describes a large India traffic-object dataset with pothole among 24 classes, but not aggregate or metal-fragment labels. The paper says release is for academic/non-commercial research through TiHAN-IIT Hyderabad; confirm actual availability and terms before considering it. It is not required for the current image-surface MVP.

The user-provided [Indian Road Damage & Infrastructure Dataset (IRDID)](https://github.com/ahs695/Indian-Road-Damage-Infrastructure-Dataset) was audited at commit `98b12608720a2903878176598a3c94cf4d5561b6`. Its repository declares CC BY 4.0 and 1,200 image-level labels across six classes, but the checked-out copy has only 1,049 images; 151 labelled image records have no matching file after normalizing the documented class-folder names. The supplied split lists have 840/180/180 IDs, but exact duplicate image bytes occur across splits (77 train/validation, 67 train/test, and 11 validation/test duplicate groups). Metadata also names third-party map, news, stock-photo, and social-media sources; rights for those individual images have not been independently verified. The labels are image-level only: there are no crack/pothole boxes, aggregate masks, or metal-fragment annotations. Do not train or report held-out metrics from its published split without repairing missing files, grouping duplicate images before splitting, and resolving image provenance.

None of the reviewed India-only candidates provides individual stone-aggregate masks or a separate metal-fragment class. Those remain unavailable until India-only labels are supplied or collected and reviewed. The roadside-debris Roboflow link provided by the user did not resolve to an inspectable dataset page in this review; available search results did not confirm its geography, label taxonomy, or license. In particular, generic debris labels cannot stand in for metal-fragment labels. The user explicitly directed that ACAD and all non-Indian data be excluded.

## Setup and local workflow

From the repository root, using the project's supported Python 3.12 environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
python -m scripts.analyze_road_image /path/to/your/road-image.jpg
```

No checkpoint download is configured. The legacy `ROADIQ_VISION_MODEL_PATH` is rejected when it points to the known multinational checkpoint. The local CLI validates the caller-provided image and returns an `unrated` report with defect measurements unavailable. The Roboflow India-specific datasets and papers are data candidates only; no candidate checkpoint is configured or verified. Once an India-only dataset and checkpoint are selected and pinned, their preprocessing, architecture, hardware requirements, licensing, and evaluation protocol must replace this placeholder guidance.

## What the MVP can and cannot report

Implemented:

- image byte/type/dimension validation and EXIF orientation handling;
- heuristic resolution, exposure, and edge-detail quality observations, explicitly unvalidated on RoadIQ data;
- a named tile grayscale contrast proxy, never described as physical roughness/IRI;
- test-injected detector outputs for wrapper tests only;
- structured model-load and inference errors, with unsupported or unavailable measurements left null.

Unavailable until a reviewed model and labels exist:

- pavement ROI mask and usable-area fraction;
- asphalt/concrete classification;
- individual stone-aggregate segmentation, counts, size/coverage/boundary statistics, and aggregate-loss proxy;
- literal metal-fragment detection (reported separately from ordinary stone aggregates);
- raveling and other visible deterioration classes;
- mask-derived defect area, calibrated physical sizes, and counts per square metre.

No RoadIQ held-out India-only evaluation has run. Missing defect detections must never be interpreted as evidence that the road is undamaged. A 2D image does not establish internal structural strength, weather resistance, or actual skid resistance. All heuristic cutoffs and confidence thresholds need review against labelled, held-out Indian road images before product interpretation.

## Calibration behavior

Calibration may be passed as `ImageCalibration` or a matching dictionary with `method`, `pixels_per_mm`, `usable_area_m2`, `image_sha256`, and `verified`. It is considered bound to the image only when verified, positive, and associated with the exact uploaded-byte SHA-256. The current baseline does not segment aggregates or gaps, so physical measurements remain unavailable even when calibration is valid. Calibration alone never creates an aggregate count or pixel-to-ground measurement.

