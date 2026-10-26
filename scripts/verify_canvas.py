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
from canvas_query import run_query, QueryError


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

    def test_query_engine_matches_independent_slice(self):
        block, view, _ = run_query({'title': 'France months', 'purpose': 'test', 'measures': ['net_revenue', 'orders'], 'group_by': ['month'], 'filters': {'countries': ['France'], 'start': '2011-01-01'}}, META_SCOPE)
        mask = DATA.date_id.between('2011-01-01', META['end']) & DATA.country.eq('France')
        self.assertAlmostEqual(sum(r['net_revenue'] for r in block['rows']), float(DATA.loc[mask, 'amount'].sum()), places=1)
        sales = DATA.loc[mask & (DATA.quantity > 0)]
        self.assertEqual(sum(r['orders'] for r in block['rows']), sales.groupby('month', observed=True).invoice.nunique().sum())
        self.assertEqual(block['evidence']['tool'], 'query')
        self.assertEqual(block['evidence']['scope']['country'], 'France')
        compare, _, _ = run_query({'measures': ['orders'], 'group_by': ['country'], 'filters': {'countries': ['France', 'Germany'], 'start': '2011-01-01', 'end': '2011-06-30'}, 'compare_period': {'start': '2010-01-01', 'end': '2010-06-30'}}, META_SCOPE)
        de = next(r for r in compare['rows'] if r['country'] == 'Germany')
        prev = DATA[DATA.date_id.between('2010-01-01', '2010-06-30') & DATA.country.eq('Germany') & (DATA.quantity > 0)].invoice.nunique()
        self.assertEqual(de['orders_previous'], prev)
        json.dumps(compare, allow_nan=False)
        for bad in [{'measures': ['profit']}, {'group_by': ['zodiac']}, {'filters': {'sql': 'x'}}, {'filters': {'countries': ['Narnia']}}, {'filters': {'products': ['NOPE']}}, {'group_by': ['date']}, {'product_text': 'christmas'}]:
            with self.assertRaises(QueryError):
                run_query(bad, META_SCOPE)

    def test_agent_loop_without_network(self):
        query = {'title': 'Monthly revenue 2011', 'purpose': 'Check the Q4 peak', 'measures': ['net_revenue', 'orders'], 'group_by': ['month'], 'filters': {'start': '2011-01-01'}}
        turn1 = {'tool_calls': [call('c1', 'query_retail', query), call('c2', 'query_retail', {'title': 'bad', 'purpose': 'x', 'measures': ['profit']})]}
        fixed = {'title': 'Orders by country', 'purpose': 'Is it UK-led?', 'measures': ['orders'], 'group_by': ['country'], 'limit': 5, 'filters': {'start': '2011-09-01', 'end': '2011-11-30'}}
        turn2 = {'tool_calls': [call('c3', 'query_retail', fixed)]}
        seen = []

        def fake(messages, tools=None, tool_choice='required', timeout=45):
            seen.append(messages[-1])
            if len(seen) == 1:
                return turn1
            if len(seen) == 2:
                self.assertIn('error', json.loads(messages[-1]['content']))
                return turn2
            rows = json.loads(messages[-1]['content'])['rows']
            nov = next(r for r in json.loads(messages[-4]['content'])['rows'] if r['month'] == '2011-11')
            answer = f"Revenue peaked in November 2011 at £{nov['net_revenue']:,.2f} (E1). The United Kingdom placed {rows[0]['orders']:,} orders in autumn (E2). Profit rose 37.5%."
            return {'tool_calls': [call('c4', 'present_answer', {'title': 'Q4 giftware peak', 'answer': answer, 'hypothesis': 'Seasonal gift buying drives Q4.', 'verdict': 'supported', 'reasoning': 'E1 shows the peak.',
                    'evidence': [{'ref': 'E1', 'role': 'supports', 'caption': 'November is highest'}, {'ref': 'E2', 'role': 'context'}, {'ref': 'E9', 'role': 'supports'}], 'caveats': ['December is partial.'], 'follow_ups': ['Which products drove November?']})]}

        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', side_effect=fake):
            value = investigate({'message': 'Why are sales highest in Q4 2011?'})
        json.dumps(value, allow_nan=False)
        self.assertEqual(value['mode'], 'llm')
        self.assertEqual(value['verdict'], 'supported')
        note, *charts = value['blocks']
        self.assertEqual(note['kind'], 'note')
        self.assertEqual(note['verdict'], 'supported')
        self.assertEqual([c['role'] for c in charts], ['supports', 'context'])
        self.assertEqual(charts[0]['subtitle'], 'November is highest')
        self.assertEqual({e['target'] for e in value['connections']}, {note['id']})
        self.assertTrue(any('E9' in w for w in value['warnings']))
        self.assertTrue(any('37.5%' in w for w in value['warnings']), value['warnings'])
        self.assertFalse(any('£' in w and 'could not be matched' in w and 'Revenue' in w for w in value['warnings']))
        self.assertEqual(value['followUps'][0]['prompt'], 'Which products drove November?')

    def test_agent_plain_text_and_failures(self):
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', return_value={'content': 'RFM means recency, frequency and monetary value.'}):
            value = investigate({'message': 'What is RFM?'})
        self.assertEqual(value['blocks'], [])
        self.assertIn('RFM', value['message'])
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', return_value={'content': ''}):
            with self.assertRaises(ProviderError):
                investigate({'message': 'Investigate sales'})
        playbook = {'tool_calls': [call('p1', 'run_playbook', {'playbook': 'baskets', 'country': 'France', 'start': '2011-01-01'})]}
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', side_effect=[playbook] * 7):
            value = investigate({'message': 'Bundles in France'})
        self.assertEqual(value['verdict'], 'inconclusive')
        self.assertTrue(all(b['evidence']['scope']['country'] == 'France' for b in value['blocks'][1:]))
        query = {'tool_calls': [call('q1', 'query_retail', {'title': 'Revenue by year', 'purpose': 'x', 'measures': ['net_revenue'], 'group_by': ['year']})]}
        with patch('canvas_agent.configured', return_value=True), patch('canvas_agent.completion', side_effect=[query, ProviderError('The configured model could not be reached.')]):
            value = investigate({'message': 'Revenue by year?'})
        self.assertEqual(value['verdict'], 'inconclusive')
        self.assertEqual(value['blocks'][1]['title'], 'Revenue by year')
        self.assertIn('could not be reached', value['warnings'][0])


def call(id, name, args):
    return {'id': id, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}


META_SCOPE = {'start': META['start'], 'end': META['end'], 'country': 'all'}


if __name__ == '__main__':
    unittest.main()
