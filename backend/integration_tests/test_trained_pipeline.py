"""Explicit real-asset gate. Missing assets FAIL; no mock or silent skip.

Run: python -m pytest backend/integration_tests -q
Standard unit tests intentionally remain runnable without optional ML assets.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.vision import reset_detector_for_tests

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def live_client():
    checkpoint = ROOT / "models/india-yolo11n-v1/detector.pt"
    assert checkpoint.is_file(), "Real India-trained weights required. Run documented preparation/training first."
    assert checkpoint.with_suffix(".json").is_file(), "Trained checkpoint/evaluation provenance required."
    os.environ["ROADIQ_DETECTOR_MODEL_PATH"] = str(checkpoint)
    os.environ["ROADIQ_DETECTOR_DEVICE"] = "cpu"
    roi_checkpoint = ROOT / "models/india-roi-v3-letterbox-v1/roi.pt"
    assert roi_checkpoint.is_file(), "Real corrected-aspect ROI checkpoint required."
    os.environ["ROADIQ_SEGMENTATION_MODEL_PATH"] = str(roi_checkpoint)
    os.environ["ROADIQ_SEGMENTATION_DEVICE"] = "cpu"
    reset_detector_for_tests()
    with TestClient(create_app()) as client:
        ready = client.get("/api/v1/vision-readiness").json()
        assert ready["ready"] is True
        assert ready["roi"]["status"] == "loaded"
        yield client
    os.environ.pop("ROADIQ_DETECTOR_MODEL_PATH", None)
    os.environ.pop("ROADIQ_SEGMENTATION_MODEL_PATH", None)
    reset_detector_for_tests()


def test_real_india_image_to_actual_model_to_http_contract(live_client):
    manifest = ROOT / "data/rdd2022-india-v1/manifest.jsonl"
    assert manifest.is_file(), "Frozen labelled holdout required; no synthetic substitute."
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    selected = [row for row in rows if row["split"] == "test" and any(box[0] == 3 for box in row["boxes_xyxy_px"])][:8]
    assert selected, "Genuine heldout pothole-labelled samples required."
    predictions = 0
    for row in selected:
        path = manifest.parent / row["image_path"]
        response = live_client.post("/api/v1/image-analyses", files={"image": (path.name, path.read_bytes(), "image/jpeg")})
        assert response.status_code == 200
        result = response.json()
        assert result["model"]["load_status"] == "loaded"
        assert result["model"]["training_status"] == "roadIQ_trained"
        assert len(result["model"]["checkpoint"]["sha256"]) == 64
        assert result["model"]["checkpoint"]["heldout_evaluation"]["images"] == 993
        assert any("Source-heldout detector AP50" in reason for reason in result["visual_distress"]["reliability_reasons"])
        assert result["processing_time_ms"]["detector"] > 0
        assert result["processing_time_ms"]["segmentation"] > 0
        assert result["model"]["segmentation"]["load_status"] == "loaded"
        preprocessing = result["model"]["segmentation"]["preprocessing_geometry"]
        assert preprocessing["method"] == "letterbox_bilinear_rgb_nearest_mask_v1"
        assert preprocessing["source_size_px"] == [result["image"]["width_px"], result["image"]["height_px"]]
        mask = result["pavement_region"]["mask_rle"]
        assert mask["size_px"] == [result["image"]["height_px"], result["image"]["width_px"]]
        assert sum(mask["counts"]) == result["image"]["width_px"] * result["image"]["height_px"]
        assert result["rsqi"]["value"] is None
        assert result["visual_distress"]["reference_percentile"]["value"] is None
        predictions += sum(len(defect["detections"]) for defect in result["defects"])
    assert predictions > 0, "Checkpoint produced no candidates across eight actual damaged holdout images."


def test_unsuitable_image_never_receives_positive_grade(live_client):
    buffer = io.BytesIO()
    Image.new("RGB", (640, 480), "black").save(buffer, format="PNG")
    result = live_client.post("/api/v1/image-analyses", files={"image": ("unsuitable.png", buffer.getvalue(), "image/png")}).json()
    assert result["visual_distress"]["status"] == "unusable"
    assert result["visual_distress"]["grade"] is None
    assert result["rsqi"]["value"] is None
    assert all(defect["count"]["value"] is None for defect in result["defects"])
