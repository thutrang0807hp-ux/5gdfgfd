"""Local, single-user Vietnamese web interface for the real gflow CLI."""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '.data'
OUTPUT = ROOT / 'out'
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()
WORK: queue.Queue = queue.Queue(maxsize=30)
RECOVERY_RE = re.compile(r'gflow\s+data\s+download\s+([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})(?![0-9a-fA-F-])')


def recovery_media(message: str) -> str | None:
    match = RECOVERY_RE.search(message)
    return match.group(1).lower() if match else None


def command() -> list[str]:
    return [sys.executable, '-m', 'gflow_cli']


def build_args(payload: dict, destination: Path) -> list[str]:
    action = payload.get('action', 'generate')
    profile = payload.get('profile', 'default')
    if not isinstance(profile, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', profile):
        raise ValueError('Tên tài khoản chỉ gồm chữ, số, dấu gạch ngang hoặc gạch dưới.')
    if action in ('login', 'status'):
        return ['auth', action, '--profile', profile] + (['--browser', 'chrome'] if action == 'login' else [])
    if action == 'download':
        media_id = payload.get('media_id', '')
        try:
            media_id = str(uuid.UUID(media_id))
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Mã video phải là UUID, không phải liên kết hay câu lệnh.') from None
        return ['data', 'download', media_id, '--profile', profile, '--out', str(destination)]
    if action != 'generate':
        raise ValueError('Thao tác không hợp lệ.')
    prompt = payload.get('prompt', '')
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 5000:
        raise ValueError('Nhập mô tả từ 1 đến 5000 ký tự.')
    kind = payload.get('kind', 'image')
    aspect = payload.get('aspect', '16:9')
    choices = ['16:9', '9:16'] + (['1:1', '4:3', '3:4'] if kind == 'image' else [])
    if kind not in ('image', 'video') or aspect not in choices:
        raise ValueError('Loại nội dung hoặc tỉ lệ không hợp lệ.')
    if kind == 'video' and payload.get('confirm_video') is not True:
        raise ValueError('Cần xác nhận sử dụng credit Google Flow để tạo video.')
    args = [kind, 't2i' if kind == 'image' else 't2v', '--profile', profile,
            '--aspect', aspect, '--out' if kind == 'image' else '--out-dir', str(destination)]
    if kind == 'image':
        model = payload.get('model', 'nano2')
        if model not in ('nano2', 'nano-pro', 'nano2-lite'):
            raise ValueError('Model không hợp lệ.')
        args += ['--model', model]
    # End option parsing: even a prompt starting with -- is plain text.
    return args + ['--', prompt.strip()]


def save_jobs() -> None:
    DATA.mkdir(exist_ok=True)
    temp = DATA / 'jobs.tmp'
    temp.write_text(json.dumps(JOBS, ensure_ascii=False), encoding='utf-8')
    temp.replace(DATA / 'jobs.json')


def load_jobs() -> None:
    path = DATA / 'jobs.json'
    if path.exists():
        JOBS.update(json.loads(path.read_text(encoding='utf-8')))
        for job in JOBS.values():
            if job['status'] in ('queued', 'running'):
                job.update(status='interrupted', message='Ứng dụng đã khởi động lại. Kiểm tra Flow trước khi tạo lại; tác vụ có thể đã được gửi.')
            if job.get('kind') == 'video' and job['status'] == 'failed':
                media_id = recovery_media(job.get('message', ''))
                if media_id:
                    job.update(status='download_failed', media_id=media_id)
        save_jobs()


def execute(args: list[str], env: dict, minimize: bool) -> subprocess.CompletedProcess:
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
    process = subprocess.Popen(command() + args, cwd=ROOT, env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding='utf-8',
                               errors='replace', **options)
    stopped = threading.Event()
    watcher = None
    if minimize and sys.platform == 'win32':
        from windows_background import minimize_flow_windows
        watcher = threading.Thread(target=minimize_flow_windows,
                                   args=(process.pid, stopped), daemon=True)
        watcher.start()
    try:
        try:
            stdout, stderr = process.communicate(timeout=1200)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    finally:
        stopped.set()
        if watcher:
            watcher.join(timeout=2)


def complete_job(job_id: str, result: subprocess.CompletedProcess) -> None:
    from gflow_cli.redaction import redact_sensitive_text
    raw = result.stdout + '\n' + result.stderr
    message = redact_sensitive_text(raw)[-16000:]
    with LOCK:
        job = JOBS[job_id]
        media_id = recovery_media(raw) if job.get('kind') == 'video' else None
        status = 'succeeded' if result.returncode == 0 else 'failed'
        if result.returncode != 0 and media_id:
            status = 'download_failed'
            job['media_id'] = media_id
        job.update(status=status, exit_code=result.returncode, message=message)
        save_jobs()


def worker() -> None:
    while True:
        job_id, args = WORK.get()
        with LOCK:
            JOBS[job_id]['status'] = 'running'
            save_jobs()
        env = dict(os.environ, GFLOW_CLI_UPDATE_CHECK='0', NO_COLOR='1', TERM='dumb',
                   GFLOW_CLI_OUTPUT_DIR=str(OUTPUT), PYTHONUTF8='1')
        try:
            # One queue serializes all browser-owning commands, including login.
            job = JOBS[job_id]
            result = execute(args, env, minimize=job.get('background', True) and job['action'] != 'login')
            complete_job(job_id, result)
        except subprocess.TimeoutExpired:
            status, code, message = 'indeterminate', None, 'Quá thời gian chờ. Kiểm tra dự án trên Google Flow trước khi thử lại; nội dung có thể vẫn đang được tạo.'
        except OSError:
            status, code, message = 'failed', None, 'Không khởi chạy được gflow-cli. Kiểm tra cài đặt Python.'
        else:
            WORK.task_done()
            continue
        with LOCK:
            JOBS[job_id].update(status=status, exit_code=code, message=message)
            save_jobs()
        WORK.task_done()


def enqueue(payload: dict) -> dict:
    job_id = uuid.uuid4().hex
    destination = OUTPUT / job_id
    source = None
    if payload.get('action') == 'recover':
        source_id = payload.get('source_id')
        if not isinstance(source_id, str):
            raise ValueError('Tác vụ gốc không hợp lệ.')
        with LOCK:
            source = dict(JOBS.get(source_id, {}))
            if any(j.get('source_id') == source_id and j['status'] in ('queued', 'running') for j in JOBS.values()):
                raise ValueError('Video này đang được tải lại. Hãy chờ tác vụ hiện tại.')
        media_id = source.get('media_id') or recovery_media(source.get('message', ''))
        if not media_id or source.get('kind') != 'video':
            raise ValueError('Chưa có mã video để tải lại. Hãy dùng mã video trong thông báo lỗi.')
        payload = dict(action='download', kind='video', media_id=media_id,
                       profile=source.get('profile', payload.get('profile', 'default')),
                       background=payload.get('background', True), source_id=source_id,
                       prompt=source.get('prompt', ''))
    args = build_args(payload, destination)
    with LOCK:
        if WORK.full():
            raise ValueError('Hàng đợi đã đầy. Hãy chờ các tác vụ hiện tại hoàn tất.')
        destination.mkdir(parents=True)
        job = dict(id=job_id, action=payload.get('action', 'generate'),
                   prompt=payload.get('prompt', ''), kind=payload.get('kind', 'image'),
                   profile=payload.get('profile', 'default'),
                   background=payload.get('background') is not False,
                   media_id=payload.get('media_id'), source_id=payload.get('source_id'),
                   status='queued', created=time.time(), message='', exit_code=None)
        JOBS[job_id] = job
        save_jobs()
        WORK.put_nowait((job_id, args))
        return dict(job)


def snapshot() -> list[dict]:
    with LOCK:
        jobs = [dict(j) for j in sorted(JOBS.values(), key=lambda j: j['created'], reverse=True)]
    for job in jobs:
        folder = OUTPUT / job['id']
        job['files'] = [p.relative_to(OUTPUT).as_posix() for p in folder.rglob('*')
                        if p.is_file() and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.mp4')
                        and p.resolve().is_relative_to(OUTPUT.resolve())] if folder.exists() else []
    return jobs


class Handler(BaseHTTPRequestHandler):
    def respond(self, code: int, value: dict | list) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def allowed(self) -> bool:
        expected = f'127.0.0.1:{self.server.server_port}'
        origin = self.headers.get('Origin')
        return (self.headers.get('Host') in (expected, f'localhost:{self.server.server_port}')
                and (not origin or origin in (f'http://{expected}', f'http://localhost:{self.server.server_port}')))

    def do_GET(self) -> None:
        if not self.allowed():
            self.respond(403, {'error': 'Chỉ truy cập từ ứng dụng trên máy này.'})
            return
        path = unquote(urlsplit(self.path).path)
        if path == '/api/health':
            from importlib.metadata import version
            from gflow_cli.auth import status
            state = status('default')
            self.respond(200, dict(ok=True, version=version('gflow-cli'),
                                  session_saved=bool(state['cookies_present']),
                                  display_available=bool(os.environ.get('DISPLAY') or sys.platform in ('win32', 'darwin'))))
            return
        if path == '/api/jobs':
            self.respond(200, snapshot())
            return
        if path in ('/GFlow-Studio-Portable-Windows.zip', '/demo/GFlow-Studio-Portable-Windows.zip'):
            file = ROOT / 'demo' / 'GFlow-Studio-Portable-Windows.zip'
        elif path in ('/demo', '/demo/'):
            file = ROOT / 'demo' / 'index.html'
        elif path in ('/', '/app.js', '/style.css'):
            file = ROOT / 'static' / {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[path]
        elif path.startswith('/out/'):
            file = (OUTPUT / path[5:]).resolve()
            if not file.is_relative_to(OUTPUT.resolve()) or file.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.mp4'):
                self.respond(404, {'error': 'Không tìm thấy tệp.'})
                return
        else:
            self.respond(404, {'error': 'Không tìm thấy.'})
            return
        if not file.is_file():
            self.respond(404, {'error': 'Không tìm thấy tệp.'})
            return
        import mimetypes
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(file.stat().st_size))
        if file.suffix == '.zip':
            self.send_header('Content-Disposition', 'attachment; filename="GFlow-Studio-Portable-Windows.zip"')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        with file.open('rb') as stream:
            import shutil
            shutil.copyfileobj(stream, self.wfile)

    def do_POST(self) -> None:
        if not self.allowed():
            self.respond(403, {'error': 'Nguồn yêu cầu không hợp lệ.'})
            return
        if self.path != '/api/jobs':
            self.respond(404, {'error': 'Không tìm thấy.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32000 or self.headers.get('Content-Type') != 'application/json':
                raise ValueError('Yêu cầu JSON không hợp lệ.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Yêu cầu không hợp lệ.')
            self.respond(202, enqueue(payload))
        except (ValueError, TypeError) as exc:
            self.respond(400, {'error': str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    try:
        import gflow_cli  # noqa: F401
    except ImportError:
        parser.error('Chưa cài gflow-cli. Xem README.md để cài đặt.')
    OUTPUT.mkdir(exist_ok=True)
    load_jobs()
    threading.Thread(target=worker, daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'GFlow Studio đang chạy trên cổng {server.server_port}. Nhấn Ctrl+C để dừng.')
    if args.open:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{server.server_port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
