# Task C image-analysis service

Current India implementation: [MEASUREMENT_AND_SCORING_SPEC.md](MEASUREMENT_AND_SCORING_SPEC.md), [MODEL_CARD.md](MODEL_CARD.md) and [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md) supersede the earlier model-availability status below. The existing service remains the integration boundary; genuine detector/semantic adapters add observations while retaining the older experimental texture path. No individual aggregate, metal, material, physical dimension or condition-grade validation is implied.

## Status and interface

Task C provides a synchronous backend service. Task D owns the HTTP upload route and should pass the uploaded image bytes to:

```python
from app.services.vision import analyze_road_image

report = analyze_road_image(
    image_bytes,
    source_name="road.jpg",  # display/provenance label only; never treated as a path
    calibration=None,         # optional ImageCalibration or matching dictionary
    segmentation_model=None,  # optional injected model for tests; production loads configured checkpoint
)
```

The function returns a JSON-ready dictionary validated by `ImageAnalysisResponse`. It accepts JPEG, PNG, and WebP bytes; it does not accept a path or remote URL. `ImageValidationError` carries a stable `code` and user-safe `message` for empty, unsupported, oversized, or corrupt images. The service limits uploads to 10 MiB, dimensions to 10,000 pixels per edge and 40 megapixels total, and rejects images below 320×240 for inference. Task D should enforce the byte limit while streaming uploads as well, before buffering the full request.

The service is observation-only. It does not implement an API route or RSQI. `analysis_status` remains `unrated` while the required pavement ROI, material, and aggregate evidence is unavailable. Detected boxes include pixel and normalized coordinates; confidence values are raw model scores and are not calibrated probabilities.

## Local hackathon MVP

Run the local end-to-end demo from the repository root:

```bash
PYTHONPATH=backend python -m scripts.demo_road_image --output-dir /tmp/roadiq-demo --seed 42
```

The command analyzes a deterministic synthetic input and writes `annotated-preview.jpg` plus `analysis-report.json`. Pass `--image /path/to/road.jpg` to analyze a local JPEG, PNG, or WebP instead. No image is uploaded. The output contains a quality report, a named texture proxy, a high-frequency texture-candidate RLE mask and area ratio, and an annotated preview. The preview explicitly labels candidates as not particle segmentation. Results remain unrated; particle counts, physical measurements, and calibrated confidence are unavailable. Synthetic output demonstrates pipeline plumbing only.

An optional India-road semantic segmentation checkpoint can gate candidate regions to its predicted road mask. This ROI is experimental and uncalibrated, and does not turn texture candidates into aggregate masks. Browser upload/report and HTTP API integration are outside Task C and are not implemented.

## India-only model policy

The project owner directed that model data remain India-only. Therefore no non-Indian road imagery may be used for training, fine-tuning, validation, or evaluation. The previously wired DetectionBench RF-DETR checkpoint was fine-tuned on the six-country RDD2022 corpus, so the service now refuses to load it. No India-only damage checkpoint is currently active; without an injected test detector, damage outputs remain unavailable. The RF-DETR smoke test from the earlier implementation is historical plumbing evidence only and is not a current India-focused quality result.

India-only damage candidates have been reviewed, but no additional damage dataset was selected or downloaded. (The owner asked to keep this prototype to one or two datasets.) The candidates below remain reference notes only:

- The official [RDD2022 release](https://github.com/sekilab/RoadDamageDetector) documents an India-specific partition with 7,706 labelled training images and 1,959 unlabelled test images. Its archive returned HTTP 403 in this environment.
- The user-provided [Siddhesh Roboflow project](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india/dataset/2) advertises 7,706 images, CC BY 4.0, and object-detection exports. The opened v2 page reports 5,394/1,541/771 train/validation/test images, Auto-Orient and stretch-resize to 720×720. The dataset page does not establish that every source image or split is independent, and its taxonomy/source relationship must be checked against the original RDD2022 India annotations before use. Do not train or claim metrics from it until a local export is reviewed, split leakage is checked, labels are mapped, and a checksum is recorded.
- The dataset's current [Roboflow overview](https://universe.roboflow.com/siddhesh-onuvb/road-damage-detection-india) is inspectable and lists 7,706 images, CC BY 4.0, and nine RDD-style damage labels (D00, D01, D10, D11, D20, D40, D43, D44, D50). It has no published project description, and no aggregate-instance or metal-fragment classes. Confirm India-only source images and split hygiene from an export before using it.
- The user-provided [RDD2020 Mendeley record](https://data.mendeley.com/datasets/5ty2wb6gvg) describes 26,336 images from India, Japan, and the Czech Republic with D00/D10/D20/D40 damage annotations and lists CC BY-NC 3.0. It is mixed-country and must not be used as a whole. The owner approved non-commercial licensed data for the free prototype, so an India-only country partition may be considered for damage experiments after verifying an India-only manifest, terms, and split provenance. The public metadata lists 1.85 GB of files, but archive retrieval through Mendeley's public download endpoint failed during this session; no archive was fetched. It has no aggregate-instance or metal-fragment labels.
- The user-provided [Indian Roads Dataset on Kaggle](https://www.kaggle.com/datasets/mitangshu11/indian-roads-dataset) appears India-focused and is described elsewhere as road/pothole/speed-breaker imagery, but its Kaggle card and license could not be independently inspected here. Treat geography, labels, annotation format, and usage rights as unverified; do not download or train until the dataset card/license are confirmed.
- The user-provided [BharatPotHole Kaggle dataset](https://www.kaggle.com/datasets/surbhisaswatimohanty/bharatpothole) is described by its associated iWatchRoad project as 7,000+ annotated Indian dashcam frames for pothole detection. Its paper notes that cracks, shadows, debris, stains, and utility covers can appear but are not labelled as pothole instances. The Kaggle card/license was not inspectable here, so verify dataset-specific reuse terms and split/group leakage before download or training. It could support pothole boxes only; it does not supply stone-aggregate or metal-fragment labels.
- A separate [Roboflow RDD2022-India copy](https://universe.roboflow.com/prakhar-kpb1v/rdd2022-india-il8ju/dataset/5) advertises different split sizes and a ten-class taxonomy. Its export was inaccessible here. Treat it as a separate copy/version, not interchangeable with the Siddhesh project.

India-specific adjacent segmentation data are candidates, not replacements for road pavement data:

- The [Indian Roads semantic segmentation dataset](https://platform.ultralytics.com/ultralytics/datasets/indian-roads-semantic-segmentation) corresponds to the e-Yantra/IIT Bombay Indian Roads dataset, downloaded free from Kaggle dataset ID `eyantraiit/semantic-segmentation-datasets-of-indian-roads`. The public metadata reports GPL-2.0. The downloaded archive was CRC-verified (2,881,656,373 bytes; SHA-256 `a25aa4922fa4b7af7098832fad3f31f226721d4638abca1970081c0fe35a09af`), and contains 3,227 India images with pixel labels for road, footpath, shallow path, and pothole. The published split is 2,475 train / 752 validation over disjoint sequences (4 train and 3 validation sequence IDs); there is no independent test split. All image/mask filename-stem pairs were validated and no exact duplicate raw-image hashes were found. The dataset supports a compact U-Net experiment for semantic road ROI and pothole masks only; it has no aggregate-instance or metal-fragment labels. The trainer extracts only the primary raw-image and label-mask tree, excluding a duplicate NumPy representation. No checkpoint is currently produced or active.
- The official [India Driving Dataset (IDD)](https://insaan.iiit.ac.in/datasets/) offers India-collected semantic segmentation (20K images; official page lists 14K train, 2K validation, and 4K test across the complete split). Access requires registration, and its data-use terms must be checked before reuse. A public [IDD drivable-area baseline](https://github.com/SenorPsycho/idd-road-segmentation) describes a ResNet-50/U-Net model trained on IDD and reports 0.9649 best validation IoU; this is the baseline author's validation result, not a RoadIQ result. The repository README describes a checkpoint-path option, but this review could not verify an obtainable checkpoint artifact, its hash, or exact weight provenance. Also, “drivable” is a road-scene proxy and is not necessarily the usable pavement ROI required by RoadIQ.
- The public [RSPNet repository](https://github.com/YLong-maker/RSPNet) lists Semantic-FPN and U-Net segmentation weights evaluated on IDD (reported mIoU 89.13 and 89.20), with release links to `.pth` files. This makes it a possible India-trained ROI lead, but the weight files were not fetched or hash-verified, and the repository page does not identify a code or weight license. Its exact target-mask semantics and preprocessing also need verification; a drivable/road mask may include shoulders or vehicles and is not automatically a pavement ROI. Do not configure these weights until license, provenance, preprocessing, and output classes are reviewed.
- The user's [RDS roadside-debris lead](https://universe.roboflow.com/rds-hkpkm/roadside-debris) could not be fetched at that slug. The same RDS workspace exposes an [H4B garbage/debris dataset](https://universe.roboflow.com/rds-hkpkm/h4b) listing 599 images, classes `Garbage` and `Debris`, and CC BY 4.0. Its Indian-road provenance is unverified and labels are generic debris, so it does not meet the India-only or metal-fragment requirements and is excluded.
- The [Custom Dash-Cam Dataset for Unmarked Road Boundary Detection in Rural Indian Terrains](https://zenodo.org/records/15869374) advertises India dashcam frames with polygonal road-boundary labels and a 96.5 MB archive. Zenodo shows no populated license on the record, so do not download or use it until the author clarifies reuse terms. Boundary polygons also need review to see whether they define a pavement mask rather than a drivable boundary.
- The [ThirdEye Indian Road Driving Dataset](https://huggingface.co/datasets/thirdeyelabs/indian-road-dataset) advertises CC BY 4.0 and 645,714 Delhi NCR frames, but it requires accepting access conditions and identifies its detection/segmentation labels as machine-generated and not human-verified. It contains traffic-object classes, not aggregates or metal fragments; its 210 GB size and pseudo-label provenance make it a weak ROI-validation source. Do not treat it as gold held-out evaluation data.
- The peer-reviewed [Indian Footpath Damage Segmentation dataset](https://www.nature.com/articles/s41597-025-06207-x) and [Zenodo record](https://zenodo.org/records/17154852) provide 583 India-collected footpath images with pixel masks; the archive is 4.5 GB. The paper describes Pune pedestrian footpaths (not carriageway pavement), so it is adjacent-domain data only and must not be presented as validation of the road-surface model. Review the record's license and mask schema before any use.
- [iWatchRoadv2](https://arxiv.org/html/2510.16375v1) describes 7,000+ manually box-annotated pothole frames from Indian dashcam footage and links a Kaggle dataset. The paper is licensed CC BY-NC-SA 4.0; separately verify the dataset's license and files. It reports pothole boxes, not aggregate or metal labels, and is a preprint rather than an independently reproduced RoadIQ result.
- [DriveIndia](https://arxiv.org/html/2507.19912v1) describes 66,986 India traffic-object images with pothole among 24 classes, but not aggregate or metal-fragment labels. [TiHAN's dataset page](https://tihan.iith.ac.in/TiAND.html) says the camera dataset covers 3,000 km and requires an EULA and access request; the paper describes academic/non-commercial research. It may support general road-scene or pothole detection after access and exact terms are reviewed, but it is not a pavement mask dataset.

The user-provided [Indian Road Damage & Infrastructure Dataset (IRDID)](https://github.com/ahs695/Indian-Road-Damage-Infrastructure-Dataset) was audited at commit `98b12608720a2903878176598a3c94cf4d5561b6`. Its repository declares CC BY 4.0 and 1,200 image-level labels across six classes, but the checked-out copy has only 1,049 images; 151 labelled image records have no matching file after normalizing the documented class-folder names. The supplied split lists have 840/180/180 IDs, but exact duplicate image bytes occur across splits (77 train/validation, 67 train/test, and 11 validation/test duplicate groups). Metadata also names third-party map, news, stock-photo, and social-media sources; rights for those individual images have not been independently verified. The labels are image-level only: there are no crack/pothole boxes, aggregate masks, or metal-fragment annotations. Do not train or report held-out metrics from its published split without repairing missing files, grouping duplicate images before splitting, and resolving image provenance.

An additional similarly named [IRD-Dataset on Zenodo](https://zenodo.org/records/21370736) advertises 4,352 images with boxes, polygons, and masks, but its record explicitly says the images were collected in Baghdad, Iraq. Exclude it under the India-only direction, regardless of its annotation richness.

None of the reviewed India-only candidates provides individual stone-aggregate masks or a separate metal-fragment class. Those remain unavailable until India-only labels are supplied or collected and reviewed. The roadside-debris Roboflow link provided by the user did not resolve to an inspectable dataset page in this review; available search results did not confirm its geography, label taxonomy, or license. In particular, generic debris labels cannot stand in for metal-fragment labels. The user explicitly directed that ACAD and all non-Indian data be excluded. The owner may still provide separate India road labels for stone aggregates and metal fragments; neither is present in the selected dataset.

The follow-up source search did not identify a free India-only set with both instance-level aggregate and metal-fragment labels. The [Indian Footpath Damage set](https://www.nature.com/articles/s41597-025-06207-x) has masks for cracks and surface irregularities on Pune pedestrian footpaths, but it does not add these two classes and was not downloaded. A visual sample of eight full-resolution frames from the selected Indian Roads dataset showed wide road scenes, including interlocking paving blocks rather than exposed aggregate grains; those frames are not useful aggregate instances. For manual collection, see the [India aggregate/metal annotation guide](INDIA_AGGREGATE_METAL_ANNOTATION_GUIDE.md).

## Setup and local workflow

From the repository root, using the project's supported Python 3.12 environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
python -m scripts.analyze_road_image /path/to/your/road-image.jpg
```

No usable trained India-only checkpoint is active. `ROADIQ_SEGMENTATION_MODEL_PATH` can point to a locally trained checkpoint; set `ROADIQ_SEGMENTATION_DEVICE` to `cuda` or `cpu` as available. To prepare the selected archive, run `python -m scripts.train_indian_road_segmentation prepare --archive /path/to/indian-roads.zip --output /path/to/indian-roads`. Full training defaults to CUDA and writes an India-only checkpoint with sequence split and validation metadata; use `train --data-root ... --output ...`. Sample/batch-limited runs are smoke-only and never save checkpoints. The smoke test completed on CPU, but it is not a quality result. In this runner, `nvidia-smi` fails and PyTorch reports `cuda.is_available() == False`; no full training was attempted. The legacy `ROADIQ_VISION_MODEL_PATH` is rejected when it points to the known multinational checkpoint. The local CLI validates the caller-provided image and returns an `unrated` report with defect measurements unavailable. No paid API, paid dataset tier, or paid checkpoint is required or configured. The Roboflow India-specific datasets and papers are data candidates only; no candidate checkpoint is configured or verified. The selected semantic dataset and trainer are documented above; a reviewed and trained checkpoint plus a separately labelled damage dataset are still absent.

For a repeatable no-download demo, use the one-command runner documented in the root README. It accepts `--image /path/to/road.jpg` to analyze a local image instead of generating a synthetic one; both paths save an annotated preview and JSON report together. The generated file is explicitly synthetic, and candidate masks demonstrate only analyzer plumbing. The lower-level CLI remains available for independent input/output paths:

```bash
PYTHONPATH=backend python -m scripts.analyze_road_image /path/to/road.jpg \
  --annotated-output /tmp/road-annotated.jpg \
  --report-output /tmp/road-report.json
```

## What the MVP can and cannot report

Implemented:

- image byte/type/dimension validation and EXIF orientation handling;
- heuristic resolution, exposure, and edge-detail quality observations, explicitly unvalidated on RoadIQ data;
- a named tile grayscale contrast proxy, never described as physical roughness/IRI;
- an untrained Pillow high-frequency texture heuristic that emits an image-space RLE mask, bounding box, candidate area ratio, boundary-pixel statistic, preview annotation, and measured per-call time for textured regions; the output is explicitly not a particle mask or verified pavement ROI;
- test-injected detector outputs for wrapper tests only;
- structured model-load and inference errors, with unsupported or unavailable measurements left null.

Unavailable until a reviewed model and labels exist:

- trained India-only segmentation inference (the code path and optional RLE output exist, but no trained checkpoint is available);
- asphalt/concrete classification;
- individual stone-aggregate segmentation, counts, size/coverage/gap statistics, and aggregate-loss proxy. The texture heuristic cannot separate particles; its confidence and aggregate measurements remain null;
- literal metal-fragment detection (reported separately from ordinary stone aggregates);
- raveling and other visible deterioration classes;
- mask-derived defect area, calibrated physical sizes, and counts per square metre.

No RoadIQ held-out India-only evaluation has run. Missing defect detections must never be interpreted as evidence that the road is undamaged. A 2D image does not establish internal structural strength, weather resistance, or actual skid resistance. All heuristic cutoffs and confidence thresholds need review against labelled, held-out Indian road images before product interpretation.

The local JSON result places this texture-region candidate under `aggregate_analysis.surface_region` and returns the annotated JPEG data URI in the existing top-level `annotated_image` measurement. Its RLE uses the existing `row_major_binary_rle_v1` mask format. The aggregate and defect observations remain separate. The preview highlights high-frequency texture only; it does not identify stone versus binder, pavement boundaries, cracks, or metal. Do not use candidate area as aggregate coverage or the bounding box as a particle measurement. Overall road analysis remains `unrated`.

## Dataset manifest and evaluation

The JSONL manifest fields, annotation states, source/provenance requirements, scene-group split policy, duplicate checks, evaluator command, and limitations are documented in [`DATASET_MANIFEST.md`](DATASET_MANIFEST.md). `scripts.evaluate_aggregate_baseline` uses reviewed aggregate-instance labels in the untouched `test` split, runs the same image service, and emits pixel IoU/precision/recall plus file hashes and per-image timing. It explicitly leaves instance-count MAE null because the heuristic cannot count instances. COCO polygons/uncompressed RLE and grayscale instance-ID PNG masks are supported; compressed COCO RLE is not. No aggregate-instance dataset is bundled or downloaded, so no RoadIQ aggregate metrics exist. The India-road trainer can compute semantic segmentation metrics on its published validation sequences, but these are not independent test results and do not label aggregates.

## Calibration behavior

Calibration may be passed as `ImageCalibration` or a matching dictionary with `method`, `pixels_per_mm`, `usable_area_m2`, `image_sha256`, and `verified`. It is considered bound to the image only when verified, positive, and associated with the exact uploaded-byte SHA-256. The current baseline does not segment aggregates or gaps, so physical aggregate measurements remain unavailable even when calibration is valid. Semantic road/pothole pixel masks are image-space only and are not calibrated physical measurements. Calibration alone never creates an aggregate count or pixel-to-ground measurement.
