# Implementation baseline — 16 October 2026

Handoff archive SHA-256: `884893465b5b20d86d36d02dfac3cfe4cb15c4722c0dce70a8b9a17f62c9fb71`. All four files were extracted/read. Fresh clone at main `c6993d7`; clean tree, fetched all branches. Initial DNS failure resolved on retry. Owner-authorized combined feature branch and scope are recorded in TASKS.md.

| Layer | Confirmed existing implementation | Work required |
| --- | --- | --- |
| CV | Safe Pillow intake/EXIF, texture proxy, optional India U-Net adapter, detector protocol, dataset validator | Genuine trained India detector, provenance, readiness, source geometry |
| Scoring | Five-component evidence-gated legacy RSQI and tested caps | Separate observational VDA; leave RSQI unavailable with missing inputs |
| API | Health + image upload, current scorer boundary | Bound streaming, avoid event-loop inference, additive typed findings |
| UI | React/Leaflet Bengaluru OSM fixtures, Everyday/Engineer, actual upload and CLI import | Actual detector overlay, findings and model reliability |
| Data | India segmentation trainer and manifests; no local datasets/weights | Rights ledger, lawful acquisition, duplicate-aware frozen holdout, real training/evaluation |
| Release | Windows launcher/build and prior history | Verify changed source, packaging limitations; do not reuse old EXE claims |

Environment: Windows, Python 3.12.3, Node 25.9.0/npm 11.12.1; RTX 4060 Laptop 8 GiB, about 24 GiB RAM, initially 42.5 GiB free disk. Global Torch 2.13 CPU only; install CUDA Torch in project venv. Frontend dependencies installed from existing lock; Node engine warning for Vitest excludes Node 25, though all baseline commands work. Reproduce with supported Node 24 LTS.

Executed baseline: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/Scripts/python -m pytest backend/tests -q`: **103 passed**, one Starlette multipart deprecation warning (13.66 s). Frontend `npm run test`: **9 passed**; `npm run lint` and `npm run build`: passed. No baseline browser or fresh Windows package check yet.

Execution checklist:
- [x] Read handoff, inspect source/docs/workflow, reconcile owner scope, run baseline.
- [x] Verify primary rights/class map; prepare and freeze India-only split with duplicate audit.
- [x] Actually train and evaluate a detector; record failures and limitations.
- [x] Integrate checkpoint, quality/provenance, dimensionally correct observations and separate VDA.
- [x] Verify upload/report, regression tests, real-model evaluation/demo; document actual outcomes.
- [x] Assess P1 against its real-data gates: physical/cohort/survey inputs absent and P0 quality inadequate; defer those features, retain actual JSON export. Commit/review delivery is recorded in HANDOFF.md.

These checks mean the work was executed, not that scientific quality passed. Detector AP50 .137644 / AP50–95 .054486, no fixed-.25 longitudinal/transverse predictions, native pothole-mask IoU zero and ROI overlap below a constant-road diagnostic keep the overall verdict **PARTIALLY VERIFIED**. Final tests, standalone package outcomes and remaining evidence gaps are in VALIDATION_REPORT.md.

Scientific choices: boxes cannot provide damaged area, crack widths or depths; no grade trained from absent grade labels; no numeric RSQI or percentile from detector confidence. Preserve existing heuristics as explicitly experimental. Independent capture metadata and field measurements may be unavailable and must remain disclosed.
