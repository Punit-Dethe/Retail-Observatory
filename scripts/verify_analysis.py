"""Integration checks against real warehouse data and independently calculated totals."""
from pathlib import Path
import json
import math
import sqlite3
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from analytics import META, DATA, analyze
from app import scope


def near(a, b, tolerance=.1):
    assert abs(a-b) <= tolerance, (a, b)


def check_payload(a):
    json.dumps(a, allow_nan=False)
    s = a['summary']
    near(s['revenue'], s['grossRevenue'] - s['returns'])
    near(sum(r['revenue'] for r in a['trend']), s['revenue'])
    near(sum(r['revenue'] for r in a['countries']), s['revenue'])
    near(sum(r['revenue'] for r in a['daily']), s['revenue'])
    assert sum(r['count'] for r in a['orderDistribution']) == s['orders']
    assert sum(r['customers'] for r in a['segments']) == s['customers']
    assert sum(r['customers'] for r in a['clusters']) == s['customers']
    assert len(a['customers']) == s['customers']
    for row in a['cohorts']:
        assert row['retention'][0] == 100
        assert all(v is None or 0 <= v <= 100 for v in row['retention'])
    for rule in a['basket']['rules']:
        near(rule['support'], rule['count']/a['basket']['transactions']*100, .001)
        assert 0 < rule['confidence'] <= 100 and rule['lift'] > 1
    if a['pareto']:
        assert a['pareto'][-1] == {'percentProducts': 100.0, 'percentRevenue': 100.0}


def main():
    q = META['quality']
    assert q['rawRows'] == q['cleanRows'] + sum(r['rows'] for r in q['exclusions'])
    full = analyze(META['start'], META['end'])
    check_payload(full)
    with sqlite3.connect(ROOT / 'data/retail.sqlite') as conn:
        gross, net, orders = conn.execute('SELECT SUM(CASE WHEN quantity>0 THEN amount ELSE 0 END),SUM(amount),COUNT(DISTINCT CASE WHEN quantity>0 THEN invoice END) FROM fact_transaction').fetchone()
        orphans = conn.execute('SELECT count(*) FROM fact_transaction f LEFT JOIN dim_product p ON f.product_id=p.product_id WHERE p.product_id IS NULL').fetchone()[0]
    near(full['summary']['grossRevenue'], gross)
    near(full['summary']['revenue'], net)
    assert full['summary']['orders'] == orders and orphans == 0
    assert not full['previous']['available']
    assert full['partialMonths'] == ['2011-12']
    # Independently verify the highest-lift basket rule by invoice membership.
    rule = full['basket']['rules'][0]
    sales = DATA[DATA.quantity > 0]
    a = set(sales.loc[sales['name'].eq(rule['antecedent']), 'invoice'])
    b = set(sales.loc[sales['name'].eq(rule['consequent']), 'invoice'])
    assert len(a & b) == rule['count']
    near(len(a & b)/len(a)*100, rule['confidence'], .01)
    near((len(a & b)/len(a))/(len(b)/full['summary']['orders']), rule['lift'], .01)
    for args in [('2011-01-01', '2011-12-09', 'France'), ('2011-12-09', '2011-12-09', 'United Kingdom'), ('2020-01-01', '2020-01-31', 'all'), ('2011-12-09', '2011-12-09', 'Saudi Arabia')]:
        result = analyze(*args)
        check_payload(result)
        print(f'PASS scope {args}: {result["summary"]["orders"]:,} orders')
    assert analyze('2011-01-01', '2011-12-09', 'France')['previous']['available']
    try:
        scope({'start': ['2011-02-01'], 'end': ['2011-01-01']})
        raise AssertionError('Reversed dates accepted')
    except ValueError:
        pass
    print('PASS raw reconciliation, warehouse joins, SQL totals, credit arithmetic, time/country rollups, distributions, customer partitions, cohort bounds, exact basket support/confidence/lift, partial-month coverage, empty and small selections, date validation.')
    print(json.dumps(full['summary'], indent=2))


if __name__ == '__main__':
    main()
