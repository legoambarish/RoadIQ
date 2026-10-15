# RoadIQ image dataset manifest

RoadIQ does not bundle or download an aggregate dataset. Each dataset owner must record source, provenance, license/permission evidence, annotation type, review state, and a route/session scene group before using images. Keep aggregate-instance annotations separate from road-defect and semantic road masks.

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
{"image_id":"example-002","image_path":"images/example-002.jpg","label_available":true,"label_path":"labels/example-002.json","label_type":"aggregate_instance","annotation_status":"reviewed","source":"owner-collected example","provenance":"permission record: RIGHTS-001","split":"test","scene_group":"route-099-session-b"}
```

Aggregate labels and road-defect labels are different tasks. `aggregate_instance` should represent individually reviewed stone-particle instances. Metal-fragment labels require a separately agreed label taxonomy; do not classify metal as aggregate or generic debris. `road_semantic_segmentation` describes pixel classes such as road/pothole and does not imply instance counts.

## Validation

From the repository root, after installing `backend/requirements.txt`:

```bash
PYTHONPATH=backend python -m scripts.validate_dataset_manifest path/to/manifest.jsonl
```

The script validates JSONL/required fields, image decode and paths, label state, unique IDs, scene-group split isolation, exact SHA-256 duplicates, and near duplicates with 64-bit difference hash (Hamming distance at most 4). Exact/near duplicates crossing splits and scene groups crossing splits are errors. Duplicate content inside one split is reported as a warning for review. The near-duplicate candidate index is capped to bound work; the report states when that cap prevents complete comparison. Use capture-session/route groups even after deduplication because perceptual hashes cannot identify every same-scene frame.

The validator checks file presence and manifest consistency, not license validity, annotation correctness, or label semantics. It never downloads data. Only report model metrics from a documented, untouched test split after its provenance, scene groups, annotation review, and label protocol have been checked.
