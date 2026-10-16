"""Train/evaluate a reproducible India-only YOLO11n detector from random weights.

No COCO detector or multinational road weights are loaded. AMP's upstream
auto-check downloads pretrained models, so it is explicitly disabled here.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import time
from pathlib import Path

from backend.scripts.prepare_rdd_india import CLASS_MAP, sha256


def run(args: argparse.Namespace) -> None:
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path("artifacts/ultralytics-settings").resolve()))
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")
    import torch
    import ultralytics
    from ultralytics import YOLO
    ultralytics.settings.update({"sync": False})
    torch.set_num_threads(4)
    if not torch.cuda.is_available() and args.device != "cpu":
        raise RuntimeError("Requested GPU training but CUDA unavailable")
    data = args.data.resolve()
    audit = json.loads((data / "split-audit.json").read_text(encoding="utf-8"))
    manifest_hash = sha256(data / "manifest.jsonl")
    if manifest_hash != audit["manifest_sha256"]:
        raise RuntimeError("frozen manifest changed")
    if not audit["duplicate_audit_complete"]:
        raise RuntimeError("incomplete duplicate audit")
    args.output.mkdir(parents=True, exist_ok=True)
    experiment = args.output / "experiment.json"
    if experiment.exists():
        raise FileExistsError("experiment identity exists; use a different run name")
    meta = {"model_version": args.name, "architecture": "yolo11n", "framework": f"ultralytics-{ultralytics.__version__}",
            "framework_license": "AGPL-3.0", "training_country": "India", "dataset": "RDD2022 India",
            "dataset_license": "CC-BY-4.0", "dataset_source": "https://figshare.com/articles/dataset/21431547",
            "class_names": list(CLASS_MAP.values()), "manifest_sha256": manifest_hash,
            "archive_sha256": audit["archive_sha256"], "splits": audit["split_counts"],
            "seed": args.seed, "epochs_requested": args.epochs, "batch": args.batch, "imgsz": args.imgsz,
            "pretrained": False, "amp": False, "device": args.device,
            "hardware": torch.cuda.get_device_name(0) if torch.cuda.is_available() else platform.processor(),
            "python": platform.python_version(), "torch": str(torch.__version__),
            "training_status": "roadIQ_trained", "confidence_calibrated": False,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "split_limitations": audit["limitations"]}
    experiment.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"event": "training_started", **meta}), flush=True)
    start = time.monotonic()
    model = YOLO("yolo11n.yaml")

    def epoch_end(trainer):
        print(json.dumps({"event": "epoch_completed", "epoch": trainer.epoch + 1,
                          "elapsed_seconds": round(time.monotonic() - start, 1),
                          "metrics": {str(k): float(v) for k, v in trainer.metrics.items()}}), flush=True)
    model.add_callback("on_fit_epoch_end", epoch_end)
    model.train(data=str(data / "dataset.yaml"), epochs=args.epochs, batch=args.batch, imgsz=args.imgsz,
                device=args.device, workers=0, seed=args.seed, deterministic=True, pretrained=False,
                amp=False, optimizer="AdamW", lr0=0.001, lrf=0.05, weight_decay=0.0005,
                warmup_epochs=2, mosaic=0.5, close_mosaic=5, fliplr=0.5, flipud=0.0,
                degrees=0.0, perspective=0.0, mixup=0.0, patience=12, plots=True,
                project=str(args.output.resolve()), name="fit", exist_ok=False, verbose=False, cache=False)
    best = Path(model.trainer.best)
    if not best.is_file():
        raise RuntimeError("training did not produce best checkpoint")
    checkpoint = args.output / "detector.pt"
    shutil.copy2(best, checkpoint)
    meta.update({"checkpoint_sha256": sha256(checkpoint), "training_seconds": round(time.monotonic() - start, 3),
                 "epochs_completed": int(model.trainer.epoch) + 1,
                 "selected_by": "best validation fitness; test not used for selection"})
    # Evaluate once on the frozen labelled holdout, not the official unlabelled test.
    evaluated = YOLO(str(checkpoint))
    metrics = evaluated.val(data=str(data / "dataset.yaml"), split="test", imgsz=args.imgsz, batch=args.batch,
                            device=args.device, workers=0, plots=True, save_json=True,
                            project=str(args.output.resolve()), name="heldout", exist_ok=False, verbose=False)
    per_class = []
    for index, name in enumerate(CLASS_MAP.values()):
        per_class.append({"class": name, "precision": float(metrics.box.p[index]), "recall": float(metrics.box.r[index]),
                          "ap50": float(metrics.box.ap50[index]), "ap50_95": float(metrics.box.ap[index])})
    report = {"dataset_split": "frozen_grouped_labelled_test", "images": audit["split_counts"]["test"],
              "manifest_sha256": manifest_hash, "checkpoint_sha256": meta["checkpoint_sha256"],
              "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map),
              "precision": float(metrics.box.mp), "recall": float(metrics.box.mr), "per_class": per_class,
              "speed_ms_per_image": metrics.speed, "precision_recall_policy": "Ultralytics validation max-mean-F1 confidence, IoU=0.5; AP integrates confidence sweep",
              "deployment_threshold": 0.25, "calibrated_confidence": False,
              "limitations": audit["limitations"], "evaluated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    meta["heldout_evaluation"] = report
    checkpoint.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    experiment.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (args.output / "heldout-metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"event": "training_and_holdout_completed", **report}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/rdd2022-india-v1"))
    parser.add_argument("--output", type=Path, default=Path("models/india-yolo11n-v1"))
    parser.add_argument("--name", default="india-yolo11n-scratch-v1")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--seed", type=int, default=20261016)
    run(parser.parse_args())
