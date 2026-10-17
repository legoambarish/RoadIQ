"""Transparent image-space measurements derived from current model predictions."""
from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExperimentalImageIndicator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["candidate-coverage-v1"] = "candidate-coverage-v1"
    status: Literal["available", "limited", "unavailable"]
    candidate_count: int | None = Field(default=None, ge=0)
    candidate_box_coverage_percent: float | None = Field(default=None, ge=0, le=100)
    predicted_pothole_pixel_fraction_percent: float | None = Field(default=None, ge=0, le=100)
    provisional_score: float | None = Field(default=None, ge=0, le=100)
    provisional_score_formula: str | None = None
    unavailable_reason: str | None = None
    limitations: list[str] = Field(default_factory=list)


_LIMITATIONS = [
    "Detector boxes are model candidates, not confirmed defects or damage-area masks.",
    "Box coverage is the union of candidate boxes divided by the whole oriented image area; it is not RSQI or a condition score.",
    "Predicted pothole-pixel fraction, when available, comes from an unvalidated semantic mask and is not a ground-truth measurement.",
    "Zero detected candidates does not establish that the road is defect-free.",
    "Model accuracy on arbitrary field images is not established.",
    "The provisional score is an unvalidated demo heuristic, not RSQI or a road-condition grade; missed detections can yield an unjustifiably high value.",
]

_SCORE_FORMULA = (
    "clamp(100 - 10*candidate_count - 3*candidate_box_coverage_percent "
    "- 2*predicted_pothole_pixel_fraction_percent, 0, 100); "
    "missing pothole fraction contributes 0"
)


def _rectangle_union_area(boxes: list[tuple[float, float, float, float]]) -> float:
    x_edges = sorted({edge for box in boxes for edge in (box[0], box[2])})
    union_area = 0.0
    for left, right in zip(x_edges, x_edges[1:]):
        if right <= left:
            continue
        intervals = sorted(
            (top, bottom)
            for box_left, top, box_right, bottom in boxes
            if box_left < right and box_right > left
        )
        if not intervals:
            continue
        covered_y = 0.0
        start, end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start > end:
                covered_y += end - start
                start, end = next_start, next_end
            else:
                end = max(end, next_end)
        covered_y += end - start
        union_area += (right - left) * covered_y
    return union_area


def _available_pothole_fraction(report: dict[str, Any]) -> float | None:
    for observation in report.get("defects", []):
        if observation.get("class") != "pothole":
            continue
        geometry = observation.get("mask_geometry")
        fraction = geometry.get("affected_pavement_pixel_fraction") if isinstance(geometry, dict) else None
        if type(fraction) in (int, float) and math.isfinite(fraction) and 0 <= fraction <= 1:
            return round(fraction * 100, 4)
    return None


def calculate_experimental_image_indicator(report: dict[str, Any]) -> ExperimentalImageIndicator:
    """Report model observations with a separate, unvalidated demo score—not RSQI."""
    quality = report.get("image_quality")
    quality = quality if isinstance(quality, dict) else {}
    model = report.get("model")
    model = model if isinstance(model, dict) else {}
    errors = report.get("processing_errors")
    inference_failed = isinstance(errors, list) and any(
        isinstance(error, dict) and error.get("code") == "inference_failed" for error in errors
    )
    if model.get("load_status") != "loaded":
        return ExperimentalImageIndicator(
            status="unavailable",
            unavailable_reason="The detector model is not loaded.",
            limitations=_LIMITATIONS,
        )
    if inference_failed:
        return ExperimentalImageIndicator(
            status="unavailable",
            unavailable_reason="Detector inference failed.",
            limitations=_LIMITATIONS,
        )
    inference_status = model.get("inference_status")
    limited_quality = (
        inference_status == "limited_quality"
        and quality.get("usable") is False
        and quality.get("issues") == ["effective_resolution_below_minimum"]
    )
    if not (quality.get("usable") is True and inference_status == "completed") and not limited_quality:
        reason = (
            "Image-quality checks prevented detector inference."
            if quality.get("usable") is not True
            else "Detector inference did not complete."
        )
        return ExperimentalImageIndicator(
            status="unavailable",
            unavailable_reason=reason,
            limitations=_LIMITATIONS,
        )

    image = report.get("image")
    if not isinstance(image, dict):
        raise ValueError("image dimensions are required for candidate coverage")
    width, height = image.get("width_px"), image.get("height_px")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive integers")

    observations = report.get("defects")
    if not isinstance(observations, list):
        raise ValueError("defect observations must be a list after completed inference")
    detections: list[dict[str, Any]] = []
    for observation in observations:
        items = observation.get("detections", [])
        if not isinstance(items, list):
            raise ValueError("defect detections must be a list")
        detections.extend(items)

    boxes: list[tuple[float, float, float, float]] = []
    for detection in detections:
        bbox = detection.get("bbox_xyxy_px")
        if not isinstance(bbox, dict):
            raise ValueError("each detector candidate must include a source-coordinate box")
        coordinates = tuple(bbox.get(name) for name in ("x_min", "y_min", "x_max", "y_max"))
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in coordinates):
            raise ValueError("candidate box coordinates must be finite numbers")
        x_min = min(float(width), max(0.0, float(coordinates[0])))
        y_min = min(float(height), max(0.0, float(coordinates[1])))
        x_max = min(float(width), max(0.0, float(coordinates[2])))
        y_max = min(float(height), max(0.0, float(coordinates[3])))
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("candidate box must have positive clipped area")
        boxes.append((x_min, y_min, x_max, y_max))

    image_area = width * height
    coverage = 100 * _rectangle_union_area(boxes) / image_area
    coverage_percent = round(coverage, 4)
    pothole_fraction_percent = _available_pothole_fraction(report)
    score = max(
        0.0,
        min(
            100.0,
            100.0
            - 10.0 * len(detections)
            - 3.0 * coverage_percent
            - 2.0 * (pothole_fraction_percent or 0.0),
        ),
    )
    return ExperimentalImageIndicator(
        status="limited" if limited_quality else "available",
        candidate_count=len(detections),
        candidate_box_coverage_percent=coverage_percent,
        predicted_pothole_pixel_fraction_percent=pothole_fraction_percent,
        provisional_score=round(score, 1),
        provisional_score_formula=_SCORE_FORMULA,
        limitations=(
            [*_LIMITATIONS, "Image resolution is below the supported minimum; this is a limited preview only."]
            if limited_quality else _LIMITATIONS
        ),
    )
