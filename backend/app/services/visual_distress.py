"""Versioned observational VDA. No invented grade, confidence or physical score."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VisualDistressAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["vda-observations-v1"] = "vda-observations-v1"
    status: Literal["defects_detected", "no_defect_detected", "low_confidence", "unusable", "unavailable"]
    summary: str
    detection_count: int | None = Field(default=None, ge=0)
    counts_by_model_class: dict[str, int] = Field(default_factory=dict)
    caution_flags: list[str] = Field(default_factory=list)
    reliability: Literal["limited", "unavailable"]
    reliability_reasons: list[str]
    score_eligible: Literal[False] = False
    grade: None = None
    score: None = None
    confidence: None = None
    physical_measurements: dict[str, Any] = Field(default_factory=lambda: {
        "pothole_depth_mm": None, "crack_width_mm": None, "affected_ground_area_m2": None,
        "reason": "No validated physical calibration/defect geometry; 2D RGB cannot establish depression depth."})
    reference_percentile: dict[str, Any] = Field(default_factory=lambda: {
        "value": None, "status": "unavailable", "reason": "No eligible RSQI scores or fixed compatible reference cohort."})


def assess_visual_distress(report: dict[str, Any]) -> VisualDistressAssessment:
    quality = report.get("image_quality") or {}
    model = report.get("model") or {}
    detections = [item for observation in report.get("defects", []) for item in observation.get("detections", [])]
    counts: dict[str, int] = {}
    cautions: list[str] = []
    for item in detections:
        name = item["model_label"]
        counts[name] = counts.get(name, 0) + 1
        if name in {"pothole", "d40"}:
            cautions.append(f"localized_pothole_candidate:{item.get('instance_id', 'unknown')}:inspection_required_depth_unknown")
        if name in {"alligator_crack", "d20"}:
            cautions.append(f"localized_fatigue_crack_candidate:{item.get('instance_id', 'unknown')}")
        if item.get("edge_clipped"):
            cautions.append(f"partial_edge_instance:{item.get('instance_id', 'unknown')}")
        if item.get("small_box_resolution"):
            cautions.append(f"small_extent_unresolved_geometry:{item.get('instance_id', 'unknown')}")
    reasons = ["Raw detector scores are not calibrated detection probabilities or assessment reliability.",
               "Material, occlusion and viewpoint support are not independently validated.",
               "Condition/severity labels and field measurements are absent; no engineering grade is assigned."]
    pavement = report.get("pavement_region") or {}
    roi_fraction = (pavement.get("usable_area_ratio") or {}).get("value")
    roi_warning = isinstance(roi_fraction, (float, int)) and 0 <= roi_fraction < .1
    if not pavement.get("mask_rle"):
        reasons.append("Usable pavement ROI is unavailable; no affected-road-area denominator.")
    if roi_warning:
        reasons.append("Predicted road-class coverage is below 10%; this unvalidated visibility heuristic limits interpretation and does not prove absence of pavement.")
    for observation in report.get("defects", []):
        geometry = observation.get("mask_geometry") or {}
        mask_iou = geometry.get("heldout_pothole_iou_model_input_resolution")
        if isinstance(mask_iou, (int, float)):
            reasons.append(f"Experimental pothole mask model source-heldout IoU is {mask_iou:.3f} at model-input resolution; predicted areas are not validated defect measurements.")
    errors = {error.get("code") for error in report.get("processing_errors", [])}
    ready = model.get("load_status") == "loaded" and "inference_failed" not in errors
    count = len(detections) if ready and quality.get("usable") is True else None
    if quality.get("usable") is False:
        status, summary, reliability = "unusable", "Image quality prevents supported assessment. Submit a clearer road photo.", "unavailable"
    elif not ready:
        status, summary, reliability = "unavailable", "Defect inference is unavailable. No road condition is inferred.", "unavailable"
    elif quality.get("issues") or roi_warning:
        status, summary, reliability = "low_confidence", "Image quality or predicted road-visibility warnings limit these candidate observations. No condition grade is assigned.", "limited"
    elif detections:
        status, summary, reliability = "defects_detected", f"{len(detections)} visible defect candidate(s) detected; inspect localized findings. Severity and physical dimensions remain unknown.", "limited"
    else:
        status, summary, reliability = "no_defect_detected", "No supported defect detected at this model threshold. This does not establish intact or healthy pavement.", "limited"
    if quality.get("issues"):
        reasons.extend(f"Image quality warning: {issue}" for issue in quality["issues"])
    return VisualDistressAssessment(status=status, summary=summary, reliability=reliability, reliability_reasons=reasons,
                                    detection_count=count, counts_by_model_class=counts, caution_flags=cautions)
