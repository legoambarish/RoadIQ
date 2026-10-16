"""Real HTTP admission/liveness boundary with an explicitly blocking test analyzer.

This checks threading/backpressure, not learned-model accuracy. The separate
integration gate requires the genuine trained assets and source images.
"""
from concurrent.futures import ThreadPoolExecutor
import io
import threading

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def test_two_blocked_analyses_keep_health_live_and_reject_excess_then_release(monkeypatch):
    entered = 0
    condition = threading.Condition()
    release = threading.Event()

    def blocking_analyzer(*, image_bytes, source_name):
        nonlocal entered
        with condition:
            entered += 1
            condition.notify_all()
        if not release.wait(timeout=10):
            raise RuntimeError("Test did not release its blocking analyzer")
        return {"image": {"format": "jpeg"}, "image_quality": {"usable": True, "issues": []},
                "model": {"load_status": "not_configured"}, "defects": [], "processing_errors": []}

    monkeypatch.setattr("app.api.routes.image_analysis.analyze_road_image", blocking_analyzer)
    stream = io.BytesIO()
    Image.new("RGB", (400, 300), "gray").save(stream, format="JPEG")
    payload = stream.getvalue()
    with TestClient(create_app()) as client, ThreadPoolExecutor(max_workers=2) as pool:
        def upload():
            return client.post("/api/v1/image-analyses", files={"image": ("road.jpg", payload, "image/jpeg")})
        jobs = [pool.submit(upload) for _ in range(2)]
        try:
            with condition:
                assert condition.wait_for(lambda: entered == 2, timeout=5), "Inference blocked the event loop or failed admission"
            assert client.get("/api/v1/health").status_code == 200
            excess = upload()
            assert excess.status_code == 503
            assert excess.headers["Retry-After"] == "2"
        finally:
            release.set()
        assert [job.result(timeout=5).status_code for job in jobs] == [200, 200]
        assert upload().status_code == 200, "Admission slot leaked after completed work"
