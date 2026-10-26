# Deploy the dashboard and API on Vercel

The repository includes a Vite static build, one Python function (`api/index.py`), SPA/API routing in `vercel.json`, and a compressed cleaned warehouse in `data/deploy/`. You do not need a separate backend service or an external database for this demonstration deployment.

## Import settings

Import `Punit-Dethe/Retail-Observatory` into Vercel. Use:

| Setting | Value |
|---|---|
| Production branch | `main` |
| Root Directory | repository root (leave empty) |
| Framework Preset | `Vite` |
| Install Command | `npm ci` (or Vercel's default npm install) |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Python version | `3.12`, configured by `.python-version` |

Leave Fluid compute enabled. `vercel.json` sets the Python function's maximum duration to 180 seconds. A model investigation makes several model requests and stops gathering evidence by 140 seconds on Vercel, leaving headroom for a cold start. Do not use `npm start` as the build command; that launches the local long-running server.

## Environment variables

In the import form's Environment Variables section, or Project → Settings → Environment Variables, add these three separate entries. Select Production and Preview if you want model chat in both. Use the plain value: no quotes, no `Bearer ` prefix, and no `NAME=` text in an individual value field.

| Name | Value |
|---|---|
| `RETAIL_LLM_BASE_URL` | `https://tokenharbor.ai/v1` |
| `RETAIL_LLM_MODEL` | `deepseek-v4.1-flash:free` |
| `RETAIL_LLM_API_KEY` | your complete Token Harbor API key |

Mark the API key as Secret/Sensitive if offered. **Do not prefix these names with `VITE_`**: the Python function reads them, and the credential must not become part of browser JavaScript. No `VITE_API_URL` is needed; frontend and API share the deployment domain.

If Vercel offers an import/paste mode for dotenv, use:

```dotenv
RETAIL_LLM_BASE_URL=https://tokenharbor.ai/v1
RETAIL_LLM_MODEL=deepseek-v4.1-flash:free
RETAIL_LLM_API_KEY=PASTE_YOUR_KEY_HERE
```

The checked-in `.env.example` contains placeholders only. Your local `.env` is excluded from Git and Vercel uploads/functions. After changing a hosted variable, create a new deployment/redeploy: existing deployments do not receive changed values.

## Runtime data

The original 132 MB local SQLite warehouse remains ignored. Its approximately 20 MB gzip snapshot is tracked under `data/deploy/`, together with a hash/size manifest. On a cold start, the function verifies and unpacks the snapshot to its temporary directory, then opens it read-only. No source download, ETL, API key or network storage is needed to initialize the data.

Scientific Python dependencies and the snapshot must fit Vercel's function bundle limit. `excludeFiles` removes frontend/development assets from the function; do not remove these exclusions. A first API request can be slower because the function initializes the warehouse and dataframe. Default dashboard presets and the starting canvas are bundled in the frontend and do not wait for that initialization.

After changing the warehouse or cleaning pipeline locally, rebuild the deployment snapshot and commit both files before deploying:

```powershell
python scripts/pack_warehouse.py
```

Large raw transaction exports can exceed Vercel's response limit; hosted requests return a clear error, and you can narrow dates or run a full export locally. This is a fixed historical snapshot, not a shared writable database. Boards remain in browser storage and can be exported as JSON.

## After deploying

1. Open `/` and `/canvas` directly, then refresh both URLs.
2. Open `/api/health`; expect `{"status":"ok",...}`.
3. Open `/api/canvas/capabilities`; expect `llmConfigured: true` when all model settings are present. This reports configuration, not proof of provider availability.
4. Ask a typed product or market question. Inspect the resulting evidence scope and charts.

Local checks cover snapshot integrity, routed function requests, same-origin POSTs, cross-origin rejection and real guided analysis. A production Vercel deployment still needs to be checked after import; this repository setup is not a claim that a live cloud deployment has already succeeded.

References: [Vite SPA routing](https://vercel.com/docs/frameworks/frontend/vite), [Python file-based functions](https://vercel.com/docs/functions/runtimes/python/api-directory), [Python bundling](https://vercel.com/docs/functions/runtimes/python), [environment variables](https://vercel.com/docs/environment-variables), [function duration](https://vercel.com/docs/functions/configuring-functions/duration).
