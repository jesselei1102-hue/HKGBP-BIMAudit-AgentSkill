# Upgrade ledger — raise every task to the S14 reference granularity (2026-10-13)

Operator request: review all work and raise it to the S14 two-prompt standard (analysis JSON + on-screen
summary → report from JSON only: Excel + HTML). Keep the four layers; merging similar tasks is fine; judged
on results only.

## Standard (what "done" means for a task group)
1. Extract recipe (L3) with exact revit-mcp calls and the extract files they produce.
2. Analysis script (tools/<group>/analyze.py): read-only, works only on the extract, writes the analysis JSON,
   prints the on-screen summary. Every value traces to an element id / parameter, or is reported as a gap.
3. Report script: from the JSON only → Excel (frozen header, 3 dp, Pass green / Fail red / N/A yellow) +
   self-contained HTML (dashboard, sortable tables, collapsible detail, fix directions, disclaimer footer).
4. L2 card §9 "Executable spec": scope, classification, association, formulas, JSON sections, summary, report.
5. Run on the open model copy; results reconciled against any previous run.

## Groups
- G1 S14 (+V13 shares the data) — reference
- G2 room-use: S13, S10/S11, S15/S16
- G3 area-scheme: V09/S05/S02, V10/S08/S07, V11, V12, V07/S06, V08/S12, V14, V06
- G4 drawing presentation: V01–V05, A01–A03
- G5 lists: S01, S03, S04, S18, S09/S17, A04
- G6 A1 model health

## Log
G1: extract saved in work/model-audit-runs/audit-2026-10-13-s14/_raw (rooms 66, polygons 12, curtain walls 74, panels 220, panel bbox samples 16, FS windows 12, doors 102).
G1: Ruling: lighting 1/10 and reg 36 (1/10, 1/10) for lavatories, not the prompt's 1/8 and toilet exclusion — legislation text governs (Memory fact knowledge-hk-gbp-submission-tl-20261013-013631) — cost if wrong: thresholds are rule data in analyze.py DEFAULT_RULES, override with --rules.
G1: Ruling: association by side probes (9 samples, 1 ft beyond wall face) against room polygons where fetched, bbox otherwise; internal glazing (rooms both sides) not counted per reg 30(2)(b) — cost if wrong: RECEPTION 64 loses 15.84 m² that the previous run counted.
G1: Ruling: wall orientation from the typical 3.28 ft bbox thickness, not the smaller extent — fixed short glass returns (236955/238370/1047065/1047095) wrongly credited to FR7/FR8 — cost if wrong: none (FR7 still passes).
G1: Ruling: louvre panels deducted from glass and not counted as openable; shown separately — cost if wrong: no room changes status (pass_only_if_louvre_counted = 0).
G1: Ruling: opening-top 2 m test uses sampled panel bbox per (type, centre height) group; all 193 assigned hung panels ≥ 2 m (min 2.349 m) — cost if wrong: one sample per group; groups are uniform by construction.
G1: analysis → 29 assessed (23 reg 30, 6 reg 36), 24 pass, 5 fail (FUNCTION ROOM 1/2 G/F, RECEPTION, ACTIVITY AREA 1/F, 2/F); 9 pending; 28 excluded; reconciles with the previous run (12/23 at 1/8 + RECEPTION internal glass = previous 13).
G1: report → xlsx 6 sheets (openpyxl reads clean, -W error) + HTML viewed in browser at 339 px: no overflow, sort works, fix directions shown.
G1: Ruling: my hand transcription of get_rooms shortened 'FUNCTION ROOM n' to 'FRn' (16 rooms) — caught when the S14 schedule CSV disagreed; rooms.tsv names re-checked against the model-sourced previous JSON (66/66 ids, all areas equal) and fixed; rule '^FR\d+$' removed — cost if wrong: none now; lesson → extract files must be checked against a second model read before analysis (added to R-S14 as step 8 below).
G1: added schedule-vs-model comparison (--schedule): 10 table rows all with issues, 20 assessed rooms missing from the table; GUARD ROOM (pending) is in the table and measures 1.960 glass / 1.690 openable.
G1: renderer: evidence kinds 'table' and 'report' render as links (test_task_report_links_not_images RED→GREEN, test_render 12/12); schema enum extended.
G1: audit-results.json rebuilt from the analysis JSON (F13–F19, 29 calcs); bim/ap rendered exit 0; AP view: no overflow at 339 px, all assets 200.
G1: complete (test_s14 12/12, test_render 12/12, check_package 17/17).
G2: extract in audit-2026-10-13-g2/_raw: rooms (copied from S14), 141 fixtures (count = query_model, 45 per floor + 6 unlevelled counters), 102 doors (family counts asserted in save_doors.py), S10/S11/S13/parking schedule CSVs exported by Revit (no transcription).
G2: Ruling: doors carry no From/To Room — association by 7×7 grid over the door box (+0.5 ft) with a 30 % hit threshold; first version (+1 ft, no threshold) credited corner doors to neighbours (FUNCTION ROOM 8 got 4 doors) — cost if wrong: door counts are medium confidence, stated per check.
G2: Ruling: S13 basis B (function rooms as place of public entertainment) failures are UNCLEAR (AP decides INP-12), basis A (office) failures are FAIL — follows AUD-S13 card ("Pass/Fail 附条件") — cost if wrong: none, both bases shown.
G2: Ruling: S15 decided N/A from an upper bound (sum of storey plan boxes 3,775 m² < 3,960 m²), not from rooms alone (lower bound 1,973 m²) — cost if wrong: if a floor plate extends beyond the room extents; G3 GFA re-checks.
G2: cross-task: 'Room 22/42/55' hold accessible WCs → S14 now classifies rooms by fixture evidence (--fixtures): 3 more reg 36 rooms, all without windows (F20).
G2: results — S13 office basis PASS on all floors; L1 fails: schedule lacks UFA/required columns, 6 unlevelled counters; S10: capacity rounding wrong for FUNCTION ROOM 7 (7 vs 8, both floors), claimed 900 mm doors are 850 mm clear, 2 exits claimed where 1 door modelled (FR1/FR2 G/F, FR5/FR6 1/F+2/F, GUARD ROOM); S11 arithmetic PASS, limits UNCLEAR; 12 stray doors at z −17 ft (A1).
G2: complete (test_room_use 13/13, test_s14 12/12, check_package all PASS; HTML viewed at 339 px, filters work).
G3: extract in audit-2026-10-13-g3/_raw: 68 Areas + property line from 6 get_element_data calls saved verbatim by the harness (mcp/*.json → parse_areas.py; no hand copying), 15 raster images, 8 sheets exported and read (table_values.tsv, 60 readings, each with confidence).
G3: Ruling: APP-151 item flags mapped to cap / no cap by matching the model's GFA DEDUCT flags to the C003 columns (2.2, 21 no cap; 2.3, 25 capped) — the sums reproduce the table to 3 dp — cost if wrong: a new flag (27) would show '?' until mapped.
G3: Ruling: one table reading (item 2.2 G/F, 250 vs 255) is medium confidence; decided by the table's own row total 288.999 — never by the model value.
G3: Ruling: missing table readings give UNCLEAR, not FAIL.
G3: results — GFA 3,944.120 − 425.039 = 3,519.081 by two independent model paths, equal to every table figure; capped 3.498 % ≤ 10 %; SC 41.531 %, PR 1.142 pass on both height bases; L1 fails: all 10 calculation tables are raster images, two unlabelled 0.180 m² accountable areas, UFA scheme empty, R/F compartment missing from C005, FRC HEIGHT 0, served façade typed, height basis 12.15 vs 17.35 m, no BEAM Plus target rating on any sheet (S07), ADM-2 App G missing.
G3: cross-task: A001 legend 'ELR = ELECTRIC ROOM', 'FR = FLAT' → S14 ELR rooms and roof FR excluded with the legend as reason (pending 9 → 1: GUARD ROOM).
G3: complete (test_area_scheme 10/10; all suites green; check_package all PASS).
G4: extract in audit-2026-10-13-g4/_raw: 53 placed views, per-view counts for 27 drawing views (query_model SpecificView, analysis only), view scales/templates, 16 title blocks + project info (verbatim), 9 colour regions sampled on sheet exports, rvt header (Format 2027), A006/A007 exports read.
G4: Ruling: readings apply only to the sheets actually read (A007 elevations 1–2 FAIL; A008 elevations 3–4 UNCLEAR) — caught before reporting — cost if wrong: none.
G4: Ruling: Revit version read from the .rvt BasicFileInfo text (local file, read-only) — closes GAP-04 for version where the harness can read the file.
G4: results — block plan site is light green 230,250,240 (not pink); coordinates table is an image but encloses exactly 3,082 m²; level heads 'SFL 17.25 m' (not X.XXX mPD) on sections/elevations; elevations show no street levels; compartment and UFA diagrams have 0 dimensions; no halftone on GFA/compartment diagrams; GFA and legend colours equal Table 1 exactly; door tags 8–11 of 26–30 per floor; 2 TR/F part plans without grids; title blocks: XX-XX-2018 dates, 'Author', address of another project, BIM ref R19 vs file 2027; 4 other .rvt files in the submission folder; no prescribed-window diagram.
G4: complete (test_drawings 7/7; check_package all PASS).
G5/G6: extract in audit-2026-10-13-g5/_raw: 19 levels, base / survey points, property-line box, drawing list (read from A001), schedule list.
G5/G6: results — 4 boundary coordinates equal the model corners converted with the base point to 0.001 m; drawing list matches all 16 sheets but is not a Sheet List schedule; Development Schedule GFA / SC / greenery / car park equal their sources; height 17.35 vs 12.15 m explained by levels [INFERENCE]; 7 levels whose name disagrees with the elevation (e.g. 'FFL 0.30 G/I' at 20.000 m); List of Modifications missing for the item 25 void; lift-shaft concessions not claimed (N/A).
G4: Ruling: V13 diagram search matched the S14 *schedule* name and passed — fixed to exclude schedules; test_window_schedule_is_not_a_diagram RED on the old code, GREEN on the fix.
G5: Ruling: A04 roll-up rows derived from group checks (first draft had model-specific text) — cost if wrong: none.
FULL: tools/common/build_results.py combines S14 + G2–G5 into audit-2026-10-13-full/audit-results.json: 36 tasks, 67 findings (1 Blocker, 29 Major, 37 Minor), 59 unclear, 11 MA items, 17 evidence (5 workbooks, 5 detailed reports, crops); render_report validation caught finding / input / A1 id formats and an applicability field — all fixed; bim/ap rendered exit 0; AP view 426 px no overflow, 17/17 assets 200.
FULL: complete (check_package all PASS incl. tools 13/13 and groups 4/4; tests: s14 12, room_use 13, area_scheme 10, drawings 8, lists_health 7, render 12 = 62 OK).
Final review: self-review (no subagent: harness policy is not to spawn agents unless the operator asks).
Final: minor (deferred): build_results.py has no unit test of its own (exercised end-to-end by the full run + render_report schema validation).
Final: minor (deferred): GEN-01 raster tables produce one finding per task (10) plus the A04 Blocker; could be merged into one cross-task finding.

## SKILLS（2026-10-13）
- Found: §9 pointers for 30 cards (A01–A04, V01–V14, S01–S09, S12, S17, S18) had gone into 30 extensionless files named `AUD-xxx*` (unexpanded shell glob), not into the cards. Earlier claim "§9 in all 36 cards" was wrong. Fixed: appended each into its card; every card now has exactly one §9.
- Added `work/model-audit/skills/` (6 SKILL.md: gbp-model-audit + G1–G5), README Skills section with install dirs (Claude Code / Cursor / Hermes).
- check_package: new `skills` file list + check_skills (frontmatter, name = folder, `<PKG>/` refs exist, cross-skill refs); AUD sections check now requires one §9 per card and no extensionless files. Current run: only FAIL = the 30 stray files, awaiting operator OK to delete.
- Ruling: skills hold no rules, only when-to-use, two-stage flow, commands and pointers — one source of truth in L1–L4 — cost if wrong: harness without file access to the package cannot run from the skill alone.

## CURSOR-REVIEW FIXES (2026-10-14)
- Cursor run (Desktop/Cursor Projects/HK GBP/model-audit, 2026-10-13 17:13–17:51) reviewed: S14 / G2 matched ours; G3 had 8 sheet values labelled "OCR" that are not on C001 (3000, 3516.591, 1245.930, 1.172, 12.18, 17.68, 21.016, 9) and ~20 table values copied from the model ("FILLED from model extract"); G4 skipped colour and sheet reading; 21 louvre panels extracted with kind '?'.
- Stray files: 30 extensionless `AUD-xxx*` files confirmed gone (operator OK'd deletion); check_package AUD sections 36/36 clean.
- New tools/common/readings.py: rejects model-derived / assumed readings; mismatch → FAIL only with a crop of the cell, else UNCLEAR; sheet judgements need a `finding`. New tools/common/crop_readings.py (box → crops/<key>.png).
- G3 / G5 use it; S05-HGT no longer hard-coded FAIL; missing height no longer crashes (Cursor's patch, re-done with a test).
- S14: panel kind must be H or L, else exit 2 (test_unknown_kind_stops RED→GREEN).
- G4: sample_colours.py works without regions (whole-sheet stats); analyser uses them for pink / Table 1, halftone stays UNCLEAR without regions (calibration: whole-sheet grey 21 % on C002 that has no halftone).
- Self-review found hard-coded sample-model verdicts in analysers (same class as Cursor's fabrication): S08-L2, S07-C4, S05-L2, S07-C6 (PASS without comparison), S12-FRC ("0 on all" — WRONG: model has 5000/3500/3500/3600 mm), V06-L4, A02-L3, A03-L4 (links never counted), V01-L5, V03/V04-L3, V01-L6-num (3082 hard-coded), S03-L1/L2/L3, MA-1.1/1.3/1.5/2.1/6.1, A04-L1/L2/L6, S18-C1. All now computed or read from readings with `finding`; missing → UNCLEAR.
- Our data: observation rows added after re-reading C001, C003, A001 exports (2026-10-14); height crops cut and viewed; OST_RvtLinks re-queried (0) → model_counts.json. rerun_full.sh re-runs everything: 66 findings (was 67) — only change is the false S12-FRC finding removed.
- Cursor data through the new code: S14 stops with the panel-kind error; G3/G4/G5 have 0 definite disagreements with ours (false verdicts → UNCLEAR with reasons); whole-sheet colours give V01-L3 FAIL, A02-L1/L2 PASS.
- Tests: s14 13, room_use 13, area_scheme 18, drawings 13, lists_health 10, render 12 = 79 OK; new tests seen failing on the old analysers (Cursor copy) first.
- Ruling: a match between a reading and the model may PASS without a crop (medium) — a mismatch may not FAIL without one — cost if wrong: a value silently copied from the model without a tag still passes; mitigated by the rejected-note rule and the operator gate.
- Ruling: default S14 / G2 room rules (ELR, GUARD ROOM, FUNCTION ROOM) stay sample-tuned and overridable (--rules) — cost if wrong: another project needs its own rules file.

## PER-TASK RUNS (2026-10-14)
- tools/common/tasks.py: --tasks on G2-G5 analysers; NEEDS per task (required / optional inputs); a task missing a required input gets one <task>-INPUT UNCLEAR and is not judged on empty data; optional gaps are named; output keeps only the chosen tasks; partial reports named GBP_<G>_<tasks>_...
- Fixed silent omissions found on the way: G3 GEN-01 judged PASS when rasters.tsv was absent; V11/V12 and V13-C1/C2 vanished without --g2 / --s14; G2 table-vs-model checks vanished without the schedule CSV; G5 S09/S17 verdict was hard-coded (now reading 'lift_shaft_concession', re-read on C003).
- build_results.py: --update <tasks JSON> merges into the group JSON (old kept as .prev.json), rebuilds the group report, then combines; --s14 optional; meta project / harness / Revit version from arguments and G4 A03-L3 (were hard-coded); AP decisions moved to --decisions JSON (sample's in audit-2026-10-13-full/decisions.json); exits 2 with a message when --update has no matching --group.
- Docs: AUD-000 §10.4 (rules), §10.3 tool paths corrected (tools/lists_health/), per-task tables in G2 §8, G3 §6, G4 §5, G5 §3, one line in 36 cards, RUN.md §6c + single-task prompt, skills.
- Tests: s14 13, room_use 19, area_scheme 21, drawings 16, lists_health 24, render 12, update 5 = 110 OK; new tests seen failing first. check_package all PASS.
- Real data: check_tasks_real.py — all 40 task runs equal the group runs; rerun_full.sh 66 findings / 59 unclear, no task change; --update demo on a copy changed no task.
- Ruling: S10 and S15 need fixtures (UFA / UFS exclude rooms with fitments) — cost if wrong: one extra extraction step for S10 alone.
- Ruling: V13 runs without S14 (diagram check) and names the two checks it cannot judge — cost if wrong: none; C1 / C2 appear once S14 is passed.
- Ruling: A04 alone still computes every G5 task (roll-up) and needs every input — cost if wrong: A04 is never cheap to run alone.
- Synced the package to the Cursor copy again (backup scratchpad/cursor-package-backup-20261014b).

## G2 EXTRACT SCRIPT (2026-10-14)
- New package tool tools/extract/g2_extract.py: turns MCP responses saved verbatim in _raw/mcp/ (rooms*, fixtures*, doors*, room_boundaries*, query_*) into rooms.tsv, fixtures.tsv, doors_all.tsv, room_polygons.json. Recognises revit-mcp and mcp-servers-for-revit response shapes; no project numbers (completeness from saved query_model ids); parameter names configurable; non-m² areas / non-mm widths converted from internal values; stops on unknown format, failed read, duplicate, missing / extra id, truncated query_model, fixture or door without a box.
- Verified: reproduces both Cursor S10 extractions byte for byte (revit-mcp run and mcp-servers-for-revit run). revit-mcp query_model shape ('Element Ids', analysis.totalElements) checked on the open model (read-only, 3 ids); that call exposed the truncation case, now a stop + test.
- R-G2 recipe rewritten (save verbatim, step 5 = this script, never hand-written converters); G2 spec, G2 skill, README, check_package updated. Tests: extract_g2 11 + others = 121 OK; check_package all PASS. Synced to the Cursor copy.
- Note: the script was written before its tests (new file); its tests were run after; the truncation check was test-first.

## EXTRACT SCRIPTS G1-G5 (2026-10-14)
- tools/extract/mcp_formats.py (shared): both MCP shapes, merge / order options, completeness from query_model ids, truncation and 'maxResults 0 on revit-mcp returns no ids' stops, unit conversion from internal values, Out object writes only after every check (a stopped run leaves nothing).
- g1_extract.py (S14): panel H / L from family + type names (fixes Cursor's '?'), walls / glass doors by configurable patterns, every panel box kept (no sampling), stale cw_/pn_ parts stop. Real data: Cursor 2026-10-13 revit-mcp dumps -> cw / pn / windows / doors identical to our extract cell for cell; S14 32 rooms same results; 2 openings formerly tied to stairs S-1 become unassigned because our 2026-10-13 room tops were wrong (no effect on assessed rooms).
- g3_extract.py: replaces parse_areas.py (now a wrapper; its hard-coded 'assert 68' gone); merges the same Area across files; --param-map for other templates. Real data: our areas.tsv / area_schemes.tsv byte-identical; Cursor's identical except row order; unplaced property line 1715 left out with a warning.
- g5_extract.py: levels / points / schedule list. New read-only revit-mcp calls on 2026-10-14 (saved in _agent/fixtures_real/g5_revit_mcp_20261014): levels.tsv and all_schedules.tsv byte-identical, points.tsv value-identical; G5 analysis 57 checks identical.
- g4_extract.py: sheets (JSON-string list handled), views on sheets, view properties (control-character type names -> 'Section (ARC_gbp)', custom scale), per-view counts from view_counts_<id>.json, link count. New read-only calls (fixtures_real/g4_revit_mcp_20261014): view_props.tsv byte-identical; views_on_sheets.tsv identical except 4 GBP schedules on C007 that today's get_views_on_sheets no longer lists (2026-10-13 extract had them with negative sheet y) - [GAP] model change or old extract error, not verified; 5 view counts identical.
- Found and fixed: R-S14 / R-G2 / R-G3 said 'maxResults 0' - on revit-mcp that returns NO ids (mcp-servers-for-revit: 0 = all); docs corrected, scripts stop with that explanation.
- Fixtures note: responses typed back from the conversation are semantically identical to the MCP output but \uXXXX escapes are decoded (not byte-verbatim); view_props.json control characters re-escaped by script.
- Docs: R-S14, R-G2, R-G3, R-G4, R-G5 rewritten to 'save verbatim -> run g*_extract.py'; skills G1-G5, README, check_package. Tests: 155 OK (extract g1 9, g2 11, g3 10, g4 8, g5 7 + earlier suites). Synced to the Cursor copy.
- Not automatable (stay sheet readings): G3 table values, G4 readings / coords, G5 drawing list. mcp-servers-for-revit lacks room boundaries, sheets, views-on-sheets and schedule-list tools: G4 / G5 extraction needs revit-mcp.
- Note: extract scripts were written before their unit tests; validation was against real data first, then tests; truncation and atomic-write checks were test-first.

## CURSOR FULL RUN 2026-10-14/15 REVIEW
- Cursor's first pass stopped after G1 at the gate; G1 reused 2026-10-13 dumps, merged doors.json from two runs and trimmed query_pn to 220 ids (live query had 436) - S14 results still equal ours (32 rooms, 24 pass). Operator decided not to add guards (high-density testing artefact).
- Second pass G2-G5 found three package bugs (all fixed test-first, RED seen on the old code):
  1. Schedule CSVs from mcp-servers-for-revit are tab-delimited; geom.read_schedule_csv assumed commas -> S13 counts 0 (15 false FAIL), S10 rows unmatched (27 false 'not listed'), S11 missing. Now the delimiter is read from the header line (geom.schedule_rows); S14 compare_schedule likewise.
  2. G5 car-park count used a comma-only regex -> UNCLEAR on tab exports; now uses schedule_rows.
  3. G4 V03/V04-L5 treated a reading 'not read' (confidence low) as read -> FAIL; now not read -> count / UNCLEAR.
- Cursor's data through the fixed code: G2 201 checks identical to ours. Remaining differences are Cursor's sheet judgements: S05-L2, S08-L2, S18-C1, A04-L6 marked PASS where the sheets do not meet the rule (class only, no App G, no modification list, a Development Schedule 'NIL' taken as the N/A table); V11 G/F read 442 while its own crop shows 445 (7 rows sum to 445); halftone UNCLEAR without regions (by design); 12 extra V10/V11 view checks (more views counted).
- Our rerun after the fixes: unchanged. Tests 162 OK; check_package all PASS; Cursor copy synced.

## READING EVIDENCE + REVIEW TABLE (2026-10-15)
- readings.observation: a PASS judgement ('it is on the sheet') needs a crop; a FAIL ('it is not there') must name the sheets looked at; otherwise UNCLEAR with readings.OBS_FIX as the fix. Applies to G3 appendices / BEAM rating / site class, G4 streets, G5 coordinates format / bearings / modification list / N/A table, and the G5 lift-shaft 'not claimed' reading.
- readings.listing -> out["readings"] in G3 / G4 / G5; tasks.print_summary prints 'Readings to check' (with / without crop) at the gate; task_report adds 'Sheet readings to check' (HTML with each crop embedded as base64, Excel sheet 'Readings').
- Tests first (G3 ObservationEvidence 4, G5 coords_format PASS without crop), RED on the old code, then GREEN; 166 tests OK; check_package PASS.
- Our data: two PASS judgements had no crop (coords_format on A001, lift_shaft_concession on C003) - boxes added, crops cut and viewed (both show what the finding says); rerun_full unchanged (66 findings).
- Cursor 2026-10-14 data through the new rules: S18-C1 (PASS while saying 'not seen') -> UNCLEAR. S05-L2, S08-L2, A04-L6 keep PASS because they carry crops - they are caught only by the operator looking at the crop in the review table (by design: the script cannot judge whether a crop meets the rule).
- Docs: L3 reading rules, G3 / G4 specs, RUN.md §6b, G3 / G4 / G5 skills. Synced to the Cursor copy.
