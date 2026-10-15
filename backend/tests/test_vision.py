from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image, ImageDraw

from app.schemas.image_analysis import ImageAnalysisResponse
from app.services.vision import (
    ImageValidationError,
    analyze_road_image,
    reset_detector_for_tests,
)
import app.services.vision as vision


def road_image_bytes(size: tuple[int, int] = (400, 300)) -> bytes:
    image = Image.new("RGB", size, (84, 86, 82))
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], 14):
        draw.line((x, 0, x + 40, size[1]), fill=(95 + x % 17, 95, 91), width=1)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class FakePredictions:
    class_id = [0, 3]
    confidence = [0.81, 0.90]
    xyxy = [[10, 20, 110, 50], [150, 100, 220, 200]]
    class_names = ["longitudinal_crack", "pothole"]


class FakeDetector:
    model_name = "test road defect detector"
    model_version = "fixture-1"
    training_status = "pretrained_baseline"

    def __init__(self, predictions: object | None = None) -> None:
        self.predictions = predictions if predictions is not None else FakePredictions()
        self.calls = 0
        self.threshold = None

    def predict(self, image: Image.Image, threshold: float) -> object:
        self.calls += 1
        self.threshold = threshold
        assert image.mode == "RGB"
        return self.predictions


def by_class(report: dict[str, object]) -> dict[str, dict[str, object]]:
    return {item["class"]: item for item in report["defects"]}


def test_valid_image_produces_contract_payload_and_pixel_boxes() -> None:
    detector = FakeDetector()
    report = analyze_road_image(road_image_bytes(), source_name="road.png", detector=detector)
    ImageAnalysisResponse.model_validate(report)

    defects = by_class(report)
    assert report["analysis_status"] == "unrated"
    assert report["image"]["width_px"] == 400
    assert report["image"]["format"] == "png"
    assert report["image_quality"]["usable"] is True
    assert defects["crack"]["count"]["value"] == 1
    assert defects["pothole"]["count"]["value"] == 1
    assert defects["raveling"]["count"]["status"] == "unavailable"
    assert defects["crack"]["detections"][0]["bbox_xyxy_px"]["x_max"] == 110
    assert defects["crack"]["detections"][0]["bbox_xyxy_normalized"]["x_max"] == 0.275
    assert detector.threshold == 0.25
    assert report["surface_type"]["value"] == "unknown"
    assert report["aggregate_analysis"]["aggregate_count"]["value"] is None
    assert report["aggregate_analysis"]["aggregate_count_per_m2"]["value"] is None
    assert report["texture_features"]["is_physical_roughness"] is False


def test_no_detections_are_observed_as_zero_only_for_supported_classes() -> None:
    empty = type("EmptyPredictions", (), {"class_id": [], "confidence": [], "xyxy": []})()
    report = analyze_road_image(road_image_bytes(), detector=FakeDetector(empty))
    defects = by_class(report)
    assert defects["crack"]["count"]["value"] == 0
    assert defects["crack"]["count"]["status"] == "observed"
    assert defects["pothole"]["count"]["value"] == 0
    assert defects["pothole"]["confidence"] is None
    assert defects["raveling"]["count"]["value"] is None


@pytest.mark.parametrize(
    ("payload", "code"),
    [(b"", "empty_image"), (b"not an image", "corrupt_image")],
)
def test_empty_and_corrupt_images_fail_gracefully(payload: bytes, code: str) -> None:
    with pytest.raises(ImageValidationError) as exc:
        analyze_road_image(payload)
    assert exc.value.code == code
    assert exc.value.message


def test_unsupported_format_is_rejected() -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), "red").save(buffer, format="GIF")
    with pytest.raises(ImageValidationError, match="Only JPEG, PNG, and WebP"):
        analyze_road_image(buffer.getvalue())


def test_upload_byte_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vision, "MAX_IMAGE_BYTES", 8)
    with pytest.raises(ImageValidationError) as exc:
        analyze_road_image(road_image_bytes())
    assert exc.value.code == "image_too_large"


def test_low_resolution_blocks_detector_and_keeps_measurements_unavailable() -> None:
    detector = FakeDetector()
    report = analyze_road_image(road_image_bytes((100, 100)), detector=detector)
    assert detector.calls == 0
    assert report["image_quality"]["usable"] is False
    assert by_class(report)["crack"]["count"]["value"] is None
    assert report["aggregate_analysis"]["visible_coverage_ratio"]["value"] is None


def test_calibration_must_be_verified_and_bound_to_same_file() -> None:
    image_bytes = road_image_bytes()
    digest = hashlib.sha256(image_bytes).hexdigest()
    calibration = {
        "method": "checkerboard demo",
        "pixels_per_mm": 2.5,
        "usable_area_m2": 1.0,
        "image_sha256": digest,
        "verified": True,
    }
    report = analyze_road_image(image_bytes, calibration=calibration, detector=FakeDetector())
    assert report["calibration"]["status"] == "observed"
    assert report["aggregate_analysis"]["aggregate_count_per_m2"]["value"] is None
    calibration["image_sha256"] = "0" * 64
    mismatch = analyze_road_image(image_bytes, calibration=calibration, detector=FakeDetector())
    assert mismatch["calibration"]["status"] == "unavailable"


def test_missing_configured_checkpoint_is_a_structured_model_error(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_detector_for_tests()
    monkeypatch.setenv("ROADIQ_VISION_MODEL_PATH", "/missing/road-damage-checkpoint.pth")
    report = analyze_road_image(road_image_bytes())
    assert report["model"]["load_status"] == "failed"
    assert report["processing_errors"][0]["code"] == "model_load_failed"
    assert by_class(report)["crack"]["count"]["value"] is None
    reset_detector_for_tests()


def test_unpinned_checkpoint_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    checkpoint = tmp_path / "other-model.pth"
    checkpoint.write_bytes(b"not the pinned model")
    reset_detector_for_tests()
    monkeypatch.setenv("ROADIQ_VISION_MODEL_PATH", str(checkpoint))
    report = analyze_road_image(road_image_bytes())
    assert report["model"]["load_status"] == "failed"
    assert report["processing_errors"][0]["code"] == "model_load_failed"
    assert by_class(report)["crack"]["count"]["value"] is None
    reset_detector_for_tests()
    monkeypatch.setenv("ROADIQ_VISION_MODEL_PATH", "/missing/road-damage-checkpoint.pth")
    report = analyze_road_image(road_image_bytes())
    assert report["model"]["load_status"] == "failed"
    assert report["processing_errors"][0]["code"] == "model_load_failed"
    assert by_class(report)["crack"]["count"]["status"] == "unavailable"
    reset_detector_for_tests()


def test_inference_failure_is_reported_without_substituting_zeroes() -> None:
    class BrokenDetector(FakeDetector):
        def predict(self, image: Image.Image, threshold: float) -> object:
            raise RuntimeError("inference unavailable")

    report = analyze_road_image(road_image_bytes(), detector=BrokenDetector())
    assert report["processing_errors"][0]["code"] == "inference_failed"
    assert by_class(report)["crack"]["count"]["value"] is None
    assert by_class(report)["pothole"]["count"]["value"] is None

