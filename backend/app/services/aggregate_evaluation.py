"""Held-out pixel-mask evaluation for the untrained aggregate texture baseline.

Labels are 8-bit PNG instance-ID masks: zero is background and each positive ID is an
individually annotated stone aggregate. The baseline predicts regions, not instances;
therefore instance-count MAE is intentionally unavailable.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from app.services.aggregate_baseline import METHOD
from app.services.dataset_manifest import validate_dataset_manifest
from app.services.vision import analyze_road_image


def _decode_rle(mask_rle: dict[str, Any]) -> Image.Image:
    height, width = mask_rle["size_px"]
    flat = bytearray(height * width)
    offset = 0
    foreground = False
    for run in mask_rle["counts"]:
        end = offset + run
        if foreground:
            flat[offset:end] = b"\xff" * run
        offset = end
        foreground = not foreground
    if offset != height * width:
        raise ValueError("predicted RLE does not match its declared dimensions")
    return Image.frombytes("L", (width, height), bytes(flat))


def _manifest_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_target_mask(label_path: Path, row: dict[str, Any], image_size: tuple[int, int]) -> Image.Image:
    if label_path.suffix.lower() == ".json":
        try:
            coco = json.loads(label_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{row['image_id']}: cannot parse COCO annotation file") from exc
        if not isinstance(coco, dict) or not isinstance(coco.get("images"), list) or not isinstance(coco.get("annotations"), list):
            raise ValueError(f"{row['image_id']}: expected COCO JSON with images and annotations arrays")
        requested_id = row.get("annotation_image_id")
        image_record = next((item for item in coco["images"] if requested_id is not None and item.get("id") == requested_id), None)
        if image_record is None:
            image_name = Path(row["image_path"]).name
            matching = [item for item in coco["images"] if Path(str(item.get("file_name", ""))).name == image_name]
            if len(matching) == 1:
                image_record = matching[0]
        if image_record is None and len(coco["images"]) == 1:
            image_record = coco["images"][0]
        if image_record is None:
            raise ValueError(f"{row['image_id']}: COCO image record is ambiguous; set annotation_image_id in the manifest")
        if (image_record.get("width"), image_record.get("height")) != image_size:
            raise ValueError(f"{row['image_id']}: COCO and source image dimensions differ")
        image_id = image_record.get("id")
        categories = {category.get("id"): category.get("name") for category in coco.get("categories", []) if isinstance(category, dict)}
        mask = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask)
        for annotation in coco["annotations"]:
            if annotation.get("image_id") != image_id:
                continue
            category_name = categories.get(annotation.get("category_id"))
            if category_name not in {None, "stone_aggregate", "aggregate"}:
                continue
            segmentation = annotation.get("segmentation")
            if isinstance(segmentation, dict):
                size = segmentation.get("size")
                counts = segmentation.get("counts")
                height, width = image_size[1], image_size[0]
                if size != [height, width] or not isinstance(counts, list) or any(not isinstance(run, int) or run < 0 for run in counts):
                    raise ValueError(f"{row['image_id']}: only uncompressed COCO RLE with matching dimensions is supported")
                total = height * width
                column_major = bytearray(total)
                offset = 0
                foreground = False
                for run in counts:
                    end = offset + run
                    if end > total:
                        raise ValueError(f"{row['image_id']}: COCO RLE runs exceed the image dimensions")
                    if foreground:
                        column_major[offset:end] = b"\xff" * run
                    offset = end
                    foreground = not foreground
                if offset != total:
                    raise ValueError(f"{row['image_id']}: COCO RLE runs do not cover the image")
                instance_mask = Image.frombytes("L", (height, width), bytes(column_major)).transpose(Image.Transpose.TRANSPOSE)
                mask = ImageChops.lighter(mask, instance_mask)
                draw = ImageDraw.Draw(mask)
            elif isinstance(segmentation, list):
                for polygon in segmentation:
                    if not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2:
                        raise ValueError(f"{row['image_id']}: COCO polygons require at least three x/y points")
                    points = [(float(polygon[index]), float(polygon[index + 1])) for index in range(0, len(polygon), 2)]
                    draw.polygon(points, fill=255)
            else:
                raise ValueError(f"{row['image_id']}: COCO segmentation must be polygon lists or uncompressed RLE")
        return mask

    with Image.open(label_path) as source:
        if source.mode not in {"1", "L"}:
            raise ValueError(f"{row['image_id']}: instance-ID masks must be 8-bit grayscale PNGs")
        mask = source.convert("L")
        if mask.size != image_size:
            raise ValueError(f"{row['image_id']}: label and image dimensions differ")
        return mask.point(lambda pixel: 255 if pixel > 0 else 0)


def evaluate_aggregate_texture_baseline(manifest: str | Path) -> dict[str, Any]:
    """Evaluate reviewed test-split masks from a validated JSONL manifest."""
    manifest_path = Path(manifest).expanduser().resolve()
    validation = validate_dataset_manifest(manifest_path)
    if not validation["valid"]:
        raise ValueError("manifest validation failed: " + "; ".join(validation["errors"][:5]))

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        row = json.loads(line)
        if row.get("split") == "test":
            if row.get("label_type") != "aggregate_instance" or not row.get("label_available"):
                continue
            if row.get("annotation_status") != "reviewed":
                raise ValueError(f"line {line_number}: aggregate test annotations must be reviewed")
            rows.append(row)
    if not rows:
        raise ValueError("manifest has no reviewed aggregate_instance labels in the test split")

    tp = fp = fn = 0
    per_image: list[dict[str, Any]] = []
    excluded_low_quality: list[str] = []
    for row in rows:
        image_path = (manifest_path.parent / row["image_path"]).resolve()
        label_path = (manifest_path.parent / row["label_path"]).resolve()
        image_bytes = image_path.read_bytes()
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        labels = _load_target_mask(label_path, row, image.size)

        started = time.perf_counter()
        service_report = analyze_road_image(image_bytes, source_name=image_path.name)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if not service_report["image_quality"]["usable"]:
            excluded_low_quality.append(row["image_id"])
            continue
        predicted_mask = _decode_rle(service_report["aggregate_analysis"]["surface_region"]["mask_rle"])
        target_mask = labels.resize(predicted_mask.size, Image.Resampling.NEAREST).point(
            lambda pixel: 255 if pixel > 0 else 0
        )
        predicted = predicted_mask.tobytes()
        target = target_mask.tobytes()
        image_tp = sum(1 for p, t in zip(predicted, target) if p and t)
        image_fp = sum(1 for p, t in zip(predicted, target) if p and not t)
        image_fn = sum(1 for p, t in zip(predicted, target) if not p and t)
        tp += image_tp
        fp += image_fp
        fn += image_fn
        union = image_tp + image_fp + image_fn
        per_image.append({
            "image_id": row["image_id"],
            "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "label_sha256": hashlib.sha256(label_path.read_bytes()).hexdigest(),
            "iou": image_tp / union if union else None,
            "precision": image_tp / (image_tp + image_fp) if image_tp + image_fp else None,
            "recall": image_tp / (image_tp + image_fn) if image_tp + image_fn else None,
            "inference_time_ms": round(elapsed_ms, 3),
        })

    union = tp + fp + fn
    predicted_positive = tp + fp
    actual_positive = tp + fn
    return {
        "evaluation_status": "computed" if per_image else "no_usable_test_images",
        "manifest_sha256": _manifest_digest(manifest_path),
        "split": "test",
        "label_type": "aggregate_instance",
        "label_encoding": "COCO polygon instances or 8-bit grayscale PNG instance IDs; 0=background",
        "method": METHOD,
        "training_status": "untrained_baseline",
        "images_in_test_split": len(rows),
        "images_evaluated": len(per_image),
        "images_excluded_low_quality": excluded_low_quality,
        "metrics": {
            "pixel_iou": tp / union if union else None,
            "pixel_precision": tp / predicted_positive if predicted_positive else None,
            "pixel_recall": tp / actual_positive if actual_positive else None,
            "aggregate_instance_count_mae": None,
            "aggregate_instance_count_mae_reason": "the baseline predicts texture regions and does not separate/count individual instances",
        },
        "per_image": per_image,
        "limitations": [
            "Pixel metrics compare a heuristic texture-region mask with the union of instance masks; they do not measure instance segmentation quality.",
            "These results are valid only for the exact manifest digest and reviewed test labels reported above.",
            "Per-image inference times vary by hardware and are diagnostic, not a benchmark claim.",
        ],
    }
