"""Acquire the two reviewed India datasets without downloading other countries.

Uses HTTP Range to retrieve the stored India.zip member of the official Figshare
release. The old country-specific S3 URL returns 403. No API key is required.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import time
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from zipfile import ZipFile

RDD_RECORD = "https://api.figshare.com/v2/articles/21431547"
RDD_URL = "https://api.figshare.com/v2/file/download/38030910"
SEG_URL = "https://www.kaggle.com/api/v1/datasets/download/eyantraiit/semantic-segmentation-datasets-of-indian-roads"


def fresh_url(url: str) -> str:
    # Figshare redirects expire after ten seconds. Intermediary caches otherwise
    # replay expired signatures across range requests even with no-cache headers.
    if "figshare.com/" in url:
        return url + ("&" if "?" in url else "?") + f"roadiq_request={time.time_ns()}"
    return url


def event(message: str, **fields: object) -> None:
    print(json.dumps({"time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": message, **fields}), flush=True)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


class RemoteRange(io.RawIOBase):
    """Seekable read-only ZIP directory access; reject servers ignoring ranges."""
    def __init__(self, url: str, size: int):
        self.url, self.size, self.position = url, size, 0
        self.session = None

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if not 0 <= self.position <= self.size:
            raise ValueError("range seek outside archive")
        return self.position

    def read(self, size: int = -1) -> bytes:
        size = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if size == 0:
            return b""
        if size > 4 * 1024 * 1024:
            raise ValueError("directory read unexpectedly large")
        for attempt in range(5):
            try:
                import requests
                if self.session is None:
                    self.session = requests.Session()
                    if "figshare.com" in self.url:
                        try:
                            self.session.get("https://s3-eu-west-1.amazonaws.com/", timeout=20).close()
                        except requests.RequestException:
                            pass
                with self.session.get(fresh_url(self.url), headers={"Range": f"bytes={self.position}-{self.position + size - 1}"}, timeout=(20, 30), stream=True) as response:
                    if response.status_code != 206:
                        raise RuntimeError("server did not honor HTTP range")
                    data = response.raw.read(size + 1)
                break
            except Exception as exc:
                event("directory_range_retry", offset=self.position, attempt=attempt + 1, error_type=type(exc).__name__)
                if attempt == 4:
                    raise
        if len(data) != size:
            raise RuntimeError("short or overlong range response")
        self.position += len(data)
        return data


def download(url: str, target: Path, *, byte_range: tuple[int, int] | None = None) -> str:
    partial = target.with_suffix(target.suffix + ".part")
    headers = {"Range": f"bytes={byte_range[0]}-{byte_range[1]}"} if byte_range else {}
    event("download_started", file=target.name)
    digest, count, last = hashlib.sha256(), 0, time.monotonic()
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        if byte_range and response.status != 206:
            raise RuntimeError("server did not honor HTTP range")
        with partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                count += len(chunk)
                if time.monotonic() - last > 15:
                    event("download_progress", file=target.name, bytes=count)
                    last = time.monotonic()
    if byte_range and count != byte_range[1] - byte_range[0] + 1:
        raise RuntimeError("download length mismatch")
    partial.replace(target)
    event("download_completed", file=target.name, bytes=count, sha256=digest.hexdigest())
    return digest.hexdigest()


def parallel_download(url: str, target: Path, *, start: int = 0, size: int, workers: int = 12) -> str:
    """Bounded parallel range acquisition; each range is verified and retryable."""
    chunks = target.parent / (target.name + ".chunks")
    chunks.mkdir(parents=True, exist_ok=True)
    chunk_size = 4 * 1024 * 1024
    count = (size + chunk_size - 1) // chunk_size
    event("parallel_download_started", file=target.name, bytes=size, workers=workers, chunks=count)
    thread_state = threading.local()

    def fetch(index: int) -> int:
        offset = index * chunk_size
        length = min(chunk_size, size - offset)
        destination = chunks / f"{index:06d}.bin"
        if destination.exists() and destination.stat().st_size == length:
            return length
        for attempt in range(5):
            try:
                import requests
                if not hasattr(thread_state, "session"):
                    thread_state.session = requests.Session()
                    if "figshare.com" in url:
                        try:
                            thread_state.session.get("https://s3-eu-west-1.amazonaws.com/", timeout=20).close()
                        except requests.RequestException:
                            pass
                with thread_state.session.get(fresh_url(url), headers={"Range": f"bytes={start + offset}-{start + offset + length - 1}"}, timeout=(20, 120), stream=True) as response:
                    expected = f"bytes {start + offset}-{start + offset + length - 1}/"
                    if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith(expected):
                        raise RuntimeError("server returned wrong byte range")
                    data = response.raw.read(length + 1)
                if len(data) != length:
                    raise RuntimeError("range response length mismatch")
                destination.write_bytes(data)
                return length
            except Exception as exc:
                event("range_retry", file=target.name, chunk=index, attempt=attempt + 1, error_type=type(exc).__name__)
                if attempt == 4:
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise AssertionError("unreachable")

    completed, last = 0, time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for future in as_completed([executor.submit(fetch, i) for i in range(count)]):
            completed += future.result()
            if time.monotonic() - last >= 15 or completed == size:
                event("parallel_download_progress", file=target.name, bytes=completed, total=size)
                last = time.monotonic()
    partial = target.with_suffix(target.suffix + ".assembled")
    digest = hashlib.sha256()
    with partial.open("wb") as output:
        for index in range(count):
            data = (chunks / f"{index:06d}.bin").read_bytes()
            digest.update(data)
            output.write(data)
    partial.replace(target)
    event("parallel_download_completed", file=target.name, sha256=digest.hexdigest(), bytes=size)
    return digest.hexdigest()


def acquire(root: Path, segmentation: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if segmentation:
        # Public card: GPL 2; source archive v2. Rights obligations stay attached.
        target = root / "indian-roads-v2.zip"
        if not target.exists():
            parallel_download(SEG_URL, target, size=2881656373)
        with target.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != "a25aa4922fa4b7af7098832fad3f31f226721d4638abca1970081c0fe35a09af":
            raise RuntimeError("segmentation archive differs from reviewed v2; review before training")
        return
    record = get_json(RDD_RECORD)
    if record["license"]["name"] != "CC BY 4.0":
        raise RuntimeError("official RDD2022 license changed; review before use")
    (root / "rdd2022-official-record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    file = next(item for item in record["files"] if item["id"] == 38030910)
    remote = RemoteRange(RDD_URL, file["size"])
    with ZipFile(remote) as archive:
        members = [item for item in archive.infolist() if item.filename.endswith("/India.zip") or item.filename == "India.zip"]
        if len(members) != 1:
            raise RuntimeError(f"expected one India ZIP, got {[x.filename for x in members]}")
        member = members[0]
        if member.compress_type != 0:
            raise RuntimeError("India member is not stored; cannot directly range-download")
        remote.seek(member.header_offset)
        header = remote.read(30)
        filename_length, extra_length = struct.unpack_from("<HH", header, 26)
        start = member.header_offset + 30 + filename_length + extra_length
        (root / "rdd2022-india-member.json").write_text(json.dumps({"name": member.filename, "start": start, "size": member.file_size, "crc32": member.CRC}), encoding="utf-8")
        target = root / "RDD2022_India.zip"
        if not target.exists():
            digest = parallel_download(RDD_URL, target, start=start, size=member.file_size)
        else:
            with target.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
        import zlib
        member_crc = 0
        with target.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                member_crc = zlib.crc32(chunk, member_crc)
        if target.stat().st_size != member.file_size or member_crc != member.CRC:
            raise RuntimeError("India member differs from official outer ZIP directory")
        # Validate the nested ZIP CRCs before using any images.
        with ZipFile(target) as india:
            bad = india.testzip()
            if bad:
                raise RuntimeError(f"India ZIP CRC failure: {bad}")
        ledger = {"source": RDD_RECORD, "outer_file_id": file["id"], "outer_published_md5_not_locally_verified": file["computed_md5"],
                  "member": member.filename, "member_crc32": member.CRC, "member_crc32_verified": True,
                  "all_inner_member_crcs_verified": True, "size": member.file_size, "sha256": digest,
                  "license": record["license"], "geography": "India", "retrieval_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        (root / "rdd2022-india-acquisition.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        event("india_archive_verified", **ledger)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/sources"))
    parser.add_argument("--segmentation", action="store_true")
    args = parser.parse_args()
    acquire(args.output, args.segmentation)
