"""Serve the built dashboard and genuine local models on one loopback origin."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--device", default="cpu", help="cpu or CUDA device index")
    parser.add_argument("--allow-unavailable-models", action="store_true", help="explicit dashboard-only mode")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend"))
    frontend = root / "frontend" / "dist"
    if not (frontend / "index.html").is_file():
        parser.error("Build frontend first: cd frontend; npm ci; npm run build")
    for variable, relative in (("ROADIQ_DETECTOR_MODEL_PATH", "models/india-yolo11n-coco-v2/detector.pt"),
                               ("ROADIQ_SEGMENTATION_MODEL_PATH", "models/india-roi-v5/roi.pt")):
        path = Path(os.getenv(variable, str(root / relative))).expanduser().resolve()
        if not path.is_file() and not args.allow_unavailable_models:
            parser.error(f"Missing model: {relative}. Follow docs/TRAINING_AND_DEMO.md, or explicitly use --allow-unavailable-models.")
        if path.is_file():
            os.environ[variable] = str(path)
    os.environ["ROADIQ_DETECTOR_DEVICE"] = args.device
    os.environ["ROADIQ_SEGMENTATION_DEVICE"] = "cuda:" + args.device if args.device.isdigit() else args.device
    os.environ.setdefault("YOLO_CONFIG_DIR", str(root / "artifacts" / "ultralytics-settings"))
    from app.api.routes.image_analysis import vision_readiness
    from app.main import create_app
    import uvicorn
    readiness = vision_readiness()
    if not args.allow_unavailable_models and (not readiness["ready"] or readiness["roi"]["status"] != "loaded"):
        parser.error("Configured model failed provenance/load checks. Inspect GET /api/v1/vision-readiness in dashboard-only mode.")
    print(json.dumps({"event": "local_app_starting", "url": f"http://127.0.0.1:{args.port}",
                      "detector": readiness["detector"]["status"], "roi": readiness["roi"]["status"]}), flush=True)
    uvicorn.run(create_app(frontend_directory=frontend), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
