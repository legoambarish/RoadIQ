from __future__ import annotations

import json

import pytest

from app.services.india_detector import (
    APPROVED_PRETRAINING_CHECKPOINT_SHA256,
    APPROVED_PRETRAINING_SOURCE,
    validate_pretraining_provenance,
)
from backend.scripts.train_india_detector import calculate_class_weights
from backend.scripts.train_india_roi import validation_selection_score


def test_detector_class_weights_use_only_training_boxes(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {"split": "train", "boxes_xyxy_px": [[0, 0, 1, 1]] * 9 + [[1, 0, 1, 1]] +
         [[2, 0, 1, 1]] * 4 + [[3, 0, 1, 1]] * 16},
        {"split": "validation", "boxes_xyxy_px": [[1, 0, 1, 1]] * 1000},
        {"split": "test", "boxes_xyxy_px": [[1, 0, 1, 1]] * 1000},
    ]
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    weights, counts = calculate_class_weights(manifest)

    assert counts == [9, 1, 4, 16]
    assert sum(weights) / len(weights) == pytest.approx(1)
    assert weights[1] > weights[2] > weights[0] > weights[3]


def test_detector_class_weights_reject_missing_training_classes(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"split": "train", "boxes_xyxy_px": [[0, 0, 1, 1]]}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="every class"):
        calculate_class_weights(manifest)


def test_pretraining_provenance_accepts_explicit_coco_and_legacy_scratch_only():
    assert validate_pretraining_provenance({"pretrained": False}) is False
    metadata = {
        "pretrained": True,
        "pretraining_source": APPROVED_PRETRAINING_SOURCE,
        "pretraining_dataset": "COCO 2017",
        "pretraining_license": "AGPL-3.0 (Ultralytics model weights)",
        "pretraining_checkpoint_sha256": APPROVED_PRETRAINING_CHECKPOINT_SHA256,
    }
    assert validate_pretraining_provenance(metadata) is True
    with pytest.raises(ValueError, match="provenance"):
        validate_pretraining_provenance({**metadata, "pretraining_dataset": "unknown"})
    with pytest.raises(ValueError, match="provenance"):
        validate_pretraining_provenance({**metadata, "pretraining_checkpoint_sha256": "a" * 64})


def test_unet_selection_uses_validation_road_and_pothole_iou():
    scores = {"iou_by_class": {"road": 0.8, "pothole": 0.2}}
    assert validation_selection_score(scores) == pytest.approx(0.5)
    with pytest.raises(ValueError, match="both road and pothole"):
        validation_selection_score({"iou_by_class": {"road": 0.8, "pothole": None}})
