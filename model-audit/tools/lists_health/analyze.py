#!/usr/bin/env python3
"""G5 lists (AUD-S01 drawing list, S03 coordinates, S04 Development Schedule, S09 / S17 lift shaft, S18 modifications,
A04 submission roll-up) and G6 model health (AUD-A1, MA-1 to MA-7).  Read-only; works on the R-G5 extract plus
the analysis JSONs of the other groups.

Usage:
  python analyze.py --raw <g5 extract> --project <name> --model <path> --out <json>
                    --g2 <G2 json> --g3 <G3 json> --g4 <G4 json> --s14 <C14 json> --g3raw <g3 extract> --g4raw <g4 extract>
                    [--schedules <all_schedules.tsv>]
Stdlib only.
"""
import argparse
import datetime
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from geom import read_tsv, schedule_rows  # noqa: E402
import readings  # noqa: E402
import tasks as T  # noqa: E402

GROUP = ["AUD-S01", "AUD-S03", "AUD-S04", "AUD-S09", "AUD-S17", "AUD-S18", "AUD-A1", "AUD-A04"]
_X = "R-G5 step %s (L3-SOP/SOP-AUD-mcp-revit-mcp.md §10)"
INPUTS = {
    "levels.tsv": _X % 1, "points.tsv": _X % 1, "drawing_list.tsv": _X % 3, "schedule list": _X % 2 + " (--schedules)",
    "G3 table_values.tsv": "R-G3 step 6 (--g3raw)", "G3 rasters.tsv": "R-G3 step 5 (--g3raw)",
    "G4 readings.tsv": "R-G4 step 8 (--g4raw)", "G4 coords.tsv": "R-G4 step 8 (--g4raw)",
    "G4 rvt_info.json": "R-G4 step 7 (--g4raw)", "G2 parking schedule CSV": "R-G2 step 4 (export PARKING SCHEDULE)"}


def _I(n, req=True):
    return (n, req, INPUTS[n])


def _J(g, why):
    return ("%s analysis JSON" % g, True, "run %s first, pass --%s (%s)" % (g, g.lower(), why))


NEEDS = {
    "AUD-S01": [_I("drawing_list.tsv"), _J("G4", "title blocks"), _I("schedule list", False)],
    "AUD-S03": [_I("points.tsv"), _I("G4 coords.tsv"), _I("G4 readings.tsv", False)],
    "AUD-S04": [_J("G3", "GFA, SC, greenery"), _I("G3 table_values.tsv"), _I("points.tsv"), _I("levels.tsv", False),
                _I("G3 rasters.tsv", False), _I("G2 parking schedule CSV", False)],
    "AUD-S09": [_I("G3 table_values.tsv", False)], "AUD-S17": [_I("G3 table_values.tsv", False)],
    "AUD-S18": [_J("G3", "concessions"), _I("G4 readings.tsv", False), _I("schedule list", False)],
    "AUD-A1": [_I("points.tsv"), _I("levels.tsv"), _I("G4 rvt_info.json"), _I("G3 rasters.tsv"), _J("G2", "stray doors"),
               _J("G3", "site area"), _J("G4", "links, title blocks"), _J("S14", "room warnings"), _I("G4 coords.tsv", False)],
}
NEEDS["AUD-A04"] = sorted({n for v in NEEDS.values() for n in v})        # the roll-up needs every task of the group
TABLE_TASKS = {"coords": ["AUD-S03"], "levels": ["AUD-A1"], "rollup": ["AUD-A04"]}

FT = 0.3048


class Out:
    def __init__(self):
        self.checks, self.warnings = [], []

    def add(self, cid, task, item, obj, expected, actual, status, cite="", method="", confidence="high", evidence="",
            fix="", basis="", object_id=None):
        self.checks.append({"id": cid, "task": task, "item": item, "object": obj, "object_id": object_id,
                            "expected": expected, "actual": actual, "status": status, "cite": cite, "basis": basis,
                            "method": method, "confidence": confidence, "evidence": evidence, "fix": fix})


def jload(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def chk(d, cid):
    return next((c for c in d["checks"] if c["id"] == cid), None)


def main():
    ap = argparse.ArgumentParser()
    for k in ("raw", "project", "model", "out"):
        ap.add_argument("--" + k, required=True)
    for k in ("g2", "g3", "g4", "s14", "g3raw", "g4raw", "schedules"):
        ap.add_argument("--" + k)
    T.add_arg(ap)
    a = ap.parse_args()
    wanted = T.parse(a.tasks, GROUP)
    ex = lambda d, n: bool(d) and os.path.exists(os.path.join(d, n))
    jl = lambda p: jload(p) if p and os.path.exists(p) else None
    G2, G3, G4, S14 = jl(a.g2), jl(a.g3), jl(a.g4), jl(a.s14)
    pdir = os.path.join(os.path.dirname(os.path.abspath(a.g2)), "_raw") if a.g2 else None
    pcsv = [f for f in os.listdir(pdir) if "PARKING" in f] if pdir and os.path.isdir(pdir) else []
    have = {"levels.tsv": ex(a.raw, "levels.tsv"), "points.tsv": ex(a.raw, "points.tsv"),
            "drawing_list.tsv": ex(a.raw, "drawing_list.tsv"),
            "schedule list": bool(a.schedules and os.path.exists(a.schedules)),
            "G3 table_values.tsv": ex(a.g3raw, "table_values.tsv"), "G3 rasters.tsv": ex(a.g3raw, "rasters.tsv"),
            "G4 readings.tsv": ex(a.g4raw, "readings.tsv"), "G4 coords.tsv": ex(a.g4raw, "coords.tsv"),
            "G4 rvt_info.json": ex(a.g4raw, "rvt_info.json"), "G2 parking schedule CSV": bool(pcsv),
            "G2 analysis JSON": G2 is not None, "G3 analysis JSON": G3 is not None, "G4 analysis JSON": G4 is not None,
            "S14 analysis JSON": S14 is not None}
    gp = T.gaps(wanted, NEEDS, have)
    torun = set(GROUP) if "AUD-A04" in wanted and not T.blocked("AUD-A04", gp) else set(wanted)

    def run(task):
        return task in torun and not T.blocked(task, gp) and not T.gaps([task], NEEDS, have).get(task, {}).get("required")

    rd = lambda d, n: read_tsv(os.path.join(d, n)) if ex(d, n) else []
    levels, pts, dl = rd(a.raw, "levels.tsv"), rd(a.raw, "points.tsv"), rd(a.raw, "drawing_list.tsv")
    tv, rejected = readings.load(os.path.join(a.g3raw or "", "table_values.tsv"), a.g3raw or "")
    rd4 = {r["key"]: r for r in rd(a.g4raw, "readings.tsv")}
    coords = rd(a.g4raw, "coords.tsv")
    rasters = rd(a.g3raw, "rasters.tsv")
    scheds = read_tsv(a.schedules) if have["schedule list"] else []
    pbp = next((q for q in pts if q["kind"] == "Project Base Point"), None)
    E0 = N0 = None
    if pbp:
        E0, N0 = float(pbp["ew_mm"]) / 1000, float(pbp["ns_mm"]) / 1000
    O = Out()
    tables = {}

    # ------------------------------------------------------------ S01 drawing list
    if run('AUD-S01'):
        sheets = {r[0]: r[1] for r in G4["tables"]["titleblocks"]["rows"]}
        has_sheet_list = any("sheet list" in s["name"].lower() or "drawing list" in s["name"].lower() for s in scheds)
        O.add("S01-L1", "AUD-S01", "Drawing list is a model sheet-list schedule (GEN-01)", "A001 drawing list",
              "Sheet List schedule", "no sheet-list schedule in the model (%d schedules)" % len(scheds) if scheds else "not checked",
              "FAIL" if scheds and not has_sheet_list else "UNCLEAR", cite="BIMGBPS §5.3.1; §4.2(b)",
              method="get_all_schedules", fix="Replace the pictured list with a Sheet List schedule")
        for r in dl:
            m = sheets.get(r["number"])
            st = "PASS" if m and m.strip().upper() == r["title"].strip().upper() else "FAIL"
            O.add("S01-L2-%s" % r["number"], "AUD-S01", "List row equals the model sheet", r["number"], m or "(no sheet)",
                  r["title"], st, cite="BIMGBPS §5.3.1 (GEN-06)", method="list read from A001 vs title blocks")
        for n_, t in sheets.items():
            if n_ not in {r["number"] for r in dl}:
                O.add("S01-L2-miss-%s" % n_, "AUD-S01", "Every sheet is in the list", n_, "listed", "missing", "FAIL")

    # ------------------------------------------------------------ S03 coordinates
    if run('AUD-S03'):
        x0, y0 = float(pbp["x_ft"]), float(pbp["y_ft"])
        pl_min = next(p for p in pts if p["kind"] == "Property Line bbox min")
        pl_max = next(p for p in pts if p["kind"] == "Property Line bbox max")
        corners = {"A": (float(pl_min["x_ft"]), float(pl_max["y_ft"])), "B": (float(pl_max["x_ft"]), float(pl_max["y_ft"])),
                   "C": (float(pl_max["x_ft"]), float(pl_min["y_ft"])), "D": (float(pl_min["x_ft"]), float(pl_min["y_ft"]))}
        rows = []
        for c in coords:
            x, y = corners[c["point"]]
            e = E0 + (x - x0) * FT
            n = N0 + (y - y0) * FT
            de, dn = e - float(c["E_m"]), n - float(c["N_m"])
            ok = abs(de) < 0.0015 and abs(dn) < 0.0015
            rows.append([c["point"], c["E_m"], c["N_m"], round(e, 3), round(n, 3), round(de, 4), round(dn, 4), "PASS" if ok else "FAIL"])
            O.add("S03-L4-%s" % c["point"], "AUD-S03", "Tabulated coordinate equals the model boundary corner", "point " + c["point"],
                  "%.3f, %.3f" % (e, n), "%s, %s" % (c["E_m"], c["N_m"]), "PASS" if ok else "FAIL",
                  cite="BIMGBPS §5.3.3 (GEN-06)", method="property-line corner converted with the project base point "
                  "(E %.3f, N %.3f, angle %s°)" % (E0, N0, pbp["angle_true_north"]), confidence="medium",
                  evidence="corner taken from the property-line box (rectangular site)")
        tables["coords"] = {"title": "Boundary coordinates: table vs model", "columns": [
            "Point", "Table E", "Table N", "Model E", "Model N", "ΔE (m)", "ΔN (m)", "Status"], "rows": rows}
        ctv = rd4.get("coords_table", {}).get("value", "not read")
        O.add("S03-L1", "AUD-S03", "Coordinates table generated from the model (GEN-01)", "A001", "model-generated",
              ctv, "FAIL" if "raster" in ctv.lower() else "UNCLEAR", cite="BIMGBPS §4.2(b)",
              fix="Use spot coordinates or a schedule driven by the boundary")
        st, txt, cf = readings.observation(rd4, "coords_format", a.g4raw)
        O.add("S03-L2", "AUD-S03", "HK1980 grid, 3 decimals", "A001", "HK1980, 0.001 m", txt, st, cite="LIM-03", confidence=cf,
              method="sheet export read (readings key 'coords_format')",
              fix={"PASS": "", "FAIL": "Give the coordinates in HK1980 to 3 decimals",
                   "UNCLEAR": readings.obs_fix(rd4, "coords_format", a.g4raw, "Read the coordinates table; record key 'coords_format' with a finding")}[st])
        sides = []
        if len(coords) >= 3:
            for i, p in enumerate(coords):
                q = coords[(i + 1) % len(coords)]
                sides.append("%s–%s %.3f m" % (p["point"], q["point"], math.hypot(float(q["E_m"]) - float(p["E_m"]),
                                                                                float(q["N_m"]) - float(p["N_m"]))))
        st, txt, cf = readings.observation(rd4, "coords_bearings", a.g4raw)
        O.add("S03-L3", "AUD-S03", "Bearings and distances given", "A001", "bearing and length per side", txt, st,
              cite="BIMGBPS §5.3.3 ('with bearings and distances')", confidence=cf,
              method="sheet export read (readings key 'coords_bearings')",
              fix={"PASS": "", "FAIL": "Add each side with its bearing: " + ", ".join(sides),
                   "UNCLEAR": readings.obs_fix(rd4, "coords_bearings", a.g4raw, "Read the coordinates table; record key 'coords_bearings' with a finding")}[st])
        O.add("S03-C1", "AUD-S03", "Coordinates agree with the survey / lease plan", "site", "INP-01", "not available", "UNCLEAR")

    # ------------------------------------------------------------ S04 Development Schedule
    if run('AUD-S04'):
        acc = G3["summary"]["gfa"]["accountable"]
        green = chk(G3, "V14-C1")
        ds = sorted(r["name"] for r in rasters if "development schedule" in r["name"].lower())
        O.add("S04-L1", "AUD-S04", "Development Schedule generated from the model (GEN-01)", "C001",
              "model-generated", "raster image: " + "; ".join(ds) if ds else "no raster named 'Development Schedule'",
              "FAIL" if ds else "UNCLEAR", cite="BIMGBPS §4.2(b)",
              fix="Rebuild the Development Schedule from model values (Function B)" if ds else "Check how the schedule is made")
        sc_chk = chk(G3, "S05-T-sc")
        num = lambda s: float(re.search(r"-?[\d.]+", str(s)).group()) if s is not None and re.search(r"[\d.]", str(s)) else None
        for key, item, model, fmt in (("gfa", "Gross floor area", acc, "%.3f"),
                                      ("sc_pct", "Site coverage", num(sc_chk["expected"]) if sc_chk else None, "%.3f"),
                                      ("greenery_devsched", "Greenery requirement", num(green["actual"]) if green else None, "%.3f")):
            r = tv.get(key)
            t = num(r["value"]) if r else None
            st = "UNCLEAR" if model is None or t is None else readings.status(abs(model - t) < 0.006, r)
            O.add("S04-L2-%s" % key, "AUD-S04", "Development Schedule entry equals its source", item,
                  fmt % model if model is not None else None, r["value"] if r else "(not read)", st,
                  cite="BIMGBPS §5.3.4 (GEN-06)", method="G3 model values vs the value read from C001",
                  confidence=readings.confidence(r), fix={"PASS": "", "FAIL": "Correct the Development Schedule entry",
                                                          "UNCLEAR": readings.CROP_FIX if t is not None else
                                                          "Read this value from the sheet into table_values.tsv"}[st])
        park = None
        if pcsv:
            for row in schedule_rows(os.path.join(pdir, pcsv[0])):
                if row and row[0].strip().lower() == "grand total":
                    vals = [c for c in row[1:] if c.strip()]
                    park = int(float(vals[-1])) if vals and re.match(r"^\d+(\.0+)?$", vals[-1].strip()) else None
        r = tv.get("carpark")
        t = int(num(r["value"])) if r and num(r["value"]) is not None else None
        st = "UNCLEAR" if park is None or t is None else readings.status(park == t, r)
        O.add("S04-L2-carpark", "AUD-S04", "Development Schedule entry equals its source", "Car park", park,
              r["value"] if r else "(not read)", st, cite="BIMGBPS §5.3.4 (GEN-06)", confidence=readings.confidence(r),
              method="PARKING SCHEDULE grand total vs the value read from C001",
              fix={"PASS": "", "FAIL": "Correct the car park entry", "UNCLEAR": readings.CROP_FIX if t is not None else
                   "Read the car park entry and export the PARKING SCHEDULE"}[st])
        lv = {r["name"]: float(r["elevation_mm"]) / 1000 for r in levels}
        msl = next((v for k, v in lv.items() if "MEAN STREET" in k.upper()), None)
        h1, h2 = tv.get("height_c001"), tv.get("height_devsched")
        v1, v2 = (num(h1["value"]) if h1 else None), (num(h2["value"]) if h2 else None)
        expl = []
        if msl is not None and v1 is not None and v2 is not None:
            for v, label in ((v1, "C001"), (v2, "Development Schedule")):
                near = min(lv.items(), key=lambda kv: abs(kv[1] - msl - v))
                if abs(near[1] - msl - v) < 0.06:
                    expl.append("%s %.2f m ≈ level '%s' − mean street level" % (label, v, near[0]))
                near = min(lv.items(), key=lambda kv: abs(kv[1] - float(pbp["elev_mm"]) / 1000 - v))
                if abs(near[1] - float(pbp["elev_mm"]) / 1000 - v) < 0.06:
                    expl.append("%s %.2f m ≈ level '%s' − project base point" % (label, v, near[0]))
        st = "UNCLEAR" if v1 is None or v2 is None else readings.status(abs(v1 - v2) < 0.005, h1, h2)
        O.add("S04-L3", "AUD-S04", "Height column uses the same basis as the C001 calculation", "Development Schedule",
              "%s m (C001)" % (h1["value"] if h1 else "(not read)"), "%s m" % (h2["value"] if h2 else "(not read)"), st,
              basis="Major" if st == "FAIL" else "", cite="Cap. 123F reg 23(1) (LIM-13); INP-11", method="levels in the model",
              confidence="medium", evidence=("[INFERENCE] " + "; ".join(expl)) if expl else "",
              fix={"PASS": "", "FAIL": "AP to fix one height basis: from the mean street level to the main roof (reg 23(1))",
                   "UNCLEAR": "Read both heights, with crops, into table_values.tsv"}[st])
        if rejected:
            O.warnings.append(readings.warning(rejected))

    # ------------------------------------------------------------ S09 / S17 lift shaft, S18 modifications
    for task in ("AUD-S09", "AUD-S17"):
        if not run(task):
            continue
        r = tv.get("lift_shaft_concession")
        claimed = (r.get("finding") or "").strip().upper() if r else ""
        if claimed == "PASS" and not readings.has_crop(r, a.g3raw):
            claimed = ""                                                   # 'not claimed' must be shown by a crop
        st = {"PASS": "N/A", "FAIL": "UNCLEAR"}.get(claimed, "UNCLEAR")
        O.add("%s-APL" % task[4:], task, "Lift-shaft concession (APP-89) claimed", "C003 items 18 and 34", "claimed",
              (r["value"] + " (%s)" % r["sheet"]) if r else "not read", st, cite="PNAP APP-89 (APL-05)",
              basis="conditional" if st == "N/A" else "", method="C003 concession table read (table_values key "
              "'lift_shaft_concession': finding PASS = not claimed, FAIL = claimed)",
              fix={"N/A": "State N/A with the APL-05 reason on the drawings",
                   "UNCLEAR": "Read C003 items 18 and 34; record 'lift_shaft_concession'" if not claimed else
                   "Concession claimed: check the lift-shaft GFA (AUD-S09 / S17 L2)"}[st])
    item25 = next((r for r in G3["tables"]["concessions"]["rows"] if r[0] == "25"), None) if run("AUD-S18") else None
    if item25:
        in_model = [s["name"] for s in scheds if "modification" in s["name"].lower()]
        st, txt, cf = readings.observation(rd4, "modification_list", a.g4raw)
        if in_model:
            st, txt = "PASS", "schedule in the model: " + ", ".join(in_model)
        O.add("S18-C1", "AUD-S18", "Every item needing a modification is in the List of Modifications",
              "item 25 %s (%s m², %s)" % (item25[5] if len(item25) > 5 else "", item25[4], item25[2]), "listed (Form BA16)",
              txt, st, basis="Missing" if st == "FAIL" else "", confidence=cf,
              cite="Cap. 123F reg 23(3)(a); PNAP ADM-2 Appendix E (APL-07)",
              method="schedules in the model + sheet read (readings key 'modification_list')",
              fix={"PASS": "", "FAIL": "Add the List of Modifications (ADV-33 Appendix A3 Table 1), or withdraw the item 25 "
                   "concession (INP-13)", "UNCLEAR": readings.obs_fix(
                       rd4, "modification_list", a.g4raw, "Look for a List of Modifications on the sheets; record "
                       "'modification_list' with a finding")}[st])

    # ------------------------------------------------------------ G6 A1 model health
    if run('AUD-A1'):
        rvt = jload(os.path.join(a.g4raw, "rvt_info.json"))
        fmt_ok = str(rvt.get("format", "")).isdigit()
        O.add("MA-1.1", "AUD-A1", "Revit version recorded", rvt.get("file", "model"), "readable",
              "Format %s, build %s" % (rvt.get("format"), rvt.get("build")), "PASS" if fmt_ok else "UNCLEAR",
              method="rvt_info.py", basis="" if fmt_ok else "GAP-04")
        size = rvt.get("size_mb")
        O.add("MA-1.3", "AUD-A1", "File size ≤ 500 MB", rvt.get("file", "model"), "≤ 500 MB",
              "%.2f MB" % size if size is not None else "not read",
              "UNCLEAR" if size is None else ("PASS" if size <= 500 else "FAIL"), method="rvt_info.py")
        lk = chk(G4, "A03-L4")
        O.add("MA-1.5", "AUD-A1", "No Revit links", "model", "0", lk["actual"] if lk else "not counted",
              lk["status"] if lk else "UNCLEAR", evidence="CAD imports: GAP-03", method="G4 A03-L4")
        hk = 800000 <= E0 <= 870000 and 800000 <= N0 <= 850000
        O.add("MA-2.1", "AUD-A1", "Shared coordinates set to HK1980", "Project Base Point",
              "E / N in HK1980 (E 800,000–870,000, N 800,000–850,000)",
              "E %.3f, N %.3f, angle %s°, elevation %s mm" % (E0, N0, pbp["angle_true_north"], pbp["elev_mm"]),
              "PASS" if hk else "FAIL", method="base point parameters",
              fix="" if hk else "Set the project / survey base point to HK1980 grid coordinates")
        bad = []
        for r in levels:
            m = re.search(r"(?:SFL|FFL)\s*(-?\d+(?:\.\d+)?)", r["name"])
            if not m:
                continue
            named = float(m.group(1))
            actual = float(r["elevation_mm"]) / 1000
            if abs(named - actual) > 0.0005:
                bad.append((r, named, actual))
        for r, named, actual in bad:
            O.add("MA-4.6-%s" % r["id"], "AUD-A1", "Level name agrees with its elevation", r["name"], "%.3f m" % named,
                  "%.3f m" % actual, "FAIL", basis="Major" if r["building_story"] == "1" else "Minor", object_id=int(r["id"]),
                  cite="BIMGBPS §4.2(e); GEN-04", method="Level Elevation parameter",
                  fix="Rename the level or correct its elevation; delete it if unused")
        tables["levels"] = {"title": "Levels", "columns": ["ID", "Name", "Type", "Elevation (m)", "Building storey", "Name agrees"],
                            "rows": [[int(r["id"]), r["name"], r["type"], float(r["elevation_mm"]) / 1000, r["building_story"],
                                      "no" if any(b[0] is r for b in bad) else ""] for r in levels]}
        O.add("MA-3.1", "AUD-A1", "No pictured tables (manual input)", "model", "0 raster tables", "%d raster images" % len(rasters),
              "FAIL" if rasters else "PASS", cite="BIMGBPS §5.1.2")
        s2 = next((w for w in S14["summary"]["data_quality_warnings"] if "implausible" in w), None)
        if s2:
            O.add("MA-4.4", "AUD-A1", "Room areas plausible for their names", "rooms (S14 warning)", "sized for the name", s2[:120],
                  "FAIL", basis="Minor", fix="Rename the roof room or split it")
        stray = chk(G2, "A1-DOORS-OFF")
        if stray:
            O.add("MA-5.2", "AUD-A1", stray["item"], stray["object"], stray["expected"], stray["actual"], stray["status"],
                  basis="Minor", evidence=stray["evidence"], fix=stray["fix"])
        nl = [c for c in G2["checks"] if c["id"].startswith("S13-L4")]
        if nl:
            O.add("MA-5.3", "AUD-A1", "Every model element has a level", "plumbing fixtures", "level set",
                  "%d unlevelled counters" % len(nl), "FAIL", basis="Minor", fix=nl[0]["fix"])
        site_m = next((c["expected"] for c in G3["checks"] if c["id"].startswith("S02-L2-")), None)
        poly = None
        if len(coords) >= 3:
            xy = [(float(r["E_m"]), float(r["N_m"])) for r in coords]
            poly = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(xy, xy[1:] + xy[:1]))) / 2
        st = "UNCLEAR" if site_m is None or poly is None else ("PASS" if abs(site_m - poly) < 0.5 else "FAIL")
        O.add("MA-6.1", "AUD-A1", "Property line closed and equal to the site area", "Property Line",
              "%.3f m² (property line)" % site_m if site_m is not None else "property line area",
              "%.3f m² enclosed by the boundary coordinates" % poly if poly is not None else "coordinates not read", st,
              method="G3 property-line Area vs shoelace area of the coordinates (coords.tsv)",
              fix={"PASS": "", "FAIL": "Make the property line and the boundary coordinates agree",
                   "UNCLEAR": "Read the boundary coordinates into coords.tsv"}[st])
        tbc = chk(G4, "A01-L1")
        if tbc:
            O.add("MA-7.1", "AUD-A1", tbc["item"], tbc["object"], tbc["expected"], tbc["actual"], tbc["status"])

    # ------------------------------------------------------------ A04 roll-up
    if run('AUD-A04'):
        allc = G2["checks"] + G3["checks"] + G4["checks"] + O.checks
        per = {}
        for c in allc:
            p = per.setdefault(c["task"], {"PASS": 0, "FAIL": 0, "UNCLEAR": 0, "N/A": 0})
            p[c["status"]] = p.get(c["status"], 0) + 1
        s14 = S14["summary"]
        per["AUD-S14"] = {"PASS": s14["both_pass_count"], "FAIL": s14["rooms_included_count"] - s14["both_pass_count"],
                          "UNCLEAR": s14["rooms_pending_count"], "N/A": 0}
        fails = sorted(t for t, p in per.items() if p["FAIL"])
        cap = [c for c in (chk(G4, "A03-L3"), next((c for c in O.checks if c["id"] == "MA-1.3"), None)) if c]
        cs = [c["status"] for c in cap]
        O.add("A04-L1", "AUD-A04", "Capacity and format", "file", "A03-L3 and MA-1.3 pass", ", ".join(
            "%s %s" % (c["id"], c["status"]) for c in cap) or "not checked",
              "FAIL" if "FAIL" in cs else ("PASS" if cs and all(s == "PASS" for s in cs) else "UNCLEAR"))
        O.add("A04-L2", "AUD-A04", "No typed figures (§5.1.2)", "drawings", "0 pictured tables", "%d raster tables" % len(rasters),
              "FAIL" if rasters else "PASS", basis="Blocker" if rasters else "", cite="BIMGBPS §5.1.2",
              fix="Rebuild every calculation table from the model" if rasters else "")
        l3 = [c for c in allc if c["status"] == "FAIL" and (c["id"] in ("V11-L2", "V10-L4", "V08-L4") or c["id"].startswith("V10-L5"))]
        O.add("A04-L3", "AUD-A04", "Areas checkable (§4.2(e)(f))", "area schemes", "UFA areas, halftone, labels",
              "; ".join("%s %s" % (c["id"], c["item"]) for c in l3) or "no defect found", "FAIL" if l3 else "PASS",
              basis="Major", evidence="from G3 / G4 checks")
        miss = lambda prefix: [c for c in allc if c["task"].startswith(prefix) and c.get("basis") == "Missing" and c["status"] == "FAIL"]
        mv, ms = miss("AUD-V"), miss("AUD-S")
        pics = [c for c in allc if c["id"].endswith("GEN01") and c["status"] == "FAIL" and c["task"].startswith("AUD-S")]
        O.add("A04-L4", "AUD-A04", "Applicable views present", "view tasks", "no Missing",
              "; ".join("%s: %s" % (c["task"], c["item"]) for c in mv) or "none missing", "FAIL" if mv else "PASS", basis="Major")
        O.add("A04-L5", "AUD-A04", "Applicable schedules present and model-generated", "schedule tasks", "no Missing, no pictures",
              "%d missing (%s); %d pictured tables" % (len(ms), ", ".join(c["task"] for c in ms), len(pics)),
              "FAIL" if ms or pics else "PASS", basis="Major")
        na = [c for c in allc if c["status"] == "N/A"]
        st, txt, cf = readings.observation(rd4, "na_table", a.g4raw)
        O.add("A04-L6", "AUD-A04", "N/A table with reasons on the drawings", "%d N/A items" % len(na), "N/A + reason table",
              txt, st if na else "N/A", basis="Partial" if st == "FAIL" and na else "", confidence=cf,
              evidence=", ".join(sorted({c["task"] for c in na})), method="sheet read (readings key 'na_table')",
              fix={"PASS": "", "FAIL": "Add an N/A and reasons table (templates/na-table-template.md) to A001",
                   "UNCLEAR": readings.obs_fix(rd4, "na_table", a.g4raw, "Look for an N/A table on the sheets; record 'na_table' with a finding")}[st] if na else "")
        tables["rollup"] = {"title": "Task roll-up (all groups)", "columns": ["Task", "PASS", "FAIL", "UNCLEAR", "N/A"],
                            "rows": [[t, p["PASS"], p["FAIL"], p["UNCLEAR"], p["N/A"]] for t, p in sorted(per.items())]}

    O.warnings += ["A04 is a roll-up of G2, G3, G4, S14 and this group; it adds no measurement of its own.",
                   "Boundary corners are taken from the property-line bounding box: valid because the site is a rectangle "
                   "(coordinates enclose exactly the property-line area)."]
    out = {"project_info": {"project_name": a.project, "model_path": a.model, "group": "G5 lists and G6 model health",
                            "tasks": list(GROUP), "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "read_only": True, "rules": {"Lists": "BIMGBPS §5.3.1, 5.3.3, 5.3.4, 5.3.9, 5.3.17, 5.3.18",
                                                         "Model health": "BIMGBPS §4.2, §4.3 (Roadmap MA-1 to MA-7)"}},
           "checks": O.checks, "tables": tables,
           "summary": {"data_quality_warnings": O.warnings}}
    if "rollup" in tables:
        out["summary"]["tasks_with_fail"] = sorted(r[0] for r in tables["rollup"]["rows"] if r[2])
    out["readings"] = readings.listing(rd4, a.g4raw) + readings.listing(
        tv, a.g3raw, keys={"gfa", "sc_pct", "greenery_devsched", "carpark", "height_c001", "height_devsched",
                           "lift_shaft_concession"})
    T.finish(out, wanted, GROUP, gp, TABLE_TASKS)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    T.print_summary(out, "G5 / G6 lists and model health")
    if out["summary"].get("tasks_with_fail"):
        print("Tasks with at least one FAIL (all groups): %s" % ", ".join(out["summary"]["tasks_with_fail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
