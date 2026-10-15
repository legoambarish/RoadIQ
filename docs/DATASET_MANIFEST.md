# RoadIQ image dataset manifest

RoadIQ does not bundle or download an aggregate dataset. Each dataset owner must record source, provenance, license/permission evidence, annotation type, review state, and a route/session scene group before using images. Keep aggregate-instance annotations separate from road-defect and semantic road masks.

## Quick dataset candidate audit — 2026-10-16

A short search did not identify a rights-cleared, India-only dataset of individually annotated stone aggregates in in-service road-surface photos. The India-affiliated [RoadDefects-ISeg record](https://zenodo.org/records/17194814) describes crack, lane, pothole, and speed-breaker labels, not aggregate particles; its acknowledgments also identify several upstream sources, so its imagery should not be presumed India-only. The [MTRSD repository](https://github.com/fjaklj/Multi-Type-Road-Surface-Dataset-MTRSD) labels broad road-surface categories such as asphalt and cement, not aggregate instances. [ACAD](https://huggingface.co/datasets/igtsd/acad_dataset) provides CC BY 4.0 procedurally generated concrete aggregate instances, but its synthetic controlled images are not India-collected road photos. None is treated as RoadIQ aggregate training/evaluation data in this branch; no dataset was downloaded. For the hackathon demo, use the clearly labeled synthetic input and keep real aggregate metrics pending.

## JSON Lines format

Create one UTF-8 JSON object per image in `manifest.jsonl`. Paths are relative to the manifest directory and must stay inside it. The validator accepts these fields:

| Field | Meaning |
| --- | --- |
| `image_id` | Stable, unique identifier within the manifest. |
| `image_path` | Relative path to a decodable image. |
| `label_available` | Boolean; distinguishes unlabelled images from empty annotations. |
| `label_path` | Relative label file, or `null` when labels are unavailable. |
| `label_type` | `none`, `aggregate_instance`, `road_defect`, or `road_semantic_segmentation`. |
| `annotation_status` | `not_started`, `in_progress`, `reviewed`, or `rejected`. |
| `source` | Dataset/source name, collection name, or documented owner source. |
| `provenance` | Human-readable origin/rights note or a stable reference to a provenance record. |
| `split` | `train`, `validation`, or `test`. |
| `scene_group` | Route/session/continuous-scene ID; keep a group in exactly one split. |

Example only (paths and source are placeholders; this is not a real dataset):

```jsonl
{"image_id":"example-001","image_path":"images/example-001.jpg","label_available":false,"label_path":null,"label_type":"none","annotation_status":"not_started","source":"owner-collected example","provenance":"permission record: RIGHTS-001","split":"train","scene_group":"route-001-session-a"}
{"image_id":"example-002","image_path":"images/example-002.jpg","label_available":true,"label_path":"labels/aggregate-instances.json","label_type":"aggregate_instance","annotation_status":"reviewed","source":"owner-collected example","provenance":"permission record: RIGHTS-001","split":"test","scene_group":"route-099-session-b","annotation_image_id":2}
```

Aggregate labels and road-defect labels are different tasks. `aggregate_instance` should represent individually reviewed stone-particle instances. Metal-fragment labels require a separately agreed label taxonomy; do not classify metal as aggregate or generic debris. `road_semantic_segmentation` describes pixel classes such as road/pothole and does not imply instance counts.

For aggregate evaluation, the label can be a shared COCO instance JSON (`label_path` may repeat) or an 8-bit grayscale PNG with 0 as background and positive pixel IDs for separate particles. COCO JSON may use polygon masks or **uncompressed** RLE masks. When one COCO file contains multiple images, set the optional `annotation_image_id` to the matching COCO image ID; otherwise the evaluator matches the image basename or accepts a single-image COCO file. Compressed COCO RLE is not supported by this lightweight evaluator. Mark test labels `reviewed`; reserve their scene groups for test only.

## Validation

From the repository root, after installing `backend/requirements.txt`:

```bash
PYTHONPATH=backend python -m scripts.validate_dataset_manifest path/to/manifest.jsonl
```

The script validates JSONL/required fields, image decode and paths, label state, unique IDs, scene-group split isolation, exact SHA-256 duplicates, and near duplicates with 64-bit difference hash (Hamming distance at most 4). Exact/near duplicates crossing splits and scene groups crossing splits are errors. Duplicate content inside one split is reported as a warning for review. The near-duplicate candidate index is capped to bound work; the report states when that cap prevents complete comparison. Use capture-session/route groups even after deduplication because perceptual hashes cannot identify every same-scene frame.

The validator checks file presence and manifest consistency, not license validity, annotation correctness, or label semantics. It never downloads data. Only report model metrics from a documented, untouched test split after its provenance, scene groups, annotation review, and label protocol have been checked.

## Baseline evaluation

Run the pixel-region baseline evaluator after manifest validation:

```bash
PYTHONPATH=backend python -m scripts.evaluate_aggregate_baseline path/to/manifest.jsonl
```

It refuses manifests with split/hash errors, requires reviewed `aggregate_instance` labels in the untouched `test` split, runs the same image-quality and analysis service as inference, and reports pixel IoU, precision, and recall against the union of aggregate instances. Low-quality test images are listed as excluded. The JSON report includes the manifest SHA-256, each evaluated image/label SHA-256, method version, per-image measurements, and inference time. Instance-count MAE is explicitly null because this region baseline cannot separate or count particles. Pixel metrics therefore measure region overlap only, not instance-segmentation quality. The repository currently contains no aggregate-labeled test set, so the evaluator has unit-test coverage but no RoadIQ accuracy result.
