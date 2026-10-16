"""Image-projected semantic-mask geometry, never inferred from detection boxes."""
from __future__ import annotations

from typing import Any
from PIL import Image, ImageChops, ImageOps


def semantic_mask_geometry(mask: Image.Image, pavement: Image.Image | None = None) -> dict[str, Any]:
    binary = mask.convert("L").point(lambda value: 255 if value else 0)
    area = binary.histogram()[255]
    # Four-neighbor lattice edge perimeter, including boundaries at the image edge.
    padded = ImageOps.expand(binary, border=1, fill=0)
    w, h = padded.size
    vertical = ImageChops.difference(padded.crop((0, 1, w, h)), padded.crop((0, 0, w, h - 1)))
    horizontal = ImageChops.difference(padded.crop((1, 0, w, h)), padded.crop((0, 0, w - 1, h)))
    perimeter = vertical.histogram()[255] + horizontal.histogram()[255]
    components = None
    try:
        import cv2
        import numpy as np
        components = int(cv2.connectedComponents(np.asarray(binary), connectivity=8)[0] - 1)
    except ImportError:
        pass
    ratio, denominator = None, None
    if pavement is not None:
        if pavement.size != mask.size:
            raise ValueError("mask and pavement must use the same source coordinates")
        road = pavement.convert("L").point(lambda value: 255 if value else 0)
        denominator = road.histogram()[255]
        if denominator:
            ratio = ImageChops.multiply(binary, road).histogram()[255] / denominator
    bbox = binary.getbbox()
    return {"method": "semantic_mask_grid_geometry_v1", "coordinate_system": "exif_oriented_source_pixels",
            "measurement_status": "experimental_model_prediction", "physical_measurement_validated": False,
            "segmented_area_px": area, "image_projected_fraction": area / (mask.width * mask.height),
            "grid_boundary_length_px": perimeter, "connected_components_8": components,
            "component_count_is_instance_count": False, "bbox_xyxy_px": list(bbox) if bbox else None,
            "affected_pavement_pixel_fraction": ratio, "pavement_denominator_px": denominator,
            "edge_clipped": bool(bbox and (bbox[0] == 0 or bbox[1] == 0 or bbox[2] == mask.width or bbox[3] == mask.height)),
            "physical_area_m2": None, "physical_depth_mm": None, "crack_length_px": None,
            "uncertainty": None, "limitations": ["Predicted semantic pixels; not instance ground truth.",
                "Image projection and grid perimeter depend on viewpoint/resolution; not metric ground measurements.",
                "Pixel precision/uncertainty has not been calibrated."]}
