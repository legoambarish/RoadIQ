"""India-only semantic road and pothole segmentation baseline.

The optional PyTorch dependency is imported only when training or loading weights.
The dataset adapter reads the e-Yantra/IIT Bombay Indian Roads directory layout and
keeps its published train/validation sequence split intact.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
from typing import Any

from PIL import Image

MODEL_NAME = "RoadIQ India road/pothole segmentation baseline"
MODEL_VERSION = "indian-roads-unet-v1"
CLASS_NAMES = ("road", "footpath", "shallow", "pothole")
EXTENDED_CLASS_NAMES = CLASS_NAMES + ("background_unobserved",)
SOURCE_LABEL_TO_MODEL_ID = {0: 0, 2: 1, 3: 2, 4: 3}
IGNORE_LABEL = 255
DEFAULT_INPUT_SIZE = (512, 288)  # width, height
LETTERBOX_MODE = "letterbox_bilinear_rgb_nearest_mask_v1"
DATASET_ID = "eyantraiit/semantic-segmentation-datasets-of-indian-roads"
DATASET_LICENSE = "GPL-2.0 (as reported by the public Kaggle dataset metadata)"


def _torch() -> Any:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "PyTorch is required for the India road segmentation baseline. "
            "Install a PyTorch build compatible with the available hardware."
        ) from exc
    return torch


def encode_binary_mask_rle(mask: Image.Image, foreground_label: str) -> dict[str, Any]:
    """Encode a binary PIL mask as row-major alternating background/foreground runs."""
    binary = mask.convert("L")
    counts: list[int] = []
    current = 0
    run_length = 0
    for pixel in binary.tobytes():
        value = 1 if pixel else 0
        if value == current:
            run_length += 1
        else:
            counts.append(run_length)
            run_length = 1
            current = value
    counts.append(run_length)
    return {
        "encoding": "row_major_binary_rle_v1",
        "size_px": [binary.height, binary.width],
        "foreground_label": foreground_label,
        "counts": counts,
    }


def letterbox_pair(image: Image.Image, size: tuple[int, int], mask: Image.Image | None = None):
    """Keep aspect ratio; padding 254 is a synthetic ignore sentinel, not source 255."""
    width, height = size
    scale = min(width / image.width, height / image.height)
    resized = (max(1, min(width, round(image.width * scale))), max(1, min(height, round(image.height * scale))))
    left, top = (width - resized[0]) // 2, (height - resized[1]) // 2
    rgb = Image.new("RGB", size, (0, 0, 0))
    rgb.paste(image.convert("RGB").resize(resized, Image.Resampling.BILINEAR), (left, top))
    target = None
    if mask is not None:
        if mask.size != image.size:
            raise ValueError("image/mask source coordinates differ")
        target = Image.new("L", size, 254)
        target.paste(mask.convert("L").resize(resized, Image.Resampling.NEAREST), (left, top))
    geometry = {"method": LETTERBOX_MODE, "source_size_px": list(image.size), "input_size_px": list(size),
                "resized_size_px": list(resized), "padding_ltrb_px": [left, top, width - resized[0] - left, height - resized[1] - top],
                "actual_scale_xy": [resized[0] / image.width, resized[1] / image.height],
                "mask_projection": "crop padding, argmax on model grid, nearest-neighbor resize to source; no physical scale"}
    return rgb, target, geometry


class IndianRoadMaskDataset:
    """PIL/PyTorch dataset for an extracted directory containing Raw_images and Masks."""

    def __init__(self, root: str | Path, split: str, size: tuple[int, int] = DEFAULT_INPUT_SIZE, *, include_background: bool = False, preserve_aspect: bool = False) -> None:
        if split not in {"train", "val"}:
            raise ValueError("split must be 'train' or 'val'; the source has no independent test split")
        self.root = Path(root).expanduser().resolve()
        self.split = split
        self.size = size
        self.include_background = include_background
        self.preserve_aspect = preserve_aspect
        masks_root = self.root / "Masks" / split
        mask_paths = sorted(masks_root.rglob("*_gtFine_labelTrainIds.png"))
        if not mask_paths:
            raise FileNotFoundError(f"No Indian-road masks found under {masks_root}")
        self.pairs: list[tuple[Path, Path]] = []
        missing: list[Path] = []
        for mask_path in mask_paths:
            stem = mask_path.name.removesuffix("_gtFine_labelTrainIds.png")
            sequence = mask_path.parent.name
            image_path = self.root / "Raw_images" / split / sequence / f"{stem}_leftImg8bit.jpg"
            if image_path.is_file():
                self.pairs.append((image_path, mask_path))
            else:
                missing.append(image_path)
        if missing:
            sample = ", ".join(str(path) for path in missing[:3])
            raise ValueError(f"{len(missing)} masks have no matching raw image; examples: {sample}")

    def __len__(self) -> int:
        return len(self.pairs)

    def sequence_ids(self) -> set[str]:
        return {image_path.parent.name for image_path, _ in self.pairs}

    def __getitem__(self, index: int) -> tuple[Any, Any]:
        torch = _torch()
        image_path, mask_path = self.pairs[index]
        width, height = self.size
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        with Image.open(mask_path) as source:
            source_mask = source.convert("L")
        if self.preserve_aspect:
            image, source_mask, _ = letterbox_pair(image, (width, height), source_mask)
        else:
            image = image.resize((width, height), Image.Resampling.BILINEAR)
            source_mask = source_mask.resize((width, height), Image.Resampling.NEAREST)

        image_tensor = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8)
        image_tensor = image_tensor.view(height, width, 3).permute(2, 0, 1).float().div_(255.0)
        source_tensor = torch.frombuffer(bytearray(source_mask.tobytes()), dtype=torch.uint8)
        source_tensor = source_tensor.view(height, width)
        target = torch.full_like(source_tensor, IGNORE_LABEL)
        for source_id, model_id in SOURCE_LABEL_TO_MODEL_ID.items():
            target[source_tensor == source_id] = model_id
        if self.include_background:
            target[source_tensor == 1] = 4
            # The acquired v2 labelTrainIds masks encode outside/background as
            # 255 (there are no ID=1 pixels). Preserve the legacy ignore policy
            # unless the explicit v2 source-background training mode is used.
            target[source_tensor == 255] = 4
        return image_tensor, target.long()


def create_unet(num_classes: int = len(CLASS_NAMES), base_channels: int = 16) -> Any:
    """Create a compact four-level U-Net without pretrained or external weights."""
    torch = _torch()
    nn = torch.nn
    functional = torch.nn.functional

    class ConvBlock(nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.layers = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            )

        def forward(self, tensor: Any) -> Any:
            return self.layers(tensor)

    class CompactUNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            channels = [base_channels * (2**level) for level in range(5)]
            self.encoder1 = ConvBlock(3, channels[0])
            self.encoder2 = ConvBlock(channels[0], channels[1])
            self.encoder3 = ConvBlock(channels[1], channels[2])
            self.encoder4 = ConvBlock(channels[2], channels[3])
            self.bottleneck = ConvBlock(channels[3], channels[4])
            self.pool = nn.MaxPool2d(2)
            self.up4 = nn.ConvTranspose2d(channels[4], channels[3], kernel_size=2, stride=2)
            self.decoder4 = ConvBlock(channels[4], channels[3])
            self.up3 = nn.ConvTranspose2d(channels[3], channels[2], kernel_size=2, stride=2)
            self.decoder3 = ConvBlock(channels[3], channels[2])
            self.up2 = nn.ConvTranspose2d(channels[2], channels[1], kernel_size=2, stride=2)
            self.decoder2 = ConvBlock(channels[2], channels[1])
            self.up1 = nn.ConvTranspose2d(channels[1], channels[0], kernel_size=2, stride=2)
            self.decoder1 = ConvBlock(channels[1], channels[0])
            self.classifier = nn.Conv2d(channels[0], num_classes, kernel_size=1)

        @staticmethod
        def _join(upsampled: Any, skip: Any) -> Any:
            if upsampled.shape[-2:] != skip.shape[-2:]:
                upsampled = functional.interpolate(
                    upsampled, size=skip.shape[-2:], mode="bilinear", align_corners=False
                )
            return torch.cat((upsampled, skip), dim=1)

        def forward(self, tensor: Any) -> Any:
            level1 = self.encoder1(tensor)
            level2 = self.encoder2(self.pool(level1))
            level3 = self.encoder3(self.pool(level2))
            level4 = self.encoder4(self.pool(level3))
            center = self.bottleneck(self.pool(level4))
            decoded4 = self.decoder4(self._join(self.up4(center), level4))
            decoded3 = self.decoder3(self._join(self.up3(decoded4), level3))
            decoded2 = self.decoder2(self._join(self.up2(decoded3), level2))
            decoded1 = self.decoder1(self._join(self.up1(decoded2), level1))
            return self.classifier(decoded1)

    return CompactUNet()


class IndiaRoadSegmentationModel:
    """Load a trained checkpoint and return image-sized labels and raw confidences."""

    model_name = MODEL_NAME
    model_version = MODEL_VERSION
    training_status = "trained_on_india_only_dataset"
    provider = "pytorch"
    input_size_px = {"width": DEFAULT_INPUT_SIZE[0], "height": DEFAULT_INPUT_SIZE[1]}

    def __init__(self, checkpoint_path: str | Path, device: str | None = None) -> None:
        torch = _torch()
        import os
        torch.set_num_threads(int(os.getenv("ROADIQ_TORCH_THREADS", "4")))
        self.torch = torch
        self.path = Path(checkpoint_path).expanduser().resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"India segmentation checkpoint does not exist: {self.path}")
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        checkpoint = torch.load(self.path, map_location=self.device, weights_only=True)
        if checkpoint.get("format_version") not in (1, 2) or checkpoint.get("class_names") not in (list(CLASS_NAMES), list(EXTENDED_CLASS_NAMES)):
            raise ValueError("Checkpoint format or India-road class map is unsupported.")
        self.checkpoint_metadata = checkpoint.get("metadata", {})
        with self.path.open("rb") as source:
            self.checkpoint_metadata = {**self.checkpoint_metadata, "sha256": hashlib.file_digest(source, "sha256").hexdigest()}
        if checkpoint.get("format_version") == 2:
            import json
            if checkpoint.get("class_names") != list(EXTENDED_CLASS_NAMES) or self.checkpoint_metadata.get("training_country") != "India" or self.checkpoint_metadata.get("pretrained_weights_used") is not False:
                raise ValueError("v2 segmentation provenance/class map is unsupported")
            evaluation = json.loads((self.path.parent / "roi-evaluation.json").read_text(encoding="utf-8"))
            if evaluation.get("checkpoint_sha256") != self.checkpoint_metadata["sha256"] or evaluation.get("manifest_sha256") != self.checkpoint_metadata.get("split_audit", {}).get("manifest_sha256"):
                raise ValueError("v2 segmentation checkpoint/evaluation identity mismatch")
            heldout_keys = (
                "images", "evaluation_split", "metrics_at_model_input_resolution",
                "metrics_at_source_resolution", "road_or_pothole_roi_iou_source_resolution",
            )
            self.checkpoint_metadata["heldout_evaluation"] = {
                key: evaluation[key] for key in heldout_keys if key in evaluation
            }
        self.class_names = tuple(checkpoint["class_names"])
        self.preprocessing = self.checkpoint_metadata.get("input_preprocessing", "legacy_stretch_v1")
        if self.preprocessing not in ("legacy_stretch_v1", LETTERBOX_MODE):
            raise ValueError("unsupported segmentation preprocessing")
        self.model_version = self.checkpoint_metadata.get("model_version", "indian-roads-unet-v2") if len(self.class_names) == 5 else MODEL_VERSION
        self.input_size_px = self.checkpoint_metadata.get("input_size_px", self.input_size_px)
        if any(not isinstance(self.input_size_px.get(key), int) or not 16 <= self.input_size_px[key] <= 2048 for key in ("width", "height")):
            raise ValueError("unsupported segmentation input dimensions")
        self.network = create_unet(
            num_classes=len(self.class_names),
            base_channels=int(checkpoint.get("base_channels", 16)),
        ).to(self.device)
        self.network.load_state_dict(checkpoint["state_dict"], strict=True)
        self.network.eval()

    def predict(self, image: Image.Image) -> dict[str, Any]:
        torch = self.torch
        width, height = image.size
        input_width, input_height = self.input_size_px["width"], self.input_size_px["height"]
        geometry = None
        if self.preprocessing == LETTERBOX_MODE:
            resized, _, geometry = letterbox_pair(image, (input_width, input_height))
        else:
            resized = image.convert("RGB").resize((input_width, input_height), Image.Resampling.BILINEAR)
        tensor = torch.frombuffer(bytearray(resized.tobytes()), dtype=torch.uint8)
        tensor = tensor.view(input_height, input_width, 3).permute(2, 0, 1).float().div_(255.0).unsqueeze(0)
        with torch.inference_mode():
            logits = self.network(tensor.to(self.device))
            if geometry:
                left, top, right, bottom = geometry["padding_ltrb_px"]
                logits = logits[:, :, top:input_height - bottom, left:input_width - right]
            else:
                logits = torch.nn.functional.interpolate(
                    logits, size=(height, width), mode="bilinear", align_corners=False
                )
            probabilities = torch.softmax(logits, dim=1)[0]
            labels_device = probabilities.argmax(dim=0)
            confidence = probabilities.max(dim=0).values.mean().item()
            class_confidence = {
                name: float(probabilities[index][labels_device == index].mean().item())
                for index, name in enumerate(self.class_names)
                if bool((labels_device == index).any())
            }
            labels = labels_device.to(torch.uint8).cpu().contiguous()
        label_image = Image.frombytes("L", (labels.shape[1], labels.shape[0]), labels.numpy().tobytes())
        if geometry:
            label_image = label_image.resize((width, height), Image.Resampling.NEAREST)
        return {
            "mask": label_image,
            "confidence_raw_mean": float(confidence),
            "class_confidence_raw_mean": class_confidence,
            "confidence_calibrated": False,
            "preprocessing_geometry": geometry,
            "confidence_resolution": "unpadded model grid" if geometry else "source resolution",
        }
