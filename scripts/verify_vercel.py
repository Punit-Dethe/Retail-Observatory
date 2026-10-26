"""Bounded deployment checks without a Vercel account or model request."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Thread
from http.server import ThreadingHTTPServer
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from warehouse import materialize_warehouse


class VercelChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = materialize_warehouse(ROOT / 'data/deploy', cls.temp.name)
        os.environ['RETAIL_WAREHOUSE_PATH'] = str(cls.db)
        spec = importlib.util.spec_from_file_location('retail_vercel_entry', ROOT / 'api/index.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), module.handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        os.environ.pop('RETAIL_WAREHOUSE_PATH', None)
        cls.temp.cleanup()

    def request(self, method, path, value=None, origin=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=30)
        headers = {'Content-Type': 'application/json', 'Host': 'retail-example.vercel.app'}
        if origin:
            headers['Origin'] = origin
        conn.request(method, path, json.dumps(value) if value is not None else None, headers)
        response = conn.getresponse()
        status, body = response.status, response.read()
        conn.close()
        return status, json.loads(body)

    def test_snapshot_and_rewrite(self):
        self.assertEqual(materialize_warehouse(ROOT / 'data/deploy', self.temp.name), self.db)
        status, value = self.request('GET', '/api?__route=health')
        self.assertEqual(status, 200)
        self.assertEqual(value['status'], 'ok')
        status, value = self.request('GET', '/api/canvas/catalog?q=22423')
        self.assertEqual(status, 200)
        self.assertTrue(any(p['code'] == '22423' for p in value['products']))
        self.assertEqual(self.request('GET', '/canvas')[0], 404)

    def test_same_origin_hosted_analysis_and_rejection(self):
        payload = {'message': 'Explore sales', 'tool': 'sales', 'scope': {'start': '2011-01-01', 'end': '2011-12-09', 'country': 'France'}}
        with patch.dict(os.environ, {'VERCEL': '1'}):
            status, result = self.request('POST', '/api?__route=canvas/investigate', payload, 'https://retail-example.vercel.app')
            self.assertEqual(status, 200)
            self.assertEqual(result['mode'], 'guided')
            self.assertEqual(len(result['blocks']), 6)
            self.assertEqual(result['blocks'][0]['evidence']['scope']['country'], 'France')
            self.assertEqual(self.request('POST', '/api?__route=canvas/investigate', payload, 'https://unrelated.example')[0], 403)


if __name__ == '__main__':
    unittest.main()
