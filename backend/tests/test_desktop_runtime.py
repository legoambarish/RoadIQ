import threading

from fastapi.testclient import TestClient

from app.main import create_app


def test_packaged_app_serves_dashboard_and_static_assets(tmp_path):
    index_path = tmp_path / 'index.html'
    index_path.write_text('<!doctype html><html><body>RoadIQ packaged dashboard</body></html>', encoding='utf-8')
    assets = tmp_path / 'assets'
    assets.mkdir()
    (assets / 'app.js').write_text('window.roadiq = true;', encoding='utf-8')

    client = TestClient(create_app(frontend_directory=tmp_path))

    page = client.get('/')
    assert page.status_code == 200
    assert 'RoadIQ packaged dashboard' in page.text
    assert 'text/html' in page.headers['content-type']
    assert client.get('/assets/app.js').text == 'window.roadiq = true;'
    assert client.get('/api/v1/health').json() == {'status': 'ok', 'service': 'RoadIQ API'}
    assert client.post('/__roadiq_internal/restart').status_code == 404


def test_desktop_restart_route_requires_token_and_signals_shutdown(tmp_path):
    app = create_app(frontend_directory=tmp_path)
    app.state.launcher_token = 'a' * 64
    app.state.restart_requested = threading.Event()
    client = TestClient(app)

    assert client.post('/__roadiq_internal/restart').status_code == 403
    response = client.post(
        '/__roadiq_internal/restart',
        headers={'Authorization': f"Bearer {app.state.launcher_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {'status': 'restart_requested'}
    assert app.state.restart_requested.is_set()


def test_instance_lock_records_metadata_and_releases(tmp_path):
    from launcher import InstanceLock, read_instance_metadata

    path = tmp_path / 'RoadIQ' / 'instance.lock'
    lock = InstanceLock(path)
    assert lock.try_acquire()
    expected = {'pid': 123, 'port': 54321, 'token': 'a' * 64, 'executable': r'C:\RoadIQ\RoadIQ.exe'}
    lock.write_metadata(expected)
    assert read_instance_metadata(path) == expected
    lock.release()

    next_lock = InstanceLock(path)
    assert next_lock.try_acquire()
    next_lock.release()


def test_restart_owner_validation_rejects_unrelated_executable():
    from launcher import is_owned_roadiq_process

    record = {
        'pid': 1,
        'port': 54321,
        'token': 'a' * 64,
        'executable': r'C:\RoadIQ\RoadIQ.exe',
    }
    assert is_owned_roadiq_process(record, r'C:\RoadIQ\RoadIQ.exe')
    assert not is_owned_roadiq_process(record, r'C:\Windows\notepad.exe')
    assert not is_owned_roadiq_process(record, None)