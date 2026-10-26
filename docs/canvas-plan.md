# Retail investigation canvas — implementation plan

Branch `feature/retail-investigation-canvas` starts at the completed dashboard and performance revision, merged into `main` at `6fafb77`.

## Product

DashboardGPT is the interaction reference: an open pan/zoom canvas, a floating conversation on the right, and movable chart and text objects. Related answers form spatial neighborhoods, not enclosing boxes. Follow-ups expand an investigation from selected evidence. Connections are optional, labelled relationships and do not claim causality.

The existing dashboard remains available at `/`; the new workspace lives at `/canvas`. Preserve the original neutral/blue visual world and locally bundled typography. No purple theme or enclosing tablet frame.

## Build sequence

1. Canvas and conversation: reusable node-canvas library, chart/note nodes, spatial placement, selection, movement, pan/zoom, fit view, optional connections, contextual floating chat and real starter analysis.
2. Real analysis: registered retail tools for sales, markets, products, customers and baskets. Guided requests work without an LLM; a server-side compatible model adapter can plan calls when configured. Both modes use the same calculations and evidence outputs.
3. Persistence and inspection: local saved investigations, rename/new board, undo/redo, note editing, JSON import/export, result data/provenance inspection, honest empty/error/loading/cancel behavior. Preserve exact GBP and window definitions.
4. Bounded checks: production build, focused analysis invariants and a single desktop/mobile interaction pass. No broad benchmarks.

## Model boundary

Without a key: explicitly labelled guided analysis uses named supported questions and a conservative intent router, never pretends to be an open-ended LLM. All figures derive from real UCI data. With configuration: the model requests approved tools; server validates arguments and executes fixed functions, then returns traceable charts and summaries. No arbitrary SQL/Python execution from the model in this first version. Keys remain server-side. No unsupported future-demand probabilities or causal claims.

## References

Reference-only clones under ignored `references/`: `immannino/sql.garden` (GPL-3.0-or-later) for canvas/SQL/tool patterns and `microsoft/data-formulator` (MIT) for analysis/provenance patterns. This app reuses the MIT node library and its own existing retail engine. Reference GPL source is not copied into the application.

## First implementation

Delivered at `/canvas`: starter charts from existing real-data presets, movable/resizable chart and note nodes, pan/zoom, optional links, contextual chat, product lookup, five registered investigations, evidence/result inspection, editable notes, local multiple-board saving, undo/redo and JSON import/export. A footer link in the dashboard opens the canvas. Both source repositories are available locally for reference; this is an extension of the existing retail application rather than a fork of either repository.

The dashboard also exposes a separate Playground navigation pill. Canvas controls fold into the left tool rail: a board menu for rename/switch/new/import/export and a scope popover for preset/custom dates and markets. There is no permanent canvas header or filter bar. Chat uses a wider floating dock with rounded corners and top/right/bottom insets and a neutral gray/charcoal palette. The neutral workspace retains a clearly visible dot grid. Chart colors remain unchanged. Scope changes apply only to subsequently requested findings.

The production frontend builds successfully. Focused Python checks cover independent revenue totals, normalized product order share, all five real tools, empty/unsupported requests, input validation and the model tool protocol with controlled responses. Browser inspection covers desktop/mobile layout and a real market comparison. A user-configured model successfully completed a live market investigation on 25 October 2026; see `canvas-llm.md` for setup and verification details.

Known canvas limitation: follow-ups are placed beside a selected node without collision avoidance, so a new neighborhood can overlap nearby existing findings. Existing nodes remain movable; automatic placement needs a separate refinement.
