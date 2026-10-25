---
name: Retail Observatory
description: Calm, information-rich retail analytics with clear methods and restrained pastel accents.
colors:
  ink: "#202521"
  muted: "#626862"
  canvas: "#eeefeb"
  surface: "#fbfcf9"
  line: "#e4e6e1"
  blue: "#3974bd"
  metric-light: "#f9fbf6"
  metric-dark: "#222822"
  metric-blue: "#bed3ef"
  metric-blue-ink: "#25374c"
  insight-sage: "#e7ecdf"
  chart-blue-light: "#a9bfe2"
  chart-lavender: "#b4b0d9"
  chart-sage: "#8da89a"
  chart-sand: "#d6af8c"
  chart-neutral: "#c8c9c4"
  button-light: "#f9fbf6"
  button-hover: "#e8ede3"
  button-border: "#d6dcd3"
  button-primary-hover: "#3b453c"
  white: "#ffffff"
  field-bg: "#f6f9f0"
  field-border: "#dce4d2"
  segment-track: "#e2e5df"
  tag-bg: "#e9eee2"
  tag-ink: "#60704c"
typography:
  headline:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "37px"
    fontWeight: 550
    lineHeight: 1.15
    letterSpacing: "-1.3px"
  metric:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "30px"
    fontWeight: 550
    lineHeight: 1.15
    letterSpacing: "-1px"
  title:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "14px"
    fontWeight: 550
    letterSpacing: "-0.3px"
  body:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: "17px"
rounded:
  field: "8px"
  tooltip: "12px"
  metric-mobile: "17px"
  panel-mobile: "19px"
  metric: "21px"
  panel: "23px"
  control: "25px"
  pill: "30px"
spacing:
  compact: "8px"
  control: "10px 15px"
  mobile-gap: "14px"
  gap: "18px"
  metric: "20px 22px 19px"
  panel: "22px 23px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "{spacing.control}"
  button-primary-hover:
    backgroundColor: "{colors.button-primary-hover}"
    textColor: "{colors.white}"
  button-secondary:
    backgroundColor: "{colors.button-light}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "{spacing.control}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  metric-dark:
    backgroundColor: "{colors.metric-dark}"
    textColor: "{colors.white}"
    rounded: "{rounded.metric}"
    padding: "{spacing.metric}"
  metric-blue:
    backgroundColor: "{colors.metric-blue}"
    textColor: "{colors.metric-blue-ink}"
    rounded: "{rounded.metric}"
    padding: "{spacing.metric}"
  navigation-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.pill}"
    padding: "12px 18px"
  tag:
    backgroundColor: "{colors.tag-bg}"
    textColor: "{colors.tag-ink}"
    rounded: "20px"
    padding: "4px 8px"
---

# Design System: Retail Observatory

## Overview

**Creative North Star: "The Retail Observatory"**

A calm workspace for examining real retail transactions. The supplied dashboard references establish a light neutral grey canvas, rounded panels, dark selected navigation and a powder blue secondary KPI. DM Sans carries both the conversational page headings and the compact analytical detail.

The interface operates as a college retail analytics demonstration across Overview, Sales, Customers, Products, Markets and Data lab. Charts, totals and tables provide the hierarchy; decorative imagery has no role. Data definitions and limitations sit close to the evidence they explain.

**Key Characteristics:**
- Quiet neutral surfaces with measured blue and sage emphasis.
- Large summary values above compact, information-rich charts and tables.
- Consistent rounded controls and panels across all six pages.
- Clear selections, traceable labels and restrained motion.

## Colors

The palette combines a warm grey canvas, near-white panels, deep green-black text and muted analytical accents. Frontmatter values are normative; `src/styles.css` and `src/components.tsx` are the implementation sources.

### Primary

Ink anchors selected navigation, primary actions and the brand. Blue identifies the main time series, active heatmap intensity, links and keyboard focus.

### Secondary

Powder blue distinguishes the orders KPI. Sage marks the insight panel and methodological callouts. The chart sequence proceeds through blue, pale blue, lavender, sage, sand and neutral; keep categories and their legends aligned.

### Neutral

Canvas separates near-white panels without heavy strokes. Muted text supplies supporting labels; line supplies quiet dividers within tables and grouped content. The dark revenue KPI uses lighter supporting text rather than ordinary muted text.

**The Data Color Rule.** Use accents to encode a series, category, state or meaningful emphasis. Preserve explicit labels and values alongside color.

## Typography

DM Sans Variable is bundled locally through `@fontsource-variable/dm-sans`, with DM Sans and sans-serif fallbacks. Use this single family throughout, including formulas and schema labels.

- **Headline:** the frontmatter headline role; sentence case, balanced wrapping and compact tracking. It becomes (32px) at the tablet breakpoint and (31px) on mobile, with a (16ch) mobile maximum width.
- **Metric:** tabular numerals, the frontmatter metric role; wide screens increase values to (33px). Ordinary mobile values are (25px), while long numeric and text values use smaller explicit variants.
- **Panel title:** the title role. Wide screens use (15px), mobile uses (13px). Secondary subtitles usually use (10px) with generous line height.
- **Body and labels:** body copy is (12px); chart labels and table text usually sit at (10–11px), with (8–9px) supporting mobile detail. Keep descriptions short and attach units to values.

## Layout

The centered application has a maximum width of (1800px), desktop padding of (27px 56px 0), and a shared (18px) panel rhythm. The header places brand, six-page pill navigation and source link on one row; page title and coverage indicator precede the global filter bar.

Four equal KPI columns lead into a main (2.05:1) chart/insight split. Other views use equal two-column grids; the overview lower row uses (1.1:1:0.78). Grids use `minmax(0,…)` to allow chart containers to shrink. Panels, charts and tables own their internal hierarchy rather than inheriting a uniform card layout.

- At (1500px) and above, horizontal padding becomes (72px), panels gain room and charts become taller.
- At (1190px) and below, horizontal padding becomes (32px), controls compact, and the overview lower row becomes two columns with its market donut hidden.
- At (960px) and below, navigation moves to a full-width second header row. The date trigger becomes an icon, and the main split becomes (1.65:1).
- At (700px) and below, the canvas uses (20px 18px 0) padding, navigation scrolls horizontally, the coverage badge hides, filters wrap, KPI cards form two columns, and content grids become one column with (14px) gaps. The overview market donut returns in the stack. Export uses its icon; tables retain their information through horizontal scrolling with a (640px) minimum width.
- Mobile metrics hide sparklines for legibility. Numeric values stay together; long text values wrap. Smaller wide-value variants avoid clipping. At (380px) and below, page gutters become (14px), and the customer segment legend stacks beneath its donut.

## Elevation & Depth

Resting panels are flat. Tonal surfaces, spacing and internal dividers communicate grouping. The selected segmented control has a small lift; floating date selection and chart tooltips receive shadows. Do not add persistent panel shadows or gradients.

The sidecar records the exact segmented, date-popover and tooltip shadows. Controls transition background, text and shadow over (.16s). Page content arrives over (.25s) with a small vertical movement; reduced-motion preferences disable animation and transitions. Chart series animations are disabled.

## Shapes

Panels use generous rounded corners, KPI cards slightly tighter ones, and controls use pill forms. Mobile panels and metrics reduce their radii with their padding. Borders distinguish fields and secondary controls; table rows and methodological groups use fine horizontal dividers. Heat cells use small (4px) corners, and series keys use dots or small squares. Lucide line icons and the simple bar-mark brand supply functional symbols.

## Components

- **Buttons:** compact, centered icon-and-label controls. Primary actions use ink with white text; secondary actions use a light fill and thin border. Disabled buttons lower opacity to (.45) and use an unavailable cursor. Export has a slightly roomier dark treatment.
- **Navigation:** a near-white rounded track with a dark active pill and modest neutral hover. Active pages expose `aria-current="page"`. Keep all six destinations visible through horizontal scrolling on mobile.
- **Segmented controls:** a grey track with a white selected pill. Use for date presets and small chart metric switches; preserve their group labels.
- **Fields:** soft green-neutral fill, fine borders and compact labels. Search uses a pill container; date fields use tighter corners inside a floating form. Date errors appear beside the fields. Keep explicit country, search and date labels.
- **Panels:** heading, optional short subtitle and contextual action sit above the content. Use sage fill for insight/method support, not every panel. Metric cards keep label, dominant value and explanatory note; action icons appear on hover or keyboard focus on desktop.
- **Charts:** pale dashed grids, restrained axes, compact ticks and nearby legends. Tooltips format GBP and counts consistently. A chart footer explains units, partial periods or available drill-down. Customer frequency/spend scatter charts use logarithmic axes with explicit ticks; preserve the logarithmic axis label and calculated tick arrays when extending them. The market scatter remains linear.
- **Tables and tags:** right-align numeric columns with tabular figures, use horizontal dividers and a subtle row hover. Segment tags use named pastel variants. Retention cells retain values and unobserved dashes; heatmap cells are keyboard focusable with descriptive labels.
- **States and access:** preserve the skip link, semantic page and section headings, labelled controls, loading status, alert errors and reset/retry paths. Keyboard focus uses a blue (2px) outline offset by (4px). Search inputs have no local outline, so additions must preserve a visible focus indication on their container or field. Do not claim chart color or hover alone communicates its meaning.

## Do's and Don'ts

### Do:
- **Do** carry the neutral canvas, rounded panels, dark selected pill and powder blue KPI across new screens.
- **Do** give numbers, chart labels, units and explanatory notes a clear hierarchy.
- **Do** preserve mobile value legibility, explicit logarithmic ticks and horizontally scrollable dense tables.
- **Do** retain keyboard focus, accessible labels and reduced-motion behavior.

### Don't:
- **Don't** introduce decorative imagery, ornamental gradients or persistent card shadows.
- **Don't** let a sparkline, icon or action crowd the primary metric value on mobile.
- **Don't** use color as the only explanation of a series, category or state.
- **Don't** turn chart-heavy pages into repeated equal-weight cards when their information needs different space.
