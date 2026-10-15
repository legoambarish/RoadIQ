from __future__ import annotations

from PIL import Image, ImageDraw

from app.services.aggregate_baseline import analyze_aggregate_texture_regions


def _decode_mask(rle: dict[str, object]) -> Image.Image:
    counts = rle["counts"]
    size = rle["size_px"]
    assert isinstance(counts, list) and isinstance(size, list)
    pixels = bytearray()
    foreground = 0
    for count in counts:
        pixels.extend([255 if foreground else 0] * count)
        foreground = 255 - foreground
    return Image.frombytes("L", (size[1], size[0]), bytes(pixels))


def test_optional_road_roi_gates_texture_candidates_and_is_reported() -> None:
    image = Image.new("RGB", (160, 120), (90, 90, 90))
    draw = ImageDraw.Draw(image)
    for x in range(0, 160, 8):
        draw.line((x, 0, x, 119), fill=(x % 255, 160, 80), width=2)

    road_roi = Image.new("L", image.size, 0)
    ImageDraw.Draw(road_roi).rectangle((0, 0, 79, 119), fill=255)
    result = analyze_aggregate_texture_regions(image, pavement_mask=road_roi)
    mask = _decode_mask(result["surface_region"]["mask_rle"])

    assert result["analysis_type"] == "road_roi_gated_texture_candidates"
    assert result["surface_region"]["road_roi_applied"] is True
    assert mask.crop((80, 0, 160, 120)).getbbox() is None
    assert mask.crop((0, 0, 80, 120)).getbbox() is not None
    assert "configured semantic road mask" in result["limitations"][-1]

