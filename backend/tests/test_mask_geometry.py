from PIL import Image
import pytest

from app.services.mask_geometry import semantic_mask_geometry


def test_mask_grid_area_and_boundary_are_not_box_area():
    mask = Image.new("L", (10, 10), 0)
    mask.putpixel((1, 1), 255)
    mask.putpixel((1, 2), 255)
    mask.putpixel((2, 2), 255)
    road = Image.new("L", (10, 10), 255)
    result = semantic_mask_geometry(mask, road)
    assert result["segmented_area_px"] == 3
    assert result["grid_boundary_length_px"] == 8
    assert result["image_projected_fraction"] == .03
    assert result["affected_pavement_pixel_fraction"] == .03
    assert result["physical_area_m2"] is None
    assert result["physical_depth_mm"] is None
    assert result["component_count_is_instance_count"] is False


def test_empty_roi_has_no_ratio_and_clipped_mask_has_explicit_flag():
    mask = Image.new("L", (10, 10), 0)
    mask.putpixel((0, 0), 255)
    result = semantic_mask_geometry(mask, Image.new("L", (10, 10), 0))
    assert result["affected_pavement_pixel_fraction"] is None
    assert result["edge_clipped"] is True
    assert result["grid_boundary_length_px"] == 4


def test_mismatched_mask_coordinate_systems_are_rejected():
    with pytest.raises(ValueError, match="same source coordinates"):
        semantic_mask_geometry(Image.new("L", (10, 10)), Image.new("L", (20, 20)))
