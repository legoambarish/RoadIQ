import base64
import io

from PIL import Image

from scripts.create_demo_road_image import create_synthetic_road_image
from app.services.vision import analyze_road_image


def test_synthetic_demo_image_is_deterministic_and_inference_sized() -> None:
    first = create_synthetic_road_image(seed=123)
    second = create_synthetic_road_image(seed=123)

    assert first.size == (640, 480)
    assert first.mode == "RGB"
    assert first.tobytes() == second.tobytes()


def test_synthetic_demo_image_runs_through_analysis_and_emits_annotation() -> None:
    image = create_synthetic_road_image(seed=42)
    source = io.BytesIO()
    image.save(source, format="PNG")

    report = analyze_road_image(source.getvalue(), source_name="synthetic-road-demo.png")

    assert report["analysis_status"] == "unrated"
    assert report["image"]["source_name"] == "synthetic-road-demo.png"
    assert report["aggregate_analysis"]["training_status"] == "untrained_baseline"
    assert report["aggregate_analysis"]["aggregate_count"]["value"] is None
    assert report["annotated_image"]["value"].startswith("data:image/jpeg;base64,")


def test_large_image_annotation_is_downscaled_with_its_mask() -> None:
    image = create_synthetic_road_image(seed=42).resize((1600, 1200), Image.Resampling.BILINEAR)
    source = io.BytesIO()
    image.save(source, format="JPEG", quality=85)

    report = analyze_road_image(source.getvalue(), source_name="synthetic-large-road-demo.jpg")
    encoded = report["annotated_image"]["value"].partition(",")[2]
    with Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))) as preview:
        assert preview.size == (1024, 768)
