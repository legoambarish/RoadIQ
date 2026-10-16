"""Validation for RoadIQ's documented JSON Lines image dataset manifest."""

from __future__ import annotations

import hashlib
import json
import warnings as py_warnings
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from app.services.image_fingerprints import HashTree

SPLITS = {"train", "validation", "test"}
LABEL_TYPES = {"none", "aggregate_instance", "road_defect", "road_semantic_segmentation"}
ANNOTATION_STATES = {"not_started", "in_progress", "reviewed", "rejected"}
NEAR_DUPLICATE_MAX_HAMMING = 4


def _dhash(path: Path) -> int:
    with Image.open(path) as source:
        gray = source.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        values = gray.tobytes()
    result = 0
    for y in range(8):
        offset = y * 9
        for x in range(8):
            result = (result << 1) | int(values[offset + x] > values[offset + x + 1])
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(manifest_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"cannot read manifest: {exc}"]
    for line_number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_number}: each JSONL entry must be an object")
            continue
        row["_line"] = line_number
        rows.append(row)
    return rows, errors


def validate_dataset_manifest(manifest: str | Path, *, require_rights: bool = False) -> dict[str, Any]:
    """Validate rows, files, scene-group split hygiene, and duplicate image content."""
    manifest_path = Path(manifest).expanduser().resolve()
    rows, errors = _read_rows(manifest_path)
    warnings: list[str] = []
    seen_ids: dict[str, int] = {}
    group_splits: dict[str, tuple[str, int]] = {}
    exact: dict[str, tuple[str, str, int]] = {}
    exact_duplicate_records = 0
    hashes: list[tuple[int, str, str, int]] = []
    counts_by_split = {split: 0 for split in sorted(SPLITS)}
    labels_by_type: dict[str, int] = {}

    for row in rows:
        line = row.pop("_line")
        prefix = f"line {line}"
        image_id = row.get("image_id")
        image_rel = row.get("image_path")
        label_rel = row.get("label_path")
        label_available = row.get("label_available")
        label_type = row.get("label_type")
        annotation = row.get("annotation_status")
        split = row.get("split")
        scene_group = row.get("scene_group")

        if not isinstance(image_id, str) or not image_id.strip():
            errors.append(f"{prefix}: image_id must be a non-empty string")
            continue
        if image_id in seen_ids:
            errors.append(f"{prefix}: duplicate image_id {image_id!r} (first at line {seen_ids[image_id]})")
        else:
            seen_ids[image_id] = line
        for field in ("source", "provenance", "scene_group"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{prefix}: {field} must be a non-empty string")
        if require_rights and not (isinstance(row.get("rights"), dict) and row["rights"].get("license") and row["rights"].get("source")):
            errors.append(f"{prefix}: explicit license/source rights record is required")
        if split not in SPLITS:
            errors.append(f"{prefix}: split must be one of {sorted(SPLITS)}")
        else:
            counts_by_split[split] += 1
        if isinstance(scene_group, str) and scene_group.strip() and split in SPLITS:
            prior = group_splits.get(scene_group)
            if prior and prior[0] != split:
                errors.append(f"{prefix}: scene_group {scene_group!r} leaks across {prior[0]} (line {prior[1]}) and {split}")
            else:
                group_splits[scene_group] = (split, line)
        if label_type not in LABEL_TYPES:
            errors.append(f"{prefix}: label_type must be one of {sorted(LABEL_TYPES)}")
        else:
            labels_by_type[label_type] = labels_by_type.get(label_type, 0) + 1
        if annotation not in ANNOTATION_STATES:
            errors.append(f"{prefix}: annotation_status must be one of {sorted(ANNOTATION_STATES)}")
        if not isinstance(label_available, bool):
            errors.append(f"{prefix}: label_available must be boolean")
        elif label_available and (label_type == "none" or not isinstance(label_rel, str) or not label_rel.strip()):
            errors.append(f"{prefix}: available labels require a label_path and a non-none label_type")
        elif not label_available and label_rel not in (None, ""):
            errors.append(f"{prefix}: label_path must be null/empty when label_available is false")
        if label_available and annotation not in {"in_progress", "reviewed"}:
            errors.append(f"{prefix}: available labels require annotation_status in_progress or reviewed")
        if label_available and isinstance(label_rel, str) and label_rel.strip():
            label_path = (manifest_path.parent / label_rel).resolve()
            if not label_path.is_relative_to(manifest_path.parent):
                errors.append(f"{prefix}: label_path must remain inside the manifest directory")
            elif not label_path.is_file():
                errors.append(f"{prefix}: label file does not exist: {label_rel}")
            elif row.get("label_sha256") and _sha256(label_path) != row["label_sha256"]:
                errors.append(f"{prefix}: label SHA256 differs from manifest")

        if not isinstance(image_rel, str) or not image_rel.strip():
            errors.append(f"{prefix}: image_path must be a non-empty path")
            continue
        image_path = (manifest_path.parent / image_rel).resolve()
        if not image_path.is_relative_to(manifest_path.parent):
            errors.append(f"{prefix}: image_path must remain inside the manifest directory")
            continue
        if not image_path.is_file():
            errors.append(f"{prefix}: image file does not exist: {image_rel}")
            continue
        try:
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(image_path) as image:
                    image.verify()
            digest = _sha256(image_path)
            perceptual = _dhash(image_path)
            if row.get("image_sha256") and digest != row["image_sha256"]:
                errors.append(f"{prefix}: image SHA256 differs from manifest")
        except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            errors.append(f"{prefix}: image cannot be decoded: {image_rel} ({type(exc).__name__})")
            continue
        if digest in exact:
            exact_duplicate_records += 1
            other_id, other_split, other_line = exact[digest]
            message = f"exact duplicate image content: {image_id!r} and {other_id!r}"
            if split != other_split:
                errors.append(f"{prefix}: {message} crosses {other_split} (line {other_line}) and {split}")
            else:
                warnings.append(f"{prefix}: {message} within split {split}")
        else:
            exact[digest] = (image_id, split, line)
        hashes.append((perceptual, image_id, split, line))

    # BK-tree enumerates all neighbors, instead of silently accepting a capped
    # candidate comparison. Bound diagnostic strings, not the actual audit.
    tree = HashTree()
    near_pairs = 0
    for index, (value, _image_id, _split, _line) in enumerate(hashes):
        for other in tree.neighbors(value, NEAR_DUPLICATE_MAX_HAMMING):
            near_pairs += 1
            left, right = hashes[other], hashes[index]
            distance = (left[0] ^ right[0]).bit_count()
            message = f"near-duplicate images {left[1]!r} and {right[1]!r} (dHash distance {distance})"
            if left[2] != right[2]:
                errors.append(f"{message} crosses {left[2]} (line {left[3]}) and {right[2]} (line {right[3]})")
            elif len(warnings) < 100:
                warnings.append(f"{message} within split {left[2]}; confirm same-scene grouping")
        tree.add(value, index)

    return {
        "manifest": str(manifest_path),
        "records": len(rows),
        "counts_by_split": counts_by_split,
        "label_records_by_type": labels_by_type,
        "exact_duplicate_records": exact_duplicate_records,
        "near_duplicate_hamming_threshold": NEAR_DUPLICATE_MAX_HAMMING,
        "near_duplicate_pairs": near_pairs,
        "duplicate_audit_complete": True,
        "errors": errors,
        "warnings": warnings,
        "valid": not errors,
    }
