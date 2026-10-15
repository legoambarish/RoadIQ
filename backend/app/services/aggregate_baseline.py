"""Transparent, untrained image-texture baseline for aggregate-rich regions.

This module identifies high-frequency texture candidates only. It does not separate
individual stones, identify pavement pixels, or produce calibrated confidence.
"""

from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from app.services.india_road_segmentation import encode_binary_mask_rle

METHOD = "pillow_high_frequency_texture_regions_v1"
MAX_ANALYSIS_EDGE = 512
MAX_ANNOTATION_EDGE = 1024


def _otsu_threshold(gray: Image.Image) -> int:
    histogram = gray.histogram()
    total = sum(histogram)
    if not total:
        return 255
    weighted_total = sum(index * count for index, count in enumerate(histogram))
    background_weight = 0
    background_sum = 0
    best_variance = -1.0
    threshold = 255
    for value, count in enumerate(histogram):
        background_weight += count
        if background_weight == 0:
            continue
        foreground_weight = total - background_weight
        if foreground_weight == 0:
            break
        background_sum += value * count
        mean_background = background_sum / background_weight
        mean_foreground = (weighted_total - background_sum) / foreground_weight
        variance = background_weight * foreground_weight * (mean_background - mean_foreground) ** 2
        if variance > best_variance:
            best_variance = variance
            threshold = value
    return threshold


def _bbox(mask: Image.Image) -> dict[str, int] | None:
    bounds = mask.getbbox()
    if bounds is None:
        return None
    left, top, right, bottom = bounds
    return {"x_min": left, "y_min": top, "x_max": right, "y_max": bottom}


def _boundary_length(mask: Image.Image) -> int:
    pixels = mask.convert("L").tobytes()
    width, height = mask.size
    # Horizontal and vertical foreground/background transitions, including image edges.
    perimeter = 0
    for y in range(height):
        row = y * width
        for x in range(width):
            if pixels[row + x] == 0:
                continue
            perimeter += int(x == 0 or pixels[row + x - 1] == 0)
            perimeter += int(x == width - 1 or pixels[row + x + 1] == 0)
            perimeter += int(y == 0 or pixels[row - width + x] == 0)
            perimeter += int(y == height - 1 or pixels[row + width + x] == 0)
    return perimeter


def _annotated_data_uri(image: Image.Image, mask: Image.Image) -> str:
    preview = image.copy()
    scale = min(1.0, MAX_ANNOTATION_EDGE / max(preview.size))
    if scale < 1:
        size = (max(1, round(preview.width * scale)), max(1, round(preview.height * scale)))
        preview = preview.resize(size, Image.Resampling.BILINEAR)
        mask = mask.resize(size, Image.Resampling.NEAREST)
    tint = Image.new("RGBA", preview.size, (255, 190, 40, 105))
    tint.putalpha(mask.point(lambda pixel: 105 if pixel else 0))
    annotated = Image.alpha_composite(preview.convert("RGBA"), tint)
    draw = ImageDraw.Draw(annotated)
    draw.rectangle((8, 8, min(348, annotated.width - 1), 34), fill=(20, 28, 30, 220))
    draw.text((14, 14), "TEXTURE CANDIDATE · NOT PARTICLE SEGMENTATION", fill=(255, 255, 255, 255))
    buffer = io.BytesIO()
    annotated.convert("RGB").save(buffer, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def analyze_aggregate_texture_regions(image: Image.Image) -> dict[str, Any]:
    """Return conservative image-space texture candidates, never an aggregate count."""
    rgb = image.convert("RGB")
    scale = min(1.0, MAX_ANALYSIS_EDGE / max(rgb.size))
    analysis = rgb if scale == 1 else rgb.resize(
        (max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale))),
        Image.Resampling.BILINEAR,
    )
    gray = ImageOps.grayscale(analysis)
    high_frequency = ImageChops.difference(gray, gray.filter(ImageFilter.GaussianBlur(radius=2)))
    threshold = max(8, _otsu_threshold(high_frequency))
    candidate = high_frequency.point(lambda pixel: 255 if pixel > threshold else 0)
    # Remove isolated single-pixel noise and close tiny gaps without inventing instances.
    candidate = candidate.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    candidate_pixels = candidate.histogram()[255]
    area = candidate.width * candidate.height
    bbox = _bbox(candidate)
    if scale == 1:
        bbox_source = bbox
    elif bbox is None:
        bbox_source = None
    else:
        bbox_source = {
            "x_min": max(0, round(bbox["x_min"] / scale)),
            "y_min": max(0, round(bbox["y_min"] / scale)),
            "x_max": min(rgb.width, round(bbox["x_max"] / scale)),
            "y_max": min(rgb.height, round(bbox["y_max"] / scale)),
        }
    ratio = candidate_pixels / area if area else 0.0
    return {
        "segmentation_status": "estimated",
        "analysis_type": "aggregate_rich_surface_region_candidates",
        "method": METHOD,
        "training_status": "untrained_baseline",
        "individual_particles_segmented": False,
        "aggregate_count": {"value": None, "unit": "aggregates_per_image", "status": "unavailable", "source": None,
                             "reason": "texture regions do not separate individual particles"},
        "aggregate_count_per_m2": {"value": None, "unit": "aggregates_per_m2", "status": "unavailable", "source": None,
                                    "reason": "requires individual instances, calibration, and usable physical area"},
        "surface_region": {
            "mask_rle": encode_binary_mask_rle(candidate, "texture_candidate"),
            "bbox_xyxy_px": bbox_source,
            "source_image_size_px": [rgb.height, rgb.width],
            "mask_size_px": [candidate.height, candidate.width],
            "candidate_area_px": candidate_pixels,
            "candidate_area_ratio": round(ratio, 6),
            "confidence": None,
            "confidence_status": "uncalibrated",
            "pixel_boundary_length": _boundary_length(candidate),
        },
        "size_distribution": {"value": None, "unit": "pixel_distribution", "status": "unavailable", "source": None,
                              "reason": "individual aggregate boundaries are not identified"},
        "physical_size_distribution": {"value": None, "unit": "mm_distribution", "status": "unavailable", "source": None,
                                       "reason": "requires validated instances and calibration"},
        "visible_coverage_ratio": {"value": None, "unit": "ratio", "status": "unavailable", "source": None,
                                   "reason": "candidate texture is not aggregate coverage"},
        "boundary_gap_statistics": {"value": None, "unit": "pixel_statistics", "status": "unavailable", "source": None,
                                    "reason": "individual particle boundaries and gaps are not resolved"},
        "physical_boundary_gap_statistics": {"value": None, "unit": "mm_statistics", "status": "unavailable", "source": None,
                                             "reason": "requires validated gap segmentation and calibration"},
        "aggregate_loss_indicator": {"value": None, "unit": "damage_index_0_100", "status": "unavailable", "source": None,
                                     "reason": "no validated aggregate-loss method or labels are available"},
        "physical_measurements": "unavailable_without_validated_instances_and_calibration",
        "limitations": [
            "Texture candidates are not confirmed pavement or aggregate regions.",
            "The baseline has no learned weights and has not been evaluated on held-out labeled images.",
            "No individual aggregate count, size, coverage, gap, or physical measurement is produced.",
        ],
        "annotated_image_data_uri": _annotated_data_uri(rgb, candidate),
    }
