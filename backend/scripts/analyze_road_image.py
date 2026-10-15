"""Run the Task C image service on a local image and print its JSON report."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from app.services.vision import ImageValidationError, analyze_road_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="local JPEG, PNG, or WebP image")
    parser.add_argument(
        "--annotated-output",
        type=Path,
        help="write the baseline's annotated JPEG preview to this path and reference it from the report",
    )
    parser.add_argument("--report-output", type=Path, help="also save the structured JSON report to this path")
    args = parser.parse_args()
    try:
        result = analyze_road_image(args.image.read_bytes(), source_name=args.image.name)
    except ImageValidationError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, indent=2))
        return 2
    except OSError as exc:
        print(json.dumps({"error": {"code": "file_read_failed", "message": str(exc)}}, indent=2))
        return 2
    annotation = result.get("annotated_image", {})
    data_uri = annotation.get("value") if isinstance(annotation, dict) else None
    if args.annotated_output:
        if isinstance(data_uri, str) and data_uri.startswith("data:image/jpeg;base64,"):
            try:
                args.annotated_output.parent.mkdir(parents=True, exist_ok=True)
                args.annotated_output.write_bytes(base64.b64decode(data_uri.partition(",")[2], validate=True))
                annotation["value"] = str(args.annotated_output)
                annotation["reason"] = "Annotated JPEG preview written to the CLI output path."
            except OSError as exc:
                print(
                    json.dumps({"error": {"code": "annotation_write_failed", "message": str(exc)}}, indent=2),
                    file=sys.stderr,
                )
                return 2
        else:
            print("Warning: no annotation was available; continuing with the structured report.", file=sys.stderr)
    serialized = json.dumps(result, indent=2, ensure_ascii=False)
    if args.report_output:
        try:
            args.report_output.parent.mkdir(parents=True, exist_ok=True)
            args.report_output.write_text(serialized + "\n", encoding="utf-8")
        except OSError as exc:
            print(
                json.dumps({"error": {"code": "report_write_failed", "message": str(exc)}}, indent=2),
                file=sys.stderr,
            )
            return 2
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
