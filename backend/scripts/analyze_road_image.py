"""Run the Task C image service on a local image and print its JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.vision import ImageValidationError, analyze_road_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="local JPEG, PNG, or WebP image")
    args = parser.parse_args()
    try:
        result = analyze_road_image(args.image.read_bytes(), source_name=args.image.name)
    except ImageValidationError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, indent=2))
        return 2
    except OSError as exc:
        print(json.dumps({"error": {"code": "file_read_failed", "message": str(exc)}}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
