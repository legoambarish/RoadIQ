"""Road-image validation and inference boundary for Task C.

The service returns observations only. It never calculates an RSQI or infers physical
measurements from pixels. Production inference is unavailable until an India-only
checkpoint is reviewed and configured; detector injection is retained for tests.
"""

from __future__ import annotations

import hashlib
import io
import math
import os
import threading
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from app.schemas.image_analysis import ImageAnalysisResponse
from app.services.aggregate_baseline import analyze_aggregate_texture_regions
from app.services.india_road_segmentation import (
    IndiaRoadSegmentationModel,
    encode_binary_mask_rle,
)
from app.services.mask_geometry import semantic_mask_geometry


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGE_EDGE = 10_000
MIN_IMAGE_WIDTH = 320
MIN_IMAGE_HEIGHT = 240
MODEL_NAME = "India-only road-damage model (not configured)"
MODEL_REPO = "dronefreak/rdd2022-rfdetr-nano"
MODEL_REVISION = "66429f39b916e56c6a33243d776718088f5f43ad"
MODEL_SHA256 = "2d1fba21b829ebc42f7c74f76285d97b2e3295aebe8d97e497d0cc186be98cc9"
MODEL_VERSION = f"{MODEL_REPO}@{MODEL_REVISION}"
MODEL_CLASSES = ("longitudinal_crack", "transverse_crack", "alligator_crack", "pothole")
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
TEXTURE_METHOD = "tile_grayscale_contrast_v1"


class ImageValidationError(ValueError):
    """An uploaded file is not a supported, safely decodable road image."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class VisionInferenceError(RuntimeError):
    """Reserved for callers that need an explicit inference-boundary exception type."""


class RoadDamageDetector(Protocol):
    """Small adapter interface; tests can provide a deterministic fake detector."""

    model_name: str
    model_version: str
    training_status: str

    def predict(self, image: Image.Image, threshold: float) -> Any: ...


@dataclass(frozen=True)
class ImageCalibration:
    """Optional user calibration; image hashes prevent applying it to another upload."""

    method: str
    pixels_per_mm: float
    usable_area_m2: float
    image_sha256: str
    verified: bool = False


_detector: RoadDamageDetector | None = None
_detector_lock = threading.Lock()
_segmentation_model: IndiaRoadSegmentationModel | None = None
_segmentation_lock = threading.Lock()
_detector_key: tuple[str, str, str] | None = None
_segmentation_key: tuple[str, str | None] | None = None


def _load_detector() -> RoadDamageDetector | None:
    """Reject the pinned legacy checkpoint until an India-only model is configured."""
    global _detector, _detector_key
    india_path = os.getenv("ROADIQ_DETECTOR_MODEL_PATH")
    if india_path:
        device = os.getenv("ROADIQ_DETECTOR_DEVICE", "cpu")
        tiles = os.getenv("ROADIQ_DETECTOR_TILE_SIZE", "0")
        key = (str(Path(india_path).expanduser().resolve()), device, tiles)
        with _detector_lock:
            if _detector is None or _detector_key != key:
                from app.services.india_detector import IndiaRoadDamageDetector
                _detector = IndiaRoadDamageDetector(india_path, device=device, tile_size=int(tiles))
                _detector_key = key
            return _detector
    model_path = os.getenv("ROADIQ_VISION_MODEL_PATH")
    if not model_path:
        return None
    with _detector_lock:
        try:
            path = Path(model_path).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"Configured model checkpoint does not exist: {path}")
            digest = hashlib.sha256()
            with path.open("rb") as checkpoint_file:
                for chunk in iter(lambda: checkpoint_file.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != MODEL_SHA256:
                raise ValueError("Configured checkpoint does not match the pinned legacy road-damage checkpoint.")
            raise ValueError(
                "The pinned checkpoint was trained on a multinational dataset and is disabled by the India-only data policy. "
                "No India-only road-damage checkpoint is currently configured."
            )
        except Exception as exc:  # model/runtime errors become structured processing errors
            raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc


def _load_segmentation_model() -> IndiaRoadSegmentationModel | None:
    """Load the optional India-only road/pothole baseline from a local checkpoint."""
    global _segmentation_model, _segmentation_key
    model_path = os.getenv("ROADIQ_SEGMENTATION_MODEL_PATH")
    if not model_path:
        return None
    with _segmentation_lock:
        device = os.getenv("ROADIQ_SEGMENTATION_DEVICE")
        key = (str(Path(model_path).expanduser().resolve()), device)
        if _segmentation_model is not None and _segmentation_key == key:
            return _segmentation_model
        _segmentation_model = IndiaRoadSegmentationModel(model_path, device=device)
        _segmentation_key = key
        return _segmentation_model


def reset_detector_for_tests() -> None:
    """Clear lazy model singletons so tests can verify load failures independently."""
    global _detector, _segmentation_model, _detector_key, _segmentation_key
    with _detector_lock:
        _detector = None
        _detector_key = None
    with _segmentation_lock:
        _segmentation_model = None
        _segmentation_key = None


def _measurement(
    value: Any | None,
    unit: str,
    *,
    source: str | None = None,
    reason: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    if status is None:
        status = "unavailable" if value is None else "estimated"
    if status == "unavailable":
        value, source = None, None
    return {"value": value, "unit": unit, "status": status, "source": source, "reason": reason}


def _validate_and_decode(image_bytes: bytes) -> tuple[Image.Image, str, tuple[int, int]]:
    if not isinstance(image_bytes, bytes) or not image_bytes:
        raise ImageValidationError("empty_image", "The image upload is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ImageValidationError("image_too_large", f"Image exceeds the {MAX_IMAGE_BYTES}-byte upload limit.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image_bytes)) as source:
                image_format = (source.format or "").upper()
                if image_format not in {"JPEG", "PNG", "WEBP"}:
                    raise ImageValidationError("unsupported_image_type", "Only JPEG, PNG, and WebP images are supported.")
                if getattr(source, "is_animated", False) or getattr(source, "n_frames", 1) > 1:
                    raise ImageValidationError("unsupported_animation", "Only a single still image frame is supported.")
                width, height = source.size
                if width <= 0 or height <= 0:
                    raise ImageValidationError("invalid_dimensions", "Image dimensions must be positive.")
                if width > MAX_IMAGE_EDGE or height > MAX_IMAGE_EDGE or width * height > MAX_IMAGE_PIXELS:
                    raise ImageValidationError("image_dimensions_too_large", "Image dimensions exceed the configured safety limits.")
                source.verify()
            with Image.open(io.BytesIO(image_bytes)) as source:
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.info["roadiq_stored_size"] = (width, height)
                image.info["roadiq_exif_orientation"] = source.getexif().get(274, 1)
                return image.copy(), image_format, image.size
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ImageValidationError("corrupt_image", "The upload is not a valid, decodable image.") from exc


def _quality_report(image: Image.Image) -> dict[str, Any]:
    width, height = image.size
    gray = ImageOps.grayscale(_analysis_view(image, 1024))
    mean_luma = float(ImageStat.Stat(gray).mean[0])
    edge_view = gray.filter(ImageFilter.FIND_EDGES)
    if min(gray.size) > 8:
        edge_view = edge_view.crop((2, 2, gray.width - 2, gray.height - 2))
    edge_variance = float(ImageStat.Stat(edge_view).var[0])
    histogram = gray.histogram()
    clipped_bright = sum(histogram[250:]) / (gray.width * gray.height)
    clipped_dark = sum(histogram[:6]) / (gray.width * gray.height)
    issues: list[str] = []
    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
        issues.append("effective_resolution_below_minimum")
    if mean_luma < 12:
        issues.append("severely_underexposed")
    elif mean_luma > 245:
        issues.append("severely_overexposed")
    if edge_variance < 3:
        issues.append("very_low_edge_detail_possible_blur_or_uniform_surface")
    if clipped_bright > 0.15:
        issues.append("substantial_saturated_highlights_possible_glare")
    if clipped_dark > 0.5:
        issues.append("substantial_shadow_or_dark_pixels")
    usable = not any(issue in issues for issue in ("effective_resolution_below_minimum", "severely_underexposed", "severely_overexposed"))
    return {
        "status": "observed",
        "issues": issues,
        "usable": usable,
        "source": "image_inference",
        "metrics": {
            "width_px": width,
            "height_px": height,
            "mean_luma_0_255": round(mean_luma, 3),
            "edge_detail_variance_proxy": round(edge_variance, 3),
            "saturated_highlight_ratio": round(clipped_bright, 6),
            "near_black_ratio": round(clipped_dark, 6),
        },
        "limitations": ["Heuristic quality gates have not been validated on labelled RoadIQ images."],
    }


def _texture_report(image: Image.Image) -> dict[str, Any]:
    gray = ImageOps.grayscale(_analysis_view(image, 512))
    width, height = gray.size
    tile = max(8, min(width, height) // 16)
    values: list[float] = []
    for top in range(0, height - tile + 1, tile):
        for left in range(0, width - tile + 1, tile):
            crop = gray.crop((left, top, left + tile, top + tile))
            values.append(float(ImageStat.Stat(crop).stddev[0]))
    if not values:
        return {"features": [{"name": TEXTURE_METHOD, **_measurement(None, "grayscale_intensity_std_0_255", reason="insufficient_pixels")}], "is_physical_roughness": False}
    return {
        "features": [{
            "name": TEXTURE_METHOD,
            **_measurement(round(sum(values) / len(values), 4), "grayscale_intensity_std_0_255", source="image_inference", reason="image-derived proxy; not calibrated to physical roughness"),
            "method_version": "1",
        }],
        "is_physical_roughness": False,
    }


def _analysis_view(image: Image.Image, max_edge: int) -> Image.Image:
    """Bound heuristic CPU/memory cost independently of the upload's full resolution."""
    width, height = image.size
    scale = min(1.0, max_edge / max(width, height))
    if scale == 1.0:
        return image
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(size, Image.Resampling.BILINEAR)


def _empty_aggregate_report(reason: str) -> dict[str, Any]:
    return {
        "aggregate_count": _measurement(None, "aggregates_per_image", reason=reason),
        "aggregate_count_per_m2": _measurement(None, "aggregates_per_m2", reason="requires aggregate instances, calibrated ground scale, and usable physical area"),
        "size_distribution": _measurement(None, "pixel_distribution", reason=reason),
        "physical_size_distribution": _measurement(None, "mm_distribution", reason="requires validated aggregate segmentation and per-image calibration"),
        "visible_coverage_ratio": _measurement(None, "ratio", reason=reason),
        "boundary_gap_statistics": _measurement(None, "pixel_statistics", reason=reason),
        "physical_boundary_gap_statistics": _measurement(None, "mm_statistics", reason="requires validated gap segmentation and per-image calibration"),
        "aggregate_loss_indicator": _measurement(None, "damage_index_0_100", reason=reason),
        "segmentation_status": "unavailable",
    }


def _class_name(class_id: Any, class_names: Any) -> str:
    if isinstance(class_id, str):
        return class_id.strip().lower().replace(" ", "_")
    try:
        index = int(class_id)
    except (TypeError, ValueError):
        return "unknown"
    if isinstance(class_names, dict):
        return str(class_names.get(index, class_names.get(str(index), "unknown"))).strip().lower().replace(" ", "_")
    if isinstance(class_names, (list, tuple)) and 0 <= index < len(class_names):
        return str(class_names[index]).strip().lower().replace(" ", "_")
    return MODEL_CLASSES[index] if 0 <= index < len(MODEL_CLASSES) else "unknown"


def _prediction_rows(predictions: Any) -> tuple[list[tuple[str, float, list[float]]], Any]:
    """Normalize RF-DETR/ supervision detections without coupling callers to that package."""
    class_ids = getattr(predictions, "class_id", None)
    confidences = getattr(predictions, "confidence", None)
    boxes = getattr(predictions, "xyxy", None)
    if class_ids is None or confidences is None or boxes is None:
        raise ValueError("detector output must expose class_id, confidence, and xyxy arrays")
    if not (len(class_ids) == len(confidences) == len(boxes)):
        raise ValueError("detector output arrays must have matching lengths")
    class_names = getattr(predictions, "class_names", None)
    if class_names is None:
        class_names = getattr(predictions, "names", None)
    rows: list[tuple[str, float, list[float]]] = []
    for class_id, confidence, box in zip(class_ids, confidences, boxes):
        name = _class_name(class_id, class_names)
        score = float(confidence)
        coords = [float(value) for value in box]
        if len(coords) != 4 or not math.isfinite(score) or not 0 <= score <= 1 or not all(math.isfinite(value) for value in coords):
            continue
        rows.append((name, score, coords))
    return rows, class_names


def _detection_objects(rows: list[tuple[str, float, list[float]]], width: int, height: int) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {"crack": [], "pothole": []}
    for model_class, confidence, raw_box in rows:
        if model_class in {"longitudinal_crack", "transverse_crack", "alligator_crack", "crack", "d00", "d10", "d20"}:
            canonical_class = "crack"
        elif model_class in {"pothole", "d40"}:
            canonical_class = "pothole"
        else:
            continue
        x_min = max(0.0, min(float(width), raw_box[0]))
        y_min = max(0.0, min(float(height), raw_box[1]))
        x_max = max(0.0, min(float(width), raw_box[2]))
        y_max = max(0.0, min(float(height), raw_box[3]))
        if x_max <= x_min or y_max <= y_min:
            continue
        output[canonical_class].append({
            "class": canonical_class,
            "model_label": model_class,
            "confidence": round(confidence, 6),
            "confidence_kind": "raw_model_score",
            "coordinate_system": "exif_oriented_source_pixels",
            "box_extent_width_px": round(x_max - x_min, 4),
            "box_extent_height_px": round(y_max - y_min, 4),
            "edge_clipped": x_min <= 0 or y_min <= 0 or x_max >= width or y_max >= height,
            "small_box_resolution": min(x_max - x_min, y_max - y_min) < 4,
            "bbox_xyxy_px": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
            "bbox_xyxy_normalized": {
                "x_min": round(x_min / width, 8),
                "y_min": round(y_min / height, 8),
                "x_max": round(x_max / width, 8),
                "y_max": round(y_max / height, 8),
            },
        })
    return output


def _defect_report(
    detections: dict[str, list[dict[str, Any]]],
    detector_available: bool,
    reason: str | None,
    segmentation_output: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for class_name in ("crack", "pothole", "raveling", "other_visible_deterioration"):
        supported = class_name in {"crack", "pothole"}
        observed = detector_available and supported
        class_detections = detections.get(class_name, [])
        count = len(class_detections) if observed else None
        confidence = (sum(item["confidence"] for item in class_detections) / len(class_detections)) if class_detections else None
        measurement_reason = None if observed else (reason or f"the configured checkpoint does not detect {class_name}")
        result.append({
            "class": class_name,
            "count": _measurement(count, "defects_per_image", source="image_inference" if observed else None, reason=measurement_reason, status="observed" if observed else "unavailable"),
            "visible_area_ratio": _measurement(None, "ratio", reason="bounding boxes do not provide a validated visible-area mask"),
            "confidence": round(confidence, 6) if confidence is not None else None,
            "annotation": _measurement(None, "uri", reason="annotated image storage is not part of the Task C service"),
            "detections": class_detections,
            "mask_rle": None,
        })
    if segmentation_output is not None:
        pothole = next(item for item in result if item["class"] == "pothole")
        pothole["visible_area_ratio"] = _measurement(
            segmentation_output["pothole_area_ratio"],
            "ratio",
            source="image_inference",
            status="estimated",
            reason="semantic predicted pixel fraction of the full image; not calibrated to physical pavement area",
        )
        pothole["mask_rle"] = segmentation_output["pothole_mask_rle"]
        pothole["mask_geometry"] = segmentation_output.get("pothole_geometry")
        if not detector_available:
            pothole["count"] = _measurement(
                None,
                "defects_per_image",
                reason="semantic masks do not separate pothole instances; count is unavailable",
            )
            raw_confidence = segmentation_output.get("pothole_confidence_raw")
            pothole["confidence"] = raw_confidence
    return result


def _unavailable_metal_fragments() -> dict[str, Any]:
    return {
        "class": "metal_fragment",
        "count": _measurement(None, "fragments_per_image", reason="no validated metal-fragment detector is configured"),
        "visible_area_ratio": _measurement(None, "ratio", reason="no validated metal-fragment mask is available"),
        "confidence": None,
        "annotation": _measurement(None, "uri", reason="annotated-image storage is not part of the Task C service"),
        "detections": [],
        "mask_rle": None,
    }


def _calibration_report(calibration: ImageCalibration | dict[str, Any] | None, image_sha256: str) -> dict[str, Any]:
    if calibration is None:
        return {"status": "unavailable", "method": None, "verified": False, "image_sha256": image_sha256, "reason": "no per-image ground-scale calibration was supplied"}
    try:
        candidate = calibration if isinstance(calibration, ImageCalibration) else ImageCalibration(**calibration)
        valid = (
            candidate.verified
            and bool(candidate.method.strip())
            and math.isfinite(candidate.pixels_per_mm)
            and candidate.pixels_per_mm > 0
            and math.isfinite(candidate.usable_area_m2)
            and candidate.usable_area_m2 > 0
            and candidate.image_sha256.lower() == image_sha256
        )
        reason = None if valid else "calibration must be verified, positive, and bound to this exact image checksum"
        return {
            "status": "observed" if valid else "unavailable",
            "method": candidate.method if valid else None,
            "pixels_per_mm": candidate.pixels_per_mm if valid else None,
            "usable_area_m2": candidate.usable_area_m2 if valid else None,
            "verified": valid,
            "image_sha256": image_sha256,
            "reason": reason,
        }
    except (TypeError, ValueError, AttributeError):
        return {"status": "unavailable", "method": None, "verified": False, "image_sha256": image_sha256, "reason": "calibration metadata is invalid"}


def analyze_road_image(
    image_bytes: bytes,
    *,
    source_name: str = "unknown",
    calibration: ImageCalibration | dict[str, Any] | None = None,
    detector: RoadDamageDetector | None = None,
    segmentation_model: Any | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Validate and analyze a road image; return the Task C observation payload.

    Task D's route should pass the uploaded file bytes and optional calibration here. The
    function does not accept paths or remote URLs, and it never computes a quality score.
    """
    if not math.isfinite(confidence_threshold) or not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")
    analysis_started = time.perf_counter()
    detector_ms: float | None = None
    segmentation_ms: float | None = None
    image, image_format, (width, height) = _validate_and_decode(image_bytes)
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()
    quality = _quality_report(image)
    calibration_data = _calibration_report(calibration, image_sha256)
    processing_errors: list[dict[str, Any]] = []
    actual_detector = detector
    detector_error: str | None = None
    if actual_detector is None:
        try:
            actual_detector = _load_detector()
        except Exception as exc:
            detector_error = str(exc)
            processing_errors.append({
                "code": "model_load_failed",
                "message": "The configured road-damage model could not be loaded.",
                "details": type(exc).__name__,
                "retryable": False,
            })
    quality_issues = quality.get("issues", [])
    low_resolution_preview = (
        quality["usable"] is False
        and isinstance(quality_issues, list)
        and set(quality_issues) == {"effective_resolution_below_minimum"}
        and min(width, height) >= 240
        and max(width, height) >= 320
    )
    inference_allowed = quality["usable"] or low_resolution_preview
    detector_available = actual_detector is not None and quality["usable"]
    detector_inference_completed = False
    actual_segmentation_model = segmentation_model
    segmentation_error: str | None = None
    if actual_segmentation_model is None:
        try:
            actual_segmentation_model = _load_segmentation_model()
        except Exception as exc:
            segmentation_error = f"{type(exc).__name__}: {exc}"
            processing_errors.append({
                "code": "segmentation_model_load_failed",
                "message": "The configured India road segmentation model could not be loaded.",
                "details": type(exc).__name__,
                "retryable": False,
            })
    segmentation_output: dict[str, Any] | None = None
    road_roi_mask: Image.Image | None = None
    if actual_segmentation_model is not None and inference_allowed:
        try:
            segmentation_started = time.perf_counter()
            prediction = actual_segmentation_model.predict(image)
            segmentation_ms = round((time.perf_counter() - segmentation_started) * 1000, 3)
            label_mask = prediction.get("mask") if isinstance(prediction, dict) else None
            if not isinstance(label_mask, Image.Image) or label_mask.size != image.size:
                raise ValueError("segmentation output must contain an image-sized PIL label mask")
            label_mask = label_mask.convert("L")
            road_mask = label_mask.point(lambda value: 255 if value == 0 else 0)
            road_roi_mask = road_mask
            pothole_mask = label_mask.point(lambda value: 255 if value == 3 else 0)
            # Source 'shallow' is not independently established as drivable
            # pavement. Exclude it, footpath and source background from this ROI.
            usable_pavement_mask = label_mask.point(lambda value: 255 if value in (0, 3) else 0)
            road_pixels = road_mask.histogram()[255]
            pothole_pixels = pothole_mask.histogram()[255]
            class_confidence = prediction.get("class_confidence_raw_mean") or {}
            raw_confidence = class_confidence.get("pothole") if isinstance(class_confidence, dict) else None
            if raw_confidence is not None:
                raw_confidence = float(raw_confidence)
                if not math.isfinite(raw_confidence) or not 0 <= raw_confidence <= 1:
                    raw_confidence = None
            segmentation_output = {
                "road_area_ratio": round(road_pixels / (width * height), 8),
                "road_mask_rle": encode_binary_mask_rle(road_mask, "road"),
                "pothole_area_ratio": round(pothole_pixels / (width * height), 8),
                "pothole_mask_rle": encode_binary_mask_rle(pothole_mask, "pothole"),
                "pothole_confidence_raw": raw_confidence,
                "confidence_raw_mean": prediction.get("confidence_raw_mean"),
                "confidence_calibrated": prediction.get("confidence_calibrated", False),
                "preprocessing_geometry": prediction.get("preprocessing_geometry"),
                "pothole_geometry": semantic_mask_geometry(pothole_mask, usable_pavement_mask),
                "pavement_including_potholes_mask_rle": encode_binary_mask_rle(usable_pavement_mask, "road_or_pothole"),
            }
            evaluation = getattr(actual_segmentation_model, "checkpoint_metadata", {}).get("heldout_evaluation", {})
            mask_iou = evaluation.get("metrics_at_model_input_resolution", {}).get("iou_by_class", {}).get("pothole")
            if isinstance(mask_iou, (int, float)) and math.isfinite(mask_iou):
                segmentation_output["pothole_geometry"]["heldout_pothole_iou_model_input_resolution"] = mask_iou
                segmentation_output["pothole_geometry"]["heldout_images"] = evaluation.get("images")
                segmentation_output["pothole_geometry"]["limitations"].append(
                    "Source-heldout model-input pothole IoU is reported with this prediction; area outputs are experimental and are not validated measurements.")
        except Exception as exc:
            road_roi_mask = None
            segmentation_error = f"{type(exc).__name__}: {exc}"
            processing_errors.append({
                "code": "segmentation_inference_failed",
                "message": "India road segmentation failed; ROI and mask-derived values are unavailable.",
                "details": type(exc).__name__,
                "retryable": False,
            })
    detections = {"crack": [], "pothole": []}
    if actual_detector is not None and inference_allowed:
        try:
            detector_started = time.perf_counter()
            raw = actual_detector.predict(image, confidence_threshold)
            detector_ms = round((time.perf_counter() - detector_started) * 1000, 3)
            rows, _ = _prediction_rows(raw)
            rows = [row for row in rows if row[1] >= confidence_threshold]
            detections = _detection_objects(rows, width, height)
            detector_inference_completed = True
            for class_detections in detections.values():
                for index, detection in enumerate(class_detections):
                    detection["instance_id"] = f"{image_sha256[:12]}-{detection['class']}-{index + 1}"
        except Exception as exc:
            detector_available = False
            detector_error = f"{type(exc).__name__}: {exc}"
            processing_errors.append({
                "code": "inference_failed",
                "message": "Road-damage inference failed; defect values are unavailable.",
                "details": type(exc).__name__,
                "retryable": False,
            })
    unavailable_reason = "image quality gate failed" if not quality["usable"] else (
        detector_error or "no road-damage checkpoint is configured" if actual_detector is None else detector_error
    )
    defects = _defect_report(detections, detector_available, unavailable_reason, segmentation_output)
    segmentation_metadata = {
        "name": getattr(actual_segmentation_model, "model_name", MODEL_NAME) if actual_segmentation_model else None,
        "version": getattr(actual_segmentation_model, "model_version", "not_configured") if actual_segmentation_model else "not_configured",
        "training_status": getattr(actual_segmentation_model, "training_status", "not_reported") if actual_segmentation_model else "not_reported",
        "provider": getattr(actual_segmentation_model, "provider", "pytorch") if actual_segmentation_model else None,
        "checkpoint": ({key: value for key, value in getattr(actual_segmentation_model, "checkpoint_metadata", {}).items()
                       if key in {"sha256", "model_version", "training_country", "pretrained_weights_used",
                                  "selected_epoch", "validation_metrics", "heldout_evaluation"}}
                       if actual_segmentation_model else None),
        "runtime": {"device": str(getattr(actual_segmentation_model, "device", "unknown"))} if actual_segmentation_model else None,
        "preprocessing_geometry": segmentation_output.get("preprocessing_geometry") if segmentation_output else None,
        "input_size_px": getattr(actual_segmentation_model, "input_size_px", None) if actual_segmentation_model else None,
        "dataset_id": "eyantraiit/semantic-segmentation-datasets-of-indian-roads" if actual_segmentation_model else None,
        "dataset_license": "GPL-2.0 (reported by public Kaggle metadata)" if actual_segmentation_model else None,
        "confidence_calibrated": False if actual_segmentation_model else None,
        "load_status": "loaded" if actual_segmentation_model else ("failed" if segmentation_error else "not_configured"),
    }
    model = {
        "name": getattr(actual_detector, "model_name", MODEL_NAME) if actual_detector else MODEL_NAME,
        "version": getattr(actual_detector, "model_version", MODEL_VERSION) if actual_detector else "not_configured",
        "training_status": getattr(actual_detector, "training_status", "pretrained_baseline") if actual_detector else "not_reported",
        "provider": getattr(actual_detector, "provider", "injected detector") if actual_detector is not None else None,
        "checkpoint": getattr(actual_detector, "checkpoint_metadata", None) if actual_detector is not None else None,
        "runtime": getattr(actual_detector, "runtime_metadata", None) if actual_detector is not None else None,
        "input_size_px": getattr(actual_detector, "input_size_px", None) if actual_detector is not None else None,
        "confidence_threshold": confidence_threshold,
        "load_status": "loaded" if actual_detector else ("failed" if detector_error else "not_configured"),
        "inference_status": (
            "completed" if detector_available else
            "limited_quality" if detector_inference_completed else
            "quality_blocked" if not quality["usable"] else "unavailable"
        ),
        "confidence_calibrated": False,
        "segmentation": segmentation_metadata,
        "aggregate_analysis": {
            "name": "Pillow high-frequency texture-region baseline",
            "version": "pillow_high_frequency_texture_regions_v1",
            "training_status": "untrained_baseline",
            "confidence_calibrated": False,
        },
    }
    model_observed = actual_detector is not None and detector_inference_completed
    surface_reason = "no validated asphalt/concrete classifier is configured"
    aggregate_reason = "no validated individual-aggregate segmentation model is configured"
    aggregate_started = time.perf_counter()
    aggregate_analysis = (
        analyze_aggregate_texture_regions(image, pavement_mask=road_roi_mask)
        if quality["usable"]
        else _empty_aggregate_report("image quality gate failed")
    )
    annotated_image_data_uri = aggregate_analysis.pop("annotated_image_data_uri", None)
    if quality["usable"]:
        aggregate_analysis["inference_time_ms"] = round((time.perf_counter() - aggregate_started) * 1000, 3)
    payload: dict[str, Any] = {
        "analysis_status": "unrated",
        "image": {
            "source_name": (source_name.replace("\\", "/").rsplit("/", 1)[-1] or "unknown")[:128],
            "format": image_format.lower(),
            "width_px": width,
            "height_px": height,
            "size_bytes": len(image_bytes),
            "sha256": image_sha256,
            "coordinate_system": "exif_oriented_source_pixels",
            "stored_size_px": list(image.info.get("roadiq_stored_size", (width, height))),
            "exif_orientation": image.info.get("roadiq_exif_orientation", 1),
        },
        "image_quality": quality,
        "pavement_region": {
            "usable_area_ratio": (
                _measurement(
                    segmentation_output["road_area_ratio"],
                    "ratio",
                    source="image_inference",
                    status="estimated",
                    reason="predicted road-pixel fraction; semantic road class may include adjacent paved areas",
                )
                if segmentation_output is not None
                else _measurement(None, "ratio", reason="no validated pavement-region segmentation model is configured")
            ),
            "annotation": _measurement(None, "uri", reason="mask storage is not part of the Task C service; use inline mask_rle"),
            "mask_rle": segmentation_output["road_mask_rle"] if segmentation_output is not None else None,
            "usable_pavement_including_potholes_mask_rle": segmentation_output["pavement_including_potholes_mask_rle"] if segmentation_output is not None else None,
        },
        "surface_type": {
            "value": "unknown",
            "unit": "category",
            "status": "unavailable",
            "source": None,
            "confidence": None,
            "reason": surface_reason,
        },
        "aggregate_analysis": aggregate_analysis,
        "defects": defects,
        "metal_fragments": _unavailable_metal_fragments(),
        "texture_features": _texture_report(image),
        "calibration": calibration_data,
        "annotated_image": _measurement(
            annotated_image_data_uri,
            "uri",
            source="image_inference" if annotated_image_data_uri else None,
            status="estimated" if annotated_image_data_uri else "unavailable",
            reason=("inline data URI annotates high-frequency texture candidates only; not particle segmentation"
                    if annotated_image_data_uri else "image quality gate failed"),
        ),
        "processing_errors": processing_errors,
        "model": model,
        "data_provenance": [
            {"field_path": "image_quality", "source": "image_inference"},
            {"field_path": "texture_features", "source": "image_inference"},
            *([{"field_path": "aggregate_analysis.surface_region", "source": "image_inference"}] if quality["usable"] else []),
            *([{"field_path": "defects", "source": "image_inference"}] if model_observed else []),
            *([{"field_path": "pavement_region", "source": "image_inference"}] if segmentation_output is not None else []),
        ],
        "processing_time_ms": {"total": round((time.perf_counter() - analysis_started) * 1000, 3),
                               "detector": detector_ms, "segmentation": segmentation_ms},
    }
    # Defect-only inference cannot yield the complete RoadIQ evidence required for a rating.
    if not quality["usable"]:
        payload["analysis_status"] = "unrated"
    return ImageAnalysisResponse.model_validate(payload).model_dump(by_alias=True)


def infer_road_defects(image_bytes: bytes, *, source_name: str = "unknown") -> dict[str, Any]:
    """Compatibility entry point for callers of the original placeholder function."""
    return analyze_road_image(image_bytes, source_name=source_name)
