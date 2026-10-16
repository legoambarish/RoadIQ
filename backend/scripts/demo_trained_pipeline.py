"""Genuine heldout images -> local trained models -> HTTP report/benchmark.

Missing weights, provenance, labels or failed actual inference cause failure.
The generated black/low-resolution controls test abstention plumbing only.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import platform
import random
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.vision import reset_detector_for_tests
from backend.scripts.prepare_rdd_india import CLASS_MAP, sha256


def overlap(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union else 0


def match_report(row, report):
    names = list(CLASS_MAP.values())
    predictions = [item for defect in report["defects"] for item in defect["detections"]]
    counts = {name: {"tp": 0, "fp": 0, "fn": 0} for name in names}
    matched = set()
    for prediction in sorted(predictions, key=lambda item: -item["confidence"]):
        name = prediction["model_label"]
        box = prediction["bbox_xyxy_px"]
        box = [box[key] for key in ("x_min", "y_min", "x_max", "y_max")]
        eligible = [(overlap(box, truth[1:]), i) for i, truth in enumerate(row["boxes_xyxy_px"])
                    if i not in matched and int(truth[0]) == names.index(name)]
        best = max(eligible, default=(0, -1))
        if best[0] >= .5:
            counts[name]["tp"] += 1
            matched.add(best[1])
        else:
            counts[name]["fp"] += 1
    for i, truth in enumerate(row["boxes_xyxy_px"]):
        if i not in matched:
            counts[names[int(truth[0])]]["fn"] += 1
    return counts


def summarize_counts(counts):
    total = {key: sum(item[key] for item in counts) for key in ("tp", "fp", "fn")}
    return {**total, "precision": total["tp"] / (total["tp"] + total["fp"]) if total["tp"] + total["fp"] else None,
            "recall": total["tp"] / (total["tp"] + total["fn"]) if total["tp"] + total["fn"] else None}


def group_bootstrap(records, replicates=1000):
    """Conditional sampling uncertainty; numeric source blocks are only route proxies."""
    import numpy as np
    groups = sorted({row["scene_group"] for row in records})
    if len(groups) < 2:
        return {"status": "unavailable", "reason": "Fewer than two source-block groups"}
    grouped = {name: [summarize_counts([row["matching_iou50_conf25"][name] for row in records if row["scene_group"] == group])
                      for group in groups] for name in CLASS_MAP.values()}
    rng = np.random.default_rng(20261016)
    samples = {name: {"precision": [], "recall": []} for name in CLASS_MAP.values()}
    for _ in range(replicates):
        indices = rng.integers(0, len(groups), len(groups))
        for name, counts in grouped.items():
            estimate = summarize_counts([counts[int(index)] for index in indices])
            for metric in ("precision", "recall"):
                if estimate[metric] is not None:
                    samples[name][metric].append(estimate[metric])
    return {"status": "computed", "source_block_groups": len(groups), "replicates": replicates,
            "seed": 20261016, "interval": "2.5 and 97.5 percentile cluster-bootstrap interval",
            "per_class": {name: {metric: {"low": float(np.percentile(values, 2.5)) if values else None,
                                                    "high": float(np.percentile(values, 97.5)) if values else None,
                                                    "defined_replicates": len(values)}
                                   for metric, values in metrics.items()} for name, metrics in samples.items()},
            "limitation": "Conditional on this dataset and source-block grouping. Unknown route/session dependence, annotation errors and deployment shift are not captured. These intervals are not road percentile ranks."}


def save_example(output, name, row, report, root):
    path = root / row["image_path"]
    directory = output / name
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, directory / path.name)
    (directory / "analysis.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    image = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(image)
    for defect in report["defects"]:
        for prediction in defect["detections"]:
            box = prediction["bbox_xyxy_px"]
            draw.rectangle(tuple(box[k] for k in ("x_min", "y_min", "x_max", "y_max")), outline="#ff9c24", width=3)
            draw.text((box["x_min"], max(0, box["y_min"] - 14)), f"prediction {prediction['model_label']} {prediction['confidence']:.3f}",
                      fill="white", stroke_width=1, stroke_fill="black")
    draw.rectangle((0, 0, image.width, 25), fill="black")
    draw.text((5, 5), "MODEL PREDICTIONS / RAW SCORES; NOT GROUND TRUTH", fill="white")
    image.save(directory / "predicted-boxes.jpg", quality=92)
    return {"name": name, "source_image_id": row["image_id"], "image_sha256": row["image_sha256"],
            "source": row["source"], "rights": row["rights"], "split": "test", "scene_group": row["scene_group"],
            "report_path": f"{name}/analysis.json", "input_path": f"{name}/{path.name}",
            "supported_source_boxes": len(row["boxes_xyxy_px"]), "status": report["visual_distress"]["status"]}


def run(args):
    import numpy as np
    root = ROOT / "data/rdd2022-india-v1"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for variable, relative in (("ROADIQ_DETECTOR_MODEL_PATH", "models/india-yolo11n-v1/detector.pt"),
                               ("ROADIQ_SEGMENTATION_MODEL_PATH", "models/india-roi-v4/roi.pt")):
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Real trained model required: {relative}")
        os.environ[variable] = str(path)
    os.environ["ROADIQ_DETECTOR_DEVICE"] = args.device
    os.environ["ROADIQ_SEGMENTATION_DEVICE"] = "cuda:" + args.device if args.device.isdigit() else args.device
    os.environ["ROADIQ_DETECTOR_TILE_SIZE"] = "0"
    os.environ["ROADIQ_TORCH_THREADS"] = "4"
    reset_detector_for_tests()
    rows = [json.loads(line) for line in (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    heldout = [row for row in rows if row["split"] == "test"]
    chosen = random.Random(20261016).sample(heldout, min(args.samples, len(heldout)))
    if len(chosen) < 20:
        raise ValueError("benchmark requires at least 20 actual heldout images")
    client = TestClient(create_app(), raise_server_exceptions=False)
    started = time.perf_counter()
    readiness = client.get("/api/v1/vision-readiness").json()
    load_ms = (time.perf_counter() - started) * 1000
    if not readiness["ready"] or readiness["roi"]["status"] != "loaded":
        raise RuntimeError(f"Genuine evaluated detector + ROI required: {readiness}")
    (output / "readiness.json").write_text(json.dumps(readiness, indent=2), encoding="utf-8")

    def upload(row):
        path = root / row["image_path"]
        return client.post("/api/v1/image-analyses", files={"image": (path.name, path.read_bytes(), "image/jpeg")})

    first = time.perf_counter()
    warmup = upload(chosen[0])
    warmup_ms = (time.perf_counter() - first) * 1000
    if warmup.status_code != 200:
        raise RuntimeError(f"real-image warmup failed: HTTP {warmup.status_code}")
    records, reports = [], {}
    for index, row in enumerate(chosen):
        start = time.perf_counter()
        response = upload(row)
        elapsed = (time.perf_counter() - start) * 1000
        record = {"image_id": row["image_id"], "scene_group": row["scene_group"], "status_code": response.status_code,
                  "http_testclient_ms": round(elapsed, 3), "source_box_count": len(row["boxes_xyxy_px"])}
        if response.status_code == 200:
            report = response.json()
            assert report["model"]["confidence_threshold"] == .25
            assert report["model"]["runtime"]["nms_iou"] == .5
            errors = [error for error in report["processing_errors"] if error.get("code") in {
                "model_load_failed", "segmentation_model_load_failed", "inference_failed", "segmentation_inference_failed"}]
            record.update({"vda_status": report["visual_distress"]["status"], "processing_time_ms": report["processing_time_ms"],
                           "inference_errors": errors, "detection_count": report["visual_distress"]["detection_count"],
                           "quality_issues": report["image_quality"]["issues"], "matching_iou50_conf25": match_report(row, report)})
            assert report["rsqi"]["value"] is None and report["visual_distress"]["reference_percentile"]["value"] is None
            reports[row["image_id"]] = report
        records.append(record)
        if index % 10 == 0:
            print(json.dumps({"event": "real_pipeline_benchmark_progress", "images": index + 1, "total": len(chosen)}), flush=True)
    successful = [r for r in records if r["status_code"] == 200]
    latency = [r["http_testclient_ms"] for r in successful]
    counts = {name: summarize_counts([r["matching_iou50_conf25"][name] for r in successful]) for name in CLASS_MAP.values()}
    negatives = [r for r in successful if r["source_box_count"] == 0]
    examples = []
    positive = next((row for row in chosen if row["image_id"] in reports and row["boxes_xyxy_px"] and reports[row["image_id"]]["visual_distress"]["detection_count"]), None)
    challenge = next((row for row in chosen if row["image_id"] in reports and not row["boxes_xyxy_px"]), None)
    for name, row in (("damaged-source-image", positive), ("no-supported-source-boxes-challenge", challenge)):
        if row:
            examples.append(save_example(output, name, row, reports[row["image_id"]], root))
    errors = sorted(successful, key=lambda row: -sum(c["fp"] + c["fn"] for c in row["matching_iou50_conf25"].values()))[:8]
    for i, record in enumerate(errors):
        row = next(row for row in chosen if row["image_id"] == record["image_id"])
        save_example(output, f"error-example-{i + 1}", row, reports[row["image_id"]], root)

    controls = []
    source = Image.open(root / chosen[0]["image_path"]).convert("RGB")
    for name, image in (("black_synthetic_control", Image.new("RGB", source.size, "black")),
                        ("low_resolution_control", source.resize((160, 120))),
                        ("blur_transform_challenge", source.filter(ImageFilter.GaussianBlur(18)))):
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        response = client.post("/api/v1/image-analyses", files={"image": (name + ".png", stream.getvalue(), "image/png")})
        response.raise_for_status()
        report = response.json()
        (output / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        image.save(output / f"{name}.png")
        controls.append({"name": name, "status": report["visual_distress"]["status"], "rsqi": report["rsqi"]["value"],
                         "quality_issues": report["image_quality"]["issues"], "not_a_road_accuracy_benchmark": True})
        assert report["rsqi"]["value"] is None
        if name != "blur_transform_challenge":
            assert report["visual_distress"]["status"] == "unusable"
    full_holdout = len(chosen) == len(heldout)
    summary = {"version": "real-http-pipeline-benchmark-v1", "images": len(chosen),
               "sampling": "full frozen labelled holdout, shuffled seed 20261016; no tuning" if full_holdout else "fixed seed 20261016 sample of frozen labelled test; no tuning",
               "full_labelled_holdout": full_holdout,
               "device": args.device, "python": platform.python_version(), "platform": platform.platform(), "processor": platform.processor(),
               "manifest_sha256": sha256(root / "manifest.jsonl"), "model_load_ms": round(load_ms, 3), "first_request_ms": round(warmup_ms, 3),
               "warm_requests": len(successful), "latency_ms": {"min": min(latency), "p50": float(np.percentile(latency, 50)), "p90": float(np.percentile(latency, 90)),
                                                             "p95": float(np.percentile(latency, 95)), "max": max(latency)},
               "http_failures": len(records) - len(successful), "inference_failures": sum(bool(r["inference_errors"]) for r in successful),
               "status_counts": dict(Counter(r["vda_status"] for r in successful)),
               "per_class_fixed_conf25_iou50": counts, "matching_policy": "Class-specific descending-score greedy IoU >= .5, unique source-box matches; runtime confidence .25/NMS .5. Quality abstentions count as misses for source boxes.",
               "conditional_group_bootstrap_95ci": group_bootstrap(successful),
               "source_empty_label_challenges": {"images": len(negatives), "with_candidate_predictions": sum(bool(r["detection_count"]) for r in negatives),
                                                 "meaning": "Unmatched source-box stress cases, not independently verified healthy negatives."},
               "examples": examples, "quality_controls": controls,
               "limitations": ["TestClient exercises genuine HTTP routing/models, excludes browser rendering and network transport.",
                               "Fixed-threshold source-box matching is not AP or field severity accuracy; confidence-sweep mAP is reported separately.",
                               "Quality transforms test known controls, not real field rejection sensitivity/specificity.",
                               "No field calibration, physical MAE or independent severity/healthy labels."]}
    (output / "pipeline-benchmark.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "per-image-benchmark.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"event": "real_pipeline_demo_completed", **summary}), flush=True)
    if summary["http_failures"] or summary["inference_failures"] or positive is None:
        raise RuntimeError("real pipeline benchmark contains failures/no actual candidates; inspect saved evidence")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/genuine-demo"))
    parser.add_argument("--samples", type=int, default=60)
    parser.add_argument("--device", default="cpu")
    run(parser.parse_args())
