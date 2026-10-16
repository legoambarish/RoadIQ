"""Evidence-state regression tests, independent of learned model quality."""
from __future__ import annotations

import copy
import io

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.visual_distress import assess_visual_distress
from app.services.vision import _detection_objects, _quality_report, _validate_and_decode


def observation(detections=None, *, issues=None, usable=True, loaded=True):
    return {"image_quality": {"usable": usable, "issues": issues or []},
            "model": {"load_status": "loaded" if loaded else "not_configured"},
            "pavement_region": {}, "defects": [{"detections": detections or []}], "processing_errors": []}


def test_no_detection_is_never_a_good_grade():
    result = assess_visual_distress(observation())
    assert result.status == "no_defect_detected"
    assert result.detection_count == 0
    assert result.score is None and result.grade is None
    assert result.confidence is None and not result.score_eligible
    assert result.reference_percentile["value"] is None
    assert "healthy" in result.summary


def test_known_detector_validation_is_disclosed_without_becoming_condition_confidence():
    report = observation()
    report["model"]["checkpoint"] = {"heldout_evaluation": {"images": 993, "map50": .1376441299, "map50_95": .0544858997}}
    result = assess_visual_distress(report)
    assert any("AP50 0.138, AP50-95 0.054 on 993" in reason for reason in result.reliability_reasons)
    assert result.status == "no_defect_detected"
    assert result.confidence is None and result.score is None and result.grade is None


@pytest.mark.parametrize("loaded", [False, True])
def test_unusable_image_does_not_get_zero_defects(loaded):
    result = assess_visual_distress(observation(usable=False, loaded=loaded))
    assert result.status == "unusable"
    assert result.detection_count is None


def test_missing_detector_does_not_imply_zero():
    result = assess_visual_distress(observation(loaded=False))
    assert result.status == "unavailable"
    assert result.detection_count is None


def test_blurry_image_without_detections_is_low_confidence():
    result = assess_visual_distress(observation(issues=["very_low_edge_detail_possible_blur_or_uniform_surface"]))
    assert result.status == "low_confidence"
    assert result.score is None


def test_low_predicted_road_coverage_warns_without_claiming_healthy_or_rejecting_counts():
    report = observation()
    report["pavement_region"] = {"usable_area_ratio": {"value": .02}, "mask_rle": {"counts": [98, 2]}}
    result = assess_visual_distress(report)
    assert result.status == "low_confidence"
    assert result.detection_count == 0 and result.grade is None
    assert any("unvalidated visibility heuristic" in reason for reason in result.reliability_reasons)


def test_localized_pothole_is_highlighted_without_any_average_area_threshold():
    detection = {"model_label": "pothole", "instance_id": "tiny-hole", "confidence": 0.31,
                 "bbox_xyxy_px": {"x_min": 10, "y_min": 10, "x_max": 12, "y_max": 12}}
    result = assess_visual_distress(observation([detection]))
    assert result.status == "defects_detected"
    assert result.counts_by_model_class == {"pothole": 1}
    assert any("tiny-hole" in flag and "depth_unknown" in flag for flag in result.caution_flags)


def test_inference_failure_overrides_loaded_model_for_no_detection_state():
    report = observation()
    report["processing_errors"] = [{"code": "inference_failed"}]
    result = assess_visual_distress(report)
    assert result.status == "unavailable" and result.detection_count is None


def test_failed_mask_benchmark_is_visible_even_with_no_detector_candidates():
    report = observation()
    report["defects"][0]["mask_geometry"] = {"heldout_pothole_iou_model_input_resolution": 0.0}
    result = assess_visual_distress(report)
    assert result.grade is None and result.score is None
    assert result.reliability == "limited"
    assert any("IoU is 0.000" in reason and "not validated" in reason for reason in result.reliability_reasons)


def test_box_extent_does_not_populate_segmentation_or_metric_measurements():
    boxes = _detection_objects([("pothole", .6, [-1, 10, 50, 30])], 400, 300)
    box = boxes["pothole"][0]
    assert box["box_extent_width_px"] == 50
    assert box["bbox_xyxy_px"]["x_min"] == 0
    assert box["edge_clipped"] is True
    assert "segmented_area_px" not in box


def test_uniform_image_quality_warns_despite_artificial_image_border_edges():
    report = _quality_report(Image.new("RGB", (640, 480), (100, 100, 100)))
    assert "very_low_edge_detail_possible_blur_or_uniform_surface" in report["issues"]


def test_glare_quality_is_a_disclosed_heuristic():
    image = Image.new("RGB", (640, 480), "gray")
    image.paste("white", (100, 100, 600, 400))
    report = _quality_report(image)
    assert "substantial_saturated_highlights_possible_glare" in report["issues"]
    assert report["limitations"]


def test_exif_rotation_uses_oriented_source_coordinates():
    buffer = io.BytesIO()
    image = Image.new("RGB", (800, 400), "gray")
    exif = Image.Exif()
    exif[274] = 6
    image.save(buffer, format="JPEG", exif=exif)
    oriented, _, dimensions = _validate_and_decode(buffer.getvalue())
    assert dimensions == (400, 800)
    assert oriented.info["roadiq_stored_size"] == (800, 400)
    assert oriented.info["roadiq_exif_orientation"] == 6


def test_animated_preview_cannot_be_misrepresented_by_first_frame_geometry():
    from app.services.vision import ImageValidationError
    stream = io.BytesIO()
    Image.new("RGB", (400, 300), "gray").save(stream, format="PNG", save_all=True,
        append_images=[Image.new("RGB", (400, 300), "white")], duration=100, loop=0)
    with pytest.raises(ImageValidationError, match="single still image"):
        _validate_and_decode(stream.getvalue())


def test_http_image_limit_and_mime_mismatch(monkeypatch):
    client = TestClient(create_app())
    monkeypatch.setattr("app.api.routes.image_analysis.MAX_IMAGE_BYTES", 32)
    oversized = client.post("/api/v1/image-analyses", files={"image": ("x.jpg", b"x" * 33, "image/jpeg")})
    assert oversized.status_code == 413
    monkeypatch.setattr("app.api.routes.image_analysis.MAX_IMAGE_BYTES", 10 * 1024 * 1024)
    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), "gray").save(buffer, format="PNG")
    mismatched = client.post("/api/v1/image-analyses", files={"image": ("x.jpg", buffer.getvalue(), "image/jpeg")})
    assert mismatched.status_code == 422


def test_health_and_missing_model_readiness_are_distinct(monkeypatch):
    monkeypatch.delenv("ROADIQ_DETECTOR_MODEL_PATH", raising=False)
    monkeypatch.delenv("ROADIQ_VISION_MODEL_PATH", raising=False)
    client = TestClient(create_app())
    assert client.get("/api/v1/health").status_code == 200
    readiness = client.get("/api/v1/vision-readiness").json()
    assert readiness["ready"] is False
    assert readiness["detector"]["status"] == "not_configured"
