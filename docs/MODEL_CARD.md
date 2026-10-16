# RoadIQ India model card

This card records actual experiments and their limits. The implementation is a local research inspection aid, with candidate observations rather than an engineering condition/safety grade. Dataset-source labels are the evaluation reference; their completeness is not independently certified. Raw model scores are uncalibrated.

## PR #18 remediation — measured results, gates not met

The remediation runs completed on the frozen India splits. The official YOLO11n COCO checkpoint was used only for detector initialization (pinned asset/hash in [DATASET_AND_RIGHTS_REGISTER.md](DATASET_AND_RIGHTS_REGISTER.md)); all RoadIQ fine-tuning/evaluation images were India-only. The U-Net used random initialization. Hyperparameters and checkpoint selection were fixed before this run's holdout evaluation, using validation data. **The same frozen holdout had been used for earlier baseline experiments, so it is not a virgin independent test set across the project's full history.** No choices for these checkpoints were made using their final test results.

### Remediated YOLO11n detector — final holdout

Trained 90/90 epochs on the RTX 4050 Laptop GPU with the approved COCO initialization, capped inverse-square-root class weights from training boxes only, batch 4, and validation-fitness checkpoint selection. Ultralytics 8.4.178 internal validation evaluated the selected checkpoint once on the frozen 993-image test split (912 supported boxes). Its reported per-class P/R are at the framework's max-mean-F1 operating point; AP50 integrates its confidence sweep. They are **not** the application's fixed-confidence .25 operating-point metrics.

| Class | Test boxes | Precision (max-F1) | Recall (max-F1) | AP50 | AP50–95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Longitudinal crack | 204 | .334544 | .259804 | .248214 | .104980 |
| Transverse crack | 15 | .122338 | .133333 | .078374 | .032025 |
| Alligator crack | 265 | .576756 | .562264 | .550157 | .228768 |
| Pothole | 428 | .446018 | .387850 | .336223 | .129169 |
| Four-class aggregate | 912 | .369914 | .335813 | **.303242** | .123735 |

Against the prior scratch-v1 detector AP50 of .137644, this run's AP50 is higher by .165598; it nevertheless misses the requested >.45 AP50 gate. Both crack recalls and pothole recall also miss their respective >.30 / >.50 gates. This improvement is real on the stated benchmark, but is not sufficient evidence of dependable detection.

The optional `faster-coco-eval` package was unavailable, so these values are from Ultralytics' internal evaluator only; no independent second AP implementation is claimed.

Detector checkpoint SHA-256: `173d10ec44da536c2848343cb4275f634e6f2494101c317f11f7863316fa9167`. India manifest SHA-256: `8aef52c077c9f9003d89bfdc67b1cd5ee2550b7cb694a9c4f6bf2cb36c2f562d`. COCO initialization SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`. Full machine-generated metrics remain local at `models/india-yolo11n-coco-v2/heldout-metrics.json`; the pinned manifest/counts and reproducible code are reviewable, while private/local weights, raw images and logs are not committed.

### Remediated U-Net v5 — source-resolution holdout

Trained 80/80 epochs, selecting epoch 68 by validation mean road/pothole IoU, with 512x288 aspect-preserving letterbox preprocessing, train-only class weighting, positive-image repeat 8, pothole CE weight floor 48 and Dice loss 1.0. The final evaluation used the sequence-reserved 350-image source test split; this sequence was also used for the earlier v2/v3 baseline reports, so it is not globally untouched across experiment history.

| Source-resolution measure | v5 result | Gate / reference | Status |
| --- | ---: | ---: | --- |
| Road IoU | .547518 | > .7391 static-road diagnostic | Fail |
| Road-or-pothole ROI union IoU | .547526 | > .7391 static-road diagnostic | Fail |
| Pothole IoU | **.000000** | > 0 | Fail |
| Five-class macro IoU | .219426 | Diagnostic only | — |

U-Net checkpoint SHA-256: `677ccbc74afc29e1c1e3a28b94c5a602d7ac613618632d48f1fae76a2ac18b83`. ROI manifest SHA-256: `1a2f0068c22457e3c458c498df19df6a9249b8a53ba7cc804d5a67838dd17b7e`. Full metrics/confusion matrices are local in `models/india-roi-v5/roi-evaluation.json`; original imagery and weights remain local.

**P0 accuracy verdict: NOT MET.** The detector's AP/recall improved over the scratch baseline but stays below every requested detector threshold, and the U-Net fails both ROI and pothole-overlap gates. Do not present the output as dependable condition assessment. The full API operating-point benchmark and model-enabled packaging need separate verification; see [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

## Data and evaluation population

The P0 crack-recall gate applies separately to both longitudinal and transverse cracks; neither class may be averaged away by another class.

| Track | Train | Validation | Test | Grouping and limits |
| --- | ---: | ---: | ---: | --- |
| RDD2022 India, four box classes | 5,235 | 1,296 | 993 | Numeric-ID blocks are capture-order proxies; exact/dHash cross-split neighbors excluded. Unknown route/session dependence remains. |
| e-Yantra IIT Bombay Indian Roads v2, five semantic classes | 2,475 | 375 | 350 | Four/two/one published sequences; 27 later-split near-duplicate exclusions. One test sequence is not 350 independent scenes. |

The RDD labelled source contains 7,706 images; 182 are excluded by the frozen preparation. The official 1,959 unlabelled India test images are not training/evaluation negatives. RoadIQ fine-tuning and evaluation imagery is India-only. Scratch-v1 used no pretrained checkpoint; the remediation uses only the approved official YOLO11n COCO initialization, without adding COCO images to the RoadIQ dataset. Of the 993 labelled test images, 569 have no **supported source boxes**, which is not a healthy-road label. Transverse cracks have only 44 train / 9 validation / 15 test boxes. Full counts: [detector-label-distribution.json](evidence/detector-label-distribution.json).

India licence/source/attribution, ignored RDD codes, selected-member CRCs, source mask IDs, acquisition and complete duplicate-audit details: [DATASET_AND_RIGHTS_REGISTER.md](DATASET_AND_RIGHTS_REGISTER.md). The original Figshare outer archive and Kaggle whole-archive hashes are not claimed because only the required country/members were acquired.

- Earlier scratch/v2-v3 baseline manifest hashes: RDD `1db2111619e93e059ec0ce20db5965ab895d40c9316c99124f624293c1cc9bcf`; ROI `bad0de0072954e4ac5b1d8bd81db544e2c0e7fc2196de93245fe682d5fa975b8`. These differ from the remediation run manifests reported above.
- Source-label review: 12 box-review cells from 11 unique RDD images and eight paired semantic examples; mapping/alignment inspection, not independent relabelling or completeness certification.
- No new independent 80–120-image field collection, severity/healthy labels, physical reference measurements or legitimate survey GPS/time was fabricated.

## Historical detector experiment — scratch-v1

The genuine `india-yolo11n-scratch-v1` run completed all **30 epochs**, taking 6,779.406 seconds through best-checkpoint preparation. Its frozen recipe is random YOLO11n, 640 pixels, batch 8, seed 20261016, AdamW lr .001 / final factor .05 / decay .0005, two warmup epochs, mosaic .5 closed for the final five epochs, horizontal flip .5, no vertical flip/perspective/mixup, deterministic setting and zero loader workers. AMP is disabled to prevent the upstream pretrained-model AMP check from downloading a checkpoint. Best validation framework fitness selects the checkpoint; for the pinned Ultralytics 8.4.178 implementation, fitness is validation mAP50–95. The CSV best is epoch 29 (.05988); the exported checkpoint exactly matches saved best.pt. The frozen test is not used for selection or operating-threshold tuning.

The four model classes are longitudinal crack, transverse crack, alligator crack and pothole. RDD rectangles supervise boxes, not damage masks, severity or physical depth. The application threshold is fixed at .25 with class-wise NMS IoU .5, max 300 detections/view and no tiling in the deployment benchmark. Optional tiled coordinates/deduplication have algorithm tests but no established accuracy gain.

### Frozen labelled detector holdout

Actual evaluated checkpoint SHA-256: `81415db053e9635c8d66b7f5d6a8171282e69d8f125cc36e49fe3933ef2807c3`. All 993 test images / 912 supported source boxes were evaluated after selection.

| Class | Source boxes | AP50 | AP50–95 |
| --- | ---: | ---: | ---: |
| Longitudinal crack | 204 | .060469 | .020542 |
| Transverse crack | 15 | **.000000** | **.000000** |
| Alligator crack | 265 | .353192 | .152575 |
| Pothole | 428 | .136916 | .044827 |
| Four-class mean | 912 | **.137644** | **.054486** |

These are framework internal confidence-sweep AP metrics, not the application operating-point precision/recall or road-condition accuracy. Framework validation uses its default NMS .7; deployment uses .5. GPU validation reports 5.771 ms/image model inference (batch 8), excluding API, ROI model, image/quality/geometry work and UI; this is not end-to-end CPU latency. Exact [heldout report](evidence/detector-heldout-metrics.json), [experiment](evidence/detector-experiment.json), [all 30 epoch rows](evidence/detector-training-results.csv), [actual fit arguments](evidence/detector-fit-arguments.json) and [selection audit](evidence/detector-selection-audit.json) are retained. Only repository-absolute paths in the fit arguments are replaced with `[repository]` for publication.

The actual [heldout precision–recall curve](evidence/detector-heldout-pr-curve.png) and [framework confusion plot](evidence/detector-heldout-confusion.png) are retained; they describe this confidence-sweep validator, separately from the fixed-threshold HTTP counts.

The report also retains the framework's max-mean-F1 precision/recall, which are not fixed-.25 values. In particular, its transverse-crack precision entry is 1.0 while recall/AP are zero: the framework precision-curve interpolation uses a left-fill value of one above all prediction scores. This does **not** demonstrate successful transverse-crack detection. Use AP and actual fixed-threshold TP/FP/FN counts to assess the failure. The optional separate `faster-coco-eval` pass did not run because that package is absent and automatic installation is disabled; the framework's internal AP evaluation completed. No second evaluator or field accuracy is claimed.

**Decision:** genuine trained candidate inference is available, but this weak source-heldout performance does not establish dependable defect detection or engineering assessment. Keep raw scores uncalibrated, no-detection distinct from healthy, and localized candidates visible. No test-driven checkpoint, threshold or architecture tuning follows this result.

### Remediated full GPU HTTP pipeline — fixed operating point

The completed pair was run through the real FastAPI image-analysis route on all 993 frozen labelled RDD images using GPU device 0, confidence .25, NMS IoU .5 and untiled inference. All 993 requests returned successfully with **zero HTTP failures and zero inference failures**. This is an actual integration/operating-point benchmark, not just an offline detector metric.

| Class | TP | FP | FN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Longitudinal crack | 40 | 36 | 164 | .526316 | .196078 |
| Transverse crack | 1 | 4 | 14 | .200000 | .066667 |
| Alligator crack | 131 | 53 | 134 | .711957 | .494340 |
| Pothole | 117 | 75 | 311 | .609375 | .273364 |

Class-specific descending-score greedy matching uses unique source boxes and IoU >= .5; quality abstentions count as misses. In this deployed operating point, every requested defect recall gate also fails. Statuses were 599 `no_defect_detected`, 282 `defects_detected`, and 112 `low_confidence`; “no defect detected” is not a certified healthy-road conclusion. Of 569 source-empty-label challenges, 18 had candidate predictions; these are incomplete labels, not verified healthy negatives.

TestClient benchmark latency: model load 1,916.55 ms, first request 1,319.191 ms, warm p50 175.678 ms / p95 190.467 ms. It excludes browser rendering and real network transport and is not a desktop end-to-end latency claim. The 1,000-replicate, 14-source-block conditional intervals and all per-image records are in local ignored output `artifacts/genuine-demo/pipeline-benchmark.json` and `per-image-benchmark.json`; no raw images or model weights are committed.

### Historical full CPU HTTP pipeline — scratch baseline

All **993** frozen labelled test images passed through FastAPI, image quality, both actual models, source masks/geometry, VDA and legacy scorer at confidence .25 / NMS .5, untiled, four Torch threads. All returned HTTP 200, with zero model-inference failures. Quality abstentions count as misses for source boxes. Class-specific descending-score greedy matching uses IoU >= .5 and unique truth matches.

| Class | TP | FP | FN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Longitudinal crack | 0 | 0 | 204 | Undefined | .000000 |
| Transverse crack | 0 | 0 | 15 | Undefined | .000000 |
| Alligator crack | 77 | 34 | 188 | .693694 | .290566 |
| Pothole | 50 | 65 | 378 | .434783 | .116822 |

Thus **neither longitudinal nor transverse cracks produce any predictions at the fixed application threshold**, and 88.3% of source pothole boxes are missed. Alligator cracks do produce the candidates counted above. This is a measured failure, not evidence that the roads are healthy. Of 569 images with no supported source boxes, 13 have candidate predictions; source-label incompleteness/ignored classes prevent calling this a certified healthy-road false-positive rate.

VDA states: 693 `no_defect_detected`, 153 `defects_detected`, 147 `low_confidence`. All RSQI values and reference percentiles remain null. Black/low-resolution controls return `unusable`; the transformed blur challenge returns `low_confidence`. These controls test plumbing, not field rejection sensitivity/specificity.

Conditional 1,000-replicate bootstrap intervals over 14 numeric source blocks: alligator precision [.598424, .794410], recall [.232745, .356870]; pothole precision [.360651, .511280], recall [.089972, .148945]. They describe this source/grouping only; route dependence, label error and deployment shift are not covered. Undefined crack precision stays null; no unsupported confidence is assigned to an individual request or road percentile.

Actual CPU TestClient timings: model load **1,965.560 ms**, first request **3,079.848 ms**; 993 warm requests min 301.352 / median **574.053** / p90 602.570 / p95 **611.372** / max 1,058.713 ms. These include both models, quality, geometry, routing and JSON, excluding browser rendering/network transport. This complete run preceded the small addition exposing existing detector AP in report provenance/reliability; that addition does not change predictions/gates and is separately covered by final real-model/browser/package tests. The full accuracy benchmark was not repeated or tuned. [Summary](evidence/pipeline-benchmark.json), [compressed per-image records](evidence/pipeline-per-image.json.gz), [execution provenance](evidence/pipeline-execution-provenance.json).

The deterministic genuine demo is India_006160: one alligator-crack match, no false candidates, and one missed source pothole. India_001993 is a hazy/shadowed, vehicle-containing no-supported-box challenge, not a certified intact road. Eight worst FP+FN examples are retained locally. Four were visually inspected: large merged/unmatched pothole boxes (India_002020, India_009171), and visibly distressed frames with no candidates (India_004755, India_009856). These observations describe disagreement with source boxes, not field-confirmed severity. [Error-review ledger](evidence/pipeline-error-review.json). Original inputs, complete JSON and predicted-box previews remain in `artifacts/genuine-demo/`; compact example JSON is committed compressed. Known low detector AP is exposed in each live report's reliability details and model provenance.

## Historical semantic ROI / pothole experiments — v2/v3

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
