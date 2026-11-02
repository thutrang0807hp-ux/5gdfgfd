import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location('studio', Path(__file__).parents[1] / 'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


@pytest.fixture
def server(tmp_path):
    with patch.object(app, 'OUTPUT', tmp_path / 'out'), patch.object(app, 'DATA', tmp_path / 'data'):
        app.OUTPUT.mkdir()
        app.JOBS.clear()
        while not app.WORK.empty():
            app.WORK.get_nowait()
        httpd = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f'http://127.0.0.1:{httpd.server_port}'
        httpd.shutdown()
        httpd.server_close()
        thread.join()


def post(url, value, origin=None):
    headers = {'Content-Type': 'application/json'}
    if origin:
        headers['Origin'] = origin
    return urllib.request.urlopen(urllib.request.Request(url + '/api/jobs', json.dumps(value).encode(), headers))


def test_health_uses_installed_engine(server):
    health = json.load(urllib.request.urlopen(server + '/api/health'))
    assert health['ok'] and health['version']
    assert isinstance(health['session_saved'], bool)


def test_standalone_demo_page(server):
    response = urllib.request.urlopen(server + '/demo')
    html = response.read().decode('utf-8')
    assert 'text/html' in response.headers['Content-Type']
    assert 'id="download-web"' in html
    assert 'id="download"' in html
    assert 'không phải ảnh/video AI' in html
    assert '<script src=' not in html


def test_enqueue_real_command_and_reload_interrupted(server):
    job = json.load(post(server, {'prompt': '--help; touch /tmp/not-a-command', 'profile': 'default'}))
    job_id, args = app.WORK.get_nowait()
    assert job['id'] == job_id
    assert args[-2:] == ['--', '--help; touch /tmp/not-a-command']
    assert args[:2] == ['image', 't2i']
    assert json.load(urllib.request.urlopen(server + '/api/jobs'))[0]['status'] == 'queued'
    app.JOBS.clear()
    app.load_jobs()
    assert app.JOBS[job_id]['status'] == 'interrupted'


@pytest.mark.parametrize('payload', [
    {'prompt': 'test', 'kind': 'video'},
    {'prompt': 'test', 'profile': '../outside'},
    {'prompt': 'test', 'model': '--help'},
    {'prompt': 'test', 'aspect': '0:0'},
    {'prompt': ''}, [],
])
def test_reject_invalid_requests(server, payload):
    with pytest.raises(urllib.error.HTTPError) as error:
        post(server, payload)
    assert error.value.code == 400
    assert not app.JOBS


def test_cross_origin_is_rejected(server):
    with pytest.raises(urllib.error.HTTPError) as error:
        post(server, {'prompt': 'test'}, 'https://unrelated.example')
    assert error.value.code == 403
    assert not app.JOBS


def test_download_path_cannot_escape_output(server):
    (app.OUTPUT.parent / 'secret.png').write_bytes(b'private')
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(server + '/out/%2e%2e/secret.png')
    assert error.value.code == 404
    (app.OUTPUT / 'image.png').write_bytes(b'example-image')
    assert urllib.request.urlopen(server + '/out/image.png').read() == b'example-image'


def test_models_are_accepted_by_real_cli(tmp_path):
    import os
    import subprocess
    env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', GFLOW_CLI_HOME=str(tmp_path / 'profiles'))
    # Missing login must produce an auth error, not invalid CLI syntax.
    args = app.build_args({'prompt': 'a mountain', 'model': 'nano2'}, tmp_path / 'out')
    result = subprocess.run(app.command() + args, capture_output=True, text=True, env=env, timeout=30)
    assert result.returncode != 0
    assert 'No such option' not in result.stderr
    assert 'session' in (result.stdout + result.stderr).lower()
