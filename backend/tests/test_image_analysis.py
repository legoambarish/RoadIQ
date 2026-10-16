"""Integration tests for the POST /api/v1/image-analyses route."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.services.scoring import (
    COMPONENTS,
    FeatureObservation,
    NormalizationProfile,
    NormalizationReference,
    ScoringConfig,
    ScoringEvidence,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _make_dummy_image(width: int = 640, height: int = 480, color=(128, 128, 128)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=color).save(buf, format="JPEG")
    return buf.getvalue()


def test_image_analysis_successful_post(client):
    img_data = _make_dummy_image()
    res = client.post(
        "/api/v1/image-analyses",
        files={"image": ("road.jpg", img_data, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "analysis_id" in data
    assert "analysis_status" in data
    assert "rsqi" in data
    assert data["rsqi"]["status"] in ("rated", "low_confidence", "unrated")
    assert data["analysis_status"] == "unrated"
    assert data["rsqi"]["value"] is None
    assert data["contract_version"] == "image-analysis-v1.2"
    assert data["experimental_image_indicator"]["status"] == "unavailable"
    assert data["experimental_image_indicator"]["candidate_count"] is None
    assert data["quality_label"] is None
    assert all(
        component["status"] == "unavailable"
        for component in data["rsqi"]["components"].values()
    )
    assert "image_quality" in data
    assert "texture_features" in data
    assert "mode_suitability" in data
    modes = data["mode_suitability"]
    assert "walking" in modes
    assert "cycling" in modes
    assert "two_wheeler" in modes
    assert "car" in modes
    assert "bus" in modes
    assert all(value is None for value in modes.values())


def test_image_analysis_endpoint_preserves_scorer_visible_defect_cap(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {name: 0.0 for name in COMPONENTS}
    values["visible_defect_burden"] = 0.25
    evidence = ScoringEvidence(
        surface_type="asphalt_bituminous",
        capture_profile="close-daylight-v1",
        image_quality_usable=True,
        usable_region_adequate=True,
        resolution_adequate=True,
        components={
            name: FeatureObservation(
                value=value,
                unit="ratio",
                status="observed",
                source="image_inference",
            )
            for name, value in values.items()
        },
    )
    config = ScoringConfig(
        normalization_profiles=(
            NormalizationProfile(
                profile_id="integration-test",
                reference_set_id="test-only",
                surface_type="asphalt_bituminous",
                capture_profile="close-daylight-v1",
                components={
                    name: NormalizationReference(
                        unit="ratio",
                        reference_min=0,
                        reference_max=1,
                    )
                    for name in COMPONENTS
                },
            ),
        ),
    )
    monkeypatch.setattr(
        "app.api.routes.image_analysis._map_vision_to_scoring_evidence",
        lambda _vision_result: evidence,
    )
    monkeypatch.setattr(
        "app.api.routes.image_analysis.DEFAULT_SCORING_CONFIG",
        config,
    )

    response = client.post(
        "/api/v1/image-analyses",
        files={"image": ("road.jpg", _make_dummy_image(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rsqi"]["value"] == pytest.approx(30.0)
    assert data["rsqi"]["status"] == "rated"
    assert data["quality_label"] == "Very Poor"
    assert "score was capped at 30.00" in data["rsqi"]["explanation"]


def test_image_analysis_returns_separate_model_coverage_indicator(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.image_analysis._bounded_analysis",
        lambda *_args: {
            "image": {"format": "jpeg", "width_px": 100, "height_px": 100},
            "image_quality": {"usable": True, "issues": []},
            "model": {"load_status": "loaded", "inference_status": "completed"},
            "processing_errors": [],
            "defects": [
                {"class": "crack", "detections": [
                    {
                        "model_label": "longitudinal_crack",
                        "bbox_xyxy_px": {"x_min": 0, "y_min": 0, "x_max": 50, "y_max": 50},
                    }
                ]},
                {"class": "pothole", "detections": [], "mask_geometry": {
                    "affected_pavement_pixel_fraction": 0.125
                }},
            ],
        },
    )

    response = client.post(
        "/api/v1/image-analyses",
        files={"image": ("road.jpg", _make_dummy_image(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["contract_version"] == "image-analysis-v1.2"
    assert data["rsqi"]["status"] == "unrated"
    assert data["rsqi"]["value"] is None
    indicator = data["experimental_image_indicator"]
    assert indicator["version"] == "candidate-coverage-v1"
    assert indicator["status"] == "available"
    assert indicator["candidate_count"] == 1
    assert indicator["candidate_box_coverage_percent"] == 25.0
    assert indicator["predicted_pothole_pixel_fraction_percent"] == 12.5
    assert indicator["unavailable_reason"] is None
    assert any("not RSQI" in item for item in indicator["limitations"])


def test_empty_file_rejected(client):
    res = client.post(
        "/api/v1/image-analyses",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert res.status_code == 400


def test_invalid_filetype_rejected(client):
    res = client.post(
        "/api/v1/image-analyses",
        files={"image": ("doc.txt", b"plain text", "text/plain")},
    )
    assert res.status_code == 422
    assert "corrupt_image" in res.text or "not a valid" in res.text
