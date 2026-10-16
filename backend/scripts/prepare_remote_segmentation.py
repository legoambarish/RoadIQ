"""Acquire only original Indian Roads images/masks via verified ZIP member CRCs.

Avoids downloading the duplicate NumPy representation. Reuses range chunks left
by acquire_india_data. Whole-archive SHA is deliberately not claimed by this path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from backend.scripts.acquire_india_data import RemoteRange, SEG_URL, event, get_json

ARCHIVE_SIZE = 2881656373
BLOCK = 4 * 1024 * 1024
PREFIX = "Indian_road_data/Indian_road_data/"


class CachedRange(RemoteRange):
    def __init__(self, cache: Path):
        super().__init__(SEG_URL, ARCHIVE_SIZE)
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)

    def block(self, index: int) -> bytes:
        length = min(BLOCK, self.size - index * BLOCK)
        path = self.cache / f"{index:06d}.bin"
        if path.exists() and path.stat().st_size == length:
            return path.read_bytes()
        saved = self.position
        super().seek(index * BLOCK)
        data = super().read(length)
        self.position = saved
        partial = path.with_suffix(f".{threading.get_ident()}.part")
        partial.write_bytes(data)
        partial.replace(path)
        return data

    def read(self, size: int = -1) -> bytes:
        start = self.position
        size = self.size - start if size < 0 else min(size, self.size - start)
        if size <= 0:
            return b""
        chunks = []
        for index in range(start // BLOCK, (start + size - 1) // BLOCK + 1):
            data = self.block(index)
            low, high = max(0, start - index * BLOCK), min(len(data), start + size - index * BLOCK)
            chunks.append(data[low:high])
        self.position = start + size
        return b"".join(chunks)


def prepare(output: Path, cache: Path) -> None:
    output = output.resolve()
    cache = cache.resolve()
    output.mkdir(parents=True, exist_ok=True)
    primary = get_json("https://www.kaggle.com/api/v1/datasets/view/eyantraiit/semantic-segmentation-datasets-of-indian-roads")
    if primary.get("currentVersionNumber") != 2 or primary.get("licenseName", "").lower().replace(" ", "") != "gpl2":
        raise RuntimeError("Primary segmentation version/license changed; review before acquisition")
    (output / "primary-source-card.json").write_text(json.dumps(primary, indent=2), encoding="utf-8")
    remote = CachedRange(cache)
    with ZipFile(remote) as archive:
        members = []
        blocks = set()
        for info in archive.infolist():
            if not info.filename.startswith(PREFIX) or info.is_dir():
                continue
            relative = PurePosixPath(info.filename[len(PREFIX):])
            if not (relative.parts[0] == "Raw_images" and relative.suffix == ".jpg" or relative.parts[0] == "Masks" and relative.name.endswith("_gtFine_labelTrainIds.png")):
                continue
            target = (output / Path(*relative.parts)).resolve()
            if not target.is_relative_to(output.resolve()):
                raise ValueError("unsafe archive path")
            members.append((info, target))
            # Conservative upper bound includes variable local-header extra data.
            end = min(ARCHIVE_SIZE, info.header_offset + 30 + len(info.filename.encode()) + 65535 + info.compress_size)
            blocks.update(range(info.header_offset // BLOCK, (end - 1) // BLOCK + 1))
        event("segmentation_primary_prefetch", files=len(members), chunks=len(blocks), max_bytes=len(blocks) * BLOCK)
        local = threading.local()

        def fetch(index):
            if not hasattr(local, "reader"):
                local.reader = CachedRange(cache)
            local.reader.block(index)
            return index
        last = time.monotonic()
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(fetch, i) for i in sorted(blocks)]
            for count, future in enumerate(as_completed(futures), 1):
                future.result()
                if time.monotonic() - last > 15:
                    event("segmentation_prefetch_progress", chunks=count, total=len(blocks))
                    last = time.monotonic()
        ledger = []
        for index, (info, target) in enumerate(members):
            target.parent.mkdir(parents=True, exist_ok=True)
            # Reading each complete member verifies its published ZIP CRC.
            with archive.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            with target.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            ledger.append({"path": target.relative_to(output).as_posix(), "zip_crc32": info.CRC, "sha256": digest})
            if index % 500 == 0:
                event("segmentation_extraction_progress", files=index, total=len(members))
        report = {"source": "https://www.kaggle.com/datasets/eyantraiit/semantic-segmentation-datasets-of-indian-roads",
                  "source_version": 2, "license": "GPL-2.0 (Kaggle public metadata)", "acquisition": "selected ZIP members through HTTP ranges",
                  "whole_archive_sha256_verified": False, "all_selected_member_crcs_verified": True,
                  "files": ledger, "retrieval_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        (output / "acquisition.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        event("segmentation_primary_ready", files=len(ledger), output=str(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/indian-roads-v2"))
    parser.add_argument("--cache", type=Path, default=Path("data/sources/indian-roads-v2.zip.chunks"))
    args = parser.parse_args()
    prepare(args.output, args.cache)
