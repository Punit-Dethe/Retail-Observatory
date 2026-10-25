# Retail Observatory

A local analytics dashboard for a college data warehousing and mining project, built on the real UCI Online Retail II dataset. React + TypeScript + Recharts frontend, Python analytics API, SQLite dimensional warehouse. No API key or Kaggle login required.

## Run

From this folder:

```powershell
npm install
npm start
```

Open **http://127.0.0.1:8000**. On Windows you can also double-click **Start Dashboard.cmd**.

Node.js 20.19+ and Python 3.10+ are required. The launcher finds the local virtual environment, the available bundled Codex Python, or a system Python. It installs missing Python requirements, downloads/builds the data when absent, builds the UI when needed, then starts the local server. Set `RETAIL_PYTHON` to choose a Python executable. The server binds only to 127.0.0.1; this is a local demonstration app, without multi-user authentication or hosted persistence.

For a self-contained Python environment:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\prepare_data.py
npm run build
.venv\Scripts\python.exe server\app.py
```

## Develop

Run `python server/app.py` in one terminal and `npm run dev` in another. The Vite development URL is http://127.0.0.1:5173 and `/api` proxies to port 8000. `npm run build` runs TypeScript checking and creates `dist/`. Run `python scripts/verify_analysis.py` for analysis invariants.

The All markets / All data, 2010 and 2011 selections read complete fixed values from `src/data/retail-presets.json`. These are versioned build assets, not runtime cache entries. They support all six views and local Revenue/Orders switches. Other countries and custom ranges continue through the analytics API.

After changing the source dataset or analytics definitions, regenerate and verify these values before rebuilding:

```powershell
python scripts/build_presets.py
python scripts/verify_presets.py
npm run build
```

Read [UI and performance notes](docs/ui-experiment.md) for the current experiment branch, baseline comparison and interaction behavior.

## What is included

- Overview with revenue, orders, customers, AOV, insights and product/market patterns.
- Sales trends, credits, order-value distribution and purchase-time heatmaps.
- RFM segmentation, K-means and silhouette quality, cohort retention and customer exploration.
- Product rankings, Pareto concentration, returns and frequent-pair association rules.
- Country comparisons and shared date/country filters.
- Data lab explaining cleaning, methods, metric definitions and limitations.
- CSV exports for the current scope; raw original workbook and reproducible pipeline.

## Data and documentation

Source: Daqing Chen, [Online Retail II, UCI](https://archive.ics.uci.edu/dataset/502/online+retail+ii), DOI [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D), **CC BY 4.0**. The user supplied the [Kaggle mirror](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci). Original workbook: 1,067,371 invoice lines, December 2009–December 2011. Data is historical. Amounts are GBP.

`data/raw/` contains source downloads. `data/retail.sqlite` contains the local star schema. `data/metadata.json` records source lineage, SHA-256 and quality counts. Large generated data and dependencies are ignored by Git and can be reproduced.

Read [methodology](docs/methodology.md) for exact definitions, ETL rules, schema, syllabus connections, caveats and a demonstration walkthrough. Read [API contract](docs/api-contract.md) for endpoints and payloads.

## Scope and limits

Metrics cover cleaned merchandise lines; service/postage/manual codes are excluded. Net revenue deducts observed credits. Product revenue rankings use positive gross sales. Customer analysis excludes unidentified shoppers. RFM and cohorts describe the selected observation window. K-means is descriptive, not a prediction. Basket mining is limited to pairs among the 80 most frequent products. Partial months and incomplete history are explicitly noted. Profit, conversion and inventory cannot be inferred from this dataset.
