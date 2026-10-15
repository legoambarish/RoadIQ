from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.aggregate_evaluation import evaluate_aggregate_texture_baseline


def test_evaluator_computes_only_pixel_metrics_on_reviewed_test_instances(tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()
    image = Image.new("RGB", (400, 300), (75, 77, 72))
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 85, 270, 220), fill=(120, 113, 101))
    for x in range(100, 270, 8):
        draw.line((x, 85, x + 4, 218), fill=(158, 149, 130), width=1)
    image.save(tmp_path / "images" / "aggregate.png")

    labels = Image.new("L", image.size, 0)
    ImageDraw.Draw(labels).ellipse((115, 100, 165, 150), fill=1)
    ImageDraw.Draw(labels).ellipse((195, 155, 255, 210), fill=2)
    labels.save(tmp_path / "labels" / "aggregate.png")
    row = {
        "image_id": "road-001",
        "image_path": "images/aggregate.png",
        "label_available": True,
        "label_path": "labels/aggregate.png",
        "label_type": "aggregate_instance",
        "annotation_status": "reviewed",
        "source": "synthetic unit test",
        "provenance": "generated fixture",
        "split": "test",
        "scene_group": "route-001-session-1",
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")

    report = evaluate_aggregate_texture_baseline(manifest)
    metrics = report["metrics"]
    assert report["evaluation_status"] == "computed"
    assert report["images_evaluated"] == 1
    assert len(report["manifest_sha256"]) == 64
    assert 0 <= metrics["pixel_iou"] <= 1
    assert 0 <= metrics["pixel_precision"] <= 1
    assert 0 <= metrics["pixel_recall"] <= 1
    assert metrics["aggregate_instance_count_mae"] is None
    assert report["per_image"][0]["inference_time_ms"] >= 0


def test_evaluator_refuses_an_unfrozen_non_test_split(tmp_path: Path) -> None:
    image = Image.new("RGB", (64, 64), "gray")
    image.save(tmp_path / "image.png")
    labels = Image.new("L", image.size, 0)
    labels.save(tmp_path / "labels.png")
    row = {
        "image_id": "road-001",
        "image_path": "image.png",
        "label_available": True,
        "label_path": "labels.png",
        "label_type": "aggregate_instance",
        "annotation_status": "reviewed",
        "source": "synthetic unit test",
        "provenance": "generated fixture",
        "split": "validation",
        "scene_group": "route-001-session-1",
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    try:
        evaluate_aggregate_texture_baseline(manifest)
    except ValueError as exc:
        assert "no reviewed aggregate_instance labels in the test split" in str(exc)
    else:
        raise AssertionError("evaluation must require the untouched test split")


def test_evaluator_reads_coco_polygon_instance_labels(tmp_path: Path) -> None:
    image = Image.new("RGB", (400, 300), (82, 84, 80))
    draw = ImageDraw.Draw(image)
    draw.ellipse((120, 80, 270, 220), fill=(146, 138, 120))
    image.save(tmp_path / "road.png")
    coco = {
        "images": [{"id": 7, "file_name": "road.png", "width": 400, "height": 300}],
        "categories": [{"id": 1, "name": "stone_aggregate"}],
        "annotations": [
            {"id": 1, "image_id": 7, "category_id": 1, "segmentation": [[145, 105, 245, 105, 245, 200, 145, 200]]},
            {"id": 2, "image_id": 7, "category_id": 1, "segmentation": {"size": [300, 400], "counts": [60150, 1, 59849]}},
        ],
    }
    (tmp_path / "instances.json").write_text(json.dumps(coco), encoding="utf-8")
    row = {
        "image_id": "road-001",
        "image_path": "road.png",
        "label_available": True,
        "label_path": "instances.json",
        "label_type": "aggregate_instance",
        "annotation_status": "reviewed",
        "source": "synthetic unit test",
        "provenance": "generated fixture",
        "split": "test",
        "scene_group": "route-001-session-1",
        "annotation_image_id": 7,
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    report = evaluate_aggregate_texture_baseline(manifest)
    assert report["images_evaluated"] == 1
    assert report["label_encoding"].startswith("COCO polygon")
