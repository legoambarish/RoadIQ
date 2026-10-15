from pathlib import Path
import secrets
import sys
import threading

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.core.config import get_settings


DESKTOP_RESTART_PATH = '/__roadiq_internal/restart'


def _bundled_frontend_directory() -> Path | None:
    """Return the packaged dashboard directory when running from the desktop bundle."""
    if not getattr(sys, 'frozen', False):
        return None

    bundle_root = getattr(sys, '_MEIPASS', None)
    if not bundle_root:
        return None

    frontend_directory = Path(bundle_root) / 'frontend' / 'dist'
    if (frontend_directory / 'index.html').is_file():
        return frontend_directory
    return None


def create_app(frontend_directory: Path | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title='RoadIQ API',
        version='0.1.0',
        description='Initial RoadIQ backend scaffold for road intelligence tooling.',
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings['cors_origins'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(health_router, prefix=settings['api_prefix'])
    app.state.launcher_token = None
    app.state.restart_requested = None

    @app.post(DESKTOP_RESTART_PATH, include_in_schema=False)
    def restart_previous_desktop_instance(authorization: str | None = Header(default=None)) -> dict[str, str]:
        token = app.state.launcher_token
        restart_requested = app.state.restart_requested
        if not isinstance(token, str) or not isinstance(restart_requested, threading.Event):
            raise HTTPException(status_code=404, detail='Not found.')
        if not secrets.compare_digest(authorization or '', f'Bearer {token}'):
            raise HTTPException(status_code=403, detail='Restart request was not authorized.')
        restart_requested.set()
        return {'status': 'restart_requested'}

    bundled_frontend = frontend_directory or _bundled_frontend_directory()
    if bundled_frontend is not None and (bundled_frontend / 'index.html').is_file():
        index_path = bundled_frontend / 'index.html'

        @app.get('/', include_in_schema=False)
        def dashboard() -> FileResponse:
            return FileResponse(index_path)

        # Keep API and launcher routes above this mount so they retain their paths.
        app.mount('/', StaticFiles(directory=str(bundled_frontend), html=True), name='dashboard-assets')
    else:
        @app.get('/')
        def root() -> dict[str, str]:
            return {'message': 'RoadIQ API is running'}

    return app


app = create_app()
