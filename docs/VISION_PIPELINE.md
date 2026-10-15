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

## Model baseline

- **Checkpoint:** RF-DETR Nano fine-tuned on RDD2022 by DetectionBench, Hugging Face repo `dronefreak/rdd2022-rfdetr-nano`.
- **Pinned revision:** `66429f39b916e56c6a33243d776718088f5f43ad`.
- **Checkpoint file:** `checkpoint_best_total.pth`, 120,825,211 bytes; SHA-256 `2d1fba21b829ebc42f7c74f76285d97b2e3295aebe8d97e497d0cc186be98cc9`.
- **Supported classes:** longitudinal crack, transverse crack, alligator crack, and pothole. The service groups the three crack classes under `crack` while preserving each original class in `model_label`.
- **Input size:** 384×384 pixels as documented for this checkpoint. RF-DETR handles its internal preprocessing; the service supplies an EXIF-corrected RGB Pillow image.
- **Model code and checkpoint license:** the publisher identifies the model as Apache-2.0. The source RDD2022 dataset is identified by the model card as CC BY-SA 4.0. Review those terms before redistribution or commercial use; the checkpoint is not included in this repository.
- **Training/evaluation provenance:** pretrained baseline, fine-tuned on RDD2022, not trained on RoadIQ. The publisher reports 60.85 mAP@50 on its own grouped 70/15/15 held-out split. This is not a RoadIQ result and is not an independent validation by this project. The card notes that the test slice differs from the official CRDDC2022 leaderboard test set and that the model drops the dataset's “other” bucket.
- **Runtime:** CPU inference is supported by the selected backend; GPU is optional. RF-DETR 1.11.2 with the resolved Transformers 5.19.0 requires a newer PyTorch stack than the workspace’s original PyTorch 2.5.1; the actual smoke run succeeded with PyTorch 2.9.1+cpu and TorchVision 0.24.1+cpu. Runtime latency has not been benchmarked. The checkpoint is about 115 MiB; a 2 GiB RAM budget is a planning estimate for loading/inference, not a measured minimum. Expect slower CPU inference than a GPU deployment.

References: [checkpoint card and metrics](https://huggingface.co/dronefreak/rdd2022-rfdetr-nano), [RF-DETR source and license](https://github.com/roboflow/rf-detr), [RDD2022 paper](https://arxiv.org/abs/2209.08538).

## Setup and local workflow

From the repository root, using the project's supported Python 3.12 environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r backend/requirements-vision.txt
cd backend
python -m scripts.download_road_damage_model
```

For CUDA, install a matching Torch/TorchVision pair from the [official PyTorch install instructions](https://pytorch.org/get-started/locally/) before installing `requirements-vision.txt`. The optional requirements enforce PyTorch 2.9.1 or newer because the resolved RF-DETR/Transformers stack needs APIs absent from the older system Torch 2.5.1.

The downloader pins the model revision and verifies the checkpoint SHA-256. Set the printed `ROADIQ_VISION_MODEL_PATH` value in the environment, then run:

```bash
python -m scripts.analyze_road_image /path/to/your/road-image.jpg
```

Without the optional detector requirements or checkpoint, the service still validates the image and returns an explicit `unrated` report with defect measurements unavailable. The local workflow uses a caller-provided image; no RoadIQ-labelled evaluation set is currently available. A CPU CLI smoke run loaded the pinned checkpoint and inferred on a generated, synthetic road-like image at threshold 0.25; it returned one crack and zero potholes with no processing error. This validates model loading and response wiring only, not detector quality.

## What the MVP can and cannot report

Implemented:

- image byte/type/dimension validation and EXIF orientation handling;
- heuristic resolution, exposure, and edge-detail quality observations, explicitly unvalidated on RoadIQ data;
- a named tile grayscale contrast proxy, never described as physical roughness/IRI;
- RF-DETR crack/pothole bounding boxes and per-image counts when a checkpoint loads;
- model-load and inference errors in the response, with unsupported or unavailable measurements left null.

Unavailable until a reviewed model and labels exist:

- pavement ROI mask and usable-area fraction;
- asphalt/concrete classification;
- individual stone-aggregate segmentation, counts, size/coverage/boundary statistics, and aggregate-loss proxy;
- literal metal-fragment detection (reported separately from ordinary stone aggregates);
- raveling and other visible deterioration classes;
- mask-derived defect area, calibrated physical sizes, and counts per square metre.

No RoadIQ held-out evaluation has run. Empty detector results mean no supported defects were detected above the selected threshold; they do not prove the road is undamaged. A 2D image does not establish internal structural strength, weather resistance, or actual skid resistance. All heuristic cutoffs and confidence thresholds need review against labelled, held-out RoadIQ images before product interpretation.

### Aggregate-data investigation

No RoadIQ-labelled stone-aggregate or metal-fragment images or pretrained checkpoints are present in this repository. The public [ACAD Amodal Concrete Aggregate Dataset](https://huggingface.co/datasets/igtsd/acad_dataset) provides 10,000 procedurally generated, instance-annotated concrete aggregate images under CC BY 4.0, with train/validation/test splits. It is a possible transfer-learning source, not evidence of performance on real asphalt/concrete road imagery; no checkpoint trained on ACAD is supplied here. A model trained or fine-tuned on ACAD must remain explicitly experimental until tested on a held-out set of real road images. It does not cover literal metal fragments.

## Calibration behavior

Calibration may be passed as `ImageCalibration` or a matching dictionary with `method`, `pixels_per_mm`, `usable_area_m2`, `image_sha256`, and `verified`. It is considered bound to the image only when verified, positive, and associated with the exact uploaded-byte SHA-256. The current baseline does not segment aggregates or gaps, so physical measurements remain unavailable even when calibration is valid. Calibration alone never creates an aggregate count or pixel-to-ground measurement.

