"""Focused checks for approved tools and evidence, without a live model call."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from canvas_agent import investigate, capabilities, ProviderError
from canvas_analysis import META, DATA, catalog, build_investigation


class CanvasChecks(unittest.TestCase):
    def test_computed_investigations(self):
        for tool in ['sales', 'markets', 'product', 'customers', 'baskets']:
            request = {'message': 'Explore the selected evidence', 'tool': tool, 'scope': {'start': '2011-01-01', 'end': '2011-12-09', 'country': 'France'}}
            if tool == 'product':
                request['productCode'] = '22423'
            value = investigate(request)
            self.assertTrue(value['blocks'])
            json.dumps(value, allow_nan=False)
            ids = {b['id'] for b in value['blocks']}
            self.assertEqual(len(ids), len(value['blocks']))
            for block in value['blocks']:
                self.assertEqual(block['evidence']['scope']['country'], 'France')
                self.assertEqual(block['evidence']['sourceSha256'], META['sourceSha256'])
                self.assertTrue(block['evidence']['definitions'])
                for row in block.get('rows', []):
                    self.assertIsInstance(row, dict)
            for edge in value['connections']:
                self.assertTrue(edge['source'] in ids and edge['target'] in ids)

    def test_sales_matches_independent_data_slice(self):
        result = build_investigation('sales', {'start': '2011-01-01', 'end': '2011-12-09', 'country': 'France'})
        rows = result['blocks'][0]['rows']
        mask = DATA.date_id.between('2011-01-01', '2011-12-09') & DATA.country.eq('France')
        self.assertAlmostEqual(sum(r['revenue'] for r in rows), float(DATA.loc[mask, 'amount'].sum()), places=2)

    def test_product_penetration(self):
        result = build_investigation('product', {'start': META['start'], 'end': META['end'], 'country': 'all'}, '22423', ['France', 'Germany'])
        row = next(r for r in result['blocks'][2]['rows'] if r['country'] == 'France')
        france = DATA[(DATA.quantity > 0) & DATA.country.eq('France')]
        expected = france[france.code.eq('22423')].invoice.nunique() / france.invoice.nunique() * 100
        self.assertAlmostEqual(row['penetration'], expected, places=3)

    def test_guidance_and_no_data(self):
        with patch('canvas_agent.configured', return_value=False):
            comparison = investigate({'message': 'Compare the UK and Germany'})
            self.assertEqual(set(comparison['blocks'][0]['evidence']['scope']['countries']), {'United Kingdom', 'Germany'})
            unknown = investigate({'message': 'Will my new product succeed?'})
            self.assertFalse(unknown['blocks'])
            empty = investigate({'message': 'Explore sales', 'tool': 'sales', 'scope': {'start': '2011-12-09', 'end': '2011-12-09', 'country': 'Saudi Arabia'}})
            self.assertEqual(empty['blocks'][0]['kind'], 'note')
        self.assertTrue(any(p['code'] == '22423' for p in catalog('22423')['products']))

    def test_validation(self):
        for payload in [None, {'message': ''}, {'message': 'x', 'tool': 'execute_sql'}, {'message': 'x', 'scope': {'start': '2012-01-01'}}, {'message': 'x', 'tool': 'product', 'productCode': 'missing'}, {'message': 'sales', 'scope': 'France'}, {'message': 'sales', 'selected': [{'evidence': 'malformed'}]}]:
            with self.assertRaises(ValueError):
                investigate(payload)

    def test_model_tool_contract_without_network(self):
        args = {'tool': 'sales', 'start': '2011-01-01', 'end': '2011-12-09', 'country': 'France', 'productCode': None, 'countries': None}
        plan = {'tool_calls': [{'id': 'call1', 'type': 'function', 'function': {'name': 'investigate_retail', 'arguments': json.dumps(args)}}]}
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', side_effect=[plan, {'content': 'The computed charts show the selected French sales window.'}]):
            value = investigate({'message': 'Investigate French sales in 2011'})
        self.assertEqual(value['mode'], 'llm')
        self.assertEqual(value['blocks'][0]['evidence']['scope']['country'], 'France')
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', return_value={'content': 'No tool call'}):
            with self.assertRaises(ProviderError):
                investigate({'message': 'Investigate sales'})


if __name__ == '__main__':
    unittest.main()
