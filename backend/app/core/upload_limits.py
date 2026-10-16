"""Bound raw multipart request bytes before the parser spools an upload to disk."""
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException


class UploadBodyTooLarge(HTTPException):
    def __init__(self):
        super().__init__(status_code=413, detail="Image upload request exceeds the byte limit.")


class ImageUploadLimitMiddleware:
    def __init__(self, app, max_bytes: int = 10 * 1024 * 1024 + 64 * 1024):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") != "POST" or not scope.get("path", "").endswith("/image-analyses"):
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        if b"content-length" in headers:
            try:
                declared = int(headers[b"content-length"])
                if declared < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({"detail": "Invalid Content-Length."}, status_code=400)(scope, receive, send)
            if declared > self.max_bytes:
                return await JSONResponse({"detail": "Image upload request exceeds the byte limit."}, status_code=413)(scope, receive, send)
        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    raise UploadBodyTooLarge
            return message
        try:
            return await self.app(scope, limited_receive, send)
        except UploadBodyTooLarge:
            return await JSONResponse({"detail": "Image upload request exceeds the byte limit."}, status_code=413)(scope, receive, send)
