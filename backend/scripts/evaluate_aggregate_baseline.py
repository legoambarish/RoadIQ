"""Evaluate the untrained aggregate texture baseline on a reviewed test split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.aggregate_evaluation import evaluate_aggregate_texture_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="validated JSONL dataset manifest")
    args = parser.parse_args()
    try:
        result = evaluate_aggregate_texture_baseline(args.manifest)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
