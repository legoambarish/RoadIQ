"""Run Task C analysis once and save a shareable preview plus JSON report."""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path
from typing import Any

from app.services.vision import ImageValidationError, analyze_road_image
from scripts.create_demo_road_image import create_synthetic_road_image


def run_demo(*, output_dir: Path, image_path: Path | None = None, seed: int = 42) -> dict[str, Any]:
    """Analyze an input image or synthetic sample and write a preview/report pair."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if image_path is None:
        image = create_synthetic_road_image(seed=seed)
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()
        source_name = "synthetic-road-demo.png"
        sample_path = output_dir / source_name
        image.save(sample_path, format="PNG")
    else:
        image_bytes = image_path.read_bytes()
        source_name = image_path.name
        sample_path = None

    report = analyze_road_image(image_bytes, source_name=source_name)
    annotation = report.get("annotated_image", {})
    data_uri = annotation.get("value") if isinstance(annotation, dict) else None
    annotation_path: Path | None = None
    if isinstance(data_uri, str) and data_uri.startswith("data:image/jpeg;base64,"):
        annotation_path = output_dir / "annotated-preview.jpg"
        annotation_path.write_bytes(base64.b64decode(data_uri.partition(",")[2], validate=True))
        annotation["value"] = str(annotation_path)
        annotation["reason"] = "Annotated JPEG preview written by the local Task C demo."

    report_path = output_dir / "analysis-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    aggregate = report.get("aggregate_analysis", {})
    surface_region = aggregate.get("surface_region", {})
    return {
        "analysis_status": report.get("analysis_status"),
        "source_name": source_name,
        "synthetic_input": image_path is None,
        "method": aggregate.get("method"),
        "training_status": aggregate.get("training_status"),
        "candidate_area_ratio": surface_region.get("candidate_area_ratio"),
        "aggregate_count": aggregate.get("aggregate_count", {}).get("value"),
        "input_image": str(sample_path) if sample_path else str(image_path),
        "annotated_image": str(annotation_path) if annotation_path else None,
        "report": str(report_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, help="analyze a local JPEG, PNG, or WebP instead of the synthetic sample")
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/roadiq-demo"))
    parser.add_argument("--seed", type=int, default=42, help="synthetic-image seed (ignored when --image is used)")
    args = parser.parse_args()
    try:
        summary = run_demo(output_dir=args.output_dir, image_path=args.image, seed=args.seed)
    except ImageValidationError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, indent=2), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"error": {"code": "demo_io_failed", "message": str(exc)}}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if summary["synthetic_input"]:
        print("Synthetic input only; candidate texture is not aggregate segmentation or model evaluation.", file=sys.stderr)
    if summary["annotated_image"] is None:
        print("Warning: this image produced no annotated preview; the structured report was still saved.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
