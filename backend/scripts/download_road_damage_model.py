"""Download the pinned, published RF-DETR Nano/RDD2022 checkpoint into the HF cache."""

from __future__ import annotations

import hashlib
from pathlib import Path


MODEL_REPO = "dronefreak/rdd2022-rfdetr-nano"
MODEL_REVISION = "66429f39b916e56c6a33243d776718088f5f43ad"
MODEL_FILE = "checkpoint_best_total.pth"
MODEL_SHA256 = "2d1fba21b829ebc42f7c74f76285d97b2e3295aebe8d97e497d0cc186be98cc9"


def main() -> int:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise SystemExit("Install optional vision requirements first: pip install -r requirements-vision.txt") from exc
    path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, revision=MODEL_REVISION)
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        raise SystemExit(f"Checkpoint checksum mismatch: expected {MODEL_SHA256}, got {digest}")
    print(f"Verified checkpoint: {path}")
    print(f"Set ROADIQ_VISION_MODEL_PATH={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
