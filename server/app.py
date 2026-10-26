"""Local-only HTTP API and production static server; no framework required."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import argparse
import csv
import io
import json
import mimetypes
import os
import sys
import traceback
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from analytics import META, analyze, select
from canvas_agent import capabilities, investigate, ProviderError
from canvas_analysis import catalog


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
    api_only = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

    def json_response(self, value, status=200):
        body = json.dumps(value, allow_nan=False, ensure_ascii=False).encode('utf-8')
        if os.environ.get('VERCEL') and len(body) > 4_000_000:
            status = 413
            body = json.dumps({'error': 'This result exceeds the hosted response limit. Choose a narrower date range or run the full export locally.'}).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path != '/api/canvas/investigate':
            return self.json_response({'error': 'Endpoint not found.'}, 404)
        try:
            # Accept the local dev UI and the same-origin deployed Vercel UI.
            origin = self.headers.get('Origin')
            port = getattr(self.server, 'server_port', 8000)
            allowed = ['http://127.0.0.1:8000', 'http://localhost:8000', 'http://127.0.0.1:5173', 'http://localhost:5173', f'http://127.0.0.1:{port}', f'http://localhost:{port}']
            if os.environ.get('VERCEL'):
                host = self.headers.get('Host', '')
                if host:
                    allowed.append(f'https://{host}')
                for key in ['VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL', 'VERCEL_BRANCH_URL']:
                    if os.environ.get(key):
                        allowed.append('https://' + os.environ[key])
            if origin and origin not in allowed:
                return self.json_response({'error': 'Cross-origin requests are not allowed.'}, 403)
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 100_000:
                raise ValueError('Send a JSON request smaller than 100 KB.')
            if 'application/json' not in self.headers.get('Content-Type', ''):
                raise ValueError('Use application/json.')
            request = json.loads(self.rfile.read(length))
            return self.json_response(investigate(request))
        except ProviderError as exc:
            return self.json_response({'error': str(exc)}, 502)
        except (ValueError, TypeError, OverflowError) as exc:
            return self.json_response({'error': str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            traceback.print_exc()
            return self.json_response({'error': 'The investigation failed. See the local server terminal for details.'}, 500)

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == '/api/canvas/capabilities':
                return self.json_response(capabilities())
            if parsed.path == '/api/canvas/catalog':
                return self.json_response(catalog(parse_qs(parsed.query).get('q', [''])[0]))
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
                if os.environ.get('VERCEL') and len(body) > 4_000_000:
                    return self.json_response({'error': 'This CSV exceeds the hosted response limit. Narrow the date range or export the complete data locally.'}, 413)
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="retail-{kind}-{start}-{end}.csv"')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith('/api/'):
                return self.json_response({'error': 'Endpoint not found.'}, 404)
            if self.api_only:
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
