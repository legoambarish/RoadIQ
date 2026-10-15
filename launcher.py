from __future__ import annotations

import ctypes
import errno
import http.client
import json
import logging
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


APP_NAME = 'RoadIQ'
CONTROL_PATH = '/__roadiq_internal/restart'
STARTUP_TIMEOUT_SECONDS = 30.0
RESTART_TIMEOUT_SECONDS = 25.0


class LaunchError(RuntimeError):
    """A startup or safe-restart failure that should be shown to the user."""


def app_data_directory() -> Path:
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    return Path.home() / 'AppData' / 'Local' / APP_NAME


def log_file_path() -> Path:
    return app_data_directory() / 'logs' / 'RoadIQ.log'


def configure_logging() -> logging.Logger:
    destination = log_file_path()
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger('roadiq')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = RotatingFileHandler(
        destination,
        maxBytes=1_000_000,
        backupCount=5,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def show_error(message: str) -> None:
    if os.name == 'nt':
        try:
            ctypes.windll.user32.MessageBoxW(None, message, 'RoadIQ could not start', 0x10)
            return
        except Exception:
            pass

    stream = getattr(sys, 'stderr', None)
    if stream is not None:
        try:
            stream.write(f'RoadIQ could not start: {message}\n')
        except Exception:
            pass


class InstanceLock:
    """Cross-process lock whose metadata is used only for a token-authenticated restart."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def try_acquire(self) -> bool:
        if self._handle is not None:
            return True

        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open('a+b')
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'\0')
            handle.flush()
        handle.seek(0)

        try:
            if os.name == 'nt':
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            handle.close()
            if error.errno in (errno.EACCES, errno.EAGAIN) or getattr(error, 'winerror', None) in (33, 36):
                return False
            raise

        self._handle = handle
        return True

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        if self._handle is None:
            raise LaunchError('RoadIQ does not hold its instance lock.')

        payload = (json.dumps(metadata, separators=(',', ':')) + '\n').encode('utf-8')
        self._handle.seek(0)
        self._handle.truncate(0)
        self._handle.seek(0)
        self._handle.write(b'\0' + payload)
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def release(self) -> None:
        if self._handle is None:
            return

        handle = self._handle
        self._handle = None
        try:
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def read_instance_metadata(path: Path) -> dict[str, Any] | None:
    try:
        with path.open('rb') as metadata_file:
            metadata_file.seek(1)  # Byte zero stays reserved for the cross-process lock.
            metadata = json.loads(metadata_file.read().decode('utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return metadata if isinstance(metadata, dict) else None


def _normalized_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def is_owned_roadiq_process(metadata: dict[str, Any], image_path: str | None) -> bool:
    """Verify both the marker's executable and the live process image before signaling."""
    if not image_path:
        return False
    pid = metadata.get('pid')
    port = metadata.get('port')
    token = metadata.get('token')
    recorded_executable = metadata.get('executable')
    if type(pid) is not int or pid <= 0:
        return False
    if type(port) is not int or not 1 <= port <= 65535:
        return False
    if not isinstance(token, str) or len(token) < 32:
        return False
    if not isinstance(recorded_executable, str):
        return False
    if Path(image_path).name.casefold() != 'roadiq.exe':
        return False
    return _normalized_path(image_path) == _normalized_path(recorded_executable)


def process_image_path(pid: int) -> str | None:
    if os.name != 'nt':
        try:
            return os.readlink(f'/proc/{pid}/exe')
        except OSError:
            return None

    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    open_process.restype = wintypes.HANDLE
    query_image = kernel32.QueryFullProcessImageNameW
    query_image.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    query_image.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    process = open_process(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not process:
        return None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not query_image(process, 0, buffer, ctypes.byref(size)):
            return None
        return buffer.value
    finally:
        close_handle(process)


def request_graceful_restart(port: int, token: str) -> bool:
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=1.5)
    try:
        connection.request(
            'POST',
            CONTROL_PATH,
            body=b'',
            headers={'Authorization': f'Bearer {token}', 'Content-Length': '0'},
        )
        response = connection.getresponse()
        response.read()
        return response.status == HTTPStatus.OK
    finally:
        connection.close()


def acquire_or_restart(lock: InstanceLock, logger: logging.Logger) -> InstanceLock:
    if lock.try_acquire():
        return lock

    logger.info('An instance lock is already held; checking its owner before requesting a restart.')
    deadline = time.monotonic() + RESTART_TIMEOUT_SECONDS
    last_signal_attempt = 0.0
    signaled_pid: int | None = None

    while time.monotonic() < deadline:
        metadata = read_instance_metadata(lock.path)
        if metadata is not None:
            pid = metadata.get('pid')
            if type(pid) is int and pid > 0:
                image_path = process_image_path(pid)
                if is_owned_roadiq_process(metadata, image_path):
                    now = time.monotonic()
                    if signaled_pid != pid or now - last_signal_attempt >= 2.0:
                        try:
                            accepted = request_graceful_restart(metadata['port'], metadata['token'])
                        except (OSError, http.client.HTTPException):
                            accepted = False
                        last_signal_attempt = now
                        signaled_pid = pid
                        if accepted:
                            logger.info('Requested a graceful RoadIQ restart for PID %s.', pid)
                elif signaled_pid != pid:
                    logger.warning('The process holding the RoadIQ lock did not verify as RoadIQ; it was left alone.')
                    signaled_pid = pid

        if lock.try_acquire():
            logger.info('The previous RoadIQ instance released its lock; starting the new instance.')
            return lock
        time.sleep(0.25)

    raise LaunchError(
        'RoadIQ could not safely restart the existing instance. No unverified process was stopped. '
        'Close the earlier RoadIQ app and try again.'
    )


def create_desktop_app(token: str, restart_requested: threading.Event):
    os.environ['API_PREFIX'] = '/api/v1'
    os.environ['FASTAPI_ENV'] = 'production'
    os.environ.setdefault('CORS_ORIGINS', 'http://127.0.0.1')

    if getattr(sys, 'frozen', False):
        backend_directory = Path(getattr(sys, '_MEIPASS')) / 'backend'
    else:
        backend_directory = Path(__file__).resolve().parent / 'backend'
    if str(backend_directory) not in sys.path:
        sys.path.insert(0, str(backend_directory))

    from app.main import app

    app.state.launcher_token = token
    app.state.restart_requested = restart_requested
    return app


def bind_loopback_socket() -> tuple[socket.socket, int]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('127.0.0.1', 0))
    listener.listen(socket.SOMAXCONN)
    listener.setblocking(False)
    return listener, listener.getsockname()[1]


def _get_http_response(port: int, path: str) -> tuple[int, str, bytes]:
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=1.0)
    try:
        connection.request('GET', path)
        response = connection.getresponse()
        body = response.read(2_000_000)
        return response.status, response.getheader('Content-Type', ''), body
    finally:
        connection.close()


def wait_for_dashboard(
    port: int,
    server_thread: threading.Thread,
    restart_requested: threading.Event,
    logger: logging.Logger,
) -> str:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if not server_thread.is_alive():
            raise LaunchError('The local RoadIQ server stopped during startup.')
        if restart_requested.is_set():
            raise LaunchError('RoadIQ was asked to restart while it was starting.')
        try:
            status, _, health_body = _get_http_response(port, '/api/v1/health')
            health = json.loads(health_body.decode('utf-8')) if status == HTTPStatus.OK else {}
            if health.get('status') != 'ok' or health.get('service') != 'RoadIQ API':
                raise LaunchError('RoadIQ backend health check returned an unexpected response.')

            status, content_type, page_body = _get_http_response(port, '/')
            if status == HTTPStatus.OK and 'text/html' in content_type.lower() and b'<html' in page_body.lower():
                return f'http://127.0.0.1:{port}/'
            raise LaunchError('The bundled RoadIQ dashboard did not return an HTML page.')
        except (OSError, http.client.HTTPException, json.JSONDecodeError, LaunchError) as error:
            last_error = error
            time.sleep(0.25)

    logger.error('Startup checks did not pass: %s', last_error)
    raise LaunchError(f'RoadIQ did not become ready within {STARTUP_TIMEOUT_SECONDS:.0f} seconds.')


def _start_server(app, listener: socket.socket):
    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host='127.0.0.1',
            port=listener.getsockname()[1],
            log_level='info',
            log_config=None,
            access_log=False,
        )
    )
    server.install_signal_handlers = lambda: None
    thread = threading.Thread(
        target=server.run,
        kwargs={'sockets': [listener]},
        name='RoadIQ-local-server',
        daemon=False,
    )
    thread.start()
    return server, thread


def run() -> int:
    logger: logging.Logger | None = None
    lock: InstanceLock | None = None
    listener: socket.socket | None = None
    server = None
    server_thread: threading.Thread | None = None
    restart_requested = threading.Event()

    try:
        logger = configure_logging()
        logger.info('Starting RoadIQ desktop application.')

        lock = InstanceLock(app_data_directory() / 'instance.lock')
        acquire_or_restart(lock, logger)

        token = secrets.token_hex(32)
        app = create_desktop_app(token, restart_requested)
        listener, port = bind_loopback_socket()
        lock.write_metadata({
            'pid': os.getpid(),
            'port': port,
            'token': token,
            'executable': str(Path(sys.executable).resolve()),
            'started_at': time.time(),
        })
        server, server_thread = _start_server(app, listener)

        dashboard_url = wait_for_dashboard(port, server_thread, restart_requested, logger)
        logger.info('Backend health and dashboard checks passed at %s.', dashboard_url)
        try:
            browser_opened = webbrowser.open(dashboard_url, new=2, autoraise=True)
        except Exception:
            browser_opened = False
            logger.exception('Opening the default browser failed.')
        if browser_opened:
            logger.info('Opened the RoadIQ dashboard in the default browser.')
        else:
            logger.warning('RoadIQ is ready, but Windows did not open the default browser.')
            show_error(
                'RoadIQ is running, but Windows could not open a browser automatically.\n\n'
                f'Open this local address:\n{dashboard_url}\n\n'
                f'Log file: {log_file_path()}'
            )

        while server_thread.is_alive():
            if restart_requested.is_set() and not server.should_exit:
                logger.info('Received a token-authenticated graceful restart request.')
                server.should_exit = True
            server_thread.join(timeout=0.25)

        if restart_requested.is_set():
            logger.info('RoadIQ stopped cleanly for restart.')
            return 0
        raise LaunchError('The RoadIQ server stopped unexpectedly. Check the startup log for details.')
    except Exception as error:
        if logger is None:
            try:
                logger = configure_logging()
            except Exception:
                logger = None
        if logger is not None:
            logger.exception('RoadIQ startup failed: %s', error)
        show_error(f'{error}\n\nLog file: {log_file_path()}')
        return 1
    finally:
        if server is not None:
            server.should_exit = True
        if server_thread is not None and server_thread.is_alive():
            server_thread.join()
        if listener is not None:
            try:
                listener.close()
            except OSError:
                pass
        if lock is not None:
            lock.release()


def main() -> None:
    raise SystemExit(run())


if __name__ == '__main__':
    main()