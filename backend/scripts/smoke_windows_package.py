"""Run the actual Windows executable with an isolated profile and no Python/Node on PATH.

Starts, uploads, relaunches through the owned-instance restart protocol, and stops
only this isolated instance. Authentication tokens never enter the saved evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import requests


def metadata(path: Path) -> dict:
    try:
        with path.open("rb") as source:
            source.seek(1)  # Windows locks byte zero; the launcher reserves it.
            return json.loads(source.read().decode("utf-8"))
    except (OSError, ValueError):
        return {}


def wait_ready(process: subprocess.Popen, lock: Path, previous_pid: int | None = None) -> dict:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Executable stopped during startup: exit {process.returncode}; inspect isolated profile logs")
        record = metadata(lock)
        if record.get("pid") and record.get("pid") != previous_pid:
            try:
                response = requests.get(f"http://127.0.0.1:{record['port']}/api/v1/health", timeout=2)
                if response.status_code == 200 and response.json().get("service") == "RoadIQ API":
                    return record
            except (requests.RequestException, ValueError):
                pass
        time.sleep(.25)
    raise TimeoutError("Executable did not become healthy within 180 seconds")


def stop_owned(record: dict) -> None:
    if record.get("token") and record.get("port"):
        try:
            requests.post(f"http://127.0.0.1:{record['port']}/__roadiq_internal/restart",
                          headers={"Authorization": f"Bearer {record['token']}"}, timeout=5).raise_for_status()
        except requests.RequestException:
            pass


def run(args) -> None:
    if os.name != "nt":
        raise RuntimeError("This check runs the real Windows package on Windows")
    executable = args.executable.resolve(strict=True)
    image = args.image.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    profile = output / "isolated-profile"
    lock = profile / "RoadIQ/instance.lock"
    if lock.exists():
        raise RuntimeError("Use a fresh output directory; never reuse another live profile")
    environment = os.environ.copy()
    for name in ("ROADIQ_DETECTOR_MODEL_PATH", "ROADIQ_SEGMENTATION_MODEL_PATH", "PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    environment.update(LOCALAPPDATA=str(profile), ROADIQ_HEADLESS="1",
                       PATH=str(Path(os.environ["SystemRoot"]) / "System32"))
    processes = []
    record = {}
    started = time.perf_counter()
    try:
        process = subprocess.Popen([str(executable)], env=environment, cwd=output,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        processes.append(process)
        record = wait_ready(process, lock)
        runtime_log = profile / "RoadIQ/logs/RoadIQ.log"
        standalone = "Running in standalone mode; no local repository detected." in runtime_log.read_text(encoding="utf-8")
        if not standalone:
            raise RuntimeError("Source checkout was discovered. Copy the EXE and use --output outside the repository to verify the standalone bundle.")
        first_pid = record["pid"]
        base = f"http://127.0.0.1:{record['port']}"
        page = requests.get(base + "/", timeout=10)
        assert page.status_code == 200 and '<div id="root">' in page.text
        readiness = requests.get(base + "/api/v1/vision-readiness", timeout=120).json()
        assert readiness["ready"] is args.require_models, readiness
        if args.require_models:
            assert readiness["roi"]["status"] == "loaded", readiness
        upload_started = time.perf_counter()
        with image.open("rb") as handle:
            response = requests.post(base + "/api/v1/image-analyses",
                                     files={"image": (image.name, handle, "image/jpeg")}, timeout=120)
        response.raise_for_status()
        analysis = response.json()
        assert analysis["contract_version"] == "image-analysis-v1.2"
        assert analysis["rsqi"]["value"] is None
        assert analysis["visual_distress"]["grade"] is None
        indicator = analysis["experimental_image_indicator"]
        if args.require_models:
            assert analysis["model"]["load_status"] == "loaded"
            assert analysis["processing_time_ms"]["detector"] > 0
            assert any(item["detections"] for item in analysis["defects"]), "Use a known candidate-producing genuine demo image"
            assert indicator["status"] in {"available", "limited"}
            assert isinstance(indicator["provisional_score"], (int, float))
        else:
            assert analysis["visual_distress"]["status"] == "unavailable"
        upload_ms = (time.perf_counter() - upload_started) * 1000
        (output / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        replacement = subprocess.Popen([str(executable)], env=environment, cwd=output,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        processes.append(replacement)
        record = wait_ready(replacement, lock, previous_pid=first_pid)
        process.wait(timeout=30)
        assert process.returncode == 0
        stop_owned(record)
        replacement.wait(timeout=30)
        assert replacement.returncode == 0
        summary = {"status": "passed", "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                   "executable_bytes": executable.stat().st_size, "models_required": args.require_models,
                   "python_and_node_on_child_path": False, "dashboard_http": page.status_code,
                   "standalone_no_source_checkout": standalone,
                   "vision_readiness": readiness, "upload_http": response.status_code,
                   "upload_ms": round(upload_ms, 2), "source_image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                   "graceful_owned_relaunch": True, "graceful_test_shutdown": True,
                   "total_seconds": round(time.perf_counter() - started, 2)}
        (output / "package-smoke.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps({"status": "passed", "evidence": str(output / "package-smoke.json")}), flush=True)
    finally:
        stop_owned(record)
        for child in processes:
            if child.poll() is None:
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Popen handles are exclusively the children created above.
                    child.terminate()
                    child.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-models", action="store_true")
    run(parser.parse_args())
