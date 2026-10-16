"""Train the existing compact U-Net with explicit background and untouched sequence test.

Version 2 explicitly learns source background/unannotated pixels (255). The final
published validation sequence is reserved as test before training; remaining
published validation sequences select checkpoints. No external pretraining.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from collections import Counter
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

from PIL import Image

from backend.scripts.prepare_rdd_india import HashTree, dhash, sha256
from app.services.india_road_segmentation import IndianRoadMaskDataset, EXTENDED_CLASS_NAMES, create_unet, IGNORE_LABEL, LETTERBOX_MODE


def metrics_from_confusion(confusion):
    values = confusion.double()
    diagonal = values.diag()
    union = values.sum(0) + values.sum(1) - diagonal
    denominator = values.sum(0) + values.sum(1)
    return {"iou_by_class": {name: float(diagonal[i] / union[i]) if union[i] else None for i, name in enumerate(EXTENDED_CLASS_NAMES)},
            "dice_by_class": {name: float(2 * diagonal[i] / denominator[i]) if denominator[i] else None for i, name in enumerate(EXTENDED_CLASS_NAMES)},
            "macro_iou": float((diagonal[union > 0] / union[union > 0]).mean()),
            "confusion_matrix_rows_true_columns_predicted": confusion.cpu().tolist()}


def prepare_splits(root: Path, output: Path, size: tuple[int, int], *, preserve_aspect=False):
    train = IndianRoadMaskDataset(root, "train", size, include_background=True, preserve_aspect=preserve_aspect)
    validation = IndianRoadMaskDataset(root, "val", size, include_background=True, preserve_aspect=preserve_aspect)
    test = IndianRoadMaskDataset(root, "val", size, include_background=True, preserve_aspect=preserve_aspect)
    sequences = sorted(validation.sequence_ids())
    if len(sequences) < 2 or train.sequence_ids() & validation.sequence_ids():
        raise ValueError("need disjoint train/validation and at least two validation sequences")
    test_sequence = sequences[-1]
    test.pairs = [(im, mask) for im, mask in test.pairs if im.parent.name == test_sequence]
    validation.pairs = [(im, mask) for im, mask in validation.pairs if im.parent.name != test_sequence]
    rows, excluded, tree, retained = [], [], HashTree(), []
    counts = Counter()
    for split, dataset in (("train", train), ("validation", validation), ("test", test)):
        pairs = []
        for image_path, mask_path in dataset.pairs:
            with Image.open(image_path) as image:
                perceptual = dhash(image)
                dimensions = image.size
            with Image.open(mask_path) as mask:
                if mask.size != dimensions:
                    raise ValueError("ROI image/mask coordinates differ")
                observed = set(mask.convert("L").getdata())
                if observed - {0, 1, 2, 3, 4, 255}:
                    raise ValueError(f"unexpected source mask IDs: {observed}")
            neighbors = tree.neighbors(perceptual)
            cross = [i for i in neighbors if retained[i]["split"] != split]
            if cross:
                excluded.append({"image_id": image_path.stem, "split": split, "reason": "cross_split_dhash_le4", "matches": [retained[i]["image_id"] for i in cross]})
                continue
            row = {"image_id": image_path.stem, "image_path": image_path.relative_to(root).as_posix(),
                   "label_path": mask_path.relative_to(root).as_posix(), "split": split, "scene_group": image_path.parent.name,
                   "source": "e-Yantra IIT Bombay Indian Roads v2", "geography": "India", "license": "GPL-2.0 (source metadata)",
                   "image_sha256": sha256(image_path), "label_sha256": sha256(mask_path), "dhash64": f"{perceptual:016x}"}
            tree.add(perceptual, len(retained))
            retained.append(row)
            rows.append(row)
            pairs.append((image_path, mask_path))
            counts[split] += 1
        dataset.pairs = pairs
    manifest = output / "roi-manifest.jsonl"
    if manifest.exists():
        raise FileExistsError("ROI manifest identity already exists; use a new experiment output")
    manifest.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    report = {"counts": dict(counts), "manifest_sha256": sha256(manifest), "test_sequence": test_sequence,
              "train_sequences": sorted(train.sequence_ids()), "validation_sequences": sorted(validation.sequence_ids()),
              "test_sequences": sorted(test.sequence_ids()), "cross_split_exclusions": excluded,
              "duplicate_audit_complete": True, "grouping": "published sequences; final validation sequence reserved for test",
              "limitation": "Only seven source sequences; no independent field collection or physical measurements."}
    (output / "roi-split-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"event": "roi_splits_frozen", **report}), flush=True)
    return train, validation, test, report


def run(args):
    import torch
    from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
    torch.set_num_threads(4)
    torch.manual_seed(args.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("This full ROI experiment requires CUDA")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    train, validation, test, audit = prepare_splits(args.data.resolve(), output, (args.width, args.height), preserve_aspect=args.preserve_aspect)
    if min(len(train), len(validation), len(test)) < 20:
        raise ValueError("too few independently grouped ROI samples")
    classes = len(EXTENDED_CLASS_NAMES)
    histogram = [0] * classes
    positive_images = []
    for _, path in train.pairs:
        with Image.open(path) as source:
            bins = source.convert("L").histogram()
        positive_images.append(bins[4] > 0)
        for source_id, model_id in ((0, 0), (2, 1), (3, 2), (4, 3), (1, 4)):
            histogram[model_id] += bins[source_id]
        histogram[4] += bins[255]
    present = sorted(x for x in histogram if x)
    median = present[len(present) // 2]
    weights = [min(8, max(.25, median / value)) if value else 0 for value in histogram]
    weights[3] = max(weights[3], args.pothole_weight_min)
    weights = torch.tensor(weights, device="cuda", dtype=torch.float32)
    network = create_unet(classes, args.base_channels).cuda()
    optimizer = torch.optim.AdamW(network.parameters(), lr=.001, weight_decay=.0001)
    criterion = torch.nn.CrossEntropyLoss(weight=weights, ignore_index=IGNORE_LABEL)
    scaler = torch.amp.GradScaler("cuda")
    loaders = {name: DataLoader(dataset, batch_size=args.batch, shuffle=name == "train", num_workers=0, pin_memory=True)
               for name, dataset in (("train", train), ("validation", validation), ("test", test))}
    if args.positive_repeat > 1:
        class AugmentedTraining(Dataset):
            def __len__(self):
                return len(train)

            def __getitem__(self, index):
                image, target = train[index]
                if torch.rand(()).item() < .5:
                    image, target = image.flip(-1), target.flip(-1)
                image = (image * (.85 + .3 * torch.rand(()).item())).clamp(0, 1)
                return image, target
        sampler = WeightedRandomSampler([args.positive_repeat if positive else 1 for positive in positive_images], len(train), replacement=True)
        loaders["train"] = DataLoader(AugmentedTraining(), batch_size=args.batch, sampler=sampler, num_workers=0, pin_memory=True)
    metadata = {"dataset_id": "eyantraiit/semantic-segmentation-datasets-of-indian-roads", "dataset_license": "GPL-2.0 (public metadata)",
                "model_version": args.name, "training_country": "India", "pretrained_weights_used": False,
                "input_size_px": {"width": args.width, "height": args.height}, "split_audit": audit,
                "seed": args.seed, "batch": args.batch, "epochs_requested": args.epochs, "hardware": torch.cuda.get_device_name(0),
                "python": platform.python_version(), "torch": str(torch.__version__), "class_loss_weights": weights.cpu().tolist(),
                "positive_image_sampling_weight": args.positive_repeat, "positive_training_images": sum(positive_images),
                "dice_loss_weight": args.dice_weight, "training_augmentation": "horizontal flip + brightness .85-1.15" if args.positive_repeat > 1 else "none",
                "source_label_mapping": {"0": "road", "1": "background_unobserved (absent)", "2": "footpath", "3": "shallow", "4": "pothole", "255": "background_unobserved"},
                "background_policy": "Source card includes backgrounds; acquired 255 outside regions are learned as source background/unannotated, not a verified occlusion taxonomy. Legacy v1 continues to ignore 255.",
                "confidence_calibrated": False, "training_status": "trained_on_india_only_dataset"}
    metadata["input_preprocessing"] = LETTERBOX_MODE if args.preserve_aspect else "legacy_stretch_v1"
    metadata["padding_policy"] = "Synthetic source sentinel 254 -> target ignore 255 in loss and evaluation; real source 255 remains background class 4" if args.preserve_aspect else "no padding"
    start, best = time.monotonic(), -1.0

    def evaluate(loader):
        confusion = torch.zeros((classes, classes), dtype=torch.int64, device="cuda")
        network.eval()
        with torch.inference_mode():
            for images, targets in loader:
                targets = targets.cuda(non_blocking=True)
                with torch.autocast("cuda"):
                    logits = network(images.cuda(non_blocking=True))
                predicted = logits.argmax(1)
                valid = targets != IGNORE_LABEL
                confusion += torch.bincount(targets[valid] * classes + predicted[valid], minlength=classes ** 2).reshape(classes, classes)
        return metrics_from_confusion(confusion)

    history = []
    for epoch in range(args.epochs):
        network.train()
        loss_sum = 0
        for images, targets in loaders["train"]:
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda"):
                logits = network(images.cuda(non_blocking=True))
                device_targets = targets.cuda(non_blocking=True)
                loss = criterion(logits, device_targets)
                if args.dice_weight:
                    valid_pixels = device_targets != IGNORE_LABEL
                    probabilities = logits.float().softmax(1) * valid_pixels.unsqueeze(1)
                    target_mask = torch.nn.functional.one_hot(device_targets.masked_fill(~valid_pixels, 0), num_classes=classes).permute(0, 3, 1, 2).float() * valid_pixels.unsqueeze(1)
                    intersection = (probabilities * target_mask).sum((0, 2, 3))
                    dice = (2 * intersection + 1) / (probabilities.sum((0, 2, 3)) + target_mask.sum((0, 2, 3)) + 1)
                    loss = loss + args.dice_weight * (1 - dice).mean()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            loss_sum += loss.item()
        scores = evaluate(loaders["validation"])
        row = {"epoch": epoch + 1, "train_loss": loss_sum / len(loaders["train"]), **scores,
               "elapsed_seconds": round(time.monotonic() - start, 2)}
        history.append(row)
        print(json.dumps({"event": "roi_epoch_completed", **row}), flush=True)
        if scores["macro_iou"] > best:
            best = scores["macro_iou"]
            state = {name: tensor.detach().cpu() for name, tensor in network.state_dict().items()}
            torch.save({"format_version": 2, "architecture": "compact_unet_4level", "base_channels": args.base_channels,
                        "class_names": list(EXTENDED_CLASS_NAMES), "state_dict": state,
                        "metadata": {**metadata, "selected_epoch": epoch + 1, "validation_metrics": scores}}, output / "roi.pt")
    checkpoint = torch.load(output / "roi.pt", map_location="cuda", weights_only=True)
    network.load_state_dict(checkpoint["state_dict"])
    heldout = evaluate(loaders["test"])
    report = {"evaluation_split": "untouched_source_validation_sequence_reserved_as_test", "images": len(test),
              "checkpoint_sha256": sha256(output / "roi.pt"), "manifest_sha256": audit["manifest_sha256"],
              "metrics_at_model_input_resolution": heldout, "input_size_px": metadata["input_size_px"],
              "elapsed_seconds": round(time.monotonic() - start, 2), "history": history, "metadata": metadata,
              "limitations": ["Source sequences from one small corpus, not India-wide deployment validation.",
                              "Metrics at model input resolution; full-resolution geometry errors not established.",
                              "Background means source unknown/background, not a validated object/occlusion taxonomy."]}
    (output / "roi-evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"event": "roi_training_and_test_completed", **{k: v for k, v in report.items() if k != "history"}}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/indian-roads-v2"))
    parser.add_argument("--output", type=Path, default=Path("models/india-roi-v2"))
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=288)
    parser.add_argument("--base-channels", type=int, default=16)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20261016)
    parser.add_argument("--name", default="indian-roads-unet-v2")
    parser.add_argument("--positive-repeat", type=float, default=1)
    parser.add_argument("--pothole-weight-min", type=float, default=0)
    parser.add_argument("--dice-weight", type=float, default=0)
    parser.add_argument("--preserve-aspect", action="store_true")
    run(parser.parse_args())
