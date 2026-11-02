"""Package a verified uv Windows runtime and hash-locked Windows wheel installation.

Inputs must be prepared with TLS/hash verification enabled. This packages files;
it does not claim Windows execution has been tested on the Linux build host.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path


def package(runtime: Path, site: Path, output: Path) -> None:
    from packaging.tags import compatible_tags, cpython_tags, parse_tag

    root = Path(__file__).resolve().parents[1]
    supported = set(cpython_tags((3, 12), platforms=['win_amd64']))
    supported.update(compatible_tags((3, 12), interpreter='cp312', platforms=['win_amd64']))
    wheels = list(site.glob('*.dist-info/WHEEL'))
    if len(wheels) < 50:
        raise ValueError('Missing expected dependency distributions')
    for wheel in wheels:
        tags = set()
        for line in wheel.read_text().splitlines():
            if line.startswith('Tag: '):
                tags.update(parse_tag(line[5:]))
        if not tags & supported:
            raise ValueError(f'Wheel incompatible with Windows Python 3.12: {wheel.parent.name}')
    native_lz4 = site / 'lz4/block/_block.cp312-win_amd64.pyd'
    if not native_lz4.is_file():
        raise ValueError('Missing precompiled Windows lz4')
    for exe in (runtime / 'python.exe', site / 'playwright/driver/node.exe', native_lz4):
        data = exe.read_bytes()
        pe = struct.unpack_from('<I', data, 0x3C)[0]
        if data[:2] != b'MZ' or data[pe:pe + 4] != b'PE\0\0':
            raise ValueError(f'Invalid Windows PE binary: {exe}')
        if struct.unpack_from('<H', data, pe + 4)[0] != 0x8664:
            raise ValueError(f'Not a Windows x64 binary: {exe}')

    files: dict[str, Path] = {}
    for source, prefix in ((runtime, 'runtime'), (site, 'runtime/Lib/site-packages')):
        for path in source.rglob('*'):
            if path.is_file():
                files[f'{prefix}/{path.relative_to(source).as_posix()}'] = path
    for name in ('app.py', 'windows_background.py', 'static/index.html', 'static/style.css', 'static/app.js'):
        files['app/' + name] = root / name
    for name in ('MO-UNG-DUNG.bat', 'DOC-TRUOC.txt'):
        files[name] = root / 'portable' / name

    hashes = []
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(files.items()):
            data = path.read_bytes()
            if name.endswith('.bat'):
                data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            archive.writestr('GFlow-Studio-Portable/' + name, data)
            hashes.append(hashlib.sha256(data).hexdigest() + '  ' + name)
        archive.writestr('GFlow-Studio-Portable/SHA256SUMS.txt', '\n'.join(hashes) + '\n')
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity verification failed')
    print(f'Packaged {len(files)} files; {len(wheels)} compatible Windows wheel distributions')
    print(f'{output}: {output.stat().st_size:,} bytes')
    print('SHA256:', hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.runtime, args.site, args.output)
