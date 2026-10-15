from __future__ import annotations

import io

import pytest
from PIL import Image

from app.schemas.image_analysis import BinaryRLEMask, ImageAnalysisResponse
from app.services.india_road_segmentation import (
    IGNORE_LABEL,
    IndianRoadMaskDataset,
    create_unet,
    encode_binary_mask_rle,
)
from app.services.vision import analyze_road_image, reset_detector_for_tests


def test_binary_rle_round_trip_and_contract_validation() -> None:
    mask = Image.new("L", (4, 2), 0)
    mask.putdata([0, 255, 255, 0, 0, 0, 255, 0])
    encoded = encode_binary_mask_rle(mask, "pothole")
    validated = BinaryRLEMask.model_validate(encoded)
    assert validated.size_px == (2, 4)
    assert validated.counts == [1, 2, 3, 1, 1]
    with pytest.raises(ValueError, match="cover exactly"):
        BinaryRLEMask.model_validate({**encoded, "counts": [7]})


def test_dataset_pairs_by_stem_and_maps_india_mask_ids(tmp_path) -> None:
    pytest.importorskip("torch")
    root = tmp_path
    sequence = "train-seq"
    image_dir = root / "Raw_images" / "train" / sequence
    mask_dir = root / "Masks" / "train" / sequence
    image_dir.mkdir(parents=True)
    mask_dir.mkdir(parents=True)
    Image.new("RGB", (32, 16), (20, 30, 40)).save(image_dir / "frame_leftImg8bit.jpg")
    Image.new("L", (32, 16)).save(mask_dir / "frame_gtFine_labelTrainIds.png")
    mask = Image.new("L", (32, 16))
    mask.putdata([0, 2, 3, 4, 255] * (32 * 16 // 5) + [255])
    mask.save(mask_dir / "frame_gtFine_labelTrainIds.png")

    dataset = IndianRoadMaskDataset(root, "train", size=(32, 16))
    image, target = dataset[0]
    assert image.shape == (3, 16, 32)
    assert target[0, :5].tolist() == [0, 1, 2, 3, IGNORE_LABEL]
    assert dataset.sequence_ids() == {sequence}


def test_unet_forward_preserves_input_resolution() -> None:
    torch = pytest.importorskip("torch")
    model = create_unet(base_channels=2).eval()
    with torch.inference_mode():
        output = model(torch.zeros((1, 3, 32, 48)))
    assert output.shape == (1, 4, 32, 48)


def test_segmentation_inference_returns_rle_and_keeps_instance_count_unavailable() -> None:
    class FakeSegmentationModel:
        model_name = "fixture segmenter"
        model_version = "fixture-1"
        training_status = "fixture"
        provider = "mock"
        path = "fixture.pt"
        device = "cpu"
        input_size_px = {"width": 4, "height": 3}

        def predict(self, image: Image.Image) -> dict[str, object]:
            labels = Image.new("L", image.size, 1)
            labels.putpixel((0, 0), 0)
            labels.putpixel((1, 0), 3)
            return {
                "mask": labels,
                "class_confidence_raw_mean": {"pothole": 0.62},
                "confidence_calibrated": False,
            }

    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), "gray").save(buffer, format="PNG")
    report = analyze_road_image(buffer.getvalue(), segmentation_model=FakeSegmentationModel())
    ImageAnalysisResponse.model_validate(report)
    pothole = next(item for item in report["defects"] if item["class"] == "pothole")
    assert report["aggregate_analysis"]["surface_region"]["road_roi_applied"] is True
    assert report["aggregate_analysis"]["analysis_type"] == "road_roi_gated_texture_candidates"
    assert report["pavement_region"]["mask_rle"]["foreground_label"] == "road"
    assert pothole["mask_rle"]["foreground_label"] == "pothole"
    assert pothole["count"]["value"] is None
    assert pothole["visible_area_ratio"]["value"] == pytest.approx(1 / 120000, abs=1e-8)
    assert pothole["confidence"] == pytest.approx(0.62)


def test_missing_segmentation_checkpoint_is_reported_without_masks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROADIQ_VISION_MODEL_PATH", raising=False)
    monkeypatch.setenv("ROADIQ_SEGMENTATION_MODEL_PATH", "/missing/india-segmenter.pt")
    reset_detector_for_tests()
    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), "gray").save(buffer, format="PNG")
    report = analyze_road_image(buffer.getvalue())
    ImageAnalysisResponse.model_validate(report)
    assert report["model"]["segmentation"]["load_status"] == "failed"
    assert report["processing_errors"][0]["code"] == "segmentation_model_load_failed"
    assert report["pavement_region"]["mask_rle"] is None
    pothole = next(item for item in report["defects"] if item["class"] == "pothole")
    assert pothole["mask_rle"] is None
    assert pothole["count"]["value"] is None
    reset_detector_for_tests()
