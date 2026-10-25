# UI experiment

Branch: `ui/playful-observatory`.

The initial completed dashboard is preserved on `main` at commit `ca32157`. This project was not previously a Git repository; it was initialized before UI experimentation. Source downloads, the generated SQLite warehouse, dependencies and built output are reproducible and ignored by Git.

## Direction

The user requests approachable, mature playfulness inspired by the first three visual references. Replace the former greenish neutral canvas with pale lavender, near-white surfaces, charcoal-plum ink, periwinkle, blush and sky accents. Use soft depth, clear hierarchy and restrained movement. Preserve all six analytical views and their data semantics.

## Motion purpose

The focal interaction is a filter change: acknowledge it immediately, show honest pending activity, maintain spatial continuity through calculation, and reveal the completed selection atomically. First loads use active skeletons. Refreshes retain a clearly labelled previous view while preventing stale-data actions. Motion must respect reduced-motion preferences and avoid artificial loading delays or fabricated completion percentages.

## Comparing versions

The app is served from the checked-out source's build. To view the baseline later, switch to `main` and run `npm run build`; to return to the experiment, switch to `ui/playful-observatory` and build again. Keep the local API running, or use `npm start`. Do not switch branches with uncommitted changes you want to retain.

Broader product-expansion and LLM ideas are deliberately outside this implementation.

## Implemented interaction behavior

- First-load dashboard skeletons use a moving light sweep, chart placeholder and visible request status.
- Filter refreshes retain the previous analytical surface, identify its actual date/country scope and mark it inert until the new response arrives. Export is disabled while pending.
- After five seconds, status changes to an honest still-calculating message. There is no artificial delay, percentage or invented server stage.
- Request IDs and AbortController prevent an older response from replacing a newer selection.
- Navigation uses a measured sliding selection capsule; controls and panels use restrained motion and depth. No per-dot scatter animation was added.
- Reduced motion disables animation; hidden-document loops pause. Status and skeleton content remain visible.

## Verification

The production build passes. Desktop1536×1050 and mobile390×844 were inspected across the six views. Mobile page width remains390px; tables retain independent scrolling.

A QA-only browser transport wrapper delayed delivery of **real** API responses without modifying values or project source. Germany arrived before an older France response; after both settled the view correctly retained Germany with753 orders and£374,573.51 net revenue. A6.2-second response delay displayed the slow-request message, with the previous selection clearly shown and noninteractive. Reduced-motion emulation reported zero running animations. An intentionally aborted fetch recovered through Retry; no-data selections recovered through Reset. Customer search and filtered CSV responses passed.

Review fixes increased white-tooltip secondary text contrast to5.91:1 and the previous-scope caption to5.06:1, and provided an accessible Export CSV name at mobile width. Confirmation screenshots are in `docs/screenshots/ui-experiment/`.

The one mechanical detector run compared the new world against the former DESIGN.md and reported688 advisory palette/type/radius differences, plus a bounded width-transition warning for the absolutely positioned navigation capsule. The design documents are updated to record the intentional replacement. The raw scan remains in `docs/ui-design-audit.json`; it was not rerun or represented as a clean scan. The independent visual/accessibility review owns the material findings.
