# UI and performance experiment

Branch: `ui/playful-observatory`.

The original completed dashboard is preserved on `main` at `ca32157`. The rejected purple studio experiment is retained as checkpoint `d486601`. The current revision follows the user's later feedback: restore the original palette, horizontal width and open page layout, and focus on actual responsiveness.

## Current interaction requirements

- No tablet-style enclosing panel or purple theme.
- No update banner inserted above the cards. Status must not move the layout.
- Keep cards mounted when data changes and smoothly interpolate numeric values.
- Show immediate navigation/pending feedback; avoid artificial loading delays.
- Honor reduced motion and handle interrupted requests safely.
- Render all customer scatter points efficiently instead of creating thousands of SVG nodes.

## Fixed All markets values

`src/data/retail-presets.json` contains real, complete analysis values for All markets combined with All data, 2010 and 2011. These are generated at build preparation time by `scripts/build_presets.py` and checked into source. They are ordinary versioned data assets, not a browser or runtime query cache. Default and preset views read them directly. The same values support all six pages and local chart metric switches.

Country filters and custom dates continue through the existing API. The analytics definitions and data-cleaning rules are unchanged. After a source dataset or analysis definition change, regenerate the fixed values and rebuild:

```powershell
python scripts/build_presets.py
python scripts/verify_presets.py
npm run build
```

The artifact records the source workbook SHA-256 and analysis-source SHA-256. The verification script independently reconciles each preset with warehouse SQL totals.

For delivery, Vite injects these values into an inert `application/json` script in the built HTML. The frontend parses that data once; the presets do not become a large executable JavaScript object and do not need a network request. Less-than characters are escaped before embedding. Country and custom-date requests still use the existing API.

The user requested closing without further checks; no additional benchmarking or browser verification was run after the final delivery and numeric-animation clamp changes.

## Comparing versions

Switch to `main` and run `npm run build` for the original baseline. Switch to `ui/playful-observatory` and build again for the current revision. Keep the API running or use `npm start`. Commit or retain any local changes before switching branches.

Broader product-expansion and LLM ideas are outside this implementation.
