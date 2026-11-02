"""Atomic, hash-checked update of only application files; retains profiles/media."""
from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

# The release builder fills these before embedding this file in CAP-NHAT.bat.
REVISION = ''
FILES: dict[str, str] = {}


def apply_update(root: Path, revision: str, files: dict[str, str], fetch=None) -> None:
    if not (root / 'runtime/python.exe').is_file() or not (root / 'app/app.py').is_file():
        raise ValueError('Hay dat CAP-NHAT.bat canh MO-UNG-DUNG.bat trong ban portable cu.')
    if fetch is None:
        def fetch(name):
            url = f'https://raw.githubusercontent.com/thutrang0807hp-ux/5gdfgfd/{revision}/{name}'
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read(2_000_001)
    allowed = {'app.py', 'windows_background.py', 'static/index.html',
               'static/app.js', 'static/style.css'}
    if set(files) != allowed:
        raise ValueError('Danh sach tep cap nhat khong hop le.')
    with tempfile.TemporaryDirectory(prefix='.gflow-update-', dir=root) as temp:
        staged, backups, installed = {}, {}, []
        for index, (name, expected) in enumerate(files.items()):
            content = fetch(name)
            if len(content) > 2_000_000 or hashlib.sha256(content).hexdigest() != expected:
                raise ValueError('Tep tai ve khong dung SHA256: ' + name)
            path = Path(temp) / str(index)
            path.write_bytes(content)
            staged[name] = path
        try:
            for name, path in staged.items():
                target = root / 'app' / name
                if not target.resolve().is_relative_to((root / 'app').resolve()):
                    raise ValueError('Duong dan cap nhat khong hop le.')
                backups[name] = target.read_bytes() if target.exists() else None
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, target)
                installed.append(name)
        except Exception:
            for name in reversed(installed):
                target = root / 'app' / name
                old = backups[name]
                if old is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(old)
            raise


if __name__ == '__main__':
    root = Path.cwd()
    print('GFlow Studio - cap nhat tai lai video va tu thu nho Chrome.')
    print('Tai khoan, lich su va video da tai se duoc giu nguyen.')
    input('Dong cua so dong lenh GFlow dang chay, roi nhan Enter de cap nhat: ')
    try:
        apply_update(root, REVISION, FILES)
    except Exception as exc:
        print('CHUA CAP NHAT: ' + str(exc))
        input('Nhan Enter de dong.')
        raise SystemExit(1)
    print('Cap nhat thanh cong. Dang mo GFlow Studio...')
    os.startfile(str(root / 'MO-UNG-DUNG.bat'))
