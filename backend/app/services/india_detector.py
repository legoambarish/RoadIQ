"""Local India-only checkpoint adapter; no implicit weight downloads.

Ultralytics outputs boxes in the EXIF-oriented input image coordinate system after
reversing letterbox padding. Optional tiling explicitly reconstructs coordinates
and uses class-wise NMS. Boxes remain boxes, never damage masks.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image

CLASSES = ("longitudinal_crack", "transverse_crack", "alligator_crack", "pothole")


def tile_windows(width: int, height: int, size: int, overlap: float = 0.25, max_tiles: int = 16) -> list[tuple[int, int, int, int]]:
    if min(width, height, size) <= 0 or not 0 <= overlap < 0.75:
        raise ValueError("invalid tile dimensions or overlap")
    step = max(1, int(size * (1 - overlap)))

    def offsets(length: int) -> list[int]:
        positions = list(range(0, max(1, length - size + 1), step))
        return sorted(set(positions + [max(0, length - size)]))
    windows = [(x, y, min(width, x + size), min(height, y + size)) for y in offsets(height) for x in offsets(width)]
    if len(windows) > max_tiles:
        raise ValueError(f"tiling exceeds resource limit ({max_tiles} tiles)")
    return windows


def _iou(a: list[float], b: list[float]) -> float:
    intersection = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def class_nms(rows: list[tuple[int, float, list[float]]], threshold: float = 0.5) -> list[tuple[int, float, list[float]]]:
    kept = []
    for row in sorted(rows, key=lambda x: (-x[1], x[0], x[2])):
        if all(row[0] != other[0] or _iou(row[2], other[2]) <= threshold for other in kept):
            kept.append(row)
    return kept


class IndiaRoadDamageDetector:
    model_name = "RoadIQ India YOLO11n visible-defect detector"
    training_status = "roadIQ_trained"
    provider = "ultralytics_local"

    def __init__(self, checkpoint: str | Path, device: str = "cpu", tile_size: int = 0) -> None:
        path = Path(checkpoint).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("Configured India detector checkpoint does not exist")
        metadata_path = path.with_suffix(".json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if metadata.get("checkpoint_sha256") != digest:
            raise ValueError("checkpoint hash differs from training provenance")
        if metadata.get("training_country") != "India" or metadata.get("dataset") != "RDD2022 India":
            raise ValueError("checkpoint does not meet India-only road-data policy")
        if metadata.get("class_names") != list(CLASSES) or metadata.get("pretrained") is not False:
            raise ValueError("unsupported class map or unreviewed pretraining provenance")
        if not metadata.get("manifest_sha256") or not metadata.get("heldout_evaluation"):
            raise ValueError("checkpoint is missing frozen data/evaluation provenance")
        # Caller-supplied checkpoints are trusted local research assets, never uploads.
        os.environ.setdefault("YOLO_AUTOINSTALL", "false")
        os.environ.setdefault("YOLO_CONFIG_DIR", str(Path("artifacts/ultralytics-settings").resolve()))
        import ultralytics
        ultralytics.settings.update({"sync": False})
        from ultralytics import YOLO
        import torch
        torch.set_num_threads(int(os.getenv("ROADIQ_TORCH_THREADS", "4")))
        self.network = YOLO(str(path))
        if [self.network.names[i] for i in range(len(CLASSES))] != list(CLASSES):
            raise ValueError("network class map differs from provenance")
        self.device, self.tile_size = device, tile_size
        self.image_size = int(metadata.get("imgsz", 640))
        if not 160 <= self.image_size <= 1280 or tile_size < 0:
            raise ValueError("inference size outside supported resource bounds")
        self.input_size_px = {"width": self.image_size, "height": self.image_size}
        self.model_version = metadata["model_version"]
        self.checkpoint_metadata = {"sha256": digest, "manifest_sha256": metadata["manifest_sha256"],
                                    "training_country": "India", "license": "AGPL-3.0",
                                    "dataset_license": "CC-BY-4.0", "pretrained": False,
                                    "heldout_evaluation": {key: metadata["heldout_evaluation"].get(key) for key in
                                        ("dataset_split", "images", "map50", "map50_95", "manifest_sha256", "checkpoint_sha256")}}
        self.runtime_metadata = {"device": device, "letterbox_reversed_by": "ultralytics_orig_shape",
                                 "coordinate_system": "EXIF-oriented source image pixels", "tile_size": tile_size,
                                 "confidence_calibrated": False, "nms_iou": 0.5, "max_detections_per_view": 300}
        self._lock = threading.Lock()

    def predict(self, image: Image.Image, threshold: float) -> Any:
        windows = tile_windows(*image.size, self.tile_size) if self.tile_size else [(0, 0, image.width, image.height)]
        rows = []
        with self._lock:
            for x, y, right, bottom in windows:
                view = image.crop((x, y, right, bottom))
                prediction = self.network.predict(view, conf=max(0.001, threshold), iou=0.5, imgsz=self.image_size,
                                                  device=self.device, max_det=300, verbose=False)[0]
                if tuple(prediction.orig_shape) != (view.height, view.width):
                    raise ValueError("model returned mismatched source coordinate system")
                boxes = prediction.boxes
                for cls, score, box in zip(boxes.cls.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.xyxy.cpu().tolist()):
                    mapped = [box[0] + x, box[1] + y, box[2] + x, box[3] + y]
                    if all(math.isfinite(v) for v in mapped) and 0 <= score <= 1:
                        rows.append((int(cls), float(score), mapped))
        rows = class_nms(rows)
        return SimpleNamespace(class_id=[r[0] for r in rows], confidence=[r[1] for r in rows],
                               xyxy=[r[2] for r in rows], class_names=list(CLASSES))
