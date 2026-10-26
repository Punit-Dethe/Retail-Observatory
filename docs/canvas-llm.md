# Model connection and calculation boundary

The canvas works immediately in **Guided analysis** mode. The supported sales, market, product, customer and basket questions execute real registered Python calculations over the cleaned warehouse. Guided mode is a deterministic intent router, not a simulated LLM.

## Optional open-ended conversation

Copy `.env.example` to `.env`, set these values locally, and restart the server:

```dotenv
RETAIL_LLM_BASE_URL=https://YOUR-PROVIDER/v1
RETAIL_LLM_MODEL=YOUR-MODEL-ID
RETAIL_LLM_API_KEY=YOUR-KEY
```

The endpoint must implement chat completions with function tools and support the selected model's tool schema. Loopback local endpoints are also accepted; a local provider that does not require a key can leave it blank. Do not put a key in browser code, canvas files or chat. `.env` is ignored by Git. Environment variables take precedence over `.env` values. No provider or model is silently selected for you.

The adapter follows the documented [function calling](https://developers.openai.com/api/docs/guides/function-calling) request pattern. Guided tool buttons remain deterministic. Configuration is not proof of provider connectivity; provider errors are shown as errors rather than silently changing modes.

## How a typed question is answered

With a model configured, a typed question runs a bounded investigation loop (`server/canvas_theory.py`):

1. The model forms a testable theory (for "why" questions) or decides what to measure.
2. It gathers evidence with approved tools, usually 3–5 items over up to six turns:
   - `query_retail`: a declarative request (measures, up to two dimensions, filters, optional comparison period) validated and executed by `server/canvas_query.py`. Measures include net revenue, orders, units, customers, average order value, unit price, credit rate, repeat rate and lines per order. Dimensions include year, quarter, month, week, day, weekday, hour, country, product, customer, identified/anonymous shopper, order-value band and price band. Rejected requests return a correctable error to the model.
   - `run_playbook`: one of the five fixed investigations (needed for basket pairs and customer segments).
   - `find_products`: catalog lookup for stock codes.
3. It calls `present_answer` with an answer, the hypothesis, a verdict (`supported`, `partly_supported`, `not_supported`, `inconclusive`, `not_applicable`) and which evidence items support, challenge or give context.

The canvas shows a theory note with the verdict above the selected evidence charts, each labelled E1, E2… with its role and linked to the note. The server compares figures in the written answer with computed values and warns about any it cannot match. Near the time limit the model must answer with what it has; if the provider fails mid-investigation, computed evidence is still returned as inconclusive. Questions unrelated to the data get a short answer with no charts. Typical duration with the tested provider is 50–90 seconds.

## What a model can access

The model sees the question, limited recent history, selected-chart titles/scopes/definitions, and bounded aggregated tool results (at most 25 rows per query). It does not receive the entire million-line dataset. Configuring a remote model sends that context to your chosen provider. The API key is used only by the Python server.

The model can only describe queries through the validated schema above; the server executes fixed aggregations. There is no model-generated SQL, Python, filesystem or web access.

Each result retains its scope, source hash, definitions, eligible row count and calculation description. Model commentary is interpretation; chart data remains authoritative. The extract describes a particular retailer in 2009–2011. It cannot establish national demand, causal effects, future launch success or profit. New-product ideas need a comparable recorded product and additional evidence.

## Readiness

On 27 October 2026 the agent loop was tested live with `deepseek-v4.1-flash:free`: "Why did revenue peak in late 2011?" returned a supported theory with six computed evidence charts (91 s); a Christmas-products-by-country question returned partly supported with seven queries (54 s); an off-topic question returned a short answer without charts (4 s). `scripts/verify_canvas.py` covers the query engine against independent data slices and the agent protocol with scripted model responses. The history below describes the earlier single-tool planner.

Without model configuration, real guided investigations are available and open-ended questions are explicitly described as unsupported. With a compatible configuration, the server routes free-form questions through the tool planner. The protocol path is checked with controlled model-response fixtures. On 25 October 2026, a live question using the user-configured Token Harbor endpoint and `deepseek-v4.1-flash:free` successfully selected the approved market tool, applied a UK/Germany 2011 scope, and returned six computed blocks plus an explanation. This verifies that configuration for that request; provider availability can vary. Credentials are stored only in the ignored local `.env`.

Browser automation also submitted a typed question for recorded product 22423 in France/Germany during 2011. The model returned six product findings with the correct product, countries and dates in each evidence record. A second typed question from a selected product chart requested frequent pairs using the same scope. It preserved the product/country/date context, added linked basket findings, and honestly reported no qualifying displayed pairs under the bounded mining criteria. The UI showed real pending state and kept earlier charts in place. No model key was exposed to the browser.
