---
name: GBP Model Audit
description: Ultraviolet design theme for both the audit reports and the chat window — one accent signal, hairlines, mono metadata, light and dark.
colors:
  uv-bg: "#ffffff"
  uv-surface-1: "#f5f5f8"
  uv-surface-2: "#ececf1"
  uv-text: "#121118"
  uv-text-2: "#5d5b6b"
  uv-text-3: "#706e80"
  uv-accent: "#7b61ff"
  uv-accent-text: "#5b41e0"
  uv-on-accent: "#ffffff"
  uv-accent-soft: "rgba(123, 97, 255, 0.07)"
  uv-accent-hl: "rgba(123, 97, 255, 0.2)"
  uv-hl-tx: "#3a2a99"
  uv-danger: "#e5484d"
  uv-dock: "#121118"
  uv-dock-text: "#f2f1f7"
  uv-dock-text-2: "rgba(242, 241, 247, 0.62)"
  state-fail: "#e5484d"
  state-fail-tint: "#fbe9e7"
  state-major: "#9c2a1f"
  state-minor-tint: "#ececf1"
  state-check: "#8a4b00"
  state-check-tint: "#fdf1de"
  state-pass: "#1e6b34"
  state-pass-tint: "#e5f2e8"
  state-na: "#706e80"
typography:
  report-display:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", \"Helvetica Neue\", Arial, \"PingFang SC\", \"Microsoft YaHei\", \"Microsoft JhengHei\", sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  report-headline:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", \"Helvetica Neue\", Arial, \"PingFang SC\", \"Microsoft YaHei\", \"Microsoft JhengHei\", sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  report-title:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", \"Helvetica Neue\", Arial, \"PingFang SC\", \"Microsoft YaHei\", \"Microsoft JhengHei\", sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.35
  report-body:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", \"Helvetica Neue\", Arial, \"PingFang SC\", \"Microsoft YaHei\", \"Microsoft JhengHei\", sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  report-mono:
    fontFamily: "ui-monospace, \"SF Mono\", \"JetBrains Mono\", Menlo, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 400
  window-title:
    fontFamily: "var(--ui-font, var(--font-sans, ui-sans-serif, system-ui, sans-serif))"
    fontSize: "16px"
    fontWeight: 400
    letterSpacing: "-0.01em"
  window-body:
    fontFamily: "var(--ui-font, var(--font-sans, ui-sans-serif, system-ui, sans-serif))"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
  window-mono-label:
    fontFamily: "ui-monospace, \"SF Mono\", \"JetBrains Mono\", Menlo, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 400
rounded:
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
  section-tab:
    textColor: "{colors.uv-text-3}"
    typography: "{typography.report-body}"
    padding: "10px 0"
  section-tab-active:
    textColor: "{colors.uv-text}"
  verdict-sign:
    backgroundColor: "{colors.uv-surface-1}"
    textColor: "{colors.uv-text}"
    rounded: "{rounded.uv-md}"
    padding: "7px 12px 7px 10px"
  location-plate:
    backgroundColor: "{colors.uv-bg}"
    textColor: "{colors.uv-text}"
    rounded: "{rounded.uv-sm}"
    padding: "6px 10px 5px"
  report-button:
    backgroundColor: "{colors.uv-bg}"
    textColor: "{colors.uv-text}"
    rounded: "{rounded.uv-pill}"
    padding: "6px 12px"
  report-button-primary:
    backgroundColor: "{colors.uv-accent}"
    textColor: "{colors.uv-on-accent}"
    rounded: "{rounded.uv-pill}"
    padding: "6px 12px"
  filter-segment-on:
    backgroundColor: "{colors.uv-text}"
    textColor: "{colors.uv-bg}"
    padding: "6px 12px"
  severity-blocker:
    backgroundColor: "{colors.uv-danger}"
    textColor: "#ffffff"
    rounded: "{rounded.uv-pill}"
    padding: "2px 8px"
  severity-major:
    backgroundColor: "{colors.state-fail-tint}"
    textColor: "{colors.state-major}"
    rounded: "{rounded.uv-pill}"
    padding: "2px 8px"
  severity-minor:
    backgroundColor: "{colors.state-minor-tint}"
    textColor: "{colors.uv-text-2}"
    rounded: "{rounded.uv-pill}"
    padding: "2px 8px"
  status-unclear:
    backgroundColor: "{colors.state-check-tint}"
    textColor: "{colors.state-check}"
    rounded: "{rounded.uv-pill}"
    padding: "1px 8px"
  status-pass:
    backgroundColor: "{colors.state-pass-tint}"
    textColor: "{colors.state-pass}"
    rounded: "{rounded.uv-pill}"
    padding: "1px 8px"
  reading-card:
    backgroundColor: "{colors.uv-surface-1}"
    rounded: "{rounded.uv-md}"
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

**Creative North Star: "Address on Ultraviolet"**

The package shares one visual language — the Ultraviolet design theme ([jesselei1102-hue/design-theme](https://github.com/jesselei1102-hue/design-theme)) — across the audit reports and the chat window. White or near-black ground, 0.5px hairlines, monospace metadata, one violet signal, light and dark.

The reports (`report/render_report.py` with the CSS and JS of `templates/report-template.html`) keep the report's working-document structure: sticky header, section tabs, fix-list toolbar, and a location plate for every object (name above; kind, sheet and Revit ID on a mono district line). Colour chrome uses only Ultraviolet tokens; red / amber / green appear only as state beside their words.

The chat window (`gbp-audit` MCP App, `app/app/`) is the same token set: orbit header, tabs, dock, Run pill. The window chooses; the reports carry the results.

**Key Characteristics:**
- One Ultraviolet palette for report and window; accent only for chrome (active tab, primary button, codes, focus, signal dots).
- Report: location plates for every object, with tabular mono figures for IDs.
- Report: state colour only where it carries meaning, always beside its text.
- Light and dark via `data-theme` (sun/moon toggle); print forces light tokens.
- Window: hairline structure, mono labels, one primary violet Run pill in the dark run sheet.

## Colors

Ultraviolet neutrals and accent for chrome; a muted traffic-light set reserved for state.

### Primary
- **Ultraviolet** (`--accent`; dark `#8f7bff`): the only chrome signal — primary button, active tab rule, focus rings, finding/task codes as text (`--accent-tx`), checkbox accents, logo/signal dots. Danger (`--danger`) is for Blocker fill and fail marks only.

### Secondary
- **Surface 1 / 2** (`--s1`, `--s2`): verdict chip, reading cards, minor severity wash.
- **Dock** (`--dock-bg`): screenshot viewer head and toast; matches the window run sheet.

### Tertiary (state)
- **Fail** on Fail Tint: Fail / Missing statuses, Blocker severity fill, not-ready verdict mark.
- **Unclear Amber** on Check Tint: Unclear / Partial, "to check" severity, partial verdict mark.
- **Pass Green** on Pass Tint: Pass status, ready mark, fixed strike-through, copied button state.
- **N/A Grey** on Surface 2: N/A and not-judged; Minor severity uses text-2 on the same tint.

### Named Rules
**The Variables-Only Rule.** Report CSS and window components use only Ultraviolet variables (plus the named state tokens above). Never hard-code a chrome colour. Change the signal by editing the five accent variables in both scheme blocks of `tokens.css` / `report-css`.

**The Meaning-Only Colour Rule.** Red, amber, green and grey appear only on a status, a severity, the verdict mark, the fixed strike or the check notice, and every one of them sits beside its word.

**The One Accent Rule.** Violet is never a status colour. Status never paints a plate, a tab or the primary button.

## Typography

**Report UI:** system sans standing in for Inter / Noto Sans SC (reports must open offline with no font files).
**Report / window mono:** ui-monospace (SF Mono, JetBrains Mono, Menlo, Consolas) for every label, count, ID, file name and meta line.
**Window UI:** host `--ui-font` / `--font-sans` when available.

### Hierarchy
- **Report Display** (400, 16px): project name in the header (matches window brand weight).
- **Report Headline** (500, 15px): section headings.
- **Report Title** (500, 14px): finding titles.
- **Report Body** (400, 13px): running text; leads muted at 72ch.
- **Mono Label** (400, 11px): edition line, severity, status tags, plate district line, table headers, progress.
- **Window Title / Body / Mono** as in the Ultraviolet MCP App skill.

### Named Rules
**The Tabular Address Rule.** Every Revit ID, count and reading value uses tabular figures.

## Layout

The report is a single centred column (1240px) with 24px gutters (16px under 640px). Sticky header; under it the fix-list toolbar sticks so filters and Copy IDs stay reachable. Sections open with 36px above and a hairline below. A finding is severity · title · actions, with objects indented on tick · plate · expected/actual · copy actions. At 820px object rows stack; at 640px header and toolbar stop sticking.

The window is a narrow iframe that sizes to its content (Ultraviolet shell: top, stats, tabs, toolbar, dock).

## Elevation & Depth

Flat; depth from fills and hairlines. Report toast and screenshot dialog use `--pop-shadow`. Dark scheme may glow the accent (`--glow`) on the primary button and active tab rule.

## Shapes

Pills (99px) for buttons, filter segments, severity/status chips, icon buttons and the toast. 6–8px radii for plates, verdict chip, reading cards; 14px for the screenshot dialog. 0.5px hairlines throughout. Object rows separated by dashed hairlines; findings and sections by solid ones.

## Components

### Buttons
- **Report button:** quiet pill; hairline border; 12px; stroked SVG before the label. After copy turns Pass Green for 1.4s.
- **Report primary:** Ultraviolet fill, on-accent text ("Copy IDs in view"). One per toolbar.
- **Window Run pill:** the only primary action in the window; Ultraviolet fill inside the run sheet.

### Navigation
- **Section tabs:** tertiary text in the header, 2px accent rule under the active hash target; mono counts.
- **Window tabs:** same pattern.

### Location Plate (report signature)
Address unit: surface fill, 0.5px strong hairline, 6px radius. Line one is the object name (13px/500); line two is mono kind · sheet · ID. Dashed frame means no Revit ID. Never coloured by state.

### Fixed Row / Screenshot / Verdict
Unchanged behaviour: fixed strike in Pass Green; 96×72 shot column; verdict chip with a 6px signal dot in the verdict's state colour. Viewer head uses dock fill.

### Theme toggle
Sun/moon `icon-btn` in the header. Override in `localStorage` key `uv-theme` wins, else OS preference; print forces light tokens.

## Do's and Don'ts

### Do:
- **Do** put every object on a location plate with its Revit ID in tabular mono figures.
- **Do** show every status and severity as words on a tint.
- **Do** use only Ultraviolet variables for chrome in report and window.
- **Do** offer light and dark on screen; keep print on the light sheet.
- **Do** use stroked inline SVG icons at 14px.

### Don't:
- **Don't** use the accent for a status, or a state colour for wayfinding.
- **Don't** colour a plate by its state.
- **Don't** reintroduce direction-sign blue or a second primary action.
- **Don't** load external CSS, JS or fonts into the self-contained report file.
- **Don't** add sheet shadows beyond the toast / dialog pop shadow.
