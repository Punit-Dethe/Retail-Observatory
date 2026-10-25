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

The adapter follows the documented [function calling](https://developers.openai.com/api/docs/guides/function-calling) request pattern. Configured mode makes up to two model calls per question: one constrained analysis-plan tool call, then a bounded explanation of actual computed results. Guided tool buttons remain deterministic. Configuration is not proof of provider connectivity; provider errors are shown as errors rather than silently changing modes.

## What a model can access

The model sees the question, limited recent history, selected-chart titles/scopes/definitions, and bounded aggregated results for the explanation. It does not receive the entire million-line dataset. Configuring a remote model sends that context to your chosen provider. The API key is used only by the Python server.

The approved function chooses one of five analysis tools, dates, country/comparison countries and an optional recorded product code. The server validates these arguments and executes fixed calculations. There is no arbitrary model-generated SQL, Python, filesystem or web access in this version.

Each result retains its scope, source hash, definitions, eligible row count and calculation description. Model commentary is interpretation; chart data remains authoritative. The extract describes a particular retailer in 2009–2011. It cannot establish national demand, causal effects, future launch success or profit. New-product ideas need a comparable recorded product and additional evidence.

## Readiness

Without model configuration, real guided investigations are available and open-ended questions are explicitly described as unsupported. With a compatible configuration, the server routes free-form questions through the tool planner. The protocol path is checked with controlled model-response fixtures. On 25 October 2026, a live question using the user-configured Token Harbor endpoint and `deepseek-v4.1-flash:free` successfully selected the approved market tool, applied a UK/Germany 2011 scope, and returned six computed blocks plus an explanation. This verifies that configuration for that request; provider availability can vary. Credentials are stored only in the ignored local `.env`.
