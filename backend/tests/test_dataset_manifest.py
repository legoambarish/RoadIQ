from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.dataset_manifest import validate_dataset_manifest


def _manifest_row(image_id: str, path: str, split: str = "train", group: str | None = None, **changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "image_id": image_id,
        "image_path": path,
        "label_available": False,
        "label_path": None,
        "label_type": "none",
        "annotation_status": "not_started",
        "source": "synthetic test fixture",
        "provenance": "test-only generated image",
        "split": split,
        "scene_group": group or f"scene-{image_id}",
    }
    row.update(changes)
    return row


def _write_manifest(root: Path, rows: list[dict[str, object]]) -> Path:
    path = root / "manifest.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def _image(path: Path, *, offset: int = 0) -> None:
    image = Image.new("RGB", (96, 72), (90 + offset, 92, 88))
    draw = ImageDraw.Draw(image)
    for x in range(4 + offset % 3, 96, 13):
        draw.ellipse((x, 10, x + 8, 18), fill=(120, 116, 105))
    image.save(path)


def test_manifest_parses_distinct_aggregate_and_defect_label_types(tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()
    _image(tmp_path / "images" / "a.png")
    _image(tmp_path / "images" / "b.png", offset=1)
    (tmp_path / "labels" / "a.json").write_text("[]", encoding="utf-8")
    (tmp_path / "labels" / "b.json").write_text("[]", encoding="utf-8")
    rows = [
        _manifest_row("a", "images/a.png", label_available=True, label_path="labels/a.json", label_type="aggregate_instance", annotation_status="reviewed"),
        _manifest_row("b", "images/b.png", label_available=True, label_path="labels/b.json", label_type="road_defect", annotation_status="reviewed", split="train"),
    ]
    report = validate_dataset_manifest(_write_manifest(tmp_path, rows))
    assert report["valid"] is True
    assert report["label_records_by_type"]["aggregate_instance"] == 1
    assert report["label_records_by_type"]["road_defect"] == 1


def test_manifest_rejects_missing_label_and_scene_group_split_leak(tmp_path: Path) -> None:
    _image(tmp_path / "a.png")
    _image(tmp_path / "b.png", offset=1)
    rows = [
        _manifest_row("a", "a.png", group="same-road", split="train", label_available=True, label_path="absent.json", label_type="aggregate_instance", annotation_status="reviewed"),
        _manifest_row("b", "b.png", group="same-road", split="test"),
    ]
    report = validate_dataset_manifest(_write_manifest(tmp_path, rows))
    assert report["valid"] is False
    assert any("label file" in error or "label_path" in error for error in report["errors"])
    assert any("scene_group" in error and "leaks across" in error for error in report["errors"])


def test_manifest_detects_exact_duplicate_content_across_splits(tmp_path: Path) -> None:
    _image(tmp_path / "a.png")
    (tmp_path / "copy.png").write_bytes((tmp_path / "a.png").read_bytes())
    rows = [_manifest_row("a", "a.png"), _manifest_row("copy", "copy.png", split="test")]
    report = validate_dataset_manifest(_write_manifest(tmp_path, rows))
    assert any("exact duplicate image content" in error and "crosses" in error for error in report["errors"])


def test_manifest_detects_perceptual_near_duplicate_across_splits(tmp_path: Path) -> None:
    _image(tmp_path / "a.png")
    near = Image.open(tmp_path / "a.png").copy()
    near.putpixel((48, 36), (255, 255, 255))
    near.save(tmp_path / "near.png")
    assert (tmp_path / "a.png").read_bytes() != (tmp_path / "near.png").read_bytes()
    rows = [_manifest_row("a", "a.png"), _manifest_row("near", "near.png", split="test")]
    report = validate_dataset_manifest(_write_manifest(tmp_path, rows))
    assert any("near-duplicate images" in error and "crosses" in error for error in report["errors"])


def test_manifest_flags_invalid_json_and_path_escape(tmp_path: Path) -> None:
    path = tmp_path / "manifest.jsonl"
    path.write_text('{"bad": }\n' + json.dumps(_manifest_row("escape", "../outside.jpg")) + "\n", encoding="utf-8")
    report = validate_dataset_manifest(path)
    assert report["valid"] is False
    assert any("invalid JSON" in error for error in report["errors"])
    assert any("remain inside" in error for error in report["errors"])
