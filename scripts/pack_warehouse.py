"""Reproduce the small, checked-in runtime snapshot after changing the local warehouse."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def pack():
    source = ROOT / 'data' / 'retail.sqlite'
    destination = ROOT / 'data' / 'deploy'
    destination.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    with source.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    manifest = {'sha256': digest, 'bytes': source.stat().st_size,
                'sourceSha256': json.loads((ROOT / 'data' / 'metadata.json').read_text(encoding='utf-8'))['sourceSha256']}
    archive = destination / 'retail.sqlite.gz'
    with source.open('rb') as stream, archive.open('wb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as packed:
            shutil.copyfileobj(stream, packed)
    (destination / 'warehouse.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Packed {manifest["bytes"]:,} bytes into {archive.stat().st_size:,} bytes.')


if __name__ == '__main__':
    pack()
