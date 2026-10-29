# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **BIM team (primary).** A Hong Kong BIM manager or modeller preparing a General Building Plans (GBP) submission in Revit. They run the audit on the open model, then go back into Revit to fix what failed. They work with the report open beside Revit.
- **AP / client.** The Authorized Person and the client read their own edition to see whether the package can be submitted, what is wrong, and what only they can decide or supply.

## Product Purpose

GBP Model Audit checks a Revit model prepared for a GBP submission against BIMGBPS (2019) and the cited Buildings Ordinance regulations (Cap. 123, 123F, 123H, 123I) and practice notes. An AI agent reads the model read-only through a Revit MCP server, runs the package's analysers, and writes reports. Success: the BIM team finds and fixes every failing item quickly, and the AP sees an honest readiness verdict.

## Positioning

An agent-run, read-only readiness audit organised by the BIMGBPS sections and tasks (TL-V01 to TL-A04, model health MA-1 to MA-7), where every result cites its clause, and anything that could not be decided is reported as such rather than passed.

## Operating Context

- Runs inside an agent chat (Claude, Cursor, other harnesses). The `gbp-audit` MCP server shows a chat window (an MCP App) to choose what to check; the agent does the work with whatever Revit MCP tools are connected.
- The window is a thin app: choose the checks and, before running, the outputs. Nothing else happens in the window.
- Outputs, chosen before the run: BIM team HTML report, AP / client HTML report, Excel issue list. All are written into the audit folder.
- There is no confirmation gate: reports are built as soon as the checks finish. Values read off sheet images are listed in the report as still to be checked by a person, each with its crop.
- To fix an issue, the BIM team needs a copyable Revit ID (for Revit's Select by ID, or the sheet / view name to open it) and a one-line instruction they can paste to the agent.

## Capabilities and Constraints

- Read-only on the model: the audit never changes the Revit file. Opening a view or selecting elements is allowed; writing is not.
- The `gbp-audit` server is independent of any Revit MCP server and never talks to Revit itself.
- The package must run in other harnesses (Cursor, Hermes), not only in the workspace it was written in.
- Reports are self-contained HTML with a sibling `assets/` folder: no network, no external CSS, JS or fonts. Python 3 standard library only on the report side.
- All UI and report text is in English.
- Status vocabulary: Pass, Fail, Partial, Missing, Unclear (not determinable is not a pass), N/A (conditional), Not judged. Severity: Blocker, Major, Minor.
- The report is not an approval by the Buildings Department or the Building Authority, and does not replace the AP's professional judgement.

## Brand Commitments

- MCP App windows use the operator's Ultraviolet theme (minimalist, abstract, future; light and dark).

## Evidence on Hand

- Real audit runs on the sample model `GBP_Revit_Templates_R27.rvt` under `../model-audit-runs/` (not shipped), and the test fixture run under `app/test/fixtures/run-full/`.
- No customer logos, testimonials or usage figures exist; none may be invented.

## Product Principles

1. The window chooses; the reports carry the results.
2. Every finding leads to the object to fix: where it is, its Revit ID, and what to do.
3. Unclear is never Pass; what was not checked by a person says so.
4. Read-only on the model, always.
5. Each edition says only what its reader needs: IDs and tool detail for the BIM team, decisions and readiness for the AP.
