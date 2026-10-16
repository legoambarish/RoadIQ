# RoadIQ implementation validation

**Progress snapshot: PARTIALLY VERIFIED.** Genuine ROI experiments and current regression checks are complete; detector training, its heldout test, the full real-model HTTP benchmark, browser model demo and model-enabled executable are still running/pending. This snapshot does not claim those gates passed. Final acceptance must retain the failed mask-quality results even when application plumbing passes.

## Executed checks

| Check | Actual result | Scope |
| --- | --- | --- |
| Original backend baseline | 103 passed, 13.66 s, one multipart deprecation warning | Existing scorer/schema/CV/API behavior before implementation |
| Current clean CPU backend | **135 passed**, 12.20 s, two dependency deprecation warnings | Legacy scorer regression, intake/EXIF, actual unit algorithms, VDA states, masks, uploads/concurrency, desktop ownership |
| Original frontend | 9 passed; lint and production build passed | Preserved baseline |
| Current frontend, Node 24.22.0 | **13 passed** in 3 files; lint, TypeScript and Vite production build passed | Presentation/coordinates/failed-mask warning plus retained navigation/map helpers |
| Frozen RDD validator | Valid; complete audit, no cross-split exact/near duplicates | All stored image/label hashes, rights and retained split identity |
| Runtime ROI export | All 3,200 source image/mask hashes and model-input byte pairs verified; learned tensors equal | Correct aspect export, no repeated training |
| Real CPU/source-resolution masks | All 350 images completed in 85.41 s; pothole IoU **0.000** | Actual trained model against untouched native labels; not field validation |
| Existing Task C CLI + browser import | Real India_000205.jpg, exit 0; report and annotation import visible, Unrated | Preserved baseline method explicitly untrained; import does not rescore |
| Fresh base Windows package | Standalone startup, HTTP image upload, owned relaunch/shutdown passed; no Python/Node on child PATH | Earlier base-only package; learned models explicitly unavailable, not final model-enabled verification |

Current backend command: `PYTHONPATH=backend PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-package/Scripts/python -m pytest backend/tests -q`. Frontend commands from `frontend/`: `npm run test`, `npm run lint`, `npm run build`, using the official verified portable Node 24.22.0. The host's Node 25 passed the earlier baseline but is outside Vitest's engine range; final checks use the supported LTS.

Warnings are Starlette's pending `python_multipart` import migration and deprecated AnyIO BlockingPortal alias. No optional-ML skips occurred in the clean CPU suite. The temporary CUDA install/DLL transition produced earlier skips; those were rerun after the environment was consistent. Do not report those transient runs as final evidence.

## Scientific checks and observed failures

The frozen legacy `scoring.py` and road-segment schema are unchanged from main `c6993d7`. The live API supplies no invented component values and therefore stays Unrated. VDA tests cover no supported detections versus healthy claims, blurry/no-detection cases, unavailable/failed inference, low predicted road coverage and localized potholes independent of average area. A failed mask benchmark remains visible even with zero detector candidates.

The HTTP admission test uses an explicitly blocking **test analyzer** to fill both real inference slots. Health remains responsive, an excess upload receives 503 / Retry-After 2, and completed work releases the slots. This is a threading/backpressure contract test, not model-accuracy evidence. Genuine-asset integration remains a separate fail-closed gate.

Geometry tests cover source-normalized boxes, clipping, four-neighbor mask perimeter, true mask area rather than rectangle area, zero ROI denominator, coordinate-size mismatch, overlapping-tile reconstruction/NMS and extreme-aspect tile coverage. Image tests cover EXIF orientation, glare/low-detail heuristics, resolution/exposure blocking, MIME mismatch, corrupt/animated files and pre-parser oversized/chunked multipart budgets. Algorithm tests do not establish field measurement accuracy.

The first source-group/near-neighbor union collapsed RDD into one component; it was rejected before training. The final audited capture-order split is reproducible but is not a proven route-independent field split. Duplicate exclusions can bias it; within-split near neighbors remain. The semantic holdout is one sequence with 14 pothole-positive frames. Both ROI v2/v3 have zero heldout pothole overlap; the native CPU projection confirms the failure. The v4 attempt was stopped as redundant after source/input equivalence was proved, retaining its incomplete evidence rather than relabelling a new trained result.

The native mask failure sheet shows false pothole pixels on steps/footpath edges. Error metrics, class confusion and IDs are retained in [MODEL_CARD.md](MODEL_CARD.md) and `docs/evidence/roi-*evaluation.json`. Pixel-fraction/area outputs are experimental model predictions; they cannot support trustworthy damage or physical measurements. No model was tuned using these heldout outcomes.

A diagnostic constant-road prediction has ROI IoU .739147 versus the learned .512599 on this road-dominated test sequence. An empty pothole mask has all-image area MAE 110.65 source pixels versus the learned 1,435.81; both have zero pothole overlap. Learned five-class macro IoU .225749 exceeds constant-road .147805, but that does not rescue useful ROI/damage measurement. [Baseline calculations](evidence/roi-diagnostic-baselines.json) are retained with the failure, without changing the frozen model or threshold.

## Windows and browser evidence so far

The 24,119,554-byte base executable SHA-256 is `9d73f1d74090245dffc83c55105633e23314e35e731993d75d7d632d0592a061`. It was copied outside the source checkout, launched with an isolated profile and child PATH containing only Windows System32, served the built UI and accepted a genuine image with explicit model-unavailable/Unrated output. Authenticated owned relaunch and test shutdown exited zero. [Actual base package evidence](evidence/windows-base-smoke.json). This does not verify new trained weights or the final model-enabled build.

The first package harness run incorrectly read the Windows-locked byte zero of instance metadata and timed out. The harness now seeks to byte one, matching the launcher's reserved lock byte; only its own isolated test instance was stopped. A later source-tree-discovery run was not accepted as standalone proof; the passed check confirms standalone mode outside the checkout.

Browser import was verified with a genuine source image's actual saved CLI report and companion annotation. It displayed 720x720, texture candidate ratio .129997, untrained method identity, unknown material, no individual aggregates, no RSQI rescoring and unverified preview association. Default Chromium viewport 1280x720, document width 1265; no viewport override or physical phone test. [Import verification](evidence/legacy-import-verification.json). No responsive-device or camera-accuracy result is claimed.

## Pending final gates and unavailable evidence

The actual detector-heldout/AP report, full 993-image CPU API operating-point/latency/conditional-bootstrap benchmark, genuine browser Everyday/Engineer detections/masks/download, and fresh CPU model-enabled Windows executable must finish before final handoff. The integration tests intentionally fail without genuine assets; no mock or silent skip can satisfy them.

No independent new field set, certified healthy/severity labels, physical scale/depth ground truth, real GPS/time survey collection, eligible RSQI/cohort percentile, material/occlusion validation or commercial redistribution review exists. P1 physical/percentile/survey features are gated by these missing inputs and P0 model-quality limits; no numerical population rank or condition grade is substituted. JSON observation export is implemented. Future model improvement requires a new frozen experiment and new independent evaluation, not tuning repeatedly against this consumed test.
