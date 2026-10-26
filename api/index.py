"""Vercel's single Python function, reusing the local API and calculations."""
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlencode, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from app import Handler


class handler(Handler):
    api_only = True

    def route_request(self):
        # Rewrites can deliver either the original URL or the destination URL.
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query, keep_blank_values=True)
        route = query.pop('__route', None)
        if route is not None:
            path = '/api/' + route[0].lstrip('/')
            self.path = path + ('?' + urlencode(query, doseq=True) if query else '')

    def do_GET(self):
        self.route_request()
        super().do_GET()

    def do_POST(self):
        self.route_request()
        super().do_POST()
