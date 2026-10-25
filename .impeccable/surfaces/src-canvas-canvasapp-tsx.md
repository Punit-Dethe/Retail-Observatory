---
version: 1
slug: "src-canvas-canvasapp-tsx"
primary_target: "src/canvas/CanvasApp.tsx"
related_targets: ["src/canvas/canvas.css"]
---

# Investigation canvas

Mode: Operate. A college project demonstration that also supports a real analyst's investigation over historical retail transactions.

The user asks a question in a floating conversation on the right. Approved calculations add movable charts and text notes to an open pan/zoom workspace. Follow-up questions extend the selected evidence. Related findings are separated by whitespace and headings; optional labelled edges convey relationships, without enclosing group boxes or implying causality.

Preserve the dashboard's neutral, powder-blue and dark-ink identity, bundled DM Sans typography and full-width layout. No purple theme, enclosing tablet frame or decorative fake controls. Soft shadows distinguish floating controls from the canvas. Charts remain readable at normal working zoom, with exact values and definitions in an inspector.

The initial board uses the existing real All markets presets. New questions call the real retail tools. Guided analysis is explicitly distinguished from a configured language model. No artificial LLM responses, invented progress stages or predictions of product launch success. Historical coverage and the incomplete December 2011 period must remain visible.

Existing nodes retain their layout while an analysis runs. Progress, cancel and retry stay in the chat panel. Results are placed in a new spatial neighborhood; a deliberate Show findings action focuses them. Existing charts do not jump on receipt of a reply.

Core controls: select/drag/resize, pan/zoom/fit, optional connections, editable notes, evidence/result inspection, product search, board rename/create/switch, undo/redo and JSON import/export. Saved state is local to this browser. Narrow screens retain board access and use a dismissible chat drawer. All compact controls need stable accessible names, focus states and reduced-motion support.

The canvas has no permanent top header or filter bar. A separated menu button at the top of the left tool rail opens the board actions; a scope button opens date and market controls. These overlays do not push or rearrange charts. Undo/redo also live on the rail. Desktop chat occupies the full viewport height and is about 420px wide, with evidence using the same dock. The dashboard offers a separate Playground pill beside its main navigation. Preserve this compact navigation model in later refinements.

Implementation and calculation boundaries: docs/canvas-plan.md, docs/canvas-api.md and docs/canvas-llm.md. The original dashboard stays at /; this workspace is /canvas.
