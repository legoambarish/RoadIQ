# Dataset and rights register — 2026-10-16

Two existing India road corpora are used. No third road dataset, multinational detector checkpoint, COCO pretrained weight, or external image search supplied training images. Random initialization is intentional. Raw imagery, downloaded archives, weights and private surveys stay in ignored local directories; Git contains code, compact ledgers and benchmark evidence.

## RDD2022 India

- Authority: [official project, taxonomy and download links](https://github.com/sekilab/RoadDamageDetector), [official Figshare record](https://figshare.com/articles/dataset/21431547), [machine-readable record](https://api.figshare.com/v2/articles/21431547).
- Attribution: Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal and Yoshihide Sekimoto, *RDD2022: A multi-national image dataset for automatic road damage detection*, Geoscience Data Journal, 2024. This experiment uses **only India**.
- Figshare license checked live: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Keep source, attribution, license and modification notice when sharing derivatives. Detection labels are converted from published VOC XML to YOLO, with explicit coordinate conversion; images are not relabelled as road-condition grades.
- Country-specific S3 link returned HTTP 403. The acquisition script instead reads the official outer ZIP directory, downloads its stored `RDD2022/India.zip` member by HTTP ranges, checks its CRC against that directory, then verifies every inner member CRC.
- Official outer file ID `38030910`, 13,264,172,619 bytes. Published outer MD5 `b62bd51d2ffcfaa76c60f234f0cc2bb3` is **not locally verified** because the full multinational archive was not downloaded.
- Downloaded India member: 526,709,145 bytes, CRC32 `4052154104`, SHA-256 `28eab0aa85638855e1907e63b175be2305a0accd018c54603037d3fb8cab963a`. Both its outer-directory CRC and all internal CRCs passed.
- India labelled source: 7,706 train images; official unlabelled test images are excluded from training and scored evaluation. Their absence of XML is not a healthy-road label.

Taxonomy is exactly D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole. Other source codes are retained as ignored-code counts, not silently renamed: D44=1,062, D01=179, D11=45, D50=28, D43=57, D0w0=1. Empty supported labels therefore mean **no supported source boxes**, not intact pavement. Published defect rectangles are never segmentation masks or depth labels.

The frozen manifest hash is `1db2111619e93e059ec0ce20db5965ab895d40c9316c99124f624293c1cc9bcf`. Seed 20261016 assigns numeric-ID blocks of 100 to train/validation/test. Later-split images with exact/dHash Hamming-distance <=4 neighbors in retained earlier splits are excluded. The first stricter union of coarse blocks and all near-neighbor links collapsed the corpus into a single group and was rejected before training. Its generated files are retained locally in `rejected-union-attempt-yolo/`.

| Split | Images | D00 boxes | D10 boxes | D20 boxes | D40 boxes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 5,235 | 1,074 | 44 | 1,378 | 2,124 |
| Validation | 1,296 | 228 | 9 | 322 | 542 |
| Test | 993 | 204 | 15 | 265 | 428 |

182 images were excluded; 7,524 remain in 99 numeric groups, largest group 87 images. The independent manifest validator checked all files, stored image/label hashes, explicit rights, scene groups and every dHash-neighbor pair: valid, no cross-split duplicate errors, zero exact duplicates, 410 retained near-neighbor pairs within splits. Within-split warning text is capped at 100 examples; the search itself is complete.

Numeric IDs are a **capture-order heuristic**, not verified route/session identities. Similarity can miss changed viewpoints and exclude unrelated visually similar roads. Exclusion can bias the evaluation distribution. There is no claim of route-independent, India-wide field validation. D10 has very few labels; class results are underpowered. Twelve source-box examples were visually inspected for mapping/geometry, not independently relabelled or certified as complete annotations.

## e-Yantra / IIT Bombay Indian Roads, version 2

- Authority: [primary dataset card](https://www.kaggle.com/datasets/eyantraiit/semantic-segmentation-datasets-of-indian-roads). The public API's dataset-view response describes knee-height delivery-robot and side-road imagery, with road, pothole, footpath, shallow and background categories. This is a different capture domain from RDD dashboard-camera images.
- Source credits: Simranjeet Singh, Soofiyan Atar, Aditya Panwar, Amit Kumar, Srijan Agrawal, Sravya G, Ravikumar Chaurasia, Shreyas Sule and Prof. Kavi Arya.
- Public source metadata reports **GPL-2.0**. Preserve source/license notices for this research track and honor applicable source/distribution obligations. This metadata is recorded, not replaced with the RDD license; it is not a legal clearance of every depicted person/property.
- Current version 2, archive length 2,881,656,373 bytes. Selected original JPG and `labelTrainIds.png` members only: 6,454 files / 3,227 image-mask pairs. Duplicate NumPy representations are not required. All selected files passed ZIP member CRC and have SHA-256 in local `acquisition.json`. **Whole archive SHA-256 is not claimed** for this partial-range acquisition.
- Eight paired source examples were visually inspected. Across all 3,227 masks the observed IDs are 0,2,3,4,255; there are no ID=1 pixels. Original ID counts: road 1,816,715,947; footpath 176,121,093; shallow 35,772,413; pothole 4,288,407; outside/background 941,105,340.
- Version 2 model mapping: 0 road -> model 0; 2 footpath -> 1; 3 shallow -> 2; 4 pothole -> 3; 255 outside/background -> 4 `background_unobserved`. It learns the source annotation's outside region, **not** a validated occlusion/object taxonomy. The preserved legacy v1 adapter still ignores 255 by default.

Four published train sequences (1_005, 1_012, 1_016, 1_018) remain train. Published validation sequences 1_007 and 1_017 select checkpoints; the final sequence 2_006 is reserved as test before training. Cross-split dHash<=4 candidates are excluded from later splits: retained train 2,475 / validation 375 / test 350, total 3,200, exclusions 27. Manifest SHA-256 `bad0de0072954e4ac5b1d8bd81db544e2c0e7fc2196de93245fe682d5fa975b8`. Only seven source sequences exist; a single test sequence cannot establish broad generalization.

## Runtime/framework and limits

[Ultralytics](https://www.ultralytics.com/license) reports AGPL-3.0 for the selected framework. This is an optional local research dependency, with its own source/distribution obligations; do not describe an exported proprietary deployment as cleared by this implementation. CPU/GPU [PyTorch builds](https://pytorch.org/get-started/previous-versions/) and torchvision are pinned. No upstream pretrained detector weights are used. Local weights are trusted research assets; the image upload endpoint never accepts checkpoints.

No field-grade labels, verified material/camera cohorts, physical calibration ground truth, actual survey GPS/time, stone-instance/metal-fragment labels, structural condition, safety, friction, IRI or PCI measurements were acquired. A new independent 80–120-image field collection was not fabricated. The source-heldout evaluation and small qualitative reviews must not be described as that collection. The historical 20-image ACAD synthetic-concrete texture result is unrelated to these road benchmarks.

Rebuild commands, local manifests and evidence paths: [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md). Final measured results: [MODEL_CARD.md](MODEL_CARD.md), [VALIDATION_REPORT.md](VALIDATION_REPORT.md).
