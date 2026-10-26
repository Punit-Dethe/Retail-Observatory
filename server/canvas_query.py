"""Validated declarative retail queries for the model agent.

The model describes *what* to measure (measures, dimensions, filters); the server decides *how*,
using fixed definitions over the cleaned warehouse. No model-written SQL or code is executed.
"""
import math
import re
import numpy as np
import pandas as pd
from analytics import DATA, META
from canvas_analysis import evidence, uid, validate_scope

# name: (label, format, additive-for-share, definition)
MEASURES = {
    'net_revenue': ('Net revenue', 'currency', 'Positive merchandise sales less observed credits, GBP.'),
    'gross_revenue': ('Positive sales', 'currency', 'Sum of positive merchandise line values, GBP.'),
    'credits': ('Observed credits', 'currency', 'Absolute value of negative (credit) merchandise lines, GBP. Credits can relate to sales outside the window.'),
    'credit_rate': ('Credit rate', 'percent', 'Observed credits / positive sales × 100.'),
    'orders': ('Orders', 'number', 'Distinct positive-sale invoices.'),
    'units': ('Units', 'number', 'Units on positive-sale lines.'),
    'customers': ('Identified customers', 'number', 'Distinct customer IDs on positive-sale lines; anonymous shoppers excluded.'),
    'aov': ('Average order value', 'currency', 'Positive sales / distinct positive-sale invoices, GBP.'),
    'avg_unit_price': ('Average unit price', 'currency', 'Positive sales / units sold (volume-weighted), GBP.'),
    'products': ('Distinct products', 'number', 'Distinct stock codes on positive-sale lines.'),
    'repeat_rate': ('Repeat-customer share', 'percent', 'Identified customers with two or more positive-sale invoices inside the group and window / identified customers × 100.'),
    'revenue_per_customer': ('Positive sales per identified customer', 'currency', 'Positive sales from identified customers / identified customers, GBP.'),
    'lines_per_order': ('Lines per order', 'number', 'Positive-sale lines / distinct positive-sale invoices.'),
}
DIMENSIONS = {
    'year': 'Calendar year', 'quarter': 'Calendar quarter', 'month': 'Calendar month', 'week': 'Week starting Monday',
    'date': 'Calendar day', 'weekday': 'Day of week', 'hour': 'Hour of invoice', 'country': 'Recorded customer country',
    'product': 'Product', 'customer': 'Identified customer', 'customer_type': 'Identified or anonymous shopper',
    'order_size': 'Invoice value band', 'price_band': 'Unit price band',
}
TIME_DIMS = {'year', 'quarter', 'month', 'week', 'date'}
ORDERED_DIMS = TIME_DIMS | {'weekday', 'hour', 'order_size', 'price_band'}
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ORDER_BINS = [0, 50, 100, 250, 500, 1000, np.inf]
ORDER_LABELS = ['£0–50', '£50–100', '£100–250', '£250–500', '£500–1,000', '£1,000+', 'Credit lines']
PRICE_BINS = [0, 1, 2, 5, 10, 20, 50, np.inf]
PRICE_LABELS = ['<£1', '£1–2', '£2–5', '£5–10', '£10–20', '£20–50', '£50+']
DISTINCT_COUNTS = {'orders', 'customers', 'products'}
FILTER_KEYS = ('start', 'end', 'countries', 'exclude_countries', 'products', 'product_text', 'weekdays', 'hour_from', 'hour_to', 'customer_type', 'min_price', 'max_price')
RATIOS_BY_ORDERS = {'aov', 'lines_per_order', 'credit_rate', 'avg_unit_price'}
RATIOS_BY_CUSTOMERS = {'repeat_rate', 'revenue_per_customer'}
SHAREABLE = {'net_revenue', 'gross_revenue', 'credits', 'units', 'orders', 'customers'}
COUNTRY_ALIASES = {'uk': 'United Kingdom', 'great britain': 'United Kingdom', 'britain': 'United Kingdom', 'england': 'United Kingdom', 'usa': 'USA', 'us': 'USA', 'united states': 'USA'}
CODES = set(DATA.code.cat.categories.astype(str))
BASE_DEFINITIONS = [
    'GBP; cleaned merchandise only, exact duplicates and service/nonpositive-price lines excluded.',
    'Historical extract ends 9 December 2011; December 2011 and partial filter months have incomplete coverage.',
]


class QueryError(ValueError):
    """A correctable problem in a model query; the message is returned to the model."""


def clean_text(value, limit):
    if not isinstance(value, str):
        return ''
    return re.sub(r'[\x00-\x1f\x7f]+', ' ', value).strip()[:limit]


def country_list(value, field):
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or len(value) > 12:
        raise QueryError(f'{field} must be a list of at most 12 recorded countries.')
    lookup = {c.casefold(): c for c in META['countries']}
    out = []
    for item in value:
        key = str(item).strip().casefold()
        name = lookup.get(key) or COUNTRY_ALIASES.get(key)
        if not name or name not in META['countries']:
            raise QueryError(f'Unknown country "{str(item)[:40]}". Use a recorded country name such as {", ".join(META["countries"][:5])}.')
        if name not in out:
            out.append(name)
    return out


def date_value(value, default, field):
    if value in (None, ''):
        return default
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise QueryError(f'{field} must be YYYY-MM-DD.')
    try:
        if pd.Timestamp(value).strftime('%Y-%m-%d') != value:
            raise ValueError()
    except ValueError:
        raise QueryError(f'{field} is not a real calendar date.') from None
    if value < META['start'] or value > META['end']:
        raise QueryError(f'{field} must be within the data coverage {META["start"]} to {META["end"]}.')
    return value


def parse_filters(raw, scope):
    raw = raw or {}
    if not isinstance(raw, dict):
        raise QueryError('filters must be an object.')
    allowed = set(FILTER_KEYS)
    unknown = set(raw) - allowed
    if unknown:
        raise QueryError(f'Unknown filter(s): {", ".join(sorted(unknown))[:120]}. Allowed: {", ".join(sorted(allowed))}.')
    f = {'start': date_value(raw.get('start'), scope['start'], 'filters.start'),
         'end': date_value(raw.get('end'), scope['end'], 'filters.end')}
    if f['start'] > f['end']:
        raise QueryError('filters.start must be on or before filters.end.')
    countries = country_list(raw.get('countries'), 'filters.countries')
    if not countries and raw.get('countries') is None and scope.get('country', 'all') != 'all':
        countries = [scope['country']]
    f['countries'] = countries
    f['exclude_countries'] = country_list(raw.get('exclude_countries'), 'filters.exclude_countries')
    products = raw.get('products') or []
    if isinstance(products, str):
        products = [products]
    if not isinstance(products, list) or len(products) > 10:
        raise QueryError('filters.products must be a list of at most 10 stock codes.')
    codes = []
    for item in products:
        code = str(item).strip().upper()
        if code not in CODES:
            raise QueryError(f'Unknown stock code "{str(item)[:20]}". Use find_products to look up recorded codes.')
        codes.append(code)
    f['products'] = codes
    text = clean_text(raw.get('product_text'), 40)
    if raw.get('product_text') not in (None, '') and len(text) < 2:
        raise QueryError('filters.product_text needs at least two characters.')
    f['product_text'] = text or None
    days = raw.get('weekdays') or []
    if not isinstance(days, list) or len(days) > 7:
        raise QueryError('filters.weekdays must be a list of weekday numbers (0=Mon) or names.')
    parsed_days = []
    for d in days:
        if isinstance(d, int) and 0 <= d <= 6:
            parsed_days.append(d)
        elif isinstance(d, str) and d[:3].title() in WEEKDAYS:
            parsed_days.append(WEEKDAYS.index(d[:3].title()))
        else:
            raise QueryError(f'Unknown weekday {str(d)[:12]}.')
    f['weekdays'] = sorted(set(parsed_days))
    for key in ['hour_from', 'hour_to']:
        v = raw.get(key)
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 23):
            raise QueryError(f'filters.{key} must be an hour from 0 to 23.')
        f[key] = v
    ctype = raw.get('customer_type')
    if ctype not in (None, 'identified', 'anonymous'):
        raise QueryError('filters.customer_type must be identified, anonymous or null.')
    f['customer_type'] = ctype
    for key in ['min_price', 'max_price']:
        v = raw.get(key)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0):
            raise QueryError(f'filters.{key} must be a non-negative number.')
        f[key] = float(v) if v is not None else None
    return f


def apply_filters(f, start=None, end=None):
    mask = DATA.date_id.between(start or f['start'], end or f['end'])
    if f['countries']:
        mask &= DATA.country.isin(f['countries'])
    if f['exclude_countries']:
        mask &= ~DATA.country.isin(f['exclude_countries'])
    if f['products']:
        mask &= DATA.code.isin(f['products'])
    if f['product_text']:
        names = DATA.name.cat.categories
        matched = names[names.astype(str).str.casefold().str.contains(f['product_text'].casefold(), regex=False)]
        if not len(matched):
            raise QueryError(f'No recorded product names contain "{f["product_text"]}". Try find_products or a broader word.')
        mask &= DATA.name.isin(matched)
    if f['weekdays']:
        mask &= DATA.day.isin(f['weekdays'])
    if f['hour_from'] is not None:
        mask &= DATA.hour.ge(f['hour_from'])
    if f['hour_to'] is not None:
        mask &= DATA.hour.le(f['hour_to'])
    if f['customer_type'] == 'identified':
        mask &= DATA.customer.notna()
    elif f['customer_type'] == 'anonymous':
        mask &= DATA.customer.isna()
    if f['min_price'] is not None:
        mask &= DATA.price.ge(f['min_price'])
    if f['max_price'] is not None:
        mask &= DATA.price.le(f['max_price'])
    return DATA.loc[mask]


def add_keys(df, dims):
    frame = df[['invoice', 'code', 'customer', 'quantity', 'amount']].copy()
    for d in dims:
        if d == 'year':
            frame[d] = df.date.dt.year
        elif d == 'quarter':
            frame[d] = df.date.dt.year.astype(str) + '-Q' + df.date.dt.quarter.astype(str)
        elif d == 'month':
            frame[d] = df.month.astype(str)
        elif d == 'week':
            frame[d] = (df.date.dt.normalize() - pd.to_timedelta(df.day, unit='D')).dt.strftime('%Y-%m-%d')
        elif d == 'date':
            frame[d] = df.date_id
        elif d == 'weekday':
            frame[d] = df.day
        elif d == 'hour':
            frame[d] = df.hour
        elif d == 'country':
            frame[d] = df.country.astype(str)
        elif d == 'product':
            frame[d] = df.code.astype(str)
        elif d == 'customer':
            frame[d] = df.customer
        elif d == 'customer_type':
            frame[d] = np.where(df.customer.isna(), 'Anonymous', 'Identified')
        elif d == 'order_size':
            positive = df[df.quantity > 0]
            totals = positive.groupby('invoice', observed=True).amount.sum()
            bands = pd.Series(pd.cut(totals, ORDER_BINS, labels=False, right=False), index=totals.index)
            frame[d] = df.invoice.map(bands).where(df.quantity > 0, len(ORDER_LABELS) - 1).fillna(len(ORDER_LABELS) - 1).astype(int)
        elif d == 'price_band':
            frame[d] = pd.cut(df.price, PRICE_BINS, labels=False, right=False).fillna(0).astype(int)
    if 'customer' in dims:
        frame = frame[frame.customer.notna()]
    return frame


def aggregate(frame, keys):
    if not keys:
        frame = frame.assign(_all='All')
        keys = ['_all']
    sales = frame[frame.quantity > 0]
    gs = sales.groupby(keys, observed=True, sort=False)
    identified = sales[sales.customer.notna()]
    gi = identified.groupby(keys, observed=True, sort=False)
    per_customer = identified.groupby([*keys, 'customer'], observed=True).invoice.nunique()
    repeat = (per_customer >= 2).groupby(level=list(range(len(keys)))).mean() * 100 if len(per_customer) else pd.Series(dtype=float)
    parts = {
        'gross': gs.amount.sum(), 'orders': gs.invoice.nunique(), 'units': gs.quantity.sum(), 'lines': gs.size(),
        'products': gs.code.nunique(), 'customers': gi.customer.nunique(), 'identifiedGross': gi.amount.sum(),
        'repeat': repeat, 'credits': -frame[frame.quantity < 0].groupby(keys, observed=True, sort=False).amount.sum(),
    }
    base = pd.concat([s.rename(k) for k, s in parts.items()], axis=1)
    for col in ['gross', 'orders', 'units', 'lines', 'products', 'customers', 'identifiedGross', 'credits']:
        base[col] = base[col].fillna(0)

    def ratio(a, b, scale=1.0):
        return pd.Series(np.where(b > 0, a / b.where(b > 0, 1) * scale, np.nan), index=base.index)

    out = pd.DataFrame(index=base.index)
    out['net_revenue'] = base.gross - base.credits
    out['gross_revenue'] = base.gross
    out['credits'] = base.credits
    out['credit_rate'] = ratio(base.credits, base.gross, 100)
    out['orders'] = base.orders
    out['units'] = base.units
    out['customers'] = base.customers
    out['aov'] = ratio(base.gross, base.orders)
    out['avg_unit_price'] = ratio(base.gross, base.units)
    out['products'] = base.products
    out['repeat_rate'] = base.repeat.where(base.customers > 0)
    out['revenue_per_customer'] = ratio(base.identifiedGross, base.customers)
    out['lines_per_order'] = ratio(base.lines, base.orders)
    return out


def label(dim, value, names):
    if dim == 'weekday':
        return WEEKDAYS[int(value)]
    if dim == 'hour':
        return f'{int(value):02d}:00'
    if dim == 'order_size':
        return ORDER_LABELS[int(value)]
    if dim == 'price_band':
        return PRICE_LABELS[int(value)]
    if dim == 'product':
        return names.get(str(value), str(value))
    if dim == 'year':
        return str(int(value))
    return str(value)


def clean_number(v, fmt):
    if v is None or (isinstance(v, float) and not math.isfinite(v)) or pd.isna(v):
        return None
    return round(float(v), 2) if fmt != 'number' or not float(v).is_integer() else int(v)


def parse_spec(spec, scope):
    if not isinstance(spec, dict):
        raise QueryError('Send query_retail arguments as an object.')
    top = {'title', 'purpose', 'measures', 'group_by', 'filters', 'compare_period', 'sort_by', 'sort_order', 'limit', 'min_orders', 'include_share', 'chart'}
    stray = set(spec) - top
    if stray:
        hint = ' Put row filters such as start, end, countries, products and product_text inside "filters".' if stray & set(FILTER_KEYS) else ''
        raise QueryError(f'Unknown argument(s): {", ".join(sorted(stray))[:120]}.{hint}')
    measures = spec.get('measures') or ['net_revenue']
    if isinstance(measures, str):
        measures = [measures]
    if not isinstance(measures, list) or not 1 <= len(measures) <= 4 or any(m not in MEASURES for m in measures):
        raise QueryError(f'measures must list 1–4 of: {", ".join(MEASURES)}.')
    measures = list(dict.fromkeys(measures))
    dims = spec.get('group_by') or []
    if isinstance(dims, str):
        dims = [dims]
    if not isinstance(dims, list) or len(dims) > 2 or any(d not in DIMENSIONS for d in dims) or len(set(dims)) != len(dims):
        raise QueryError(f'group_by must list 0–2 distinct of: {", ".join(DIMENSIONS)}.')
    filters = parse_filters(spec.get('filters'), scope)
    compare = spec.get('compare_period')
    if compare is not None:
        if not isinstance(compare, dict):
            raise QueryError('compare_period must be an object with start and end, or null.')
        if any(d in TIME_DIMS for d in dims):
            raise QueryError('compare_period cannot be combined with a time dimension; group by a non-time dimension or omit compare_period.')
        if len(dims) > 1:
            raise QueryError('compare_period supports at most one group_by dimension.')
        compare = {'start': date_value(compare.get('start'), None, 'compare_period.start'), 'end': date_value(compare.get('end'), None, 'compare_period.end')}
        if not compare['start'] or not compare['end'] or compare['start'] > compare['end']:
            raise QueryError('compare_period needs start and end with start on or before end.')
    sort_by = spec.get('sort_by') or None
    valid_sort = set(measures) | {f'{m}_change_pct' for m in measures if compare} | {f'{m}_change' for m in measures if compare}
    if sort_by is not None and sort_by not in valid_sort and sort_by not in dims:
        raise QueryError(f'sort_by must be one of the requested measures, their compare columns, or a group_by dimension.')
    order = spec.get('sort_order') or None
    if order not in (None, 'asc', 'desc'):
        raise QueryError('sort_order must be asc or desc.')
    limit = spec.get('limit')
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 25):
        raise QueryError('limit must be an integer from 1 to 25 (time dimensions are not limited).')
    chart = spec.get('chart') or None
    if chart not in (None, 'line', 'bar', 'table', 'donut'):
        raise QueryError('chart must be line, bar, table or donut.')
    share = bool(spec.get('include_share'))
    if share and measures[0] not in SHAREABLE:
        raise QueryError(f'include_share needs the first measure to be one of {", ".join(sorted(SHAREABLE))}.')
    min_orders = spec.get('min_orders')
    if min_orders is not None and (isinstance(min_orders, bool) or not isinstance(min_orders, int) or not 0 <= min_orders <= 100000):
        raise QueryError('min_orders must be a non-negative integer or null.')
    if min_orders and not dims:
        min_orders = None
    return {'measures': measures, 'group_by': dims, 'filters': filters, 'compare_period': compare, 'sort_by': sort_by,
            'sort_order': order, 'limit': limit, 'chart': chart, 'include_share': share, 'min_orders': min_orders or None,
            'title': clean_text(spec.get('title'), 90) or 'Retail evidence', 'purpose': clean_text(spec.get('purpose'), 200)}


def describe(spec):
    f = spec['filters']
    parts = [f"Measure {', '.join(MEASURES[m][0].lower() for m in spec['measures'])}",
             f"grouped by {' and '.join(DIMENSIONS[d].lower() for d in spec['group_by'])}" if spec['group_by'] else 'as one total',
             f"from {f['start']} to {f['end']}"]
    if f['countries']:
        parts.append('in ' + ', '.join(f['countries']))
    if f['exclude_countries']:
        parts.append('excluding ' + ', '.join(f['exclude_countries']))
    if f['products']:
        parts.append('for stock codes ' + ', '.join(f['products']))
    if f['product_text']:
        parts.append(f'for products whose name contains "{f["product_text"]}"')
    if f['weekdays']:
        parts.append('on ' + ', '.join(WEEKDAYS[d] for d in f['weekdays']))
    if f['hour_from'] is not None or f['hour_to'] is not None:
        parts.append(f"between hours {f['hour_from'] if f['hour_from'] is not None else 0} and {f['hour_to'] if f['hour_to'] is not None else 23}")
    if f['customer_type']:
        parts.append(f"{f['customer_type']} shoppers only")
    if f['min_price'] is not None or f['max_price'] is not None:
        parts.append(f"unit price £{f['min_price'] or 0}–{'£' + str(f['max_price']) if f['max_price'] is not None else 'any'}")
    if spec['compare_period']:
        parts.append(f"compared with {spec['compare_period']['start']} to {spec['compare_period']['end']}")
    return '; '.join(parts) + '. Executed by the approved query_retail engine over cleaned fact_transaction.'


def run_query(raw_spec, scope):
    """Return (block, model_view, numbers). Raises QueryError for correctable model mistakes."""
    spec = parse_spec(raw_spec, validate_scope(scope))
    f, dims, measures = spec['filters'], spec['group_by'], spec['measures']
    df = apply_filters(f)
    if 'date' in dims and (pd.Timestamp(f['end']) - pd.Timestamp(f['start'])).days > 120:
        raise QueryError('Daily grouping is limited to 120 days. Use week or month, or narrow filters.start/end.')
    if 'customer' in dims and not spec['limit']:
        spec['limit'] = 15
    names = {}
    if 'product' in dims or f['products']:
        sub = df.drop_duplicates('code')[['code', 'name']]
        names = {str(c): str(n).strip().title() for c, n in zip(sub.code, sub.name)}
    frame = add_keys(df, dims)
    agg = aggregate(frame, dims) if not frame.empty else pd.DataFrame(columns=list(MEASURES))
    overall = aggregate(add_keys(df, []), []) if not df.empty else None
    total_groups = len(agg)
    if len(agg):
        agg['orders_for_threshold'] = agg['orders']
    cols = list(measures)
    # Ratios on tiny groups mislead; always carry the denominator so the model and reader can see it.
    if any(m in RATIOS_BY_ORDERS for m in measures) and 'orders' not in measures:
        agg['sample_orders'] = agg['orders'] if len(agg) else []
        cols.append('sample_orders')
    if any(m in RATIOS_BY_CUSTOMERS for m in measures) and 'customers' not in measures:
        agg['sample_customers'] = agg['customers'] if len(agg) else []
        cols.append('sample_customers')
    if spec['include_share'] and overall is not None and len(agg):
        total = float(overall[measures[0]].iloc[0])
        agg['share_pct'] = agg[measures[0]] / total * 100 if total else np.nan
        cols.append('share_pct')
    if spec['compare_period'] and len(agg):
        prev_df = apply_filters(f, spec['compare_period']['start'], spec['compare_period']['end'])
        prev = aggregate(add_keys(prev_df, dims), dims) if not prev_df.empty else pd.DataFrame(columns=list(MEASURES))
        for m in measures:
            agg[f'{m}_previous'] = prev[m].reindex(agg.index) if len(prev) else np.nan
            agg[f'{m}_change'] = agg[m] - agg[f'{m}_previous']
            agg[f'{m}_change_pct'] = np.where(agg[f'{m}_previous'].abs() > 0, agg[f'{m}_change'] / agg[f'{m}_previous'].abs().where(agg[f'{m}_previous'].abs() > 0, 1) * 100, np.nan)
            cols += [f'{m}_previous', f'{m}_change', f'{m}_change_pct']
    agg = agg.reset_index()
    if spec['min_orders'] and len(agg):
        agg = agg[agg.orders_for_threshold >= spec['min_orders']] if 'orders_for_threshold' in agg else agg
    ordered = bool(dims) and dims[0] in ORDERED_DIMS
    if agg.empty:
        pass
    elif spec['sort_by']:
        agg = agg.sort_values(spec['sort_by'], ascending=spec['sort_order'] == 'asc', na_position='last')
    elif ordered:
        agg = agg.sort_values(dims, ascending=True)
    elif dims:
        agg = agg.sort_values(measures[0], ascending=spec['sort_order'] == 'asc', na_position='last')
    if len(dims) == 1 and dims[0] not in TIME_DIMS:
        limit = spec['limit'] or (len(agg) if ordered else 15)
        agg = agg.head(limit)
    elif len(dims) == 1 and len(agg) > 120:
        raise QueryError(f'This grouping returns {len(agg)} time periods; use a coarser time dimension or narrower dates.')

    fmt_of = lambda c: 'percent' if c.endswith(('_pct', '_rate')) or c == 'share_pct' else MEASURES.get(c.replace('_previous', '').replace('_change', ''), ('', 'number'))[1]
    rows, series, x_key = [], [], dims[0] if dims else 'scope'
    pivoted = len(dims) == 2 and not agg.empty
    if pivoted:
        m = measures[0]
        x_dim, s_dim = dims
        if x_dim not in ORDERED_DIMS and s_dim in ORDERED_DIMS:
            x_dim, s_dim = s_dim, x_dim
        totals = agg.groupby(s_dim, observed=True)[m].sum().sort_values(ascending=False)
        top = totals.head(spec['limit'] if spec['limit'] and spec['limit'] <= 6 else 6).index.tolist()
        if s_dim in ORDERED_DIMS:
            top = sorted(top)
        keep = agg[agg[s_dim].isin(top)]
        x_values = sorted(keep[x_dim].unique()) if x_dim in ORDERED_DIMS else keep.groupby(x_dim)[m].sum().sort_values(ascending=False).head(spec['limit'] or 15).index.tolist()
        if x_dim in TIME_DIMS and len(x_values) > 120:
            raise QueryError('Too many time periods for a two-dimension chart; use a coarser time dimension.')
        lookup = {(r[x_dim], r[s_dim]): r[m] for r in keep.to_dict('records')}
        series = [(re.sub(r'[.\[\]]', '', label(s_dim, v, names)) or f'series{i}', label(s_dim, v, names)) for i, v in enumerate(top)]
        for xv in x_values:
            row = {x_dim: label(x_dim, xv, names)}
            for (key, _), sv in zip(series, top):
                row[key] = clean_number(lookup.get((xv, sv), 0 if m not in ('aov', 'avg_unit_price', 'credit_rate', 'repeat_rate', 'revenue_per_customer', 'lines_per_order') else None), MEASURES[m][1])
            rows.append(row)
        x_key, fmt = x_dim, MEASURES[m][1]
        dropped = int(agg[s_dim].nunique() - len(top))
    else:
        for r in agg.to_dict('records'):
            row = {x_key: label(dims[0], r[dims[0]], names)} if dims else {'scope': 'Selected filters'}
            if dims and dims[0] == 'product':
                row['code'] = str(r['product'])
            for c in cols:
                row[c] = clean_number(r.get(c), fmt_of(c))
            rows.append(row)
        fmt = MEASURES[measures[0]][1]
        series = [(measures[0], MEASURES[measures[0]][0])]
        if spec['compare_period']:
            series.append((f'{measures[0]}_previous', MEASURES[measures[0]][0] + ' (comparison period)'))
        elif len(measures) > 1 and len({MEASURES[x][1] for x in measures}) == 1:
            series = [(x, MEASURES[x][0]) for x in measures]
        dropped = 0

    chart_type = spec['chart']
    if not dims:
        chart_type = 'table'
    elif chart_type == 'line' and dims[0] not in TIME_DIMS and not (pivoted and x_key in TIME_DIMS):
        chart_type = 'bar'
    elif chart_type == 'donut' and (pivoted or measures[0] not in SHAREABLE - DISTINCT_COUNTS or len(rows) > 8 or any((r.get(measures[0]) or 0) < 0 for r in rows)):
        chart_type = 'bar'
    elif chart_type is None:
        chart_type = 'line' if (x_key in TIME_DIMS) else 'bar'
    if chart_type == 'bar' and x_key in TIME_DIMS and len(rows) > 12:
        chart_type = 'line'

    definitions = [*BASE_DEFINITIONS, *[f'{MEASURES[m][0]}: {MEASURES[m][2]}' for m in measures]]
    if 'customer' in dims or 'customers' in measures or 'repeat_rate' in measures:
        definitions.append('Customer measures use identified shoppers only; repeat behavior is observed only inside the selected window.')
    if 'country' in dims or f['countries']:
        definitions.append('Country is recorded customer residence; this retailer is not a representative sample of national demand.')
    if 'order_size' in dims:
        definitions.append('Invoice value bands use each positive-sale invoice total within the filters; credit lines form their own band.')
    if spec['include_share']:
        definitions.append('share_pct = group value / value over all filtered lines × 100. For distinct counts (orders, customers) groups can overlap, so shares can sum above 100%.')
    if spec['compare_period']:
        definitions.append('Change compares the main window with the comparison window under identical non-date filters; _change_pct is relative to the comparison value.')
    if pivoted and dropped > 0:
        definitions.append(f'Chart shows the top {len(series)} {DIMENSIONS[s_dim].lower()} values; {dropped} smaller values are omitted.')
    if not pivoted and dims and dims[0] not in TIME_DIMS and total_groups > len(rows):
        definitions.append(f'Shows {len(rows)} of {total_groups} groups after sorting.')
    if spec['min_orders']:
        definitions.append(f"Groups with fewer than {spec['min_orders']:,} orders are excluded.")
    definitions.append('Descriptive association over historical data; it does not establish cause.')

    ev_scope = {'start': f['start'], 'end': f['end'], 'country': f['countries'][0] if len(f['countries']) == 1 else 'all'}
    if len(f['countries']) > 1:
        ev_scope['countries'] = f['countries']
    if len(f['products']) == 1:
        ev_scope['productCode'] = f['products'][0]
    ev = evidence('query', ev_scope, df, definitions, describe(spec))
    public_spec = {k: v for k, v in spec.items() if k not in ('title', 'purpose')}
    ev['spec'] = public_spec
    block = {'id': uid(), 'kind': 'chart', 'title': spec['title'], 'subtitle': spec['purpose'], 'chartType': chart_type,
             'rows': rows, 'xKey': x_key, 'series': [{'key': k, 'label': v} for k, v in series], 'format': fmt, 'evidence': ev}
    if df.empty or not rows:
        block.update({'kind': 'note', 'body': 'No eligible merchandise lines match these filters. No values have been invented; widen the dates or relax filters.', 'tone': 'amber'})
        block.pop('chartType'); block.pop('series'); block.pop('xKey')
    overall_view = None
    if overall is not None:
        overall_view = {m: clean_number(overall[m].iloc[0], MEASURES[m][1]) for m in measures}
    view = {'title': spec['title'], 'eligibleLines': int(len(df)), 'groups': total_groups, 'rowsShown': len(rows),
            'overallForFilters': overall_view, 'rows': rows[:40], 'rowsTruncatedForYou': len(rows) > 40,
            'filtersApplied': describe(spec)}
    numbers = collect_numbers(rows)
    if overall_view:
        numbers |= collect_numbers([overall_view])
    numbers.add(float(len(df)))
    numbers.add(float(total_groups))
    return block, view, numbers


def collect_numbers(rows):
    out = set()
    for row in rows:
        for v in row.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
                out.add(float(v))
    return out
