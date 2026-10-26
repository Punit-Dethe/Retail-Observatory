"""Use the local warehouse or materialize the bundled deployment snapshot in /tmp."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def materialize_warehouse(snapshot_dir, target_dir):
    snapshot_dir, target_dir = Path(snapshot_dir), Path(target_dir)
    manifest = json.loads((snapshot_dir / 'warehouse.json').read_text(encoding='utf-8'))
    target = target_dir / manifest['sha256'] / 'retail.sqlite'
    if target.is_file() and target.stat().st_size == manifest['bytes']:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name(f'{uuid.uuid4().hex}.tmp')
    try:
        with gzip.open(snapshot_dir / 'retail.sqlite.gz', 'rb') as source, pending.open('wb') as output:
            shutil.copyfileobj(source, output)
        hasher = hashlib.sha256()
        with pending.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        if pending.stat().st_size != manifest['bytes'] or digest != manifest['sha256']:
            raise RuntimeError('The deployment warehouse snapshot failed its integrity check.')
        os.replace(pending, target)
    finally:
        pending.unlink(missing_ok=True)
    return target


def database_path():
    override = os.environ.get('RETAIL_WAREHOUSE_PATH')
    if override:
        return Path(override).resolve()
    local = ROOT / 'data' / 'retail.sqlite'
    if local.is_file():
        return local
    return materialize_warehouse(ROOT / 'data' / 'deploy', Path(tempfile.gettempdir()) / 'retail-observatory')
