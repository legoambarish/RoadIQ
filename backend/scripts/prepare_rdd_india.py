"""Build a frozen, duplicate-grouped RDD2022 India detection dataset.

No official unlabelled test image is used for scored evaluation. Scene groups are
conservative numeric-ID blocks; later-split exact/dHash neighbors are excluded.
Routes remain unknown. Source XML boxes never become segmentation masks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
from backend.app.services.image_fingerprints import HashTree, dhash

CLASS_MAP = {"D00": "longitudinal_crack", "D10": "transverse_crack", "D20": "alligator_crack", "D40": "pothole"}
SOURCE = "https://figshare.com/articles/dataset/21431547"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class DuplicateGroups:
    def __init__(self, n: int):
        self.parents = list(range(n))

    def find(self, i: int) -> int:
        while self.parents[i] != i:
            self.parents[i] = self.parents[self.parents[i]]
            i = self.parents[i]
        return i

    def union(self, i: int, j: int) -> None:
        left, right = self.find(i), self.find(j)
        self.parents[max(left, right)] = min(left, right)


def parse_boxes(path: Path, width: int, height: int) -> tuple[list[list[float]], Counter]:
    tree = ET.parse(path).getroot()
    size = tree.find("size")
    if size is None or (int(size.findtext("width", "0")), int(size.findtext("height", "0"))) != (width, height):
        raise ValueError(f"XML/image dimension mismatch: {path.name}")
    boxes, ignored = [], Counter()
    for obj in tree.findall("object"):
        code = obj.findtext("name", "").strip()
        if code not in CLASS_MAP:
            ignored[code] += 1
            continue
        box = obj.find("bndbox")
        if box is None:
            raise ValueError(f"missing box: {path.name}")
        # Pascal VOC 1-based inclusive -> 0-based half-open coordinates.
        x1 = max(0.0, float(box.findtext("xmin", "nan")) - 1)
        y1 = max(0.0, float(box.findtext("ymin", "nan")) - 1)
        x2 = min(float(width), float(box.findtext("xmax", "nan")))
        y2 = min(float(height), float(box.findtext("ymax", "nan")))
        import math
        if not all(math.isfinite(x) for x in (x1, y1, x2, y2)) or x2 <= x1 or y2 <= y1:
            raise ValueError(f"invalid source box: {path.name}")
        boxes.append([list(CLASS_MAP).index(code), x1, y1, x2, y2])
    return boxes, ignored


def prepare(archive_path: Path, root: Path, seed: int = 20261016, block_size: int = 100) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    frozen = root / "manifest.jsonl"
    if frozen.exists():
        raise FileExistsError("Dataset already frozen; use a new output/version instead of changing its identity")
    extracted = root / "source"
    with ZipFile(archive_path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir() and
                   ("/train/images/" in item.filename or "/train/annotations/xmls/" in item.filename)]
        if not members:
            raise ValueError("No labelled India training images in selected archive")
        for item in members:
            if not item.filename.startswith("India/"):
                raise ValueError("non-India source in India archive")
            target = (extracted / item.filename).resolve()
            if not target.is_relative_to(extracted.resolve()):
                raise ValueError("unsafe archive path")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    images = sorted(extracted.rglob("*.jpg"))
    rows, all_ignored, class_counts = [], Counter(), Counter()
    groups, tree = DuplicateGroups(len(images)), HashTree()
    numeric_groups, exact = {}, {}
    exact_pairs, near_pairs = 0, 0
    for index, image_path in enumerate(images):
        xml_path = image_path.parents[1] / "annotations" / "xmls" / f"{image_path.stem}.xml"
        if not xml_path.is_file():
            raise ValueError(f"missing labelled training annotation: {image_path.name}")
        with Image.open(image_path) as image:
            width, height = image.size
            boxes, ignored = parse_boxes(xml_path, width, height)
            perceptual = dhash(image)
        digest = sha256(image_path)
        if digest in exact:
            groups.union(index, exact[digest])
            exact_pairs += 1
        else:
            exact[digest] = index
        for other in tree.neighbors(perceptual):
            groups.union(index, other)
            near_pairs += 1
        tree.add(perceptual, index)
        identifier = int(re.search(r"(\d+)$", image_path.stem).group(1))
        block = identifier // block_size
        if block in numeric_groups:
            groups.union(index, numeric_groups[block])
        else:
            numeric_groups[block] = index
        all_ignored.update(ignored)
        class_counts.update(CLASS_MAP[list(CLASS_MAP)[int(box[0])]] for box in boxes)
        rows.append({"image_id": image_path.stem, "image_path": image_path.relative_to(root).as_posix(),
                     "label_path": xml_path.relative_to(root).as_posix(), "label_available": True,
                     "label_type": "road_defect", "annotation_status": "in_progress",
                     "annotation_review": "published_source_boxes_structurally_checked; no independent full relabelling",
                     "source": "RDD2022 India", "provenance": f"{SOURCE}; CC BY 4.0; Arya et al.",
                     "rights": {"license": "CC-BY-4.0", "source": SOURCE}, "geography": "India",
                     "image_sha256": digest, "label_sha256": sha256(xml_path), "dhash64": f"{perceptual:016x}",
                     "width_px": width, "height_px": height, "boxes_xyxy_px": boxes,
                     "ignored_source_classes": dict(ignored), "numeric_block": block,
                     "negative_label_meaning": "no supported source boxes; not a healthy pavement grade"})
        if index % 500 == 0:
            print(json.dumps({"event": "audit_progress", "images": index, "total": len(images)}), flush=True)
    split_counts, split_classes, group_counts = Counter(), {}, Counter()
    # A pilot union of numeric blocks and every dHash edge formed one giant
    # component. Freeze block assignment first, then remove later-split near
    # neighbors; never call a random image split route-independent evidence.
    excluded, retained, retained_tree, retained_exact = [], [], HashTree(), {}
    for row in rows:
        group = f"india-numeric-block-{row['numeric_block']:05d}"
        token = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()[:8], 16) % 100
        row.update({"split": "train" if token < 70 else "validation" if token < 85 else "test", "scene_group": group})
    for split in ("train", "validation", "test"):
        for row in (r for r in rows if r["split"] == split):
            perceptual = int(row["dhash64"], 16)
            candidates = set(retained_tree.neighbors(perceptual))
            if row["image_sha256"] in retained_exact:
                candidates.add(retained_exact[row["image_sha256"]])
            cross = sorted(i for i in candidates if retained[i]["split"] != split)
            if cross:
                excluded.append({"image_id": row["image_id"], "split": split, "reason": "cross_split_exact_or_dhash_le4",
                                 "matches": [retained[i]["image_id"] for i in cross]})
                continue
            retained_tree.add(perceptual, len(retained))
            retained_exact[row["image_sha256"]] = len(retained)
            retained.append(row)
    source_count = len(rows)
    rows = retained
    class_counts = Counter(CLASS_MAP[list(CLASS_MAP)[int(box[0])]] for row in rows for box in row["boxes_xyxy_px"])
    split_lists = {split: [] for split in ("train", "validation", "test")}
    for index, row in enumerate(rows):
        group, split = row["scene_group"], row["split"]
        split_counts[split] += 1
        group_counts[group] += 1
        split_classes.setdefault(split, Counter()).update(CLASS_MAP[list(CLASS_MAP)[int(box[0])]] for box in row["boxes_xyxy_px"])
        yolo_dir = root / "yolo" / "labels" / split
        yolo_dir.mkdir(parents=True, exist_ok=True)
        lines = []
        for cls, x1, y1, x2, y2 in row["boxes_xyxy_px"]:
            lines.append(f"{int(cls)} {(x1+x2)/2/row['width_px']:.8f} {(y1+y2)/2/row['height_px']:.8f} {(x2-x1)/row['width_px']:.8f} {(y2-y1)/row['height_px']:.8f}")
        (yolo_dir / f"{row['image_id']}.txt").write_text("\n".join(lines), encoding="utf-8")
        image_dir = root / "yolo" / "images" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        image_target = image_dir / f"{row['image_id']}.jpg"
        if image_target.exists():
            if sha256(image_target) != row["image_sha256"]:
                raise ValueError("existing prepared image differs from source")
        else:
            try:
                image_target.hardlink_to(root / row["image_path"])
            except OSError:
                shutil.copyfile(root / row["image_path"], image_target)
        split_lists[split].append(str(image_target.resolve()).replace("\\", "/"))
    if set(split_counts) != {"train", "validation", "test"} or min(split_counts.values()) < 80:
        raise ValueError(f"insufficient independent grouped splits: {split_counts}")
    for split, paths in split_lists.items():
        (root / f"{split}.txt").write_text("\n".join(paths) + "\n", encoding="utf-8")
    frozen.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    config = {"path": str(root.resolve()).replace("\\", "/"), "train": "train.txt", "val": "validation.txt", "test": "test.txt", "names": dict(enumerate(CLASS_MAP.values()))}
    import yaml
    (root / "dataset.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    report = {"version": "rdd2022-india-grouped-v1", "seed": seed, "archive_sha256": sha256(archive_path),
              "manifest_sha256": sha256(frozen), "source_labelled_images": source_count, "images": len(rows), "split_counts": dict(split_counts),
              "class_counts": dict(class_counts), "class_counts_by_split": split_classes, "ignored_classes": dict(all_ignored),
              "class_map": CLASS_MAP, "exact_duplicate_pairs": exact_pairs, "near_duplicate_pairs_hamming_le4": near_pairs,
              "duplicate_audit_complete": True, "groups": len(group_counts), "largest_group_images": max(group_counts.values()),
              "grouping": f"numeric ID blocks of {block_size}; fixed seeded assignment; exclude later-split exact/dHash<=4 neighbors",
              "cross_split_exclusions": excluded, "cross_split_excluded_images": len(excluded),
              "initial_union_attempt": "REJECTED: joining numeric blocks and near-neighbor components collapsed all 7706 images into one split; no training used that attempt.",
              "limitations": ["No verified route/session metadata; scene separation heuristic, residual leakage possible.",
                              "Excluding later-split near neighbors can alter the evaluation distribution; dHash is not semantic/route identity.",
                              "Published boxes structurally checked; labels not exhaustively independently reannotated.",
                              "Official unlabelled test images excluded; empty supported boxes are not healthy labels."],
              "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (root / "split-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/rdd2022-india-v1"))
    parser.add_argument("--seed", type=int, default=20261016)
    args = parser.parse_args()
    prepare(args.archive, args.output, args.seed)
