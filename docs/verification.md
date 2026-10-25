# Verification

Verified locally on 25 October 2026 using the original UCI workbook.

- `npm run build`: TypeScript and production bundle pass. The chart-library bundle has a non-blocking size warning.
- `npm start`: launcher starts the built application and API on 127.0.0.1:8000.
- `scripts/verify_analysis.py`: raw-row reconciliation, dimension membership, independent SQLite totals, gross/credit/net arithmetic, daily/monthly/country rollups, order-value bins, customer partitions, cohort bounds, exact basket count/support/confidence/lift, partial month, filtered/empty/small selections, date validation all pass.
- HTTP: UI, health, metadata, analytics and filtered CSV return successful responses. Invalid dates/countries/export kinds return 400; unknown API route returns 404.
- Browser: all six pages render; 2011 + France yields 362 orders; customer/product search and no-match states work; custom dates update query scope; no-data scope displays a reset action.
- Desktop (1536×1050) and mobile (390×844): charts and layout inspected. Page has no horizontal overflow at mobile width; tables scroll within their own container. Mobile metrics fit without sparkline collisions. Log scatter axes use explicit ticks.
- Mechanical design detector: no findings. Independent design review: PASS; both material presentation findings resolved in confirmation review.

Screenshots are in `docs/screenshots/`. The app's data coverage and method limitations remain as documented in `docs/methodology.md`; passing checks does not turn descriptive associations or clusters into validated predictions.
