"""Generate the small Windows updater pinned to the current source commit."""
import base64
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
names = ['app.py', 'windows_background.py', 'static/index.html', 'static/app.js', 'static/style.css']
hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
source = (root / 'portable/update_portable.py').read_text()
source = source.replace("REVISION = ''", 'REVISION = ' + repr(revision))
source = source.replace('FILES: dict[str, str] = {}', 'FILES = ' + repr(hashes))
encoded = base64.b64encode(source.encode()).decode()
command = '"%~dp0runtime\\python.exe" -s -c "import base64;exec(base64.b64decode(\'' + encoded + '\'))"'
if len(command) > 7800:
    raise ValueError('Updater exceeds the Windows command-line length limit')
batch = '\n'.join([
    '@echo off', 'setlocal', 'cd /d "%~dp0"',
    'set "PYTHONHOME="', 'set "PYTHONPATH="', 'set "PYTHONNOUSERSITE=1"',
    'set "PYTHONUTF8=1"',
    'if not exist "%~dp0runtime\\python.exe" (',
    '  echo Hay chep CAP-NHAT.bat vao CUNG THU MUC voi MO-UNG-DUNG.bat roi mo lai.',
    '  pause', '  exit /b 1', ')', command,
    'if errorlevel 1 pause', '',
]).replace('\n', '\r\n')
destination = root / 'GFlow-Studio-Cap-Nhat.zip'
with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('CAP-NHAT.bat', batch)
    archive.writestr('HUONG-DAN.txt',
        'Chep CAP-NHAT.bat vao canh MO-UNG-DUNG.bat trong thu muc portable cu.\r\n'
        'Mo CAP-NHAT.bat. Dong cua so dong lenh GFlow dang chay, nhan Enter.\r\n'
        'Tai khoan, catalog video, lich su va video duoc giu nguyen.\r\n'
        'Can Internet de tai 5 tep ung dung da duoc khoa SHA256.\r\n')
    archive.writestr('update-manifest.json', json.dumps({'revision': revision, 'files': hashes}, indent=2))
print(f'Updater {destination.name}: {destination.stat().st_size} bytes; source commit {revision}')
