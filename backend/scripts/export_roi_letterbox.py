"""Version a letterbox runtime export without repeating identical 16:9 training.

This is an export, not another trained experiment. It refuses reuse when any
retained source input differs between the two preprocessing paths. Original
weights and evaluation remain immutable; full source-resolution runtime metrics
must be measured separately by evaluate_roi_source_resolution.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

from backend.app.services.india_road_segmentation import LETTERBOX_MODE, letterbox_pair


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run(args) -> None:
    import torch

    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("Deployment identity already exists; choose a new export directory")
    evaluation = json.loads((source / "roi-evaluation.json").read_text(encoding="utf-8"))
    source_hash = digest(source / "roi.pt")
    manifest_hash = digest(source / "roi-manifest.jsonl")
    if evaluation["checkpoint_sha256"] != source_hash or evaluation["manifest_sha256"] != manifest_hash:
        raise ValueError("Completed source experiment/checkpoint/manifest identity mismatch")
    checkpoint = torch.load(source / "roi.pt", map_location="cpu", weights_only=True)
    metadata = checkpoint["metadata"]
    if metadata.get("input_preprocessing", "legacy_stretch_v1") != "legacy_stretch_v1":
        raise ValueError("Only a recorded legacy stretch experiment can use this export")
    width, height = (metadata["input_size_px"][name] for name in ("width", "height"))
    rows = [json.loads(line) for line in (source / "roi-manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    counts: dict[str, int] = {}
    for index, row in enumerate(rows):
        image_path, mask_path = (args.data / row[key] for key in ("image_path", "label_path"))
        if digest(image_path) != row["image_sha256"] or digest(mask_path) != row["label_sha256"]:
            raise ValueError(f"Source bytes changed: {row['image_id']}")
        with Image.open(image_path) as opened:
            image = opened.convert("RGB")
        with Image.open(mask_path) as opened:
            mask = opened.convert("L")
        if image.width * height != image.height * width or mask.size != image.size:
            raise ValueError("Letterbox changes retained training/evaluation inputs; retraining or fresh evaluation required")
        boxed_image, boxed_mask, geometry = letterbox_pair(image, (width, height), mask)
        if any(geometry["padding_ltrb_px"]) or boxed_image.tobytes() != image.resize((width, height), Image.Resampling.BILINEAR).tobytes() or boxed_mask.tobytes() != mask.resize((width, height), Image.Resampling.NEAREST).tobytes():
            raise ValueError("Preprocessing equivalence proof failed")
        counts[row["split"]] = counts.get(row["split"], 0) + 1
        if (index + 1) % 200 == 0:
            print(json.dumps({"event": "export_source_equivalence_checked", "images": index + 1, "total": len(rows)}), flush=True)
    provenance = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "operation": "runtime_preprocessing_export_without_training",
        "source_model_version": metadata["model_version"],
        "source_preprocessing": "legacy_stretch_v1 (original loader default when metadata field is absent)",
        "source_checkpoint_sha256": source_hash,
        "source_evaluation_sha256": digest(source / "roi-evaluation.json"),
        "source_manifest_sha256": manifest_hash,
        "all_source_image_and_label_hashes_verified": True,
        "all_retained_rgb_and_mask_model_input_bytes_equal": True,
        "verified_images": len(rows), "split_counts": counts,
        "new_training_epochs": 0,
        "metric_policy": "Original GPU model-input evaluation is reused because all retained model inputs are byte-identical. CPU source-resolution projection is a separate evaluation; this is not a new trained experiment.",
        "runtime_change": "Preserve aspect ratio for other camera formats; crop padding then project argmax labels by nearest neighbor instead of interpolating logits at source resolution.",
    }
    checkpoint["metadata"] = {**metadata,
        "training_experiment_model_version": metadata["model_version"],
        "model_version": args.name, "input_preprocessing": LETTERBOX_MODE,
        "deployment_export": provenance,
        "padding_policy": "Black RGB padding, removed before source mask projection; no physical scale inferred"}
    output.mkdir(parents=True)
    torch.save(checkpoint, output / "roi.pt")
    exported = torch.load(output / "roi.pt", map_location="cpu", weights_only=True)
    if not all(torch.equal(tensor, exported["state_dict"][name]) for name, tensor in checkpoint["state_dict"].items()):
        raise RuntimeError("Export changed learned parameter tensors")
    for name in ("roi-manifest.jsonl", "roi-split-audit.json"):
        shutil.copyfile(source / name, output / name)
    export_report = {**evaluation,
        "checkpoint_sha256": digest(output / "roi.pt"),
        "deployment_export": {**provenance, "learned_parameter_tensors_verified_equal": True},
        "limitations": evaluation["limitations"] + ["Deployment export changes source mask projection; source-resolution CPU metrics are evaluated separately. No additional training or independent field data."]}
    (output / "roi-evaluation.json").write_text(json.dumps(export_report, indent=2) + "\n", encoding="utf-8")
    (output / "export-provenance.json").write_text(json.dumps(export_report["deployment_export"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "roi_runtime_export_completed", "checkpoint_sha256": export_report["checkpoint_sha256"], **provenance}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("models/india-roi-v3"))
    parser.add_argument("--data", type=Path, default=Path("data/indian-roads-v2"))
    parser.add_argument("--output", type=Path, default=Path("models/india-roi-v3-letterbox-v1"))
    parser.add_argument("--name", default="indian-roads-unet-v3-letterbox-v1")
    run(parser.parse_args())
