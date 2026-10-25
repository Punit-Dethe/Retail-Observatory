"""Download original UCI Online Retail II and build a reproducible local warehouse."""
from pathlib import Path
import hashlib
import json
import sqlite3
import urllib.request
import zipfile
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
URL = 'https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip'


def prepare():
    RAW.mkdir(parents=True, exist_ok=True)
    book = RAW / 'online_retail_II.xlsx'
    if not book.exists():
        print('Downloading UCI Online Retail II...', flush=True)
        archive = RAW / 'online-retail-ii.zip'
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as z:
            member = next(n for n in z.namelist() if n.endswith('.xlsx'))
            book.write_bytes(z.read(member))
    print('Reading both workbook sheets...', flush=True)
    sheets = pd.read_excel(book, sheet_name=None, engine='openpyxl')
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = ['invoice', 'code', 'description', 'quantity', 'date', 'price', 'customer', 'country']
    quality = {
        'rawRows': len(df), 'duplicates': int(df.duplicated().sum()),
        'missingCustomer': int(df.customer.isna().sum()),
        'missingDescription': int(df.description.isna().sum()),
        'nonPositivePrice': int((df.price <= 0).sum()),
        'cancellationRows': int(df.invoice.astype(str).str.upper().str.startswith('C').sum()),
        'negativeQuantity': int((df.quantity < 0).sum()),
    }
    # Counts below are sequential and disjoint; raw issue counts above overlap.
    cleaned = df.drop_duplicates().copy()
    steps = [{'name': 'Exact duplicate rows', 'rows': len(df) - len(cleaned)}]
    cleaned['code'] = cleaned.code.astype(str).str.strip()
    cleaned['invoice'] = cleaned.invoice.astype(str).str.strip()
    mask = cleaned['code'].str.fullmatch(r'\d{5}[A-Za-z]{0,2}', na=False)
    steps.append({'name': 'Service / non-merchandise codes', 'rows': int((~mask).sum())})
    cleaned = cleaned[mask].copy()
    mask = (cleaned.price > 0) & (cleaned.quantity != 0) & cleaned.date.notna() & cleaned.country.notna()
    steps.append({'name': 'Nonpositive prices / invalid records', 'rows': int((~mask).sum())})
    cleaned = cleaned[mask].copy()
    # C-prefixed invoices are credits, even in the unusual case of positive quantity.
    cancellation = cleaned.invoice.str.upper().str.startswith('C')
    cleaned.loc[cancellation, 'quantity'] = -cleaned.loc[cancellation, 'quantity'].abs()
    cleaned['customer'] = cleaned.customer.map(lambda x: str(int(x)) if pd.notna(x) else None)
    cleaned['amount'] = (cleaned.quantity * cleaned.price).round(4)
    cleaned['is_return'] = (cleaned.quantity < 0).astype(int)
    cleaned['date_id'] = cleaned.date.dt.strftime('%Y-%m-%d')
    cleaned['time'] = cleaned.date.dt.strftime('%H:%M:%S')
    # A deterministic most-frequent recorded description gives each product one label.
    names = cleaned.dropna(subset=['description']).groupby(['code', 'description'], observed=True).size().reset_index(name='count')
    names = names.sort_values(['count', 'description'], ascending=[False, True]).drop_duplicates('code')
    products = pd.DataFrame({'product_id': sorted(cleaned.code.unique())})
    products['name'] = products.product_id.map(names.set_index('code').description).fillna('Unlabelled product')
    countries = pd.DataFrame({'country_id': sorted(cleaned.country.unique())})
    dates = pd.DataFrame({'date': pd.date_range(cleaned.date.min().normalize(), cleaned.date.max().normalize())})
    dates['date_id'] = dates.date.dt.strftime('%Y-%m-%d')
    dates['year'] = dates.date.dt.year
    dates['month'] = dates.date.dt.month
    dates['weekday'] = dates.date.dt.dayofweek
    dates = dates.drop(columns='date')
    customers = pd.DataFrame({'customer_id': sorted(cleaned.customer.dropna().unique())})
    facts = cleaned[['invoice', 'code', 'customer', 'country', 'date_id', 'time', 'quantity', 'price', 'amount', 'is_return']].rename(columns={
        'code': 'product_id', 'customer': 'customer_id', 'country': 'country_id', 'price': 'unit_price'})
    db = ROOT / 'data' / 'retail.sqlite'
    print(f'Writing {len(facts):,} facts to the SQLite warehouse...', flush=True)
    with sqlite3.connect(db) as conn:
        for table, frame in [('dim_product', products), ('dim_country', countries), ('dim_date', dates), ('dim_customer', customers), ('fact_transaction', facts)]:
            frame.to_sql(table, conn, if_exists='replace', index=False, chunksize=10000)
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS product_pk ON dim_product(product_id)')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS country_pk ON dim_country(country_id)')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS customer_pk ON dim_customer(customer_id)')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS date_pk ON dim_date(date_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS facts_date_country ON fact_transaction(date_id,country_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS facts_invoice ON fact_transaction(invoice)')
    quality['cleanRows'] = len(cleaned)
    quality['excludedRows'] = len(df) - len(cleaned)
    quality['exclusions'] = steps
    quality['retainedMissingCustomer'] = int(cleaned.customer.isna().sum())
    metadata = {
        'name': 'Online Retail II', 'sourceUrl': 'https://archive.ics.uci.edu/dataset/502/online+retail+ii',
        'kaggleUrl': 'https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci',
        'license': 'CC BY 4.0', 'creator': 'Daqing Chen', 'rawRows': len(df),
        'start': cleaned.date_id.min(), 'end': cleaned.date_id.max(),
        'countries': countries.country_id.tolist(), 'quality': quality,
        'sourceSha256': hashlib.sha256(book.read_bytes()).hexdigest(),
        'generatedAt': pd.Timestamp.now(tz='UTC').isoformat(), 'sheets': list(sheets),
    }
    (ROOT / 'data' / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(quality, indent=2), flush=True)


if __name__ == '__main__':
    prepare()
