"""Local-only HTTP API and production static server; no framework required."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import argparse
import csv
import io
import json
import mimetypes
import sys
import traceback
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from analytics import META, analyze, select


def scope(query):
    start = query.get('start', [META['start']])[0]
    end = query.get('end', [META['end']])[0]
    country = query.get('country', ['all'])[0]
    # Parse strictly and bound cost; accept legitimate no-data dates.
    for value in [start, end]:
        if pd.Timestamp(value).strftime('%Y-%m-%d') != value:
            raise ValueError('Dates must use YYYY-MM-DD.')
    if start > end:
        raise ValueError('Start date must be on or before end date.')
    if (pd.Timestamp(end) - pd.Timestamp(start)).days > 3653:
        raise ValueError('Choose a date range of at most ten years.')
    if country != 'all' and country not in META['countries']:
        raise ValueError('Unknown country.')
    return start, end, country


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

    def json_response(self, value, status=200):
        body = json.dumps(value, allow_nan=False, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == '/api/meta':
                return self.json_response(META)
            if parsed.path == '/api/health':
                return self.json_response({'status': 'ok', 'dataset': META['name']})
            if parsed.path in ['/api/analytics', '/api/export']:
                query = parse_qs(parsed.query)
                start, end, country = scope(query)
                if parsed.path == '/api/analytics':
                    return self.json_response(analyze(start, end, country))
                kind = query.get('kind', ['trend'])[0]
                if kind == 'transactions':
                    frame = select(start, end, country)[['invoice', 'code', 'name', 'customer', 'country', 'date_id', 'time', 'quantity', 'price', 'amount', 'is_return']].copy()
                elif kind in ['products', 'customers', 'countries', 'trend']:
                    frame = pd.DataFrame(analyze(start, end, country)[kind])
                else:
                    raise ValueError('Unknown export kind.')
                # Neutralize spreadsheet formula interpretation in user-provided text.
                for column in frame.select_dtypes(include=['object', 'str', 'category']).columns:
                    frame[column] = frame[column].map(lambda v: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v)
                body = ('\ufeff' + frame.to_csv(index=False)).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="retail-{kind}-{start}-{end}.csv"')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith('/api/'):
                return self.json_response({'error': 'Endpoint not found.'}, 404)
            if not (ROOT / 'dist/index.html').exists():
                return self.json_response({'message': 'API ready. Run npm run dev for the UI, or npm run build to serve it here.'})
            # SPA fallback without rewriting missing assets to HTML.
            if parsed.path != '/' and not Path(parsed.path).suffix:
                self.path = '/index.html'
            return super().do_GET()
        except (ValueError, TypeError, OverflowError) as exc:
            return self.json_response({'error': str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            traceback.print_exc()
            return self.json_response({'error': 'The local analysis failed. See the server terminal for details.'}, 500)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Retail Observatory: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
