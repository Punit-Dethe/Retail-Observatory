"""Verify fixed frontend values against independent warehouse SQL."""
from pathlib import Path
import hashlib
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def main():
    artifact = json.loads((ROOT / 'src/data/retail-presets.json').read_text(encoding='utf-8'))
    assert artifact['analysisSourceSha256'] == hashlib.sha256((ROOT / 'server/analytics.py').read_bytes()).hexdigest(), 'Regenerate presets after analytics definitions change.'
    assert artifact['sourceSha256'] == json.loads((ROOT / 'data/metadata.json').read_text())['sourceSha256']
    assert set(artifact['datasets']) == {'all', '2010', '2011'}
    with sqlite3.connect(ROOT / 'data/retail.sqlite') as conn:
        for name, data in artifact['datasets'].items():
            f, s = data['filters'], data['summary']
            assert f['country'] == 'all'
            gross, net, orders, customers = conn.execute('''SELECT
                SUM(CASE WHEN quantity>0 THEN amount ELSE 0 END), SUM(amount),
                COUNT(DISTINCT CASE WHEN quantity>0 THEN invoice END),
                COUNT(DISTINCT CASE WHEN quantity>0 THEN customer_id END)
                FROM fact_transaction WHERE date_id BETWEEN ? AND ?''', (f['start'], f['end'])).fetchone()
            assert abs(s['grossRevenue']-gross) < .01
            assert abs(s['revenue']-net) < .01
            assert s['orders'] == orders
            assert s['customers'] == customers == len(data['customers'])
            assert abs(sum(r['revenue'] for r in data['trend'])-net) < .02
            assert abs(sum(r['revenue'] for r in data['countries'])-net) < .02
            assert sum(r['count'] for r in data['orderDistribution']) == orders
            json.dumps(data, allow_nan=False)
            print(f'PASS {name}: {orders:,} orders, {customers:,} customers, net GBP {net:,.2f}')
    print('PASS fixed JSON values match source signature and independent SQL totals for all three All markets presets.')


if __name__ == '__main__':
    main()
