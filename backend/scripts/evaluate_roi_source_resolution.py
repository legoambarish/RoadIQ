"""Evaluate genuine CPU runtime masks against untouched source-resolution labels.

Reports image-space segmentation/area errors, never physical measurement errors.
No model selection, threshold tuning, or relabelling is performed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np
from PIL import Image, ImageDraw
from app.services.india_road_segmentation import IndiaRoadSegmentationModel, EXTENDED_CLASS_NAMES


def image_overlay(image, labels):
    colors = np.array([[28, 184, 115], [76, 122, 239], [174, 105, 211], [255, 139, 22], [0, 0, 0]], dtype=np.uint8)
    colored = Image.fromarray(colors[labels])
    return Image.blend(image, colored, .42)


def scores(confusion):
    diagonal = np.diag(confusion).astype(float)
    union = confusion.sum(0) + confusion.sum(1) - diagonal
    denominator = confusion.sum(0) + confusion.sum(1)
    return {"iou_by_class": {name: float(diagonal[i] / union[i]) if union[i] else None for i, name in enumerate(EXTENDED_CLASS_NAMES)},
            "dice_by_class": {name: float(2 * diagonal[i] / denominator[i]) if denominator[i] else None for i, name in enumerate(EXTENDED_CLASS_NAMES)},
            "macro_iou": float(np.mean(diagonal[union > 0] / union[union > 0])),
            "confusion_matrix_rows_true_columns_predicted": confusion.tolist()}


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = args.checkpoint.resolve(strict=True)
    manifest = checkpoint.parent / "roi-manifest.jsonl"
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    model = IndiaRoadSegmentationModel(checkpoint, device="cpu")
    assert model.checkpoint_metadata["split_audit"]["manifest_sha256"] == manifest_hash
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    rows = [row for row in rows if row["split"] == "test"]
    assert len(rows) == 350, "This versioned evaluation expects the full frozen 350-image test sequence"
    confusion = np.zeros((5, 5), dtype=np.int64)
    total_roi_intersection, total_roi_union = 0, 0
    records = []
    started = time.perf_counter()
    for index, row in enumerate(rows):
        image_path, label_path = args.data / row["image_path"], args.data / row["label_path"]
        for path, key in ((image_path, "image_sha256"), (label_path, "label_sha256")):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row[key], "Frozen source file changed"
        image = Image.open(image_path).convert("RGB")
        source = np.array(Image.open(label_path).convert("L"))
        truth = np.full(source.shape, 4, dtype=np.uint8)
        for source_id, target_id in ((0, 0), (2, 1), (3, 2), (4, 3)):
            truth[source == source_id] = target_id
        predicted = np.array(model.predict(image)["mask"])
        assert predicted.shape == truth.shape and predicted.max() <= 4
        confusion += np.bincount((truth.astype(np.int64) * 5 + predicted).ravel(), minlength=25).reshape(5, 5)
        true_roi, pred_roi = np.isin(truth, (0, 3)), np.isin(predicted, (0, 3))
        intersection, union = int((true_roi & pred_roi).sum()), int((true_roi | pred_roi).sum())
        total_roi_intersection += intersection
        total_roi_union += union
        true_hole, pred_hole = truth == 3, predicted == 3
        true_area, pred_area = int(true_hole.sum()), int(pred_hole.sum())
        false_pixels = int((true_hole ^ pred_hole).sum())
        record = {"image_id": row["image_id"], "image_sha256": row["image_sha256"], "scene_group": row["scene_group"],
                  "source_size_px": list(image.size), "true_pothole_pixels": true_area, "predicted_pothole_pixels": pred_area,
                  "pothole_area_absolute_error_px": abs(pred_area - true_area),
                  "pothole_image_fraction_absolute_error": abs(pred_area - true_area) / truth.size,
                  "pothole_symmetric_difference_px": false_pixels, "road_or_pothole_roi_iou": intersection / union if union else None,
                  "predicted_pothole_pixels_on_source_negative": pred_area if true_area == 0 else None}
        records.append(record)
        if index % 25 == 0:
            print(json.dumps({"event": "source_resolution_roi_progress", "images": index + 1, "total": len(rows)}), flush=True)
    errors = sorted(records, key=lambda item: -item["pothole_symmetric_difference_px"])[:6]
    sheet = Image.new("RGB", (960, 6 * 205), "white")
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(errors):
        row = next(row for row in rows if row["image_id"] == record["image_id"])
        image = Image.open(args.data / row["image_path"]).convert("RGB")
        source = np.array(Image.open(args.data / row["label_path"]).convert("L"))
        truth = np.full(source.shape, 4, dtype=np.uint8)
        for source_id, target_id in ((0, 0), (2, 1), (3, 2), (4, 3)):
            truth[source == source_id] = target_id
        predicted = np.array(model.predict(image)["mask"])
        for column, (name, panel) in enumerate((("SOURCE PHOTO", image), ("SOURCE LABEL", image_overlay(image, truth)), ("MODEL PREDICTION", image_overlay(image, predicted)))):
            panel.thumbnail((318, 178))
            left, top = column * 320, index * 205
            sheet.paste(panel, (left, top + 25))
            draw.text((left + 3, top + 3), name + " / " + str(index + 1), fill="black")
    sheet.save(output / "worst-pothole-mask-errors.jpg", quality=90)
    positives = [row for row in records if row["true_pothole_pixels"] > 0]
    negatives = [row for row in records if row["true_pothole_pixels"] == 0]
    report = {"status": "completed", "images": len(rows), "source_positive_pothole_images": len(positives),
              "source_negative_pothole_images": len(negatives), "manifest_sha256": manifest_hash,
              "checkpoint_sha256": model.checkpoint_metadata["sha256"], "model_version": model.model_version,
              "device": "cpu", "preprocessing": model.preprocessing, "source_resolution_metrics": scores(confusion),
              "road_or_pothole_roi_iou": total_roi_intersection / total_roi_union if total_roi_union else None,
              "pothole_area_mae_source_px_all_images": float(np.mean([row["pothole_area_absolute_error_px"] for row in records])),
              "pothole_area_mae_source_px_positive_images": float(np.mean([row["pothole_area_absolute_error_px"] for row in positives])) if positives else None,
              "pothole_image_fraction_mae_all_images": float(np.mean([row["pothole_image_fraction_absolute_error"] for row in records])),
              "source_negative_images_with_any_predicted_pothole_pixel": sum(row["predicted_pothole_pixels"] > 0 for row in negatives),
              "worst_pothole_mask_examples": errors, "elapsed_seconds": round(time.perf_counter() - started, 2),
              "limitations": ["One source-heldout sequence, only 14 source-pothole-positive images; annotation completeness is not independently established.",
                              "Pixel metrics and area errors quantify image-space model disagreement with labels, not physical error or engineering validity.",
                              "Source negative means no pothole-labelled pixels, not certified healthy pavement.",
                              "No model selection or tuning uses this evaluation. Latency here includes hashing/metrics/previews and is not the API latency benchmark."]}
    (output / "source-resolution-evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "per-image-source-evaluation.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"event": "source_resolution_roi_completed", **report}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/indian-roads-v2")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "models/india-roi-v3-letterbox-v1/roi.pt")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/roi-source-evaluation")
    run(parser.parse_args())
