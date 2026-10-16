"""HTTP integration for Task C image observations and Task A RSQI scoring."""

from __future__ import annotations

import uuid
import threading
import time
from typing import Any, Literal

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from app.schemas.road_segment import ModeSuitability, QualityLabel
from app.services.scoring import (
    DEFAULT_SCORING_CONFIG,
    RSQIResponse,
    ScoringEvidence,
    score_surface_quality,
)
from app.services.vision import MAX_IMAGE_BYTES, ImageValidationError, analyze_road_image
from app.services.visual_distress import VisualDistressAssessment, assess_visual_distress

router = APIRouter(tags=["image-analysis"])
_analysis_slots = threading.BoundedSemaphore(2)


class ImageAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    analysis_status: Literal["completed", "low_confidence", "unrated"]
    image: dict[str, Any] | None = None
    image_quality: dict[str, Any] | None = None
    pavement_region: dict[str, Any] | None = None
    surface_type: dict[str, Any] | None = None
    aggregate_analysis: dict[str, Any] | None = None
    defects: list[dict[str, Any]] | None = None
    texture_features: dict[str, Any] | None = None
    rsqi: RSQIResponse
    quality_label: QualityLabel | None
    scoring_version: str
    mode_suitability: ModeSuitability
    annotated_image: dict[str, Any] = Field(
        default_factory=lambda: {
            "value": None,
            "unit": "uri",
            "status": "unavailable",
            "source": None,
        }
    )
    data_provenance: list[dict[str, Any]] = Field(default_factory=list)
    model: dict[str, Any] | None = None
    processing_errors: list[dict[str, Any]] = Field(default_factory=list)
    contract_version: Literal["image-analysis-v1.1"] = "image-analysis-v1.1"
    visual_distress: VisualDistressAssessment
    calibration: dict[str, Any] | None = None
    metal_fragments: dict[str, Any] | None = None
    processing_time_ms: dict[str, float | None] = Field(default_factory=dict)


def _bounded_analysis(image_bytes: bytes, source_name: str) -> dict[str, Any]:
    if not _analysis_slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Image analysis is busy; retry shortly.", headers={"Retry-After": "2"})
    try:
        return analyze_road_image(image_bytes=image_bytes, source_name=source_name)
    finally:
        _analysis_slots.release()


def _map_vision_to_scoring_evidence(
    vision_dict: dict[str, Any],
) -> ScoringEvidence:
    """Pass only explicit Task C gates; unsupported feature values remain unavailable."""
    image_quality = vision_dict.get("image_quality")
    image_quality = image_quality if isinstance(image_quality, dict) else {}
    issues = image_quality.get("issues")
    issue_names = set(issues) if isinstance(issues, list) and all(
        isinstance(issue, str) for issue in issues
    ) else set()

    surface_type_data = vision_dict.get("surface_type")
    surface_type_data = surface_type_data if isinstance(surface_type_data, dict) else {}
    surface_type = surface_type_data.get("value")
    if not isinstance(surface_type, str) or surface_type not in {
        "asphalt_bituminous",
        "cement_concrete",
    }:
        surface_type = "unknown"

    usable = image_quality.get("usable")
    return ScoringEvidence(
        surface_type=surface_type,
        capture_profile=None,
        image_quality_usable=usable if isinstance(usable, bool) else None,
        usable_region_adequate=None,
        resolution_adequate=(
            "effective_resolution_below_minimum" not in issue_names
            if isinstance(issues, list)
            else None
        ),
        components={},
    )


@router.post("/image-analyses", response_model=ImageAnalysisResult)
async def analyze_image_endpoint(image: UploadFile = File(...)) -> ImageAnalysisResult:
    """Analyze an uploaded image and return an unrated result until evidence is sufficient."""
    started = time.perf_counter()
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=422, detail="Upload is not a valid supported image MIME type (JPEG, PNG, WebP).")
    try:
        image_bytes = await image.read(MAX_IMAGE_BYTES + 1)
    except OSError as exc:
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.") from exc
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB upload limit.")

    try:
        vision_result = await run_in_threadpool(_bounded_analysis, image_bytes, image.filename or "upload")
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    actual_format = (vision_result.get("image") or {}).get("format")
    expected_format = {"image/jpeg": "jpeg", "image/png": "png", "image/webp": "webp"}[image.content_type]
    if actual_format != expected_format:
        raise HTTPException(status_code=422, detail="Declared image MIME type differs from decoded image format.")

    scoring_result = score_surface_quality(
        _map_vision_to_scoring_evidence(vision_result),
        config=DEFAULT_SCORING_CONFIG,
    )
    analysis_status: Literal["completed", "low_confidence", "unrated"]
    if scoring_result.rsqi.status == "unrated":
        analysis_status = "unrated"
    elif scoring_result.rsqi.status == "low_confidence":
        analysis_status = "low_confidence"
    else:
        analysis_status = "completed"

    raw_errors = vision_result.get("processing_errors")
    processing_errors = raw_errors if isinstance(raw_errors, list) else []
    return ImageAnalysisResult(
        analysis_id=f"img-{uuid.uuid4().hex[:12]}",
        analysis_status=analysis_status,
        image=vision_result.get("image"),
        image_quality=vision_result.get("image_quality"),
        pavement_region=vision_result.get("pavement_region"),
        surface_type=vision_result.get("surface_type"),
        aggregate_analysis=vision_result.get("aggregate_analysis"),
        defects=vision_result.get("defects"),
        texture_features=vision_result.get("texture_features"),
        rsqi=scoring_result.rsqi,
        quality_label=scoring_result.quality_label,
        scoring_version=scoring_result.scoring_version,
        mode_suitability=scoring_result.mode_suitability,
        data_provenance=vision_result.get("data_provenance") or [],
        model=vision_result.get("model"),
        processing_errors=processing_errors,
        visual_distress=assess_visual_distress(vision_result),
        calibration=vision_result.get("calibration"),
        metal_fragments=vision_result.get("metal_fragments"),
        processing_time_ms={**vision_result.get("processing_time_ms", {}), "api_total": round((time.perf_counter() - started) * 1000, 3)},
    )


@router.get("/vision-readiness")
def vision_readiness() -> dict[str, Any]:
    """Actually load the configured checkpoint; liveness stays independent."""
    from app.services.vision import _load_detector, _load_segmentation_model
    result: dict[str, Any] = {"ready": False, "detector": {"status": "not_configured"}, "roi": {"status": "not_configured"}}
    for key, loader in (("detector", _load_detector), ("roi", _load_segmentation_model)):
        try:
            model = loader()
            if model is not None:
                metadata = getattr(model, "checkpoint_metadata", None)
                if key == "roi" and metadata:
                    metadata = {name: value for name, value in metadata.items() if name in {"sha256", "model_version", "training_country", "pretrained_weights_used", "selected_epoch", "heldout_evaluation"}}
                result[key] = {"status": "loaded", "model_version": model.model_version,
                               "checkpoint": metadata, "confidence_calibrated": False}
        except Exception as exc:
            result[key] = {"status": "failed", "reason": "Configured model could not be loaded; check local setup/provenance.", "error_type": type(exc).__name__}
    result["ready"] = result["detector"]["status"] == "loaded"
    return result
