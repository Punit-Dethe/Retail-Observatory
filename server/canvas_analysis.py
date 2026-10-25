"""Approved retail investigations. Every visible value comes from warehouse data."""
from datetime import datetime, timezone
import json
import re
import uuid
import numpy as np
import pandas as pd
from analytics import DATA, META, records, summary, time_series, basket_analysis, customer_analysis

TOOLS = ('sales', 'markets', 'product', 'customers', 'baskets')
SOURCE_URL = META['sourceUrl']


def uid():
    return uuid.uuid4().hex[:12]


def validate_scope(value):
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError('Scope must be an object.')
    start, end, country = value.get('start', META['start']), value.get('end', META['end']), value.get('country', 'all')
    for date in [start, end]:
        if not isinstance(date, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) or pd.Timestamp(date).strftime('%Y-%m-%d') != date:
            raise ValueError('Use valid YYYY-MM-DD dates.')
    if start > end or start < META['start'] or end > META['end']:
        raise ValueError(f'Choose dates from {META["start"]} to {META["end"]}, with start before end.')
    if country != 'all' and country not in META['countries']:
        raise ValueError('Unknown country.')
    return {'start': start, 'end': end, 'country': country}


def data_for(scope):
    mask = DATA.date_id.between(scope['start'], scope['end'])
    if scope['country'] != 'all':
        mask &= DATA.country.eq(scope['country'])
    return DATA.loc[mask]


def catalog(query=''):
    sales = DATA[DATA.quantity > 0]
    products = sales.groupby('code', observed=True).agg(name=('name', 'first'), revenue=('amount', 'sum')).reset_index()
    if query.strip():
        text = query.strip().casefold()[:150]
        products = products[products.code.astype(str).str.casefold().str.contains(text, regex=False) | products.name.astype(str).str.casefold().str.contains(text, regex=False)]
    return {'products': records(products.sort_values('revenue', ascending=False)[['code', 'name']].head(30)), 'countries': META['countries']}


def evidence(tool, scope, df, definitions, query):
    return {'tool': tool, 'source': 'UCI Online Retail II', 'sourceUrl': SOURCE_URL,
            'sourceSha256': META['sourceSha256'], 'scope': scope, 'rowCount': int(len(df)),
            'definitions': definitions, 'query': query, 'generatedAt': datetime.now(timezone.utc).isoformat()}


def chart(title, rows, x, series, ev, kind='bar', fmt='currency', subtitle=''):
    return {'id': uid(), 'kind': 'chart', 'title': title, 'subtitle': subtitle, 'chartType': kind,
            'rows': rows, 'xKey': x, 'series': [{'key': k, 'label': label} for k, label in series],
            'format': fmt, 'evidence': ev}


def note(title, body, ev, tone='blue'):
    return {'id': uid(), 'kind': 'note', 'title': title, 'body': body, 'tone': tone, 'evidence': ev}


def followups(product=None):
    return [
        {'label': 'Compare markets', 'prompt': 'Compare the UK and Germany', 'tool': 'markets'},
        {'label': 'Explore repeat customers', 'prompt': 'Understand repeat purchases and retention', 'tool': 'customers'},
        {'label': 'Find product pairs', 'prompt': 'Which products are frequently bought together?', 'tool': 'baskets', **({'productCode': product} if product else {})},
    ]


def build_investigation(tool, scope, product_code=None, countries=None):
    if tool not in TOOLS:
        raise ValueError('Unknown investigation tool.')
    scope = validate_scope(scope)
    df = data_for(scope)
    sales = df[df.quantity > 0]
    warnings = []
    if countries:
        if not isinstance(countries, list) or len(countries) > 6 or any(c not in META['countries'] for c in countries):
            raise ValueError('Choose at most six recorded countries.')
        if scope['country'] != 'all' and any(c != scope['country'] for c in countries):
            # An explicit comparison defines its own country set rather than silently retaining one market.
            scope = {**scope, 'country': 'all'}
            df, sales = data_for(scope), data_for(scope).query('quantity > 0')
        scope = {**scope, 'countries': countries}
        df = df[df.country.isin(countries)]
        sales = sales[sales.country.isin(countries)]
    definitions = [
        'GBP; cleaned merchandise only, exact duplicates and service/nonpositive-price lines excluded.',
        'Net revenue = positive merchandise sales less observed credits. Credits can relate to sales outside the selected period.',
        'Orders = distinct positive-sale invoices. Missing customer IDs remain in sales but are excluded from customer methods.',
        'Historical extract ends 9 December 2011; December 2011 and partial filter months have incomplete coverage.',
    ]
    ev = evidence(tool, scope, df, definitions, f'Filter cleaned fact_transaction to {scope}; use approved {tool} aggregation.')
    if df.empty:
        return response(tool, 'No observations in this selection', [note('No eligible records', 'There are no merchandise lines in this date/country selection. Widen the period or choose another market.', ev, 'amber')], 'No eligible transactions were found. No results have been invented.', warnings)
    s = summary(df)
    blocks = []
    if tool == 'sales':
        trend = time_series(df, 'month')
        country = df.groupby('country', observed=True).amount.sum().sort_values(ascending=False).head(8).rename('revenue').reset_index()
        totals = sales.groupby('invoice', observed=True).amount.sum()
        bins = pd.cut(totals, [0, 50, 100, 250, 500, 1000, np.inf], labels=['£0–50', '£50–100', '£100–250', '£250–500', '£500–1,000', '£1,000+'], right=False).value_counts(sort=False)
        rhythm = sales.groupby('day', observed=True).invoice.nunique().reindex(range(7), fill_value=0)
        blocks = [
            chart('Revenue through time', trend, 'date', [('revenue', 'Net revenue')], ev, 'line', subtitle='Monthly totals · GBP'),
            chart('Sales and observed credits', trend, 'date', [('grossRevenue', 'Positive sales'), ('returns', 'Credits')], ev, 'line'),
            chart('Where revenue comes from', records(country), 'country', [('revenue', 'Net revenue')], ev, subtitle='Top eight recorded markets'),
            chart('The size of an order', [{'range': str(k), 'orders': int(v)} for k, v in bins.items()], 'range', [('orders', 'Orders')], ev, fmt='number'),
            chart('The weekly rhythm', [{'day': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i], 'orders': int(v)} for i, v in rhythm.items()], 'day', [('orders', 'Orders')], ev, fmt='number'),
            note('What this tells us', f"This selection contains {s['orders']:,} sale invoices and £{s['revenue']:,.2f} net merchandise revenue. Observed credits total £{s['returns']:,.2f} ({s['returnRate']:.2f}% of positive sales). Peaks are descriptive; they do not identify the cause of changes.", ev),
        ]
        title = 'The sales story'
        message = f"I added five views of sales and a summary. Net revenue is £{s['revenue']:,.2f} across {s['orders']:,} sale invoices. Every view uses the same selected scope."
    elif tool == 'markets':
        countries_summary = []
        for name, group in df.groupby('country', observed=True):
            cs = summary(group)
            countries_summary.append({'country': str(name), 'revenue': cs['revenue'], 'orders': cs['orders'], 'aov': cs['aov'], 'repeatRate': cs['repeatRate'], 'customers': cs['customers'], 'returnRate': cs['returnRate']})
        countries_summary.sort(key=lambda r: -r['revenue'])
        shown = countries_summary[:10]
        trend = df.groupby(['month', 'country'], observed=True).amount.sum().unstack(fill_value=0)
        top = [r['country'] for r in shown[:4]]
        trend_rows = [{'date': str(month), **{name: float(row.get(name, 0)) for name in top}} for month, row in trend.iterrows()]
        definitions += ['Country is recorded customer residence; this retailer is not a representative sample of each national market.', 'Repeat rate is calculated among identified shoppers within the selected window; it is not a causal country effect.']
        ev = evidence(tool, scope, df, definitions, 'Group selected merchandise lines by country; compute positive-invoice orders, gross AOV, observed net revenue and identified repeat shoppers.')
        blocks = [
            chart('Revenue by market', shown, 'country', [('revenue', 'Net revenue')], ev),
            chart('Basket value, compared fairly', shown, 'country', [('aov', 'Gross average order value')], ev, subtitle='Positive sales / positive invoices'),
            chart('Repeat buyers by market', shown, 'country', [('repeatRate', 'Repeat buyer share')], ev, fmt='percent'),
            chart('Markets through time', trend_rows, 'date', [(name, name) for name in top], ev, 'line'),
            chart('Evidence behind each market', shown, 'country', [('orders', 'Orders'), ('customers', 'Identified customers')], ev, 'table', 'number'),
            note('Scale is not demand', 'A larger observed sales total can reflect retailer reach, availability, pricing or wholesale orders. Compare order value and repeat behavior alongside volume. These observations do not establish how a new product would perform in another country.', ev, 'amber'),
        ]
        title, message = 'A closer look at markets', f"I compared {len(countries_summary)} recorded markets using revenue, order value, repeat purchasing and time trends. The supporting table shows the evidence count; these are retailer observations, not national demand estimates."
    elif tool == 'product':
        if product_code is None:
            if sales.empty:
                return response(tool, 'No positive purchases', [note('Only credit activity', 'This selection contains credits but no positive product purchases. Choose another period to investigate a product.', ev, 'amber')], 'No positive product purchases were found in this selection.', warnings)
            product_code = str(sales.groupby('code', observed=True).amount.sum().idxmax())
            warnings.append('No product was specified; this investigation uses the revenue-leading product in the selected scope.')
        if not isinstance(product_code, str) or not DATA.code.eq(product_code).any():
            raise ValueError('Choose a recorded stock code from the product search.')
        product = df[df.code.eq(product_code)]
        product_sales = product[product.quantity > 0]
        name = str(DATA.loc[DATA.code.eq(product_code), 'name'].iloc[0]).strip()
        pscope = {**scope, 'productCode': product_code}
        definitions += ['Product order penetration = positive invoices containing this product / all positive invoices in the same country and date window × 100.', 'Observed unit price is transaction revenue per unit, not willingness-to-pay or an elasticity estimate.']
        ev = evidence(tool, pscope, product, definitions, f'Filter product_id={product_code}; group positive and negative line values by month/country; divide product invoice counts by eligible market invoice counts.')
        if product.empty:
            return response(tool, name, [note('No observations for this product', f'{name} ({product_code}) has no eligible records in this selection. Absence of purchases does not prove lack of demand.', ev, 'amber')], f'No records for {name} were found in the chosen scope. Try a wider period or another market.', warnings)
        ps = summary(product)
        markets = []
        for country_name, group in df.groupby('country', observed=True):
            positive = group[group.quantity > 0]
            selected = group[group.code.eq(product_code)]
            sold = selected[selected.quantity > 0]
            denominator = positive.invoice.nunique()
            markets.append({'country': str(country_name), 'revenue': round(float(selected.amount.sum()), 2), 'orders': int(sold.invoice.nunique()), 'penetration': round(sold.invoice.nunique()/denominator*100, 3) if denominator else 0, 'marketOrders': int(denominator)})
        markets.sort(key=lambda r: -r['revenue'])
        price = product_sales.assign(priceBand=pd.cut(product_sales.price, [0,1,2,5,10,20,50,np.inf], labels=['<£1','£1–2','£2–5','£5–10','£10–20','£20–50','£50+'], right=False)).groupby('priceBand', observed=True).quantity.sum().rename('units').reset_index()
        buyers = product_sales.dropna(subset=['customer']).groupby('customer', observed=True).invoice.nunique()
        repeat = int((buyers >= 2).sum())
        blocks = [
            chart(f'{name.title()} · trend', time_series(product, 'month'), 'date', [('revenue', 'Net revenue')], ev, 'line'),
            chart('Where this product sells', markets[:10], 'country', [('revenue', 'Net revenue')], ev),
            chart('Share of market orders', sorted(markets, key=lambda r: -r['penetration'])[:10], 'country', [('penetration', 'Orders containing this product')], ev, fmt='percent', subtitle='Normalized by each market’s observed sale invoices'),
            chart('Observed price and volume', records(price), 'priceBand', [('units', 'Units purchased')], ev, fmt='number'),
            chart('Product buyer behavior', [{'behavior': 'One observed order', 'customers': len(buyers)-repeat}, {'behavior': 'Two or more orders', 'customers': repeat}], 'behavior', [('customers', 'Identified customers')], ev, fmt='number'),
            note('A product hypothesis, grounded in evidence', f"{name} ({product_code}) generated £{ps['grossRevenue']:,.2f} positive sales across {ps['orders']:,} invoices in this scope. {repeat:,} of {len(buyers):,} identified buyers purchased it on multiple invoices. Use market penetration alongside evidence counts before choosing a market test. This historical comparison cannot establish future demand for a new product.", ev, 'blue'),
        ]
        title, message = f'{name.title()} · investigation', f"I added five views of {name.lower()} and an evidence note. Compare normalized market order share as well as raw revenue. A market test is a hypothesis; this data alone cannot predict launch success."
    elif tool == 'customers':
        identified = sales.dropna(subset=['customer'])
        if identified.empty:
            return response(tool, 'Customer identity is missing', [note('No identified shoppers', 'Sales remain valid, but this selection has no customer IDs suitable for repeat, RFM or retention analysis.', ev, 'amber')], 'There are no identified shoppers in this selection.', warnings)
        customers, segments, clusters, cohorts, quality = customer_analysis(sales, scope['end'])
        freq = customers.frequency
        freq_bins = [('1 order', freq.eq(1)), ('2–3 orders', freq.between(2,3)), ('4–9 orders', freq.between(4,9)), ('10+ orders', freq.ge(10))]
        freq_rows = [{'frequency': name, 'customers': int(mask.sum())} for name, mask in freq_bins]
        monthly = identified.groupby('month', observed=True).customer.nunique().rename('customers').reset_index().rename(columns={'month':'date'})
        cohort_rows = [{'cohort': c['month'], 'customers': c['size'], **{f'month{i}': c['retention'][i] for i in range(1, min(7, len(c['retention'])))}} for c in cohorts]
        definitions += ['RFM segments use percentile rules on the selected window; they are descriptions, not lifecycle truth.', 'Cohort = first observed purchase inside the selected scope, not verified lifetime acquisition. Unobserved months are null.']
        ev = evidence(tool, scope, df, definitions, 'Use identified positive-sale customers; aggregate distinct invoices, gross spend and recency; build selected-window cohorts and RFM segments.')
        blocks = [
            chart('A reason to come back', freq_rows, 'frequency', [('customers','Identified customers')], ev, fmt='number'),
            chart('Customer segments', segments, 'name', [('customers','Customers')], ev, 'donut', 'number'),
            chart('Active shoppers through time', records(monthly), 'date', [('customers','Identified customers')], ev, 'line', 'number'),
            chart('Retention by observed cohort', cohort_rows, 'cohort', [('month1','Month 1'),('month2','Month 2'),('month3','Month 3'),('month6','Month 6')], ev, 'table', 'percent', 'Percent returning · null means not yet observed'),
            chart('Learned cluster profiles', clusters, 'name', [('avgMonetary','Mean positive spend')], ev, subtitle=f"K-means k={quality['k']} · silhouette {quality['silhouette'] if quality['silhouette'] is not None else 'not available'}"),
            note('Repeat behavior has a window', f"{s['customers']:,} identified customers appear here; {s['repeatRate']:.2f}% placed at least two sale invoices. Anonymous purchases represent {100-s['identifiedRevenueShare']:.2f}% of positive sales and cannot be assigned a customer segment. Retention is observed only inside the selected period.", ev),
        ]
        title, message = 'The customer story', f"I added repeat-frequency, RFM, activity, cohort and cluster views. {s['repeatRate']:.2f}% of identified shoppers made multiple purchases within this selection; that is not a lifetime retention probability."
    else:
        basket = basket_analysis(sales)
        rules = basket['rules']
        if product_code:
            if not isinstance(product_code, str) or not DATA.code.eq(product_code).any():
                raise ValueError('Unknown product code.')
            name = str(DATA.loc[DATA.code.eq(product_code), 'name'].iloc[0])
            rules = [r for r in rules if r['antecedent'] == name or r['consequent'] == name]
            warnings.append('Product-specific display is filtered from the top 20 rules among the top 80 products; an empty result is not proof of no association.')
            scope = {**scope, 'productCode': product_code}
        definitions += ['Exact pair mining among the 80 most frequent products; each product counts once per positive-sale invoice.', 'Support denominator = all selected positive merchandise invoices. Minimum pair count=max(20,ceil(0.2%×baskets)); confidence≥15%; lift>1; show top20 directional rules by lift.', 'Association is not causation. Review absolute basket counts as well as lift.']
        ev = evidence(tool, scope, df, definitions, 'Construct distinct invoice/product baskets; compute exact frequent-pair support, directional confidence and lift using approved basket_analysis.')
        rows = [{'pair': f"{r['antecedent'].strip().title()} → {r['consequent'].strip().title()}", **r} for r in rules]
        blocks = [
            chart('Product affinities', rows[:8], 'pair', [('lift','Lift')], ev, fmt='number', subtitle='Top directional rules · lift relative to independent purchases'),
            chart('How often pairs appear', rows[:8], 'pair', [('support','Support')], ev, fmt='percent'),
            chart('The strength behind each pair', rows, 'pair', [('confidence','Confidence'),('count','Baskets'),('lift','Lift')], ev, 'table', 'number', 'Support/confidence in percent; count is actual baskets'),
            note('A bundle worth investigating', f"The selected scope contains {basket['transactions']:,} positive-sale baskets. {len(rules)} displayed rules meet the bounded mining criteria. A strong association suggests a bundle experiment; it does not establish incremental revenue. No suitable rules may mean the sample or top-product restriction is too small.", ev, 'amber'),
        ]
        title, message = 'Products, better together', f"I examined {basket['transactions']:,} baskets and added {len(rules)} qualifying displayed pair rules with their evidence. Lift is association strength, not a forecast of bundle sales."
    return response(tool, title, blocks, message, warnings, product_code)


def response(tool, title, blocks, message, warnings, product=None):
    notes = [b for b in blocks if b['kind'] == 'note']
    edges = [{'source': b['id'], 'target': notes[-1]['id'], 'label': 'Evidence for'} for b in blocks[:2] if b['kind'] == 'chart'] if notes else []
    return {'id': uid(), 'title': title, 'mode': 'guided', 'message': message, 'blocks': blocks, 'connections': edges,
            'followUps': followups(product), 'warnings': warnings}


def guided_plan(message, scope, selected=None, product_code=None, countries=None):
    text = message.casefold()
    plan = {'scope': validate_scope(scope), 'product_code': product_code, 'countries': countries}
    years = set(re.findall(r'\b(2010|2011)\b', text))
    if len(years) == 1 and not re.search(r'\d{4}-\d{2}-\d{2}', text):
        year = next(iter(years))
        plan['scope'] = {**plan['scope'], 'start': f'{year}-01-01', 'end': META['end'] if year == '2011' else '2010-12-31'}
    mentioned = [c for c in META['countries'] if re.search(r'(?<!\w)' + re.escape(c.casefold()) + r'(?!\w)', text)]
    if re.search(r'\buk\b|united kingdom', text) and 'United Kingdom' not in mentioned:
        mentioned.insert(0, 'United Kingdom')
    if mentioned:
        if len(mentioned) > 1:
            plan['countries'] = mentioned[:6]
        else:
            plan['scope'] = {**plan['scope'], 'country': mentioned[0]}
    if not plan['product_code']:
        for item in selected or []:
            candidate = (item.get('evidence') or {}).get('scope', {}).get('productCode')
            if candidate:
                plan['product_code'] = candidate
                break
    code_match = re.search(r'\b(\d{5}[a-z]{0,2})\b', text, flags=re.I)
    if code_match and DATA.code.eq(code_match.group(1).upper()).any():
        plan['product_code'] = code_match.group(1).upper()
    if any(x in text for x in ['new product', 'predict', 'forecast', 'will it', 'launch success']):
        return None
    if any(x in text for x in ['together','bundle','basket','affinit','association','pair']):
        plan['tool'] = 'baskets'
    elif any(x in text for x in ['customer','retention','repeat','loyal','cohort','rfm','segment']):
        plan['tool'] = 'customers'
    elif any(x in text for x in ['product','stock code','bestseller']) or plan['product_code']:
        plan['tool'] = 'product'
    elif any(x in text for x in ['market','country','countries','compare']) or len(mentioned) > 1:
        plan['tool'] = 'markets'
    elif any(x in text for x in ['sales','revenue','order','trend','season']):
        plan['tool'] = 'sales'
    else:
        return None
    return plan


def unsupported():
    return {'id': uid(), 'title': 'Choose an investigation', 'mode': 'guided', 'blocks': [], 'connections': [],
            'message': 'Guided mode supports sales, market comparisons, recorded products, repeat customers and basket pairs. Choose a suggestion or select a product. Open-ended reasoning needs a configured model. New-product demand or launch success cannot be established from these historical transactions alone.',
            'followUps': followups(), 'warnings': []}
