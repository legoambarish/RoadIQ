"""Validate a RoadIQ JSONL image manifest and its split/duplicate hygiene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.dataset_manifest import validate_dataset_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON Lines manifest; relative paths resolve beside it")
    args = parser.parse_args()
    report = validate_dataset_manifest(args.manifest)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
