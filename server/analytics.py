"""Analysis over the cleaned merchandise fact table. All filters are inclusive."""
from functools import lru_cache
from pathlib import Path
import json
import calendar
import sqlite3
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
META = json.loads((ROOT / 'data/metadata.json').read_text(encoding='utf-8'))
with sqlite3.connect(ROOT / 'data/retail.sqlite') as conn:
    DATA = pd.read_sql_query('''SELECT f.invoice,f.product_id AS code,p.name,f.customer_id AS customer,
        f.country_id AS country,f.date_id,f.time,f.quantity,f.unit_price AS price,f.amount,f.is_return
        FROM fact_transaction f JOIN dim_product p ON f.product_id=p.product_id''', conn)
DATA['date'] = pd.to_datetime(DATA.date_id + ' ' + DATA.time)
DATA['month'] = DATA.date.dt.strftime('%Y-%m')
DATA['day'] = DATA.date.dt.dayofweek
DATA['hour'] = DATA.date.dt.hour
for col in ['code', 'name', 'country', 'month']:
    DATA[col] = DATA[col].astype('category')


def records(frame):
    return json.loads(frame.to_json(orient='records', double_precision=4))


def select(start, end, country):
    mask = DATA.date_id.between(start, end)
    if country != 'all':
        mask &= DATA.country.eq(country)
    return DATA.loc[mask]


def summary(df):
    sales = df[df.quantity > 0]
    identified = sales.dropna(subset=['customer'])
    freq = identified.groupby('customer', observed=True).invoice.nunique()
    gross = float(sales.amount.sum())
    returns = float(-df.loc[df.quantity < 0, 'amount'].sum())
    orders = int(sales.invoice.nunique())
    return {
        'revenue': round(gross - returns, 2), 'grossRevenue': round(gross, 2), 'returns': round(returns, 2),
        'orders': orders, 'customers': int(len(freq)), 'units': int(sales.quantity.sum()),
        'aov': round(gross / orders, 2) if orders else 0,
        'returnRate': round(returns / gross * 100, 2) if gross else 0,
        'repeatRate': round((freq >= 2).mean() * 100, 2) if len(freq) else 0,
        'products': int(sales.code.nunique()), 'countries': int(sales.country.nunique()), 'rows': len(df),
        'identifiedRevenueShare': round(identified.amount.sum() / gross * 100, 2) if gross else 0,
    }


def time_series(df, group):
    if df.empty:
        return []
    tmp = df.assign(grossRevenue=df.amount.clip(lower=0), returns=-df.amount.clip(upper=0))
    out = tmp.groupby(group, observed=True).agg(revenue=('amount', 'sum'), grossRevenue=('grossRevenue', 'sum'), returns=('returns', 'sum'))
    sales = df[df.quantity > 0].groupby(group, observed=True).agg(orders=('invoice', 'nunique'), customers=('customer', 'nunique'), units=('quantity', 'sum'))
    return records(out.join(sales).fillna(0).rename_axis('date').reset_index())


def customer_analysis(sales, end):
    identified = sales.dropna(subset=['customer'])
    if identified.empty:
        return pd.DataFrame(), [], [], [], {'silhouette': None, 'k': 0, 'sampleSize': 0}
    customers = identified.groupby('customer', observed=True).agg(last=('date', 'max'), frequency=('invoice', 'nunique'), monetary=('amount', 'sum'), country=('country', lambda x: x.mode().iloc[0]))
    customers['recency'] = ((pd.Timestamp(end) + pd.Timedelta(days=1)) - customers['last'].dt.normalize()).dt.days
    for key, score, inverse in [('recency', 'r', True), ('frequency', 'f', False), ('monetary', 'm', False)]:
        customers[score] = np.ceil(customers[key].rank(pct=True) * 5).clip(1, 5).astype(int)
        if inverse:
            customers[score] = 6 - customers[score]
    r, f = customers.r, customers.f
    customers['segment'] = np.select([
        (r >= 4) & (f >= 4), f >= 4, (r >= 4) & (f <= 2), (r >= 3) & (f >= 2), (r <= 2) & (f >= 3)
    ], ['Champions', 'Loyal customers', 'New customers', 'Potential loyalists', 'At risk'], default='Hibernating')
    x = StandardScaler().fit_transform(np.log1p(customers[['recency', 'frequency', 'monetary']]))
    k = min(4, len(customers), len(np.unique(x, axis=0)))
    with threadpool_limits(limits=2):
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(x)
        silhouette = float(silhouette_score(x, labels, sample_size=min(1500, len(x)), random_state=42)) if 1 < k < len(x) else None
    # Stable interpretable labels: C1 always has the highest average spend.
    order = pd.Series(customers.monetary.to_numpy()).groupby(labels).mean().sort_values(ascending=False).index.tolist()
    customers['cluster'] = [order.index(int(v)) for v in labels]
    segments = customers.groupby('segment', observed=True).agg(customers=('frequency', 'size'), revenue=('monetary', 'sum'), avgRecency=('recency', 'mean'), avgFrequency=('frequency', 'mean'), avgMonetary=('monetary', 'mean')).rename_axis('name').reset_index()
    segments['share'] = segments.customers / len(customers) * 100
    clusters = customers.groupby('cluster').agg(customers=('frequency', 'size'), avgRecency=('recency', 'mean'), avgFrequency=('frequency', 'mean'), avgMonetary=('monetary', 'mean')).reset_index()
    clusters['name'] = clusters.cluster.map(lambda n: f'Cluster {n+1}')
    # First purchase is first observed inside selected scope, never claimed lifetime acquisition.
    first = identified.assign(month=identified.month.astype(str)).groupby('customer', observed=True).month.min()
    activity = identified[['customer', 'month']].drop_duplicates().copy()
    activity['cohort'] = activity.customer.map(first)
    month_n = pd.to_datetime(activity.month.astype(str) + '-01')
    cohort_n = pd.to_datetime(activity.cohort + '-01')
    activity['age'] = (month_n.dt.year-cohort_n.dt.year)*12 + month_n.dt.month-cohort_n.dt.month
    counts = activity.groupby(['cohort', 'age'], observed=True).customer.nunique()
    sizes = first.value_counts()
    last = pd.Period(end, freq='M')
    cohorts = []
    for month in sorted(sizes.index)[-12:]:
        observed = last.ordinal - pd.Period(month, freq='M').ordinal
        cohorts.append({'month': month, 'size': int(sizes[month]), 'retention': [round(float(counts.get((month, i), 0)) / sizes[month] * 100, 1) if i <= observed else None for i in range(12)]})
    customers = customers.drop(columns='last').rename_axis('id').reset_index().sort_values('monetary', ascending=False)
    return customers, records(segments), records(clusters), cohorts, {'silhouette': round(silhouette, 3) if silhouette is not None else None, 'k': k, 'sampleSize': min(1500, len(x))}


def basket_analysis(sales):
    total = int(sales.invoice.nunique())
    empty = {'transactions': total, 'eligibleProducts': 0, 'minSupport': 0, 'rules': []}
    if not total:
        return empty
    pairs = sales[['invoice', 'code']].drop_duplicates()
    frequencies = pairs.groupby('code', observed=True).size().sort_values(ascending=False)
    eligible = frequencies.head(80).index
    pairs = pairs[pairs.code.isin(eligible)]
    inv = pd.Categorical(pairs.invoice)
    codes = pd.Categorical(pairs.code.astype(str), categories=eligible.astype(str).tolist())
    matrix = csr_matrix((np.ones(len(pairs), dtype=np.int32), (inv.codes, codes.codes)), shape=(len(inv.categories), len(eligible)))
    co = (matrix.T @ matrix).toarray()
    names = sales.drop_duplicates('code').set_index('code')['name'].astype(str).to_dict()
    rules = []
    min_count = max(20, int(np.ceil(total * 0.002)))
    # Apriori level 2: infrequent singleton pruning, then exact pair supports.
    for a in range(len(eligible)):
        for b in range(len(eligible)):
            if a == b or co[a, b] < min_count:
                continue
            confidence = float(co[a, b] / co[a, a])
            lift = confidence / (co[b, b] / total)
            if confidence >= 0.15 and lift > 1:
                rules.append({'antecedent': str(names[eligible[a]]), 'consequent': str(names[eligible[b]]), 'support': round(float(co[a, b]) / total * 100, 3), 'confidence': round(confidence * 100, 2), 'lift': round(lift, 2), 'count': int(co[a, b])})
    rules.sort(key=lambda r: (-r['lift'], -r['count']))
    return {'transactions': total, 'eligibleProducts': len(eligible), 'minSupport': round(min_count / total * 100, 3), 'rules': rules[:20]}


@lru_cache(maxsize=12)
def analyze(start, end, country='all'):
    df = select(start, end, country)
    sales = df[df.quantity > 0]
    s = summary(df)
    duration = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    previous_end = pd.Timestamp(start) - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=duration-1)
    previous = summary(select(previous_start.strftime('%Y-%m-%d'), previous_end.strftime('%Y-%m-%d'), country))
    previous['available'] = previous_start >= pd.Timestamp(META['start']) and previous_end <= pd.Timestamp(META['end'])
    country_sales = sales.groupby('country', observed=True).agg(grossRevenue=('amount', 'sum'), orders=('invoice', 'nunique'), customers=('customer', 'nunique'))
    country_net = df.groupby('country', observed=True).agg(revenue=('amount', 'sum'))
    countries = country_net.join(country_sales).fillna(0)
    countries['returns'] = countries.grossRevenue - countries.revenue
    countries['share'] = countries.grossRevenue / s['grossRevenue'] * 100 if s['grossRevenue'] else 0
    countries = countries.sort_values('revenue', ascending=False).rename_axis('country').reset_index()
    products = sales.groupby('code', observed=True).agg(name=('name', 'first'), revenue=('amount', 'sum'), units=('quantity', 'sum'), orders=('invoice', 'nunique'))
    refunds = -df[df.quantity < 0].groupby('code', observed=True).amount.sum()
    products['returns'] = products.index.map(refunds).fillna(0)
    products['returnRate'] = products.returns / products.revenue * 100
    products['price'] = products.revenue / products.units
    products = products.sort_values('revenue', ascending=False)
    pareto = []
    if len(products):
        cumulative = products.revenue.cumsum() / products.revenue.sum() * 100
        ix = np.unique(np.linspace(0, len(products)-1, min(100, len(products)), dtype=int))
        pareto = [{'percentProducts': 0, 'percentRevenue': 0}] + [{'percentProducts': round((int(i)+1)/len(products)*100, 2), 'percentRevenue': round(float(cumulative.iloc[i]), 2)} for i in ix]
    customers, segments, clusters, cohorts, cq = customer_analysis(sales, end)
    heat = sales.groupby(['day', 'hour'], observed=True).agg(orders=('invoice', 'nunique'), revenue=('amount', 'sum')).reset_index()
    totals = sales.groupby('invoice', observed=True).amount.sum()
    bins = [0, 50, 100, 250, 500, 1000, np.inf]
    labels = ['£0–50', '£50–100', '£100–250', '£250–500', '£500–1,000', '£1,000+']
    dist = pd.cut(totals, bins=bins, labels=labels, right=False).value_counts(sort=False)
    trend = time_series(df, 'month')
    daily = time_series(df, 'date_id')
    # A daily line must show zero-activity days rather than bridge silently over them.
    if daily:
        days = pd.date_range(max(pd.Timestamp(start), pd.Timestamp(META['start'])), min(pd.Timestamp(end), pd.Timestamp(META['end']))).strftime('%Y-%m-%d')
        daily = records(pd.DataFrame(daily).set_index('date').reindex(days, fill_value=0).rename_axis('date').reset_index())
    partial = []
    for row in trend:
        first = pd.Timestamp(row['date'] + '-01')
        last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
        if first < max(pd.Timestamp(start), pd.Timestamp(META['start'])) or last > min(pd.Timestamp(end), pd.Timestamp(META['end'])):
            partial.append(row['date'])
    insights = []
    if s['orders']:
        top = countries.iloc[0]
        insights.append({'title': f"{top['country']} leads the market", 'body': f"{top['share']:.1f}% of gross merchandise sales come from this market in the selected period.", 'tone': 'blue'})
        if len(products):
            top20 = products.revenue.head(max(1, int(np.ceil(len(products)*0.2)))).sum()/products.revenue.sum()*100
            insights.append({'title': 'A concentrated product portfolio', 'body': f"The top 20% of products generate {top20:.1f}% of gross merchandise sales. Use the Pareto curve to explore the long tail.", 'tone': 'green'})
        insights.append({'title': 'Customer identity has gaps', 'body': f"{100-s['identifiedRevenueShare']:.1f}% of gross sales have no customer ID. Sales remain included; customer analyses use identified shoppers only.", 'tone': 'amber'})
    return {
        'filters': {'start': start, 'end': end, 'country': country}, 'summary': s, 'previous': previous,
        'trend': trend, 'daily': daily, 'partialMonths': partial,
        'countries': records(countries), 'products': records(products.head(100).reset_index()),
        'customers': records(customers) if len(customers) else [], 'segments': segments, 'clusters': clusters,
        'clusterQuality': cq, 'cohorts': cohorts, 'heatmap': records(heat), 'basket': basket_analysis(sales),
        'orderDistribution': [{'range': str(k), 'count': int(v)} for k, v in dist.items()],
        'pareto': pareto, 'quality': META['quality'], 'insights': insights,
        'methods': {
            'clustering': 'K-means (k up to 4), seeded at 42 with 10 initializations; standardized log1p recency, frequency and monetary value. Silhouette uses at most 1,500 sampled customers. Cluster numbers ranked by average spend, not by inherent quality.',
            'basket': 'Two-item Apriori: top 80 products by distinct sale-invoice frequency; each product appears once per basket. Minimum count max(20, ceil(0.2% of baskets)), confidence ≥15%, lift >1. Supports use all selected positive merchandise invoices. Top 20 directional rules by lift; associations are not causation.',
            'cohort': 'First observed purchase within the selected date and country scope; not proven lifetime acquisition. Cohort age is calendar months. Unobserved future months are null. Current partial month can understate retention.',
            'scope': 'Exact duplicates removed. Merchandise stock codes only (five digits with up to two trailing letters); service, postage and manual adjustment codes excluded. Positive prices and nonzero quantities required. C-prefixed invoices treated as negative credits. Missing customer IDs retained for sales, excluded from customer analysis. Net revenue = positive merchandise sales less observed credits/negative quantities; credits may refer to sales outside the selected period. AOV uses positive sales / distinct positive invoices. No cost or profit data.'
        }
    }
