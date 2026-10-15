"""Prepare and train RoadIQ's experimental India-only road/pothole segmenter.

Run from backend/:
  python -m scripts.train_indian_road_segmentation prepare --archive /tmp/roadiq-indian-roads-v2.zip --output /tmp/roadiq-indian-roads
  python -m scripts.train_indian_road_segmentation train --data-root /tmp/roadiq-indian-roads --output /tmp/roadiq-india-road-unet.pt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZipFile

from PIL import Image

from app.services.india_road_segmentation import (
    CLASS_NAMES,
    DATASET_ID,
    DATASET_LICENSE,
    DEFAULT_INPUT_SIZE,
    IGNORE_LABEL,
    IndianRoadMaskDataset,
    create_unet,
)

ARCHIVE_PREFIX = "Indian_road_data/Indian_road_data/"


def prepare_archive(archive_path: Path, output_dir: Path) -> dict[str, int]:
    """Extract only raw Indian road images and semantic PNG masks, not the duplicate NumPy copy."""
    archive_path = archive_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {"images": 0, "masks": 0}
    with ZipFile(archive_path) as archive:
        for info in archive.infolist():
            name = info.filename
            if info.is_dir() or not name.startswith(ARCHIVE_PREFIX):
                continue
            relative = PurePosixPath(name[len(ARCHIVE_PREFIX):])
            if not relative.parts or relative.parts[0] not in {"Raw_images", "Masks"}:
                continue
            if relative.parts[0] == "Raw_images" and relative.suffix.lower() != ".jpg":
                continue
            if relative.parts[0] == "Masks" and not relative.name.endswith("_gtFine_labelTrainIds.png"):
                continue
            destination = (output_dir / Path(*relative.parts)).resolve()
            if not destination.is_relative_to(output_dir):
                raise ValueError(f"archive member escapes the output directory: {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            counts["images" if relative.parts[0] == "Raw_images" else "masks"] += 1
    if counts["images"] != counts["masks"]:
        raise ValueError(f"expected paired image/mask files, extracted {counts}")
    return counts


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _class_weights(dataset: IndianRoadMaskDataset) -> list[float]:
    counts = [0] * len(CLASS_NAMES)
    for _, mask_path in dataset.pairs:
        with Image.open(mask_path) as source:
            histogram = source.convert("L").histogram()
        for source_id, model_id in ((0, 0), (2, 1), (3, 2), (4, 3)):
            counts[model_id] += histogram[source_id]
    present = [count for count in counts if count]
    median = sorted(present)[len(present) // 2]
    weights = [min(8.0, max(0.25, median / count)) if count else 0.0 for count in counts]
    scale = sum(weight for weight in weights if weight) / sum(bool(weight) for weight in weights)
    return [weight / scale if weight else 0.0 for weight in weights]


def _limit_dataset(dataset: IndianRoadMaskDataset, maximum: int | None) -> None:
    if maximum is not None:
        if maximum < 1:
            raise ValueError("sample limits must be positive")
        dataset.pairs = dataset.pairs[:maximum]


def _update_confusion(confusion: Any, logits: Any, target: Any, torch: Any) -> None:
    predictions = logits.argmax(dim=1)
    valid = target != IGNORE_LABEL
    indices = target[valid] * len(CLASS_NAMES) + predictions[valid]
    confusion += torch.bincount(indices, minlength=len(CLASS_NAMES) ** 2).reshape(
        len(CLASS_NAMES), len(CLASS_NAMES)
    )


def _metrics(confusion: Any) -> dict[str, Any]:
    true_positive = confusion.diag().float()
    union = confusion.sum(dim=0) + confusion.sum(dim=1) - true_positive
    denominator = confusion.sum(dim=0) + confusion.sum(dim=1)
    iou = true_positive / union.clamp_min(1)
    dice = 2 * true_positive / denominator.clamp_min(1)
    return {
        "iou_by_class": {name: float(iou[index].item()) for index, name in enumerate(CLASS_NAMES)},
        "dice_by_class": {name: float(dice[index].item()) for index, name in enumerate(CLASS_NAMES)},
        "macro_iou": float(iou.mean().item()),
        "macro_dice": float(dice.mean().item()),
        "confusion_matrix_rows_true_columns_predicted": confusion.cpu().tolist(),
    }


def train(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError as exc:
        raise RuntimeError("Install a PyTorch build compatible with this machine before training.") from exc

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested, but this runner cannot access an NVIDIA device. "
            "Enable device passthrough or explicitly use --device cpu for a small smoke run."
        )
    device_name = "cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu"
    device = torch.device(device_name)
    if device.type == "cpu" and not args.allow_cpu:
        raise RuntimeError("Full training defaults to GPU; pass --allow-cpu only for an intentional CPU run.")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

    size = (args.width, args.height)
    train_data = IndianRoadMaskDataset(args.data_root, "train", size=size)
    val_data = IndianRoadMaskDataset(args.data_root, "val", size=size)
    overlap = train_data.sequence_ids() & val_data.sequence_ids()
    if overlap:
        raise ValueError(f"train/validation sequence leakage detected: {sorted(overlap)}")
    _limit_dataset(train_data, args.max_train_samples)
    _limit_dataset(val_data, args.max_val_samples)
    smoke = any(value is not None for value in (
        args.max_train_samples,
        args.max_val_samples,
        args.max_train_batches,
        args.max_val_batches,
    ))
    if args.epochs < 1 or args.batch_size < 1 or args.workers < 0 or args.base_channels < 1:
        raise ValueError("epochs, batch size, and base channels must be positive; workers cannot be negative")
    if args.width < 16 or args.height < 16 or args.width % 16 or args.height % 16:
        raise ValueError("training width and height must be positive multiples of 16")
    if args.learning_rate <= 0:
        raise ValueError("learning rate must be positive")
    for name in ("max_train_batches", "max_val_batches"):
        value = getattr(args, name)
        if value is not None and value < 1:
            raise ValueError(f"{name.replace('_', ' ')} must be positive")
    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_data,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=device.type == "cuda",
    )

    torch.manual_seed(args.seed)
    model = create_unet(base_channels=args.base_channels).to(device)
    class_weights = torch.tensor(_class_weights(train_data), dtype=torch.float32, device=device)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights, ignore_index=IGNORE_LABEL)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    best_macro_iou = -1.0
    last_epoch: dict[str, Any] = {}
    start = time.monotonic()
    archive_hash = _sha256(args.archive) if args.archive and not smoke else None

    print(json.dumps({
        "dataset": DATASET_ID,
        "license": DATASET_LICENSE,
        "train_images": len(train_data),
        "validation_images": len(val_data),
        "train_sequences": sorted(train_data.sequence_ids()),
        "validation_sequences": sorted(val_data.sequence_ids()),
        "input_size_px": {"width": args.width, "height": args.height},
        "device": device_name,
        "smoke_run": smoke,
        "class_loss_weights": class_weights.cpu().tolist(),
    }), flush=True)

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        train_batches = 0
        for batch_index, (images, targets) in enumerate(train_loader):
            if args.max_train_batches is not None and batch_index >= args.max_train_batches:
                break
            images, targets = images.to(device, non_blocking=True), targets.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, targets)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item())
            train_batches += 1

        model.eval()
        val_loss = 0.0
        val_batches = 0
        confusion = torch.zeros((len(CLASS_NAMES), len(CLASS_NAMES)), dtype=torch.int64, device=device)
        with torch.inference_mode():
            for batch_index, (images, targets) in enumerate(val_loader):
                if args.max_val_batches is not None and batch_index >= args.max_val_batches:
                    break
                images, targets = images.to(device, non_blocking=True), targets.to(device, non_blocking=True)
                logits = model(images)
                val_loss += float(criterion(logits, targets).item())
                val_batches += 1
                _update_confusion(confusion, logits, targets, torch)
        if train_batches == 0 or val_batches == 0:
            raise ValueError("training and validation need at least one batch each")
        last_epoch = {
            "epoch": epoch + 1,
            "train_loss": train_loss / train_batches,
            "validation_loss": val_loss / val_batches,
            **_metrics(confusion),
        }
        print(json.dumps(last_epoch), flush=True)
        if not smoke and last_epoch["macro_iou"] > best_macro_iou:
            best_macro_iou = last_epoch["macro_iou"]
            checkpoint = {
                "format_version": 1,
                "architecture": "compact_unet_4level",
                "base_channels": args.base_channels,
                "class_names": list(CLASS_NAMES),
                "state_dict": model.cpu().state_dict(),
                "metadata": {
                    "dataset_id": DATASET_ID,
                    "dataset_license": DATASET_LICENSE,
                    "source_archive_sha256": archive_hash,
                    "train_sequences": sorted(train_data.sequence_ids()),
                    "validation_sequences": sorted(val_data.sequence_ids()),
                    "input_size_px": {"width": args.width, "height": args.height},
                    "training_status": "trained_on_india_only_dataset",
                    "pretrained_weights_used": False,
                    "validation_metrics": last_epoch,
                    "class_weighting": "median_frequency_from_training_masks_v1",
                },
            }
            torch.save(checkpoint, output)
            model.to(device)
            print(json.dumps({"best_checkpoint": str(output), "best_validation_macro_iou": best_macro_iou}), flush=True)

    result = {
        "status": "smoke_only" if smoke else "completed",
        "device": device_name,
        "best_checkpoint": None if smoke else str(output),
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "last_validation": last_epoch,
        "evaluation_split": "published_validation",
        "warning": "Validation metrics are experimental and are not a final held-out test result.",
    }
    print(json.dumps(result), flush=True)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="extract only raw images and PNG masks from the dataset archive")
    prepare.add_argument("--archive", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    training = commands.add_parser("train", help="train and validate the compact India-only U-Net baseline")
    training.add_argument("--data-root", type=Path, required=True)
    training.add_argument("--output", type=Path, required=True)
    training.add_argument("--archive", type=Path, help="optional source ZIP for checkpoint provenance SHA-256")
    training.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    training.add_argument("--allow-cpu", action="store_true", help="allow slower full training on CPU")
    training.add_argument("--epochs", type=int, default=20)
    training.add_argument("--batch-size", type=int, default=8)
    training.add_argument("--workers", type=int, default=4)
    training.add_argument("--width", type=int, default=DEFAULT_INPUT_SIZE[0])
    training.add_argument("--height", type=int, default=DEFAULT_INPUT_SIZE[1])
    training.add_argument("--base-channels", type=int, default=16)
    training.add_argument("--learning-rate", type=float, default=1e-3)
    training.add_argument("--seed", type=int, default=42)
    training.add_argument("--max-train-samples", type=int)
    training.add_argument("--max-val-samples", type=int)
    training.add_argument("--max-train-batches", type=int, help="limits the run; prevents checkpoint saving")
    training.add_argument("--max-val-batches", type=int, help="limits the run; prevents checkpoint saving")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "prepare":
        counts = prepare_archive(args.archive, args.output)
        print(json.dumps({"extracted": counts, "data_root": str(args.output.resolve())}))
        return
    result = train(args)
    if result["status"] == "smoke_only":
        print("Smoke-run metrics are plumbing checks, not model-quality results.", file=sys.stderr)


if __name__ == "__main__":
    main()
