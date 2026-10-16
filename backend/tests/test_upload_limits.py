from fastapi.testclient import TestClient

from app.core.upload_limits import ImageUploadLimitMiddleware
from app.main import create_app


def client_with_small_budget():
    app = create_app()
    app.add_middleware(ImageUploadLimitMiddleware, max_bytes=512)
    return TestClient(app)


def test_declared_oversized_multipart_rejected_before_parsing():
    response = client_with_small_budget().post(
        "/api/v1/image-analyses", content=b"bad", headers={"content-length": "513"})
    assert response.status_code == 413


def test_chunked_multipart_is_bounded_without_content_length():
    header = b'--abc\r\nContent-Disposition: form-data; name="image"; filename="x.png"\r\nContent-Type: image/png\r\n\r\n'
    response = client_with_small_budget().post(
        "/api/v1/image-analyses", content=iter([header, b"x" * 600, b"\r\n--abc--\r\n"]),
        headers={"content-type": "multipart/form-data; boundary=abc"})
    assert response.status_code == 413


def test_negative_declared_length_rejected():
    response = client_with_small_budget().post(
        "/api/v1/image-analyses", content=b"", headers={"content-length": "-1"})
    assert response.status_code == 400
