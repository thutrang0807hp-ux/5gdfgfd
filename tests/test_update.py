import importlib.util
import hashlib
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('updater', Path(__file__).parents[1] / 'portable/update_portable.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


@pytest.fixture
def installation(tmp_path):
    (tmp_path / 'runtime').mkdir()
    (tmp_path / 'runtime/python.exe').write_bytes(b'Windows runtime fixture')
    (tmp_path / 'app/.data').mkdir(parents=True)
    (tmp_path / 'app/app.py').write_bytes(b'previous application')
    (tmp_path / 'app/.data/jobs.json').write_text('history')
    (tmp_path / 'data/profiles').mkdir(parents=True)
    (tmp_path / 'data/profiles/test').write_text('profile fixture')
    return tmp_path


def payload():
    names = ['app.py', 'windows_background.py', 'static/index.html', 'static/app.js', 'static/style.css']
    content = {name: ('new ' + name).encode() for name in names}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in content.items()}
    return content, hashes


def test_update_retains_login_history_and_runtime(installation):
    content, hashes = payload()
    updater.apply_update(installation, 'revision', hashes, content.__getitem__)
    assert (installation / 'app/app.py').read_bytes() == content['app.py']
    assert (installation / 'app/.data/jobs.json').read_text() == 'history'
    assert (installation / 'data/profiles/test').read_text() == 'profile fixture'
    assert (installation / 'runtime/python.exe').exists()


def test_bad_download_does_not_change_existing_installation(installation):
    content, hashes = payload()
    content['static/app.js'] = b'tampered'
    with pytest.raises(ValueError, match='SHA256'):
        updater.apply_update(installation, 'revision', hashes, content.__getitem__)
    assert (installation / 'app/app.py').read_bytes() == b'previous application'
    assert not (installation / 'app/windows_background.py').exists()
