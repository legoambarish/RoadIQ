from __future__ import annotations

import pytest

from app.services.experimental_image_indicator import calculate_experimental_image_indicator


def report(*detections):
    return {
        "image": {"width_px": 100, "height_px": 100},
        "image_quality": {"usable": True},
        "model": {"load_status": "loaded", "inference_status": "completed"},
        "processing_errors": [],
        "defects": [
            {"class": "crack", "detections": list(detections)},
            {
                "class": "pothole",
                "detections": [],
                "mask_geometry": {"affected_pavement_pixel_fraction": 0.125},
            },
        ],
    }


def box(x_min, y_min, x_max, y_max):
    return {"bbox_xyxy_px": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max}}


def test_reports_union_box_coverage_and_mask_fraction_without_rsqi_score():
    result = calculate_experimental_image_indicator(
        report(box(0, 0, 50, 50), box(25, 25, 75, 75))
    )
    assert result.status == "available"
    assert result.candidate_count == 2
    assert result.candidate_box_coverage_percent == 43.75
    assert result.predicted_pothole_pixel_fraction_percent == 12.5
    assert "not RSQI" in result.limitations[1]


def test_zero_candidates_is_numeric_but_not_a_clear_road_claim():
    result = calculate_experimental_image_indicator(report())
    assert result.candidate_count == 0
    assert result.candidate_box_coverage_percent == 0
    assert any("does not establish" in item for item in result.limitations)


@pytest.mark.parametrize(
    "updates",
    [
        {"image_quality": {"usable": False}},
        {"model": {"load_status": "not_configured", "inference_status": "unavailable"}},
        {"processing_errors": [{"code": "inference_failed"}]},
    ],
)
def test_unusable_or_unavailable_inference_has_no_numeric_indicator(updates):
    input_report = report(box(0, 0, 10, 10))
    input_report.update(updates)
    result = calculate_experimental_image_indicator(input_report)
    assert result.status == "unavailable"
    assert result.candidate_count is None
    assert result.candidate_box_coverage_percent is None


def test_low_resolution_preview_returns_limited_indicator():
    input_report = report(box(0, 0, 10, 10))
    input_report["image_quality"] = {
        "usable": False,
        "issues": ["effective_resolution_below_minimum"],
    }
    input_report["model"]["inference_status"] = "limited_quality"
    result = calculate_experimental_image_indicator(input_report)
    assert result.status == "limited"
    assert result.candidate_count == 1
    assert result.candidate_box_coverage_percent == 1
    assert any("limited preview" in item for item in result.limitations)


def test_invalid_dimensions_are_reported():
    input_report = report()
    input_report["image"]["width_px"] = 0
    with pytest.raises(ValueError, match="positive integers"):
        calculate_experimental_image_indicator(input_report)
