---
name: "Retail Observatory — Soft Studio"
description: "A mature, approachable retail analytics workspace in lilac, blush, sky and charcoal."
colors:
  ink: "#302a3c"
  muted: "#6c6379"
  line: "#e6dfef"
  accent: "#7862c7"
  outer-canvas: "#eae5f4"
  workspace: "#f7f5fb"
  mobile-canvas: "#f5f2fb"
  surface: "#ffffff"
  filter-surface: "#efebf6"
  segment-track: "#e7e0f0"
  field-surface: "#f6f2fb"
  field-border: "#ded5eb"
  field-focus: "#a48ac4"
  focus-halo: "#eee6f8"
  selection: "#dcd0f5"
  primary-hover: "#50415f"
  secondary-ink: "#4b3e5d"
  secondary-hover: "#eee7f8"
  nav-muted: "#62596f"
  nav-hover: "#f1ecf9"
  title-ink: "#41334f"
  subtitle: "#70667d"
  axis-ink: "#776c83"
  metric-charcoal: "#383143"
  metric-charcoal-label: "#ded5e9"
  metric-lilac: "#dfd5f3"
  metric-lilac-ink: "#49385f"
  metric-lilac-label: "#645275"
  metric-sky: "#e7effa"
  metric-sky-ink: "#35465d"
  metric-sky-label: "#596a80"
  metric-blush: "#f8e8ed"
  metric-blush-ink: "#614151"
  metric-blush-label: "#805e6d"
  insight-surface: "#ebe3f7"
  insight-title: "#4e3a65"
  insight-body: "#6a567c"
  insight-divider: "#dcd1eb"
  chart-sky: "#9fc7e9"
  chart-lilac: "#b6a4dd"
  chart-blush: "#cf9fb5"
  chart-peach: "#dfb08e"
  chart-neutral: "#c3bbce"
  chart-area: "#ece5f9"
  chart-pareto: "#a378ac"
  chart-pareto-area: "#f3e8f4"
  chart-sales: "#afc5e6"
  chart-credits: "#a86f6d"
  chart-distribution: "#b6a5dc"
  chart-scatter: "#8c76b9"
  chart-dominant: "#393040"
  chart-leading-market: "#5b4d6d"
  chart-grid: "#e5e7e9"
  chart-grid-warm: "#e6e5e7"
  chart-cell-ink: "#463957"
  spark-light: "#d5c7f0"
  spark-dark: "#655095"
  tag-champions: "#e6dcf5"
  tag-loyal: "#ddeaf8"
  tag-new: "#f5e5d9"
  tag-risk: "#f2dce8"
  tag-potential: "#e4e3f6"
  tag-hibernating: "#eee8f1"
  refresh-surface: "#e8ddf4"
  refresh-ink: "#634578"
  refresh-caption: "#6c537e"
  tooltip-copy: "#6c5f7a"
  refresh-track: "#dfd1ef"
  refresh-indicator: "#b295cd"
  skeleton-charcoal: "#e8e2ee"
  skeleton-lilac: "#e5dcf2"
  skeleton-sky: "#e7edf7"
  skeleton-blush: "#f4e7ee"
  skeleton-base: "#e5ddeb"
  skeleton-value: "#d9cee4"
  skeleton-lilac-bar: "#d4c5e7"
  skeleton-sky-bar: "#cbd8eb"
  skeleton-blush-bar: "#e6cfdd"
  skeleton-plot: "#d7cce7"
  skeleton-grid: "#f0eaf6"
  error: "#9d4c65"
typography:
  headline:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "42px"
    fontWeight: 500
    lineHeight: 1.16
    letterSpacing: "-1.4px"
  metric:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "32px"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-1px"
  title:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "16px"
    fontWeight: 550
    lineHeight: 1.4
    letterSpacing: "-0.35px"
  body:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: "17px"
rounded:
  cell: "6px"
  tag: "8px"
  field: "14px"
  button: "15px"
  segment-track: "16px"
  refresh: "18px"
  filter: "20px"
  metric-mobile: "20px"
  panel-mobile: "22px"
  metric: "23px"
  panel: "24px"
  navigation: "28px"
  workspace: "32px"
spacing:
  compact: "8px"
  mobile-gap: "17px"
  metric-gap: "18px"
  gap: "20px"
  control: "10px 15px"
  metric: "22px 23px 19px"
  panel: "25px 26px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "{spacing.control}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary-ink}"
    rounded: "{rounded.button}"
    padding: "{spacing.control}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  metric-charcoal:
    backgroundColor: "{colors.metric-charcoal}"
    textColor: "{colors.surface}"
    rounded: "{rounded.metric}"
    padding: "{spacing.metric}"
  metric-lilac:
    backgroundColor: "{colors.metric-lilac}"
    textColor: "{colors.metric-lilac-ink}"
    rounded: "{rounded.metric}"
    padding: "{spacing.metric}"
  navigation-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "24px"
    padding: "12px 17px"
  refresh-status:
    backgroundColor: "{colors.refresh-surface}"
    textColor: "{colors.refresh-ink}"
    rounded: "{rounded.refresh}"
    padding: "15px 18px 17px"
---

# Design System: Retail Observatory — Soft Studio

## Overview

**Creative North Star: "The Soft Studio Observatory"**

A mature, approachable workspace for serious retail analysis. Lilac, blush and sky surfaces make information welcoming; charcoal text, restrained symbols and real charts keep it credible. Rounded forms, soft depth and smooth feedback carry the playfulness. Decorative imagery and childish ornament do not belong in this world.

This is the approved visual experiment on `ui/playful-observatory`; the former green-neutral world is superseded here and remains on `main`. `src/studio.css`, imported after `src/styles.css`, is authoritative for final styles. Charts and states also draw from `src/components.tsx`, `src/pages.tsx`, `src/Loading.tsx`, `src/Navigation.tsx` and `src/App.tsx`.

**Key Characteristics:**
- Lilac framing, white analytical panels and charcoal anchors.
- A coordinated charcoal, lilac, sky and blush KPI strip.
- Soft structural shadows and rounded rectangular controls.
- Real-request feedback that preserves context and respects motion preferences.

## Colors

Frontmatter records the intentional role palette, including chart and loading variants. The sidecar supplies derived eight-step tonal ramps; these reference extensions do not create additional implemented CSS tokens.

### Primary

Charcoal anchors brand, actions and the selected navigation indicator. Violet is the main analytical series, intensity hue, focus outline and link family.

### Secondary

Lilac, sky and blush distinguish KPIs after charcoal, with separate darker ink and label companions. The chart sequence is violet, sky, lilac, blush, peach and neutral; preserve legend assignments. Credits have a separate muted rose tone. Insights and methodological support use lilac surfaces.

### Neutral

A pale lilac outer canvas surrounds a lighter workspace and white panels. Mobile uses a continuous pale canvas. Plum-grey text and lavender-grey dividers replace the old greenish neutrals.

**The Data Color Rule.** Use color for series, category, state or measured emphasis. Keep explicit names, units and values alongside it.

## Typography

Use locally bundled DM Sans Variable, with DM Sans and sans-serif fallbacks, throughout. Its rounded letterforms and moderate weights provide warmth and analytical precision.

- **Headline:** the frontmatter role, sentence case and balanced wrapping; (36px) at tablet width, (34px) on mobile with an (18ch) maximum width.
- **Metric:** tabular numbers, (32px) by default and (33px) on wide screens. Text values use (25px), with explicit smaller long-value variants. Mobile values use (27px), or (22px) for long values; narrow numeric values use (20px).
- **Panel title:** (16px), weight (550); compact/mobile titles use (15px). Subtitles use (12px), reducing to (11px).
- **Body and controls:** mostly (12px), supported by (11px) labels. Mobile preserves (10–12px) detail. Tables stay (12px), with (11px) headers. Keep explanations concise and use tabular numbers for comparisons.

## Layout

The desktop workspace is a centered inset shell: maximum width (1640px), width `calc(100% - 48px)`, margin (24px), padding (29px 40px 0). Brand, six-page navigation and source link precede the aligned page heading, global filters and analytical content.

The main rhythm is (20px), with (18px) between four equal KPIs. Charts use a (2.05:1) main split, equal two-column grids or a three-column overview row according to information needs. Panels have (25px 26px) padding. Chart heights are (266px), compact (236px), revenue (260px).

- At (1500px) and above, shell gutters increase to (47px).
- At (1260px) and below, gutters become (28px), controls compact and KPI sparklines hide. Inherited (1190px) rules also reduce the overview row to two columns and hide its market donut.
- At (960px) and below, the shell has (14px) margins, (24px) gutters and (27px) corners. Navigation occupies a scrollable second row, dates become an icon trigger, and the main split becomes (1.6:1).
- At (700px) and below, the shell becomes an edge-to-edge pale canvas with (22px 18px 0) padding. Filters use two rows; KPIs form two columns with (12px) gaps; panels stack with (17px) gaps. Coverage hides, export becomes icon-only and the market donut returns. Tables scroll at a (680px) minimum width.
- Mobile metrics keep sparklines hidden for legibility. Text values wrap; long numbers use smaller explicit variants. At (380px) and below, outer gutters become (14px).

## Elevation & Depth

Soft depth is intentional: the shell, white navigation and panels have low-opacity plum shadows. Actions and the selected indicator have stronger local lift; popovers and tooltips float above content. Use the exact sidecar shadow vocabulary. Gradients are confined to loading shimmer, where they indicate activity.

Controls use short color/background feedback, a gentle (1px) press movement and the shared ease-out curve. Page content arrives over (300ms); popovers enter over (220ms). The navigation indicator moves and changes width over (300ms). Its width transition is a deliberate bounded exception: the indicator is absolutely positioned behind stable buttons, with no page-layout effects.

## Shapes

The shell has the broadest corners, followed by navigation, panels and metrics. Controls use rounded rectangles: buttons (15px), fields (14px), selected segments (12px), tags (8px) and heat cells (6px). Brand bars, functional line icons and small rounded category tokens provide restrained character.

## Components

- **Buttons and fields:** charcoal primary, white secondary, plum hover and visible focus. Disabled controls use opacity (.48) with no shadow. Search/select containers gain a border and halo on `:focus-within`; date inputs sit in an elevated white form. Preserve labels, validation errors and an accessible name for icon-only export.
- **Navigation:** a measured charcoal indicator sits behind the active page in a white track. `aria-current` identifies selection. Font readiness and resizing update its bounds. Small screens scroll the chosen destination into view; reduced motion uses instant scrolling.
- **Segments and tags:** selected white segments lift gently above a lilac track. Customer tags use named lilac, sky, peach and blush variants with darker text. Keep their label meaning alongside color.
- **Panels and KPIs:** white panels use soft depth; insights use lilac. The KPI strip follows charcoal, lilac, sky and blush, with matching darker label companions. Desktop exploration actions appear on hover/focus; mobile hides them.
- **Charts and tables:** violet leads, with pale fills, light dashed grids, nearby legends and formatted white tooltips. Tooltip labels/body require dark plum foregrounds. Keep units, definitions and partial-period notes nearby. Customer frequency/spend scatter uses logarithmic axes with explicit tick arrays; market scatter stays linear. Numeric table columns align right; rows use subtle separators and hover.
- **Initial loading:** show the structural KPI/chart skeleton only while real requests are pending. Coordinated placeholders, transform-based shimmer and a polite live status acknowledge progress without invented values. Skeletons are hidden from assistive technology. After (5s), copy explains that calculation continues; this timer never delays results.
- **Refresh loading:** retain previous analytics at opacity (.55), label the exact prior market/date scope, and mark the surface `inert` and busy. The banner uses an indeterminate sweep, never a percentage. Keep its caption contrast readable. Filters can interrupt requests; stale responses cannot overwrite the latest selection. Errors expose retry.
- **Motion and access:** shimmer loops use (1.7s), chart sheen (2s), dots (1.2s) and refresh sweep (1.4s). Pause recurring animation while the document is hidden. Reduced motion removes all animations/transitions, hides sheen and leaves static activity indications: zero animation loops. Preserve the skip link, labelled controls, live statuses, alert errors, focusable heat cells and violet (2px) focus outline with (4px) offset.

## Do's and Don'ts

### Do:
- **Do** use lilac, blush, sky and charcoal as one coordinated mature palette.
- **Do** keep charts, values and readable explanations central to the hierarchy.
- **Do** preserve soft depth, measured navigation, mobile value legibility and explicit logarithmic ticks.
- **Do** tie loading feedback to real work, label retained data and honor interruption, hidden-document pause and reduced motion.

### Don't:
- **Don't** restore the former greenish neutral canvas on this experiment branch.
- **Don't** add childish ornament, decorative imagery, heavy shadows or unrelated accent colors.
- **Don't** present simulated progress percentages or impose loading delays.
- **Don't** leave previous results interactive while a replacement selection is pending.
- **Don't** rely on color or motion alone to explain data or state.

