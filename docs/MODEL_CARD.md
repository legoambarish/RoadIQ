# RoadIQ India model card

This card records actual experiments and their limits. The implementation is a local research inspection aid, with candidate observations rather than an engineering condition/safety grade. Dataset-source labels are the evaluation reference; their completeness is not independently certified. Raw model scores are uncalibrated.

## Data and evaluation population

| Track | Train | Validation | Test | Grouping and limits |
| --- | ---: | ---: | ---: | --- |
| RDD2022 India, four box classes | 5,235 | 1,296 | 993 | Numeric-ID blocks are capture-order proxies; exact/dHash cross-split neighbors excluded. Unknown route/session dependence remains. |
| e-Yantra IIT Bombay Indian Roads v2, five semantic classes | 2,475 | 375 | 350 | Four/two/one published sequences; 27 later-split near-duplicate exclusions. One test sequence is not 350 independent scenes. |

The RDD labelled source contains 7,706 images; 182 are excluded by the frozen preparation. The official 1,959 unlabelled India test images are not training/evaluation negatives. Only India images are used; no COCO or multinational checkpoint is loaded. Of the 993 labelled test images, 569 have no **supported source boxes**, which is not a healthy-road label. Transverse cracks have only 44 train / 9 validation / 15 test boxes. Full counts: [detector-label-distribution.json](evidence/detector-label-distribution.json).

India licence/source/attribution, ignored RDD codes, selected-member CRCs, source mask IDs, acquisition and complete duplicate-audit details: [DATASET_AND_RIGHTS_REGISTER.md](DATASET_AND_RIGHTS_REGISTER.md). The original Figshare outer archive and Kaggle whole-archive hashes are not claimed because only the required country/members were acquired.

- RDD manifest SHA-256: `1db2111619e93e059ec0ce20db5965ab895d40c9316c99124f624293c1cc9bcf`.
- ROI manifest SHA-256: `bad0de0072954e4ac5b1d8bd81db544e2c0e7fc2196de93245fe682d5fa975b8`.
- Source-label review: 12 box-review cells from 11 unique RDD images and eight paired semantic examples; mapping/alignment inspection, not independent relabelling or completeness certification.
- No new independent 80–120-image field collection, severity/healthy labels, physical reference measurements or legitimate survey GPS/time was fabricated.

## Detector experiment — running

The genuine `india-yolo11n-scratch-v1` run is still training at this progress snapshot. No heldout detector result is claimed here. Its frozen recipe is random YOLO11n, 640 pixels, batch 8, 30 requested epochs, seed 20261016, AdamW lr .001 / final factor .05 / decay .0005, two warmup epochs, mosaic .5 closed for the final five epochs, horizontal flip .5, no vertical flip/perspective/mixup, deterministic setting and zero loader workers. AMP is disabled to prevent the upstream pretrained-model AMP check from downloading a checkpoint. Best validation framework fitness selects the checkpoint; for the pinned Ultralytics 8.4.178 implementation, fitness is validation mAP50–95. The frozen test is not used for selection or operating-threshold tuning.

The four model classes are longitudinal crack, transverse crack, alligator crack and pothole. RDD rectangles supervise boxes, not damage masks, severity or physical depth. The application threshold is fixed at .25 with class-wise NMS IoU .5, max 300 detections/view and no tiling in the deployment benchmark. Optional tiled coordinates/deduplication have algorithm tests but no established accuracy gain.

## Semantic ROI / pothole experiments — actual results

Both completed experiments use a compact four-level U-Net, base channels 16, random weights, 512x288 RGB input, five classes (road, footpath, shallow, pothole, source background/unobserved), batch 8, seed 20261016 and 15 epochs. AdamW lr .001 / weight decay .0001, CUDA autocast plus GradScaler. Real source ID 255 is learned as source background in this explicit v2/v3 mode; it is not a validated object/occlusion taxonomy. Preserved legacy four-class behavior continues to ignore 255.

| Experiment | Selected epoch | Best validation macro IoU | Heldout model-input macro IoU | Heldout road IoU | Heldout pothole IoU | Elapsed seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v2, median-frequency CE (cap 8), no augmentation | 15 | .408162 | .183198 | .475790 | .000000 | 1,216.06 |
| v3, positive sampling weight 8 / pothole CE minimum 32 / soft Dice .5 | 14 | .421258 | .225628 | .512469 | .000000 | 1,719.47 |

V3's horizontal flip .5 and brightness .85–1.15 apply only to training. The improvement design and validation-only selection were recorded before inspecting heldout outcomes. Both complete reports, including all epochs/confusion matrices and the failed pothole results, remain in [v2 evaluation](evidence/roi-v2-evaluation.json) and [v3 evaluation](evidence/roi-v3-evaluation.json).

### Aspect-preserving deployment export

The active `indian-roads-unet-v3-letterbox-v1` exports the **unchanged learned v3 tensors** with correct letterbox/inverse source-mask projection. It is not another trained experiment. Original v3 weights remain SHA-256 `4324bcd279b93730fd583d6562598fe295c539b890101f5394bedb7b21a5d8b0`; active export SHA-256 is `a511f40ad30325f5165008f94af8bced0b39d3ccd08a0b9891973bceb1a542e5`.

All 3,200 retained source images are 1280x720, exactly the 512x288 training aspect. The exporter verifies every original image/mask hash and byte equality of the old/new model inputs, then verifies saved parameter tensor equality. Therefore the original GPU model-input evaluation is legitimately reused with explicit provenance; CPU/source-resolution output is evaluated afresh below. The earlier v4 correction plan was declared before inspecting v3 test results. Redundant v4 training was stopped after three epochs when the dimension/equivalence audit established that another 15-epoch run was unnecessary. Its checkpoint/log are retained as **INCOMPLETE**, with no heldout evaluation or completion claim. See [export provenance](evidence/roi-deployment-export.json), [aspect audit](evidence/roi-source-aspect-audit.json), [v4 incomplete evidence](evidence/roi-v4-incomplete.json).

At runtime, RGB is bilinearly letterboxed; padding is cropped from logits, then model-grid argmax labels project to the EXIF-oriented source by nearest neighbor. Padding/scales/source dimensions are returned. This avoids source-sized five-class softmax tensors but retains coarse-grid quantization. Square RDD uploads are a different capture domain/aspect from the semantic corpus; RDD provides no mask ground truth to validate their ROI accuracy.

### Actual deployed CPU/source-resolution mask evaluation

All 350 frozen test images and original masks were hash-verified and evaluated at 1280x720. This is the deployed CPU projection, not a resized-label proxy. It completed in 85.41 s including hashing/metrics/previews, which is **not** API latency.

| Semantic class | Source-resolution IoU | Dice |
| --- | ---: | ---: |
| Road | .512671 | .677835 |
| Footpath | .218298 | .358366 |
| Shallow | .006164 | .012253 |
| Pothole | **.000000** | **.000000** |
| Background/unobserved | .391612 | .562818 |

Macro IoU .225749; road-or-pothole ROI union IoU .512599. Only 14 test frames contain source pothole pixels (38,729 pixels total). Pothole area MAE is 1,435.81 source pixels across all images and 2,764.86 on the 14 source-positive images; full-image-fraction MAE .00155795. These small average area errors are dominated by rare positives and **do not establish useful pothole measurements**. Of 336 source-negative frames, 106 have at least one predicted pothole pixel. This is not a certified healthy-road false-positive rate.

The six largest mask-disagreement examples were inspected: amber pothole predictions occur on steps/footpath edges absent from source pothole labels. They are neighboring frames from one sequence, not six independent failure scenarios. Full confusion, per-image metrics and error IDs: [source-resolution evaluation](evidence/roi-source-resolution-evaluation.json), [per-image results](evidence/roi-per-image-source-evaluation.json), [qualitative error review](evidence/roi-error-review.json). The local contact sheet remains `artifacts/roi-source-evaluation/worst-pothole-mask-errors.jpg`; raw source photos are not committed.

Post-evaluation diagnostic baselines, computed from the retained truth/confusion counts without tuning or retraining, expose the effect of class imbalance:

| Diagnostic | Learned runtime | Constant road / empty pothole mask |
| --- | ---: | ---: |
| Road-or-pothole ROI IoU | .512599 | .739147 |
| Five-class macro IoU | .225749 | .147805 |
| Pixel accuracy | .569298 | .739027 |
| Pothole IoU | .000000 | .000000 |
| Pothole area MAE, all images (source px) | 1,435.81 | 110.65 |

The learned multi-class macro result exceeds the constant-road diagnostic, but road/ROI overlap and pixel accuracy trail it; pothole overlap is zero and its all-image area error is worse than an empty mask. **This ROI/damage model does not pass a useful measurement-quality acceptance gate.** All numbers are conditional on this one source sequence. These diagnostics neither select a checkpoint nor change the inference policy. [Actual baseline arithmetic](evidence/roi-diagnostic-baselines.json).

**Decision:** expose masks/pixel geometry for experimental model inspection with the failed source-heldout IoU shown beside them. Do not treat them as trustworthy damage-area measurements, individual instances, physical area or severity. No heldout-driven retraining/tuning followed these outcomes.

## Runtime, reproducibility and exclusions

Training host: Windows, Ryzen 7 7435HS (8 cores / 16 threads), RTX 4060 Laptop 8 GiB, approximately 24 GiB RAM. Python 3.12.3, Torch 2.9.1+cu128, torchvision .24.1+cu128, Ultralytics 8.4.178. CPU runtime uses a separate clean Torch 2.9.1+cpu / torchvision .24.1+cpu environment with four Torch threads. [Selected training versions](evidence/training-environment.json), [CPU runtime lock](evidence/cpu-runtime-lock.txt). The training venv reused system packages; the clean CPU environment passed dependency consistency and avoids the inherited unrelated MCP/google-genai Pydantic conflicts. Global libraries were preserved.

Exact acquisition/training/export/evaluation/startup/build commands are in [TRAINING_AND_DEMO.md](TRAINING_AND_DEMO.md). Raw data, weights, logs and executables remain ignored local artifacts. Frozen manifests are committed compressed; decompressed source hashes preserve the actual Windows bytes. A Linux rebuild can preserve sample/split identities without identical CRLF-dependent manifest bytes or bit-identical CUDA retraining. Use a new experiment identity for changed behavior.

Ultralytics framework AGPL-3.0 and source dataset licences have separate obligations. The local research bundle is not a clearance for proprietary/public distribution. No pretrained detector is silently acquired. Load only trusted local checkpoints; image uploads never load user weights. Hash/sidecar checks are provenance consistency checks, not cryptographic authentication of arbitrary downloaded weights.

No calibrated detection probabilities, validated capture/material/occlusion classifier, per-request statistical reliability, physical uncertainty, known-scale field MAE, crack masks/skeletons, individual aggregates, metal-fragment detector, operational severity, IRI/PCI/friction/strength, eligible RSQI reference cohort or real survey map is established. RSQI remains Unrated and percentile/physical dimensions remain null. The retained OSM sample scores are fixtures. Current tests and final acceptance status are in [VALIDATION_REPORT.md](VALIDATION_REPORT.md).
