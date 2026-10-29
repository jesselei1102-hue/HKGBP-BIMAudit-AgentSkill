# Model Audit: a plain-language guide for APs and clients

> This is a plain-language version of [README.md](README.md), written for the Authorized Person (AP) and the client.
> The BIM team's technical guide is still [README.md](README.md) and [RUN.md](RUN.md).

## What it is, in one sentence

Model Audit checks a Revit model **before** it goes to the Buildings Department as a GBP Stage I submission, and tells you what is ready, what is wrong, what is missing, and what still needs your decision.

## Think of it as a mock vetting

Before a car goes for its official roadworthiness test, a good mechanic runs through the same checklist first, so nothing fails on the day.

Model Audit does the same for your GBP submission. It goes through the BIMGBPS checklist item by item, against the open Revit model, and writes up what it finds. It does this before BD sees the package, while problems are still cheap to fix.

It **only looks**: it never changes, deletes or adds anything in the model.

## What it checks

It checks all 36 BIMGBPS submission items, plus the general health of the model file. For easier reading they are grouped by topic:

| Topic | What it is asking, in plain words | BIMGBPS items |
| --- | --- | --- |
| Light and air | Are the windows big enough for the rooms they serve? | S14, V13 |
| Rooms and people | Enough toilets? Enough exits and stair capacity for the number of people? Refuse room and telecom (TBE) room big enough? | S10, S11, S13, S15, S16 |
| Areas | Do the site area, site coverage, plot ratio, GFA and GFA concessions, open space, fire compartments and other area diagrams add up, and agree with each other? | S02, S05–S08, S12, V06–V12, V14 |
| Drawings | Are the plans, sections, elevations and details all there, correctly titled, colour-coded per BD rules, and exportable as BD expects? | V01–V05, A01–A03 |
| Lists and final check | Drawing list, coordinates, development schedule, lift shafts, list of modifications, and finally: **can the package be submitted as it is?** | S01, S03, S04, S09, S17, S18, A04 |
| Model health | Is the file itself sound: Revit version, links, imports, sheets, and level of detail? | MA-1 to MA-7 |

Each item is checked at two levels, which are reported separately:

1. **Is it there and presented correctly?** For example, is the table a live schedule rather than a pasted picture?
2. **Do the numbers comply with the regulations?** For example, is the window area at least the fraction of floor area that Cap. 123F requires?

A good score at one level never cancels a fail at the other. A correct calculation shown as a picture still fails the first level.

## What you receive

Each audit produces one folder. Before it runs, you choose which of these it writes, all from the same results:

- **AP / client report** (`report-ap.html`): this is your copy. Internal model references and tool details are removed, and the **"Decisions required"** and **"Information required"** sections come straight after the verdict.
- **BIM team report** (`report-bim.html`): opens on the fix list. Every object to fix shows where it is (sheet, view, level or element) and its Revit ID, which the team can copy into Revit's Select by ID, or copy as one line to ask the agent to find it.
- **Excel issue list** (`issues.xlsx`): one row per object, to filter and hand out the fixes.

Values the audit read off drawing images are listed as **not checked by a person**, each with a crop of the sheet, so you can check them yourself.

Every finding comes with evidence, such as an exported view, a zoomed-in crop or a colour sample, so you can see the problem rather than take it on trust.

## What the results mean

| Result | What it means for you |
| --- | --- |
| **Pass** | Present and correct. Nothing to do. |
| **Partial** | Present, but something is missing or wrong. Needs fixing. |
| **Fail** | Wrong. Needs fixing before submission. |
| **Missing** | Required for this project, but the drawing or table does not exist yet. |
| **N/A (conditional)** | Judged not to apply to this project, with the reason stated. **Needs your confirmation.** |
| **N/A, declaration needed** | Does not apply, but the drawings do not yet say so. Only a note needs adding. |
| **Unclear** | Could not be decided, because a source document, project information or a model reading was not available. Treat as "not yet checked", **never as a pass**. |
| **Not judged** | No regulatory limit applies to the numbers, so there is nothing to compare against. |

## What it needs from you

The audit deliberately stops short of making the AP's professional judgements. Expect to be asked to:

- **Confirm each N/A.** Every "not applicable" call is conditional on your confirmation.
- **Choose a basis where the rules allow more than one.** If, for example, building height could reasonably be measured two ways, the report shows both results side by side and does not pick one for you.
- **Supply project information that is not in the model**, such as site survey data or design decisions. Items that depend on missing information are marked Unclear until it arrives.

## What it cannot do

Please read these limits before relying on the results:

- **It is not BD approval.** It helps the BIM and AP review; it does not replace it.
- **Some things cannot be read from the model automatically.** These need a manual spot-check by the BIM team:
  - dimension values that were typed over by hand;
  - small gaps or overlaps in area boundaries, which are a common cause of BD returns;
  - CAD drawings imported into the model;
  - for light and air, whether a window faces a qualifying open space outside, and the free ventilation area of louvres. The audit does work out which room each window serves from the model geometry, and reports how confident each match is.
- **Some readings come from looking at the drawing sheets**, such as table values and coordinates. The audit cuts out the relevant part of each sheet, and a person has to check each crop against the finding before relying on it.
- **Some source documents are not yet in the package**, so the compliance check for those items is marked Unclear. Examples are parts of the Fire Safety Code 2011, which affect the fire-related drawings and schedules (exits, stair capacity, fire compartments), and a few PNAPs.
- **Where a secondary document disagrees with the legislation, the legislation wins**, and the report says so.
- **It has been tested on one model so far**: the Buildings Department's sample GBP Revit template. On a real project the most common finding may simply be that a required drawing or table does not exist yet.

## Why this matters to you

- **Fewer surprises from BD.** Problems are found and fixed before submission, not after a return.
- **Clear decisions.** Everything that needs the AP's judgement is collected in one place, instead of being scattered through the drawings.
- **Evidence you can check.** Each finding shows where in the model it comes from and why.
- **Your judgement stays yours.** The audit reports what it found; it does not decide on your behalf.

## For the BIM team

How to run the audit, what it needs installed, and how to maintain it is in [README.md](README.md) and [RUN.md](RUN.md).
