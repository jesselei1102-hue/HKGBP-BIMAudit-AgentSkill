---
version: 1
slug: "report-render-report-py"
primary_target: "report/render_report.py"
related_targets: ["templates/report-template.html"]
---

## Surface

GBP Model Audit reports: `report/render_report.py` renders `report-bim.html` (BIM team edition, mode Operate: find each failing object and fix it in Revit) and `report-ap.html` (AP / client edition, mode Read: readiness, decisions, what to supply), both from `audit-results.json`, with `templates/report-template.html` for CSS and JS. Self-contained HTML, no network, stdlib Python.

Audience and job: the BIM team keeps the report open beside Revit, works down the fix list, copies a Revit ID into Select by ID or a one-line instruction to the agent, and marks items done. The AP reads the verdict, the decisions only they can make, and the information to supply.

Constraints: English; no element IDs or tool identifiers in the AP edition; Unclear is never Pass; readings taken off sheet images are listed as not checked by a person, with crops; read-only on the model.

## Direction contract

THESIS: The report is an address book on Ultraviolet. Every finding is a destination with an address: sheet, view, level or element, and its Revit ID set on a location plate. It refuses the category default of a status dashboard with KPI cards over a long table of rule results.

OWN-WORLD: Ultraviolet (jesselei1102-hue/design-theme). Shell: light or dark ground, hairline header with project, verdict chip and sun/moon toggle; section tabs with a 2px accent rule under the active one. Location plates: text on a hairline frame, object name above and kind plus ID below in mono. One violet accent for chrome only. State colours only where they carry meaning: Fail red, Unclear amber, Pass green, N/A grey. System sans + mono stacks, tabular figures for IDs. No network fonts.

STORY: The BIM team sees how many objects to fix and where they are, filters by task or severity, copies an ID or agent instruction per row or for a whole finding, ticks rows off as fixed, and reaches the sheet readings still to check. The AP sees whether it can be submitted, why, and what they must decide or supply.

FIRST VIEWPORT: Header: project name, edition line in mono, verdict chip ("Not ready to submit · 1 Blocker · 29 Major · 36 Minor"), theme toggle. Under it, section tabs (Fix list, To check, Tasks, Information, N/A). Then the fix list: severity filter pills, task select, search, violet "Copy IDs in view". First rows: finding line (severity, TL code, rule, fix) with object rows beneath, each led by its location plate and two copy actions.

FORM: Ultraviolet restyle of the prior road-sign structure. Raise from the doujin event catalog (declined): the code and its position are one space, so every finding code links between the fix list and its task section, and rows marked fixed persist locally and strike through instead of vanishing. Raise from the jet-age ticket wallet (declined): nothing disappears, it cancels; a fixed row keeps its place with a struck state.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
