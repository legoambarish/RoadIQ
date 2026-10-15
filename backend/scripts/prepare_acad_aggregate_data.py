"""Prepare a deterministic ACAD aggregate-only subset in RF-DETR COCO layout.

ACAD is synthetic concrete-aggregate data. This utility is for an experimental
transfer-learning baseline, not a substitute for labelled real-road imagery.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import random
import shutil
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download


DATASET_REPO = "igtsd/acad_dataset"
DATASET_REVISION = "main"
SOURCE_SUBSET = "low_occlusion"
SPLIT_NAMES = {"train": "train", "valid": "val", "test": "test"}
DEFAULT_COUNTS = {"train": 256, "valid": 64, "test": 64}


def _load_split(source_root: Path, split: str) -> dict[str, Any]:
    path = hf_hub_download(
        repo_id=DATASET_REPO,
        filename=f"{SOURCE_SUBSET}/{split}.json",
        repo_type="dataset",
        revision=DATASET_REVISION,
        local_dir=str(source_root),
    )
    return json.loads(Path(path).read_text(encoding="utf-8"))


def prepare_dataset(output_dir: Path, source_root: Path, seed: int, counts: dict[str, int]) -> dict[str, Any]:
    source_splits = {name: _load_split(source_root, remote_split) for name, remote_split in SPLIT_NAMES.items()}
    selected: dict[str, dict[str, Any]] = {}
    for split, source in source_splits.items():
        available = source["images"]
        count = counts[split]
        if count < 1 or count > len(available):
            raise ValueError(f"{split} count must be between 1 and {len(available)}")
        rng = random.Random(f"{seed}:{split}")
        images = sorted(rng.sample(available, count), key=lambda item: int(item["id"]))
        image_ids = {int(image["id"]) for image in images}
        annotations = [
            {key: value for key, value in annotation.items() if key != "amodal_segmentation"}
            for annotation in source["annotations"]
            if int(annotation["image_id"]) in image_ids and int(annotation["category_id"]) == 1
        ]
        selected[split] = {
            "info": source.get("info", {}),
            "licenses": source.get("licenses", []),
            "categories": [{"id": 1, "name": "aggregate", "supercategory": "stone"}],
            "images": images,
            "annotations": annotations,
        }

    requests: dict[str, tuple[str, str]] = {}
    for split, manifest in selected.items():
        split_dir = output_dir / split
        split_dir.mkdir(parents=True, exist_ok=True)
        (split_dir / "_annotations.coco.json").write_text(
            json.dumps(manifest, separators=(",", ":")), encoding="utf-8"
        )
        for image in manifest["images"]:
            name = str(image["file_name"])
            relative = f"{SOURCE_SUBSET}/images/{name}"
            requests[f"{split}/{name}"] = (relative, name)

    def _download(request: tuple[str, str]) -> tuple[str, str]:
        relative, name = request
        path = hf_hub_download(
            repo_id=DATASET_REPO,
            filename=relative,
            repo_type="dataset",
            revision=DATASET_REVISION,
            local_dir=str(source_root),
        )
        return str(path), name

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(_download, request): target
            for target, request in requests.items()
        }
        for future in concurrent.futures.as_completed(futures):
            source_path, name = future.result()
            target_split = futures[future].split("/", 1)[0]
            shutil.copyfile(source_path, output_dir / target_split / name)

    counts_out = {
        split: {
            "images": len(manifest["images"]),
            "aggregate_instances": len(manifest["annotations"]),
        }
        for split, manifest in selected.items()
    }
    provenance = {
        "dataset": DATASET_REPO,
        "revision": DATASET_REVISION,
        "subset": SOURCE_SUBSET,
        "license": "CC BY 4.0",
        "seed": seed,
        "counts": counts_out,
        "limitations": [
            "ACAD images are procedurally generated concrete-aggregate scenes, not real road surfaces.",
            "Reference coins are excluded; only aggregate instances are retained.",
            "Metrics on these splits do not establish RoadIQ real-road performance.",
        ],
    }
    (output_dir / "dataset_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    (output_dir / "DATA_LICENSE.txt").write_text(
        "ACAD dataset: https://huggingface.co/datasets/igtsd/acad_dataset\n"
        "License: Creative Commons Attribution 4.0 International (CC BY 4.0).\n"
        "Subset contains synthetic concrete-aggregate images and filtered aggregate annotations.\n",
        encoding="utf-8",
    )
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/roadiq-acad-subset"))
    parser.add_argument("--source-cache", type=Path, default=Path("/tmp/roadiq-acad-source"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-images", type=int, default=DEFAULT_COUNTS["train"])
    parser.add_argument("--valid-images", type=int, default=DEFAULT_COUNTS["valid"])
    parser.add_argument("--test-images", type=int, default=DEFAULT_COUNTS["test"])
    args = parser.parse_args()
    counts = {"train": args.train_images, "valid": args.valid_images, "test": args.test_images}
    result = prepare_dataset(args.output_dir, args.source_cache, args.seed, counts)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
