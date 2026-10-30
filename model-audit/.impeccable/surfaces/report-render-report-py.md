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

THESIS: The report is road signage to the object. Every finding is a destination with an address: sheet, view, level or element, and its Revit ID set on a street-name plate. It refuses the category default of a status dashboard with KPI cards over a long table of rule results.

OWN-WORLD: Hong Kong road signage. Shell: a deep direction-sign blue band carrying the project, the verdict and the section signs in white. Ground: plain white sheet. Location plates: black text on white inside a thin black frame, object name above and kind plus ID below in a smaller line, like a bilingual street-name plate with its district line. State colours only where they carry meaning: Fail red, Unclear amber, Pass green, N/A grey. System sans stack, tabular figures for IDs.

STORY: The BIM team sees how many objects to fix and where they are, filters by task or severity, copies an ID or agent instruction per row or for a whole finding, ticks rows off as fixed, and reaches the sheet readings still to check. The AP sees whether it can be submitted, why, and what they must decide or supply.

FIRST VIEWPORT: Blue band across the top: project name, edition, audit date, and the verdict sign ("Not ready to submit · 6 Major findings"). Under it, section signs as a row of white-on-blue links (Fix list, To check, Tasks, Information, N/A). Then the fix list header: counts by severity as filter buttons, task and kind selects, "Copy all IDs" for the current filter. First rows visible: each row a finding line (severity, TL code, rule, fix) with its object rows beneath, each object led by its location plate and two copy actions.

FORM: Candidate 7 of 7 on the grounded list (Hong Kong road signage). seed:98298995d23f8274. Raise from the doujin event catalog (declined): the code and its position are one space, so every finding code links between the fix list and its task section, and rows marked fixed persist locally and strike through instead of vanishing. Raise from the jet-age ticket wallet (declined): nothing disappears, it cancels; a fixed row keeps its place with a struck state.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
