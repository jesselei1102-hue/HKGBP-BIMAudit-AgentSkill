---
name: GBP Model Audit
description: Road signage to the object for the audit reports; the operator's Ultraviolet theme for the chat window.
colors:
  sign-blue: "#17407a"
  sign-blue-deep: "#0f2f5c"
  sign-mist: "#c9d6ea"
  sheet-white: "#ffffff"
  sheet-paper: "#f3f5f8"
  plate-ink: "#121519"
  ink-secondary: "#3e4650"
  ink-muted: "#5a636d"
  rule-line: "#d6dbe1"
  rule-line-strong: "#b9c0c8"
  state-fail: "#b3261e"
  state-fail-tint: "#fbe9e7"
  state-major: "#9c2a1f"
  state-minor-tint: "#eceff2"
  state-check: "#8a4b00"
  state-check-tint: "#fdf1de"
  state-pass: "#1e6b34"
  state-pass-tint: "#e5f2e8"
  state-na: "#56616c"
  focus-blue: "#2a6fd6"
  selection-blue: "#cfe0fb"
  uv-bg: "#ffffff"
  uv-surface-1: "#f5f5f8"
  uv-surface-2: "#ececf1"
  uv-text: "#121118"
  uv-text-2: "#5d5b6b"
  uv-text-3: "#9a98a8"
  uv-accent: "#7b61ff"
  uv-accent-text: "#5b41e0"
  uv-on-accent: "#ffffff"
  uv-danger: "#e5484d"
  uv-dock: "#121118"
  uv-dock-text: "#f2f1f7"
typography:
  report-display:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "21px"
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  report-headline:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "20px"
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  report-title:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "16px"
    fontWeight: 650
    lineHeight: 1.35
  report-body:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  report-label:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
  plate-name:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "14px"
    fontWeight: 650
    lineHeight: 1.3
  plate-line:
    fontFamily: "\"Segoe UI\", system-ui, -apple-system, \"Helvetica Neue\", Arial, \"Microsoft JhengHei\", sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.35
    fontFeature: "\"tnum\" 1"
  window-title:
    fontFamily: "var(--font-sans, ui-sans-serif, system-ui, sans-serif)"
    fontSize: "16px"
    fontWeight: 400
    letterSpacing: "-0.01em"
  window-headline:
    fontFamily: "var(--font-sans, ui-sans-serif, system-ui, sans-serif)"
    fontSize: "15px"
    fontWeight: 500
  window-body:
    fontFamily: "var(--font-sans, ui-sans-serif, system-ui, sans-serif)"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
  window-mono-label:
    fontFamily: "ui-monospace, \"SF Mono\", \"JetBrains Mono\", Menlo, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 400
rounded:
  plate: "3px"
  verdict: "4px"
  control: "5px"
  uv-sm: "6px"
  uv-md: "8px"
  uv-lg: "14px"
  uv-sheet: "18px"
  uv-pill: "99px"
spacing:
  report-gutter: "24px"
  report-gutter-narrow: "16px"
  report-section: "36px"
  report-row: "8px"
  report-max-width: "1240px"
  uv-gutter: "20px"
  uv-inset: "16px"
components:
  section-sign:
    textColor: "{colors.sheet-white}"
    backgroundColor: "{colors.sign-blue}"
    typography: "{typography.report-label}"
    padding: "8px 10px 10px"
  verdict-sign:
    backgroundColor: "{colors.sheet-white}"
    textColor: "{colors.plate-ink}"
    rounded: "{rounded.verdict}"
    padding: "7px 12px 7px 10px"
  location-plate:
    backgroundColor: "{colors.sheet-white}"
    textColor: "{colors.plate-ink}"
    typography: "{typography.plate-name}"
    rounded: "{rounded.plate}"
    padding: "5px 10px 4px"
  report-button:
    backgroundColor: "{colors.sheet-white}"
    textColor: "{colors.plate-ink}"
    typography: "{typography.report-label}"
    rounded: "{rounded.control}"
    padding: "5px 10px"
  report-button-primary:
    backgroundColor: "{colors.sign-blue}"
    textColor: "{colors.sheet-white}"
    typography: "{typography.report-label}"
    rounded: "{rounded.control}"
    padding: "5px 10px"
  report-button-primary-hover:
    backgroundColor: "{colors.sign-blue-deep}"
  filter-segment-on:
    backgroundColor: "{colors.sign-blue}"
    textColor: "{colors.sheet-white}"
    padding: "6px 11px"
  severity-blocker:
    backgroundColor: "{colors.state-fail}"
    textColor: "{colors.sheet-white}"
    rounded: "{rounded.plate}"
    padding: "2px 7px"
  severity-major:
    backgroundColor: "{colors.state-fail-tint}"
    textColor: "{colors.state-major}"
    rounded: "{rounded.plate}"
    padding: "2px 7px"
  severity-minor:
    backgroundColor: "{colors.state-minor-tint}"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.plate}"
    padding: "2px 7px"
  status-unclear:
    backgroundColor: "{colors.state-check-tint}"
    textColor: "{colors.state-check}"
    rounded: "{rounded.plate}"
    padding: "1px 7px"
  status-pass:
    backgroundColor: "{colors.state-pass-tint}"
    textColor: "{colors.state-pass}"
    rounded: "{rounded.plate}"
    padding: "1px 7px"
  reading-card:
    backgroundColor: "{colors.sheet-paper}"
    rounded: "{rounded.control}"
  window-run-sheet:
    backgroundColor: "{colors.uv-dock}"
    textColor: "{colors.uv-dock-text}"
    rounded: "{rounded.uv-sheet}"
    padding: "14px 16px 12px"
  window-run-button:
    backgroundColor: "{colors.uv-accent}"
    textColor: "{colors.uv-on-accent}"
    rounded: "{rounded.uv-pill}"
    padding: "8px 18px"
  window-chip:
    textColor: "{colors.uv-text-2}"
    rounded: "{rounded.uv-pill}"
    padding: "5px 11px"
  window-chip-on:
    backgroundColor: "{colors.uv-text}"
    textColor: "{colors.uv-bg}"
    rounded: "{rounded.uv-pill}"
    padding: "5px 11px"
  window-side-item-selected:
    textColor: "{colors.uv-text}"
    rounded: "{rounded.uv-sm}"
    padding: "7px 8px"
---

# Design System: GBP Model Audit

## Overview

**Creative North Star: "Road Signs to the Object"**

The package has two visual worlds with a hard boundary between them. The audit reports (`report/render_report.py` with the CSS and JS blocks of `templates/report-template.html`) live in Hong Kong road signage: a deep direction-sign blue band across the top carries the project, the verdict sign and the section signs in white, and everything below is a plain white sheet. Each object to fix is set on a street-name plate (black text in a thin black frame, object name above, kind, sheet and Revit ID on a smaller district line), so every finding reads as a destination with an address. The report is a working document kept open beside Revit: dense, flat, legible, with colour spent only on state.

The chat window (the `gbp-audit` MCP App, `app/app/`) keeps the operator's Ultraviolet theme, the brand commitment for MCP App windows: white or near-black ground, 0.5px hairlines, monospace metadata, one violet signal and a dark rounded dock. This build extended it without changing a token: the run sheet is the dock opened up at the top of the window, and the outputs are chosen as plain selectable lines. The window chooses; the reports carry the results. Neither world borrows from the other.

**Key Characteristics:**
- Report: blue signage band over one white sheet, in every colour scheme and in print.
- Report: location plates for every object, with tabular figures for IDs.
- Report: state colour only where it carries meaning, always beside its text.
- Window: Ultraviolet tokens only, light and dark, hairline structure, mono labels.
- Window: one primary action, the violet Run pill, sitting in the dark run sheet.

## Colors

The report is white paper, black ink and one signage blue, with a muted traffic-light set reserved for state; the window is near-monochrome with a single ultraviolet signal.

### Primary
- **Direction-Sign Blue** (sign-blue): the band, the pressed filter segment, the primary button, and finding and task codes as text. It marks wayfinding, never state.
- **Ultraviolet** (uv-accent; dark scheme #8f7bff): the window's only signal: the Run pill, focus rings, checkbox accents, the selected tab rule and the logo dot. Its text variant (uv-accent-text) carries accent-coloured words.

### Secondary
- **Night Sign Blue** (sign-blue-deep): hover state of the report's primary button.
- **Sign Mist** (sign-mist): secondary text on the band (edition line, section-sign counts) and the hover underline of section signs.

### Tertiary (state, report only)
- **Fail Red** (state-fail) on Fail Tint: Fail and Missing statuses, the Blocker severity fill and the verdict mark when not ready. Major severity uses the deeper Major Red (state-major) on the same tint.
- **Unclear Amber** (state-check) on Check Tint: Unclear and Partial statuses, the "to check" severity, the not-checked-by-a-person notice and the partial verdict mark.
- **Pass Green** (state-pass) on Pass Tint: Pass status, the ready verdict mark, the fixed strike-through, the tick accent and the "copied" button state.
- **N/A Grey** (state-na) on Minor Tint: N/A and not-judged statuses; Minor severity uses Ink Secondary on the same tint.

### Neutral
- **Sheet White** (sheet-white): the report ground, plate fill, toolbar and controls. It never changes with the colour scheme.
- **Sheet Paper** (sheet-paper): the reading card body, the only tonal step on the sheet.
- **Plate Ink** (plate-ink): body text, plate text and the plate frame.
- **Ink Secondary / Ink Muted** (ink-secondary, ink-muted): leads, meta lines, table headers.
- **Rule Line / Rule Line Strong** (rule-line, rule-line-strong): section and row dividers; control borders and segment frames.
- **Ultraviolet neutrals** (uv-bg, uv-surface-1, uv-surface-2, uv-text, uv-text-2, uv-text-3, uv-dock, uv-dock-text): the window's grounds, three text levels and the dark dock. Each has a dark-scheme value in `app/app/theme/tokens.css`; hairlines are translucent (8% and 16% of the text colour in light, 7% and 14% white in dark).

### Named Rules
**The One Ground Rule.** The report keeps its white sheet in every colour scheme and in print (`color-scheme: light`, no dark block). A road sign does not invert at night.

**The Meaning-Only Colour Rule.** Red, amber, green and grey appear only on a status, a severity, the verdict mark, the fixed strike or the check notice, and every one of them sits beside its word. Colour alone never carries a status.

**The Variables-Only Rule.** Window components use only the Ultraviolet variables; `gbp.css` adds no colours of its own. Change the signal by editing the five accent variables in both scheme blocks.

## Typography

**Report Font:** Segoe UI (with system-ui, -apple-system, Helvetica Neue, Arial, Microsoft JhengHei, sans-serif)
**Window Font:** the host's `--font-sans` (with ui-sans-serif, system-ui)
**Window Mono:** ui-monospace (with SF Mono, JetBrains Mono, Menlo, Consolas)

**Character:** The report sets everything in one sans at sign weights (650 for names and headings, 600 for labels), with tabular figures for every ID and count. The system stack ships because reports must open offline with no font files; it is a constraint, not a choice to protect (see Do's and Don'ts). The window pairs a light sans (titles at weight 400 and 500) with small monospace for every label, count, file name and meta line.

### Hierarchy
- **Report Display** (650, 21px, 1.3): the project name in the band.
- **Report Headline** (650, 20px, 1.3): section headings (Fix list, To check by eye, Tasks).
- **Report Title** (650, 16px, 1.35): finding titles and sub-headings.
- **Report Body** (400, 15px, 1.5): running text; leads at 72ch, paragraphs at 75ch.
- **Report Label** (600, 13px to 13.5px): section signs, buttons, filter segments, severity and status tags (12px, 700 for severity).
- **Plate Name / Plate Line** (650 at 14px / 400 at 12px with the ID at 700): the location plate's two lines.
- **Window Title / Headline / Body** (400 at 16px / 500 at 15px / 400 at 13px, 1.4).
- **Window Mono Label** (400, 11px): run-sheet terms, counts, file names, task codes, meta. Stats use the same mono at 26px.

### Named Rules
**The Tabular Address Rule.** Every Revit ID, count and reading value uses tabular figures, so IDs line up down a column like house numbers.

## Layout

The report is a single centred column (report-max-width) with 24px gutters (16px under 640px). The band is sticky at the top; under it the fix-list toolbar is sticky at 104px, so filters and Copy IDs stay reachable while the list scrolls. Sections open with 36px above and a hairline below. A finding is a three-column head (severity, title with meta and fix, actions) with its objects indented beneath on a four-column row: tick, plate (220px to 340px), what was expected against what was found, and the two copy actions. At 820px the object row stacks into tick and plate, then the description and actions under the plate; at 640px the band, verdict and toolbar fall into one column and stop sticking. Sheet readings tile at a 300px minimum. Print drops every control, ticks and the toast, and keeps findings and task cards unbroken.

The window is a narrow iframe that sizes to its content. 20px side gutters frame the header, section heads and outputs; the run sheet and dock sit 16px in from the edges. Choose checks is a two-pane split (sections at 34%, minimum 170px, beside the task list); under 560px the sections become a wrapping row of pill chips above the list, and the run-sheet terms stack above their values.

## Elevation & Depth

Both worlds are flat; depth comes from fills and hairlines, not shadow.

### Shadow Vocabulary
- **Band separation** (`box-shadow: 0 2px 10px rgba(10,25,50,.18)`): only under the sticky report band, removed in print.
- **Plate lip** (`box-shadow: 0 1px 0 rgba(0,0,0,.08)`): a one-pixel lip under the location plate, the physical edge of a mounted sign.
- **Window popover** (`--pop-shadow`): Ultraviolet popovers only. In the dark scheme the accent gains a 10px glow (`--glow`) on the Run pill, the signal dot and the active tab rule; in light it is none.

### Named Rules
**The Flat Sheet Rule.** Nothing on the report sheet floats. Cards, tables and the verdict sign are separated by hairlines or the paper tint, never by a shadow.

## Shapes

The report is nearly square: plates and tags at 3px, the verdict sign at 4px, buttons, inputs, notices and reading cards at 5px. Frames are thin and dark where they mean "sign" (1.5px plate-ink on a plate, dashed when the object has no Revit ID) and light grey elsewhere. Object rows are separated by dashed hairlines, findings and sections by solid ones.

The window is soft and round: 0.5px hairlines throughout, 6px list items, 8px fields and next-step boxes, 14px popovers, 18px run sheet, and full pills (99px) for the dock, Run button, chips, icon buttons and the copy button.

## Components

### Buttons
- **Report button:** quiet and square-edged; white with a strong-rule border, 13px semibold, a 14px stroked SVG icon before the label. Hover darkens the border to Ink Secondary. After a copy it turns Pass Green for 1.4s. Disabled at 45% opacity.
- **Report primary:** Direction-Sign Blue fill with white text ("Copy IDs in view"); hover Night Sign Blue. One per toolbar.
- **Window Run pill:** the only primary action in the window; Ultraviolet fill, 13px, 8px by 18px inside the run sheet, glowing in dark. Hover brightens 8%.
- **Window dock and text links:** dock buttons are pills in dock text; text links are 11px mono in secondary text.

### Chips
- **Report filter segments:** a joined strip with a strong-rule frame; the pressed segment fills Direction-Sign Blue, counts follow at 80% opacity.
- **Window chips:** 0.5px pill outlines in secondary text; selected chips invert to text-colour fill on the ground colour.

### Cards / Containers
- **Reading card:** 5px radius, Rule Line frame, Sheet Paper body; the crop sits on white above a hairline and zooms on click with a blue inset outline on hover. Value at 18px/650, meta at 12.5px muted.
- **Task card:** a disclosure row (code in blue, name, L1 and L2 statuses) with a dashed rule under the open summary and the body indented to the code column.
- **Window next step:** 0.5px strong-hairline box at 8px radius; the current step takes the accent border and the 7% accent wash.

### Inputs / Fields
- **Report:** selects and search at 13px, white, strong-rule border, 5px radius. Focus everywhere is a 2px Focus Blue outline at 2px offset; text selection is Selection Blue.
- **Window:** search is an underline field (hairline, accent on focus); popover fields sit on surface-1 at 8px radius; focus is a 2px accent outline.

### Navigation
- **Section signs:** a row of white-on-blue links in the band, each led by a small stroked SVG arrow and followed by its count in Sign Mist; hover draws a 3px Sign Mist underline. Scrolls sideways when narrow.
- **Window tabs and sections:** tabs in tertiary text with a 2px accent rule under the active one; side sections highlight with the 7% accent wash and carry mono counts in small pills.

### Location Plate (signature)
The street-name plate is the report's unit of address: white fill, 1.5px Plate Ink frame, 3px radius, a 1px lip. Line one is the object name (14px/650, ellipsis); line two is kind, sheet and "ID" with the Revit ID in bold tabular figures (12px). A dashed frame means the object has no Revit ID. A plate is never coloured by state.

### Fixed Row (signature)
Ticking an object marks it fixed in this browser: the plate and description drop to 50% opacity, a 2px Pass Green line draws across the plate (0.35s, cubic-bezier(.16,1,.3,1), off under reduced motion) and the description is struck through in green. The row keeps its place; "Hide fixed" is the reader's choice.

### Verdict Sign
A white plate on the band: a 10px square mark in the verdict's state colour, the verdict words at 14px/600, then the severity counts in muted text.

### Run Sheet (window, signature of this build)
The dock opened up at the top of the window: dock fill, 18px radius, a three-column term list (mono term, value, "Change" link) and a footer with the reason line and the Run pill above a hairline. After Run it lists the checks, outputs and results folder, and offers "Copy instruction" when the host cannot accept messages.

### Output Line (window)
Each output is a checkbox line: label in 500, the file name in 11px mono tertiary, a note on the second line; selected lines take the 7% accent wash.

## Do's and Don'ts

### Do:
- **Do** put every object on a location plate with its Revit ID in tabular figures, and its finding code linked to its task card.
- **Do** keep the report on the white sheet in dark mode and in print, with the band printed in colour.
- **Do** show every status and severity as words on a tint; the tint only reinforces the word.
- **Do** strike a fixed row through in Pass Green and leave it in place.
- **Do** use stroked inline SVG icons (copy, agent, arrow) at 14px in the report and the Ultraviolet `svg.i` set at 14px in the window.
- **Do** build window additions only from the Ultraviolet variables, at 0.5px hairlines, with mono for labels and counts.

### Don't:
- **Don't** use Direction-Sign Blue for a status, or a state colour for wayfinding.
- **Don't** colour a plate by its state; the plate is the address, the tag beside the finding is the state.
- **Don't** add a dark scheme to the report.
- **Don't** add shadows to anything on the report sheet beyond the band and the plate lip.
- **Don't** bring Ultraviolet violet, pills or the dock into the reports, or the signage blue and plates into the window.
- **Don't** add a second primary action to the window; Run (or Copy instruction) is the only accent fill.
- **Don't** treat the system sans in the report as a house face to defend: if an embedded signage face can ship inside the self-contained file, it may replace it.
