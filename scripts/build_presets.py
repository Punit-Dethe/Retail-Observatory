"""Generate versioned, fixed JSON values for the three All markets selections.

This is a build-time data artifact, not a runtime cache. Country filters and
custom ranges continue to use the existing analytics API.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from analytics import META, analyze

SELECTIONS = {
    'all': (META['start'], META['end']),
    '2010': ('2010-01-01', '2010-12-31'),
    '2011': ('2011-01-01', META['end']),
}


def main():
    datasets = {}
    for name, (start, end) in SELECTIONS.items():
        began = time.perf_counter()
        datasets[name] = analyze(start, end, 'all')
        print(f'{name}: {datasets[name]["summary"]["orders"]:,} orders; {time.perf_counter()-began:.2f}s computed once', flush=True)
    artifact = {
        'meta': META,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'sourceSha256': META['sourceSha256'],
        'analysisSourceSha256': hashlib.sha256((ROOT / 'server/analytics.py').read_bytes()).hexdigest(),
        'datasets': datasets,
    }
    destination = ROOT / 'src/data/retail-presets.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    temporary.replace(destination)
    print(f'Wrote {destination} ({destination.stat().st_size / 1024 / 1024:.2f} MiB). No runtime calculation required for these selections.', flush=True)


if __name__ == '__main__':
    main()
