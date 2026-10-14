#!/usr/bin/env python3
"""G4 drawing-presentation group: AUD-V01 block plan, V02 floor plans, V03 sections, V04 elevations, V05 details,
V13 prescribed windows, A01 sheet assembly, A02 colour coding, A03 export / file; plus the drawing checks of
V08 / V10 / V11 (dimensions, grids, halftone).  Read-only; works only on the R-G4 extract.

Usage:
  python analyze.py --raw <extract dir> --project <name> --model <path> --out <json> [--s14 <C14 analysis json>]
Extract: views_on_sheets.tsv, view_props.tsv, view_counts.json, mcp/titleblocks.json (verbatim), colour_samples.json
(sample_colours.py), rvt_info.json (rvt_info.py), rasters.tsv, coords.tsv, readings.tsv.  Stdlib only.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from geom import read_tsv  # noqa: E402
import readings  # noqa: E402
import tasks as T  # noqa: E402

GROUP = ["AUD-V01", "AUD-V02", "AUD-V03", "AUD-V04", "AUD-V05", "AUD-V08", "AUD-V10", "AUD-V11", "AUD-V13",
         "AUD-A01", "AUD-A02", "AUD-A03"]
_X = "R-G4 step %s (L3-SOP/SOP-AUD-mcp-revit-mcp.md §10)"
_V = ("views (views_on_sheets.tsv, view_counts.json, view_props.tsv)", True, _X % "1-3")
_RD = ("readings.tsv", False, _X % 8 + " - sheet readings")
_CO = ("colour_samples.json", False, _X % "5-6")
NEEDS = {
    "AUD-V01": [_V, _CO, _RD, ("coords.tsv", False, _X % 8), ("G3 analysis JSON", False, "run G3 first, pass --g3")],
    "AUD-V02": [_V, _RD], "AUD-V03": [_V, _RD], "AUD-V04": [_V, _RD], "AUD-V05": [_V],
    "AUD-V08": [_V, _CO], "AUD-V10": [_V, _CO], "AUD-V11": [_V],
    "AUD-V13": [_V, ("S14 analysis JSON", False, "run G1 (S14) first, pass --s14 - glass / openable checks")],
    "AUD-A01": [_V, ("mcp/titleblocks.json", True, _X % 4)],
    "AUD-A02": [_V, ("colour_samples.json", False, _X % "5-6")],
    "AUD-A03": [("rvt_info.json", True, _X % 7), ("model_counts.json", False, _X % 4 + " - Revit link count"),
                ("rasters.tsv", False, "R-G3 step 5 - picture tables")],
}
TABLE_TASKS = {"views": ["AUD-V01", "AUD-V02", "AUD-V03", "AUD-V04", "AUD-V05", "AUD-V08", "AUD-V10", "AUD-V11"],
               "colours": ["AUD-V01", "AUD-V08", "AUD-V10", "AUD-A02"], "titleblocks": ["AUD-A01"]}

BIMGBPS = "BIMGBPS"


class Out:
    def __init__(self):
        self.checks, self.warnings = [], []

    def add(self, cid, task, item, obj, expected, actual, status, cite="", method="", confidence="high", evidence="",
            fix="", basis="", object_id=None):
        self.checks.append({"id": cid, "task": task, "item": item, "object": obj, "object_id": object_id,
                            "expected": expected, "actual": actual, "status": status, "cite": cite, "basis": basis,
                            "method": method, "confidence": confidence, "evidence": evidence, "fix": fix})


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def params(v):
    P = {}
    for p in v["InstanceParameters"]:
        P.setdefault(p["name"], p.get("displayValue", p.get("value")))
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--s14", help="S14 analysis JSON (V13 calculations)")
    ap.add_argument("--g3", help="G3 analysis JSON (property-line area for V01)")
    T.add_arg(ap)
    a = ap.parse_args()
    wanted = T.parse(a.tasks, GROUP)
    R = lambda n: os.path.join(a.raw, n)
    ex = lambda n: os.path.exists(R(n))
    views_ok = all(ex(n) for n in ("views_on_sheets.tsv", "view_counts.json", "view_props.tsv"))
    have = {_V[0]: views_ok, "readings.tsv": ex("readings.tsv"), "colour_samples.json": ex("colour_samples.json"),
            "coords.tsv": ex("coords.tsv"), "G3 analysis JSON": bool(a.g3 and os.path.exists(a.g3)),
            "S14 analysis JSON": bool(a.s14 and os.path.exists(a.s14)), "mcp/titleblocks.json": ex("mcp/titleblocks.json"),
            "rvt_info.json": ex("rvt_info.json"), "model_counts.json": ex("model_counts.json"), "rasters.tsv": ex("rasters.tsv")}
    gp = T.gaps(wanted, NEEDS, have)
    vos = read_tsv(R("views_on_sheets.tsv")) if views_ok else []
    counts = {k: v for k, v in load_json(R("view_counts.json"), {}).items() if not k.startswith("_")} if views_ok else {}
    props = {r["view_id"]: r for r in read_tsv(R("view_props.tsv"))} if views_ok else {}
    tb = load_json(R("mcp/titleblocks.json"), {"results": {}})["results"]
    col = load_json(R("colour_samples.json"), {})
    rvt = load_json(R("rvt_info.json"), {})
    rasters = read_tsv(R("rasters.tsv")) if os.path.exists(R("rasters.tsv")) else []
    coords = read_tsv(R("coords.tsv")) if os.path.exists(R("coords.tsv")) else []
    rd = {r["key"]: r for r in read_tsv(R("readings.tsv"))} if os.path.exists(R("readings.tsv")) else {}
    s14 = load_json(a.s14) if a.s14 else None
    O = Out()
    n = lambda vid, cat: counts.get(str(vid), {}).get(cat, 0)
    vname = {r["view_id"]: "%s %s (%s)" % (r["sheet"], r["view_name"], r["view_type"]) for r in vos}

    # ------------------------------------------------------------ V01 block plan
    bp = next((r for r in vos if r["view_type"] == "AreaPlan" and props.get(r["view_id"], {}).get("view_type_name") == "Block plan"), None)
    if bp:
        sc = props[bp["view_id"]]["scale"]
        O.add("V01-L1", "AUD-V01", "Block plan scale not smaller than 1:500", vname[bp["view_id"]], "≤ 1:500", "1:%s" % sc,
              "PASS" if sc.isdigit() and int(sc) <= 500 else "FAIL", cite="%s §5.2.1" % BIMGBPS, method="View Scale")
    if len(coords) >= 3:
        xs = [float(c["E_m"]) for c in coords]
        ys = [float(c["N_m"]) for c in coords]
        area = 0.0
        for i in range(len(coords)):
            j = (i + 1) % len(coords)
            area += xs[i] * ys[j] - xs[j] * ys[i]
        area = abs(area) / 2
        site = None
        if a.g3 and os.path.exists(a.g3):
            g3 = load_json(a.g3, {})
            site = next((c["expected"] for c in g3.get("checks", []) if c["id"].startswith("S02-L2-")), None)
        O.add("V01-L6-num", "AUD-V01", "Boundary coordinates enclose the site area", "A001 coordinates table",
              "%.3f m² (property line, G3)" % site if site is not None else "property line area (needs --g3)",
              "%.3f m²" % area, "UNCLEAR" if site is None else ("PASS" if abs(area - site) < 0.5 else "FAIL"),
              cite="%s §5.2.1(e)" % BIMGBPS, method="shoelace area of the tabulated points", evidence="points " +
              "; ".join("%s %s, %s" % (c["point"], c["E_m"], c["N_m"]) for c in coords))
    ct = rd.get("coords_table")
    O.add("V01-L6", "AUD-V01", "Coordinates table generated from the model (GEN-01)", "A001 coordinates table",
          "model-generated", ct["value"] if ct else "not read", "FAIL" if ct and "raster" in ct["value"] else "UNCLEAR",
          cite="%s §4.2(b), §5.2.1(e)" % BIMGBPS, method="sheet export read; Raster Images on A001",
          fix="Use survey points / spot coordinates or a schedule instead of a picture")
    s = col.get("block_plan_site")
    if s:
        top = s["top"][0][0]
        O.add("V01-L3", "AUD-V01", "Site shaded pink", "A001 block plan site", "RGB 255,218,236 (DK-AUD-004 §2)",
              "dominant fill RGB %s; pink pixels %d" % (",".join(map(str, top)), s["pink"]),
              "PASS" if s["pink"] > 0.2 * s["pixels"] else "FAIL", cite="%s §5.2.1(b)" % BIMGBPS,
              method="pixel sampling of the exported sheet (AGENT-IMAGE-SAMPLE)", evidence="region %s" % s["box"],
              fix="Change the block-plan site fill to pink 255,218,236 in BD_gbp_block plan")
    elif col.get("sheet_A001"):
        sa = col["sheet_A001"]
        O.add("V01-L3", "AUD-V01", "Site shaded pink", "A001 (whole sheet)", "RGB 255,218,236 (DK-AUD-004 §2)",
              "pink pixels on the whole sheet: %d" % sa["pink"], "FAIL" if not sa["pink"] else "UNCLEAR",
              cite="%s §5.2.1(b)" % BIMGBPS, method="whole-sheet pixel count (no region boxes)",
              fix="Change the block-plan site fill to pink 255,218,236" if not sa["pink"] else
              "Pink is on the sheet: give the site a region box (regions.json) to measure its share")
    for key, cid, item, cite, ok_status in (("lot_no", "V01-L4", "Lot number shown", "§5.2.1(c)", "PASS"),
                                            ("access_points", "V01-L7", "Vehicular access shown", "§5.2.1(f)", "PASS"),
                                            ("north", "V01-L9", "North point shown", "§5.2.1(h)", "PASS")):
        if key in rd:
            O.add(cid, "AUD-V01", item, "A001 block plan", "shown", rd[key]["value"], ok_status,
                  cite="%s %s" % (BIMGBPS, cite), method="sheet export read")
    if "streets" in rd:
        st, txt, cf = readings.observation(rd, "streets", a.raw)
        O.add("V01-L5", "AUD-V01", "Specified streets identified", "A001 block plan", "names, widths and which are specified",
              txt + ("; " + rd["streets"]["note"] if rd["streets"].get("note") else ""), st,
              basis="Partial" if st == "FAIL" else "", confidence=cf,
              cite="%s §5.2.1(d); Cap. 123F reg 18A" % BIMGBPS, method="sheet export read (finding recorded by the reader)",
              fix={"PASS": "", "FAIL": "Mark the specified streets (INP-02) and their widths",
                   "UNCLEAR": readings.obs_fix(rd, "streets", a.raw, "Record a PASS / FAIL finding for 'streets' in readings.tsv")}[st])
    O.add("V01-L8", "AUD-V01", "Special areas on the site", "site", "shown if any", "none found", "N/A",
          cite="%s §5.2.1(g)" % BIMGBPS, basis="state N/A")
    if "spot_levels_block" in rd:
        O.add("V01-L10", "AUD-V01", "Street levels in X.XXX mPD", "A001 block plan",
              "X.XXX mPD", "%d spot levels; %s" % (n(bp["view_id"], "OST_SpotElevations") if bp else 0, rd["spot_levels_block"]["value"]),
              "UNCLEAR", cite="GEN-04 (LIM-03)", method="spot elevation count + sheet read", confidence="low",
              fix=rd["spot_levels_block"]["note"])

    # ------------------------------------------------------------ V02 floor plans
    plans = [r for r in vos if r["view_type"] == "FloorPlan" and not r["view_name"].endswith("_pat")]
    for r in plans:
        v = r["view_id"]
        part = "part plan" in r["view_name"].lower() or "TR/F" in r["view_name"]
        nm = vname[v]
        O.add("V02-L2-%s" % v, "AUD-V02", "Grid lines shown", nm, "> 0", n(v, "OST_Grids"),
              "PASS" if n(v, "OST_Grids") else "FAIL", cite="%s §5.2.2(b)" % BIMGBPS, method="query_model in the view",
              fix="" if n(v, "OST_Grids") else "Show the grids in this view (or its crop) so the part plan can be located",
              object_id=int(v))
        O.add("V02-DIM-%s" % v, "AUD-V02", "Dimensions shown", nm, "> 0", n(v, "OST_Dimensions"),
              "PASS" if n(v, "OST_Dimensions") else "FAIL", cite="%s §5.2.2(d)(f)" % BIMGBPS, object_id=int(v))
        if not part:
            marks = n(v, "OST_Viewers") + n(v, "OST_Elev")
            O.add("V02-L3-%s" % v, "AUD-V02", "Section and elevation marks shown", nm, "> 0", marks,
                  "PASS" if marks else "FAIL", cite="%s §5.2.2(c)" % BIMGBPS, object_id=int(v))
            d, t = n(v, "OST_Doors"), n(v, "OST_DoorTags")
            O.add("V02-L5-%s" % v, "AUD-V02", "Door marks on all doors", nm, "%d door tags" % d, "%d door tags" % t,
                  "PASS" if t >= d else "FAIL", basis="Partial" if t else "", cite="%s §5.2.2(e)" % BIMGBPS,
                  method="door tags ÷ doors visible in the view", confidence="medium", object_id=int(v),
                  evidence="tags probably only on fire-rated doors (round 1)",
                  fix="Tag every door, or state that only fire-rated doors are marked")
            rm, rt = n(v, "OST_Rooms"), n(v, "OST_RoomTags")
            O.add("V02-L10-%s" % v, "AUD-V02", "Every room in the view is tagged", nm, rm, rt, "PASS" if rt >= rm else "UNCLEAR",
                  cite="%s §5.2.2(e)" % BIMGBPS, method="room tags ÷ rooms visible", confidence="medium", object_id=int(v),
                  evidence="untagged rooms may be small cubicles (accessible WC) or rooms of another level seen in the view range",
                  fix="Open the view and tag the remaining rooms, or explain")
        O.add("V02-L9-%s" % v, "AUD-V02", "Spot levels in X.XXX mPD", nm, "X.XXX mPD", "%d spot levels" % n(v, "OST_SpotElevations"),
              "UNCLEAR", cite="GEN-04 (LIM-03)", method="count only; text not read", confidence="low",
              fix="Read the spot-level type format (Function A manual SOP, man-version) or export the view at high resolution")
        sc = props.get(v, {}).get("scale")
        if sc:
            O.add("V02-SC-%s" % v, "AUD-V02", "Plan scale", nm, "1:100 or larger", "1:%s" % sc,
                  "PASS" if sc.isdigit() and int(sc) <= 100 else "FAIL", cite="%s §5.2.2" % BIMGBPS, method="View Scale")
    O.add("V02-C1", "AUD-V02", "Travel distance and exit widths shown and within limits", "floor plans", "FS Code Part B",
          "not checked", "UNCLEAR", cite="FS Code 2011 Part B (LIM-30)")

    # ------------------------------------------------------------ V03 sections, V04 elevations
    for vt, task, label in (("Section", "AUD-V03", "section"), ("Elevation", "AUD-V04", "elevation")):
        vs = [r for r in vos if r["view_type"] == vt and "(pattern)" not in r["view_name"]]
        main_vs = [r for r in vs if props.get(r["view_id"], {}).get("scale") != "50"]
        O.add("%s-N" % task[4:], task, "%ss in every direction" % label.title(), "sheets", "≥ 2 sections / 4 elevations",
              len(main_vs), "PASS" if len(main_vs) >= (2 if vt == "Section" else 4) else "FAIL",
              cite="%s §5.2.%s" % (BIMGBPS, 3 if vt == "Section" else 4), method="views placed on sheets")
        for r in main_vs:
            v, nm = r["view_id"], vname[r["view_id"]]
            for cat, cid, item in (("OST_Grids", "L1", "Grid lines"), ("OST_Levels", "L3", "Level heads"),
                                   ("OST_Dimensions", "L2", "Dimensions")):
                O.add("%s-%s-%s" % (task[4:], cid, v), task, item + " shown", nm, "> 0", n(v, cat),
                      "PASS" if n(v, cat) else "FAIL", cite="%s §5.2.%s" % (BIMGBPS, 3 if vt == "Section" else 4),
                      object_id=int(v))
            sp = n(v, "OST_SpotElevations")
            rkey = "section_streets" if vt == "Section" else "elevation_streets"
            rr = rd.get(rkey, {})
            seen = rr.get("value", "") if r["sheet"] in rr.get("sheet", "") else ""
            if re.match(r"(?i)\s*(not read|unread|n/?a\b)", seen) or (rr.get("confidence") or "").lower() == "low":
                seen = ""                                                   # the reader says it was not read
            ok = ("both sides" in seen) if seen else (sp >= 2 or None)
            O.add("%s-L5-%s" % (task[4:], v), task, "Adjoining street levels shown", nm, "street names and levels",
                  "%d spot levels; %s" % (sp, seen or "sheet not read"), "PASS" if ok else ("FAIL" if seen else "UNCLEAR"),
                  basis="" if ok else "Partial",
                  confidence=rd.get(rkey, {}).get("confidence", "medium"),
                  cite="%s §5.2.%s(e)" % (BIMGBPS, 3 if vt == "Section" else 4),
                  method="spot elevations in the view + sheet export read", object_id=int(v),
                  fix="" if ok else "Add the adjoining street names and levels (mPD) on both sides of the %s" % label)
        if "level_heads" in rd:
            lh = rd["level_heads"]
            mpd = bool(re.search(r"\d+\.\d{3}\s*mPD", lh["value"]))
            O.add("%s-L3" % task[4:], task, "Floor levels shown as X.XXX mPD (HKPD)", "%s level heads" % label,
                  "X.XXX mPD", lh["value"], "PASS" if mpd else "FAIL", basis="" if mpd else "Major",
                  confidence=lh.get("confidence") or "medium", cite="%s §5.2.3(c); LIM-03; GEN-04" % BIMGBPS,
                  method="sheet export read (%s); pattern X.XXX mPD" % lh["sheet"], evidence=lh.get("note", ""),
                  fix="" if mpd else "Use a level head showing elevation to 3 decimals in mPD from the survey datum (INP-16)")
        O.add("%s-L6" % task[4:], task, "Building height measured from the mean street level", "%ss" % label,
              "height dimension from MSL", "not read", "UNCLEAR", cite="Cap. 123F reg 23(1) (LIM-13); INP-11",
              basis="height basis: see G3 S05-HGT",
              fix="Show the height dimension from the mean street level and use one basis")
        O.add("%s-L7" % task[4:], task, "OZP / lease height limit line or 'NIL'", "%ss" % label, "line or NIL", "not read",
              "UNCLEAR", cite="%s §5.2.3(g)" % BIMGBPS, confidence="low",
              fix="Show the OZP / lease height limit (or 'NIL', as in the Development Schedule) on the %s" % label)

    # ------------------------------------------------------------ V05 details
    det = [r for r in vos if r["view_type"] == "Section" and props.get(r["view_id"], {}).get("scale") == "50"]
    callouts = sum(n(r["view_id"], "OST_Callouts") for r in plans)
    O.add("V05-N", "AUD-V05", "Detail views placed on sheets", "sheets", "≥ 1", len(det), "PASS" if det else "FAIL",
          cite="%s §5.2.5" % BIMGBPS, method="views at 1:50 on sheets", evidence=", ".join(vname[r["view_id"]] for r in det))
    for r in det:
        t = props[r["view_id"]].get("title_on_sheet", "")
        O.add("V05-L2-%s" % r["view_id"], "AUD-V05", "Detail titled typical / non-typical", vname[r["view_id"]],
              "TYPICAL or NON-TYPICAL in the title", t or "(no title on sheet)",
              "PASS" if re.search(r"TYPICAL", t, re.I) else "FAIL", cite="%s §5.2.5(b)" % BIMGBPS,
              fix="Title the detail 'TYPICAL' or 'NON-TYPICAL'")
    O.add("V05-L1", "AUD-V05", "Details referenced from the plans (callouts)", "floor plans", "callout / section reference",
          "%d callouts on the plans" % callouts, "PASS" if callouts else "UNCLEAR", confidence="medium",
          evidence="the 1:50 section may be referenced by a section mark (OST_Viewers)",
          fix="Check that the detail is referenced from a plan")
    O.add("V05-L4", "AUD-V05", "All parts needing details are detailed", "building", "AP list", "not determinable",
          "UNCLEAR", basis="AP")

    # ------------------------------------------------------------ V13 prescribed windows
    pw = [r for r in vos if r["view_type"] != "Schedule" and re.search(r"window|prescribed", r["view_name"], re.I)]
    O.add("V13-L1", "AUD-V13", "Dedicated prescribed-window diagram", "sheets", "diagram with window areas",
          "none (%d placed views match)" % len(pw), "FAIL" if not pw else "PASS", basis="Missing",
          cite="%s §5.2.13(a)(b)" % BIMGBPS, method="placed view names",
          fix="Add a prescribed-window diagram: per room the glass and openable panels (S14 workbook lists them)")
    if s14:
        s = s14["summary"]
        fails = [r for r in s14["rooms_included"] if r["status"] != "PASS"]
        O.add("V13-C1", "AUD-V13", "Glass ≥ 1/10 of floor area in every applicable room", "%d rooms" % s["rooms_included_count"],
              "all pass", "%d pass, %d fail" % (s["lighting_pass_count"], s["lighting_fail_count"]),
              "PASS" if not s["lighting_fail_count"] else "FAIL", cite="Cap. 123F reg 30, 36 (LIM-06, LIM-10)",
              method="S14 analysis (measured geometry)", evidence=", ".join("%s %s" % (r["name"], r["number"]) for r in fails))
        O.add("V13-C2", "AUD-V13", "Openable ≥ 1/16 (1/10 with soil fitments), top ≥ 2 m", "%d rooms" % s["rooms_included_count"],
              "all pass", "%d pass, %d fail" % (s["ventilation_pass_count"], s["ventilation_fail_count"]),
              "PASS" if not s["ventilation_fail_count"] else "FAIL", cite="Cap. 123F reg 30(2)(a)(ii), 36 (LIM-07, LIM-10)",
              method="S14 analysis")
    O.add("V13-C3", "AUD-V13", "Prescribed windows face a ≥ 4.5 m street or a 21 m² rectangular plane", "windows",
          "reg 31 test", "not computed", "UNCLEAR", cite="Cap. 123F reg 31 (LIM-08, LIM-09)", basis="INP-05")

    # ------------------------------------------------------------ V08 / V10 / V11 drawing checks
    for sheet, task, label in (("C005", "AUD-V08", "compartment"), ("C002", "AUD-V10", "GFA"), ("C004", "AUD-V11", "UFA")):
        for r in [x for x in vos if x["sheet"] == sheet and x["view_type"] == "AreaPlan"]:
            v = r["view_id"]
            if str(v) not in counts:
                continue
            O.add("%s-DIM-%s" % (task[4:], v), task, "Dimensions on the %s diagram" % label, vname[v], "> 0",
                  n(v, "OST_Dimensions"), "PASS" if n(v, "OST_Dimensions") else "FAIL",
                  cite="%s §5.2.%s(b)" % (BIMGBPS, {"AUD-V08": 8, "AUD-V10": 10, "AUD-V11": 11}[task]), object_id=int(v),
                  fix="" if n(v, "OST_Dimensions") else "Dimension the %s boundaries" % label)
            O.add("%s-GRID-%s" % (task[4:], v), task, "Grid lines on the %s diagram" % label, vname[v], "> 0",
                  n(v, "OST_Grids"), "PASS" if n(v, "OST_Grids") else "FAIL", object_id=int(v))
        if task == "AUD-V11":
            v = next((x["view_id"] for x in vos if x["sheet"] == "C004"), None)
            if v and str(v) in counts:
                O.add("V11-L2-view", "AUD-V11", "UFA diagram shows UFA areas (fill / outline)", vname[v], "UFA Areas",
                      "%d rooms, %d room tags, %d Areas" % (n(v, "OST_Rooms"), n(v, "OST_RoomTags"), n(v, "OST_Areas")),
                      "FAIL" if not n(v, "OST_Areas") else "PASS", cite="%s §5.2.11(b)" % BIMGBPS,
                      fix="Build the UFA diagram from UFA Areas (scheme ARC_gbp_ufa is empty)")
    for key, task, label in (("gfa", "AUD-V10", "GFA"), ("comp", "AUD-V08", "compartment")):
        regs = {k: v for k, v in col.items() if k.startswith(key + "_")}
        sheet = {"gfa": "C002", "comp": "C005"}[key]
        if not regs and col.get("sheet_" + sheet):
            O.add("%s-L4" % task[4:], task, "Halftone base drawing on the %s diagrams (GEN-03)" % label, sheet,
                  "grey (halftone) linework", "not measurable on the whole sheet (images and text are grey too)",
                  "UNCLEAR", cite="%s §4.2(d) (GEN-03)" % BIMGBPS, method="whole-sheet sample only",
                  fix="Give each diagram a region box (regions.json) and re-sample")
        if regs:
            gmax = max(v["grey_pct"] for v in regs.values())
            O.add("%s-L4" % task[4:], task, "Halftone base drawing on the %s diagrams (GEN-03)" % label,
                  "%d diagrams" % len(regs), "grey (halftone) linework", "grey ≤ %.2f %%, black %.1f–%.1f %%" % (
                      gmax, min(v["black_pct"] for v in regs.values()), max(v["black_pct"] for v in regs.values())),
                  "PASS" if gmax > 5 else "FAIL", cite="%s §4.2(d) (GEN-03)" % BIMGBPS,
                  method="pixel sampling of the exported sheet", fix="Set the base model to halftone in the view template")
    comp = {k: v for k, v in col.items() if k.startswith("comp_")}
    if comp:
        fills = {k: tuple(v["top"][0][0]) for k, v in comp.items()}
        same = len(set(fills.values())) < len(fills)
        O.add("V08-L3", "AUD-V08", "Different compartments in different colours", "C005",
              "distinct colour per compartment", "; ".join("%s %s" % (k[5:], ",".join(map(str, c))) for k, c in fills.items()),
              "UNCLEAR" if same else "PASS", confidence="medium", cite="%s §5.2.8(c)" % BIMGBPS,
              method="dominant fill per floor diagram",
              evidence="G/F and 1/F compartments share a colour on separate diagrams; vertically adjacent",
              fix="Use a distinct colour for each compartment if they adjoin vertically")

    # ------------------------------------------------------------ A02 colour coding
    gfa = {k: v for k, v in col.items() if k.startswith("gfa_")}
    if gfa:
        used = {c for v in gfa.values() for c, px in v["table1"].items() if px}
        O.add("A02-L1", "AUD-A02", "GFA diagram fills equal BIMGBPS Table 1 RGB", "C002 (%d diagrams)" % len(gfa),
              "exact Table 1 values", "exact: class %s" % ", ".join(sorted(used)), "PASS" if used else "FAIL",
              cite="%s §5.2.10(c) Table 1 (DK-AUD-004 §1)" % BIMGBPS, method="pixel sampling")
    elif col.get("sheet_C002"):
        sc = col["sheet_C002"]
        used = sorted(k for k, px in sc["table1"].items() if px)
        off = sorted(k for k in sc["table1"] if sc["near_table1"].get(k, 0) > sc["table1"][k])
        O.add("A02-L1", "AUD-A02", "GFA diagram fills equal BIMGBPS Table 1 RGB", "C002 (whole sheet)",
              "exact Table 1 values", "exact: class %s; near-miss larger than exact: %s" % (
                  ", ".join(used) or "none", ", ".join(off) or "none"),
              "FAIL" if off else ("PASS" if used else "UNCLEAR"), cite="%s §5.2.10(c) Table 1 (DK-AUD-004 §1)" % BIMGBPS,
              method="whole-sheet pixel count (no region boxes)",
              fix="Set the fills to the exact Table 1 RGB" if off else "")
    lg = col.get("legend_table1")
    if not lg and col.get("sheet_A001"):
        sa = col["sheet_A001"]
        missing = [c for c, px in sa["table1"].items() if not px]
        O.add("A02-L2", "AUD-A02", "Legend swatches equal Table 1", "A001 (whole sheet)", "6 classes exact",
              "%d exact" % (6 - len(missing)), "PASS" if not missing else "UNCLEAR", cite="%s Table 1" % BIMGBPS,
              method="whole-sheet pixel count (no region boxes)",
              evidence="not found exact: " + ", ".join(missing) if missing else "",
              fix="" if not missing else "Give the legend a region box to check the swatches")
        lg = None
    if lg:
        missing = [c for c, px in lg["table1"].items() if not px]
        O.add("A02-L2", "AUD-A02", "Legend swatches equal Table 1", "A001 Table 1 legend", "6 classes exact",
              "%d exact" % (6 - len(missing)), "PASS" if not missing else "FAIL", cite="%s Table 1" % BIMGBPS,
              method="pixel sampling", evidence="missing: " + ", ".join(missing) if missing else "")
    tmpl = {props[v]["template"] for v in props if props[v]["view_type_name"] == "Floor Plan (GBP)" and props[v]["template"]}
    diag = {props[r["view_id"]]["template"] for r in vos if r["sheet"] in ("C002", "C004", "C005")
            and r["view_type"] == "AreaPlan" and r["view_id"] in props and props[r["view_id"]]["template"]}
    st = "UNCLEAR" if not tmpl or not diag else ("FAIL" if tmpl & diag else "PASS")
    O.add("A02-L3", "AUD-A02", "Floor plans and GFA diagrams use separate colour systems", "view templates",
          "different templates (plans ADM-9, diagrams Table 1)",
          "plans: %s; diagrams: %s" % (", ".join(sorted(tmpl)) or "none", ", ".join(sorted(diag)) or "none"), st,
          method="View Template per view (view_props.tsv)",
          fix={"PASS": "", "FAIL": "Use separate view templates for plans and area diagrams",
               "UNCLEAR": "Extract View Template for the plans and the C002 / C004 / C005 diagrams"}[st])
    O.add("A02-L5", "AUD-A02", "Revision colour", "first submission", "revision clouds in the set colour", "first submission",
          "N/A", cite="%s §5.4" % BIMGBPS)

    # ------------------------------------------------------------ A01 sheet assembly
    sheets = sorted({r["sheet"] for r in vos})
    tbs, pinfo = [], {}
    for k, v in tb.items():
        P = params(v)
        if v["BasicElementInfo"]["category"] == "Project Information":
            pinfo = P
        else:
            tbs.append(P)
    if tbs:
        O.add("A01-L1", "AUD-A01", "One title block per sheet", "%d sheets" % 16, "16", len(tbs), "PASS" if len(tbs) == 16 else "FAIL",
              cite="%s §4.3(f)" % BIMGBPS, method="Title Blocks in the model")
        bad_no = [t["Sheet Number"] for t in tbs if not re.match(r"^[AC]\d{3}$", t.get("Sheet Number") or "")]
        O.add("A01-L3", "AUD-A01", "Drawing numbers follow A### / C###", "%d title blocks" % len(tbs), "A### / C###",
              "all match" if not bad_no else ", ".join(bad_no), "PASS" if not bad_no else "FAIL", basis="Minor",
              cite="%s §6.4" % BIMGBPS)
        ph = [t["Sheet Number"] for t in tbs if re.search(r"X", t.get("Sheet Issue Date") or "")]
        O.add("A01-L6-date", "AUD-A01", "Issue date filled (not a placeholder)", "title blocks", "a date",
              "'%s' on %d sheets" % (tbs[0].get("Sheet Issue Date"), len(ph)), "FAIL" if ph else "PASS", basis="Minor",
              cite="%s §5.5.1" % BIMGBPS, fix="Fill the issue date")
        au = [t["Sheet Number"] for t in tbs if (t.get("Drawn By") or "") in ("Author", "")]
        O.add("A01-L6-drawn", "AUD-A01", "Drawn by filled (not 'Author')", "title blocks", "initials",
              "'Author' on %s" % ", ".join(sorted(au)) if au else "filled", "FAIL" if au else "PASS", basis="Minor",
              fix="Fill 'Drawn By' on %s" % ", ".join(sorted(au)))
    if pinfo:
        name, addr = pinfo.get("Project Name", ""), (pinfo.get("Project Address") or "").replace("\r\n", " ")
        clash = ("INSTITUTIONAL" in name and "ASSEMBLY" in addr) or ("KOWLOON" in name and "TKO" in addr)
        O.add("A01-L6-addr", "AUD-A01", "Project name and address agree", "Project Information", "same project",
              "name '%s'; address '%s'" % (name, addr), "FAIL" if clash else "PASS", basis="Minor",
              fix="Correct the project address (it describes another sample project)")
        ref = pinfo.get("Title Block_BIM Reference Number", "")
        m = re.search(r"R(\d{2})", ref)
        fmt = rvt.get("format")
        if m and fmt:
            ok = fmt.endswith(m.group(1))
            O.add("A01-L5", "AUD-A01", "BIM file reference software field matches the file", "BIM Reference Number",
                  "R%s (file format %s)" % (fmt[-2:], fmt), ref, "PASS" if ok else "FAIL", basis="Minor",
                  cite="%s §6.3" % BIMGBPS, method="Project Information + rvt_info.py",
                  fix="Change the version field to R%s" % fmt[-2:])
    legends = [r["view_name"] for r in vos if r["view_type"] == "Legend"]
    O.add("A01-L4", "AUD-A01", "Legend, abbreviations and FS notes on the drawings", "A001", "present",
          "; ".join(legends), "PASS" if any("Abbreviation" in x for x in legends) and any("Fs Notes" in x for x in legends) else "FAIL",
          cite="%s §5.5.2" % BIMGBPS)

    # ------------------------------------------------------------ A03 export / file
    if rvt:
        O.add("A03-L1", "AUD-A03", "File format", rvt["file"], ".rvt", os.path.splitext(rvt["file"])[1],
              "PASS" if rvt["file"].lower().endswith(".rvt") else "FAIL", cite="%s §4.3(e)" % BIMGBPS)
        O.add("A03-L2", "AUD-A03", "File size ≤ 500 MB", rvt["file"], "≤ 500 MB", "%.2f MB" % rvt["size_mb"],
              "PASS" if rvt["size_mb"] <= 500 else "FAIL", cite="%s §4.3(b), §6.1" % BIMGBPS)
        O.add("A03-L3", "AUD-A03", "Revit version ≥ 2017", rvt["file"], "≥ 2017", "Format %s, build %s" % (rvt.get("format"), rvt.get("build")),
              "PASS" if rvt.get("format", "0").isdigit() and int(rvt["format"]) >= 2017 else "UNCLEAR",
              cite="%s §4.3(c)" % BIMGBPS, method="BasicFileInfo in the .rvt (rvt_info.py) - closes GAP-04")
        if rvt.get("other_rvt_in_folder"):
            O.add("A03-FOLDER", "AUD-A03", "Only the submission model in the submission folder", "model folder", "one .rvt",
                  "also: " + ", ".join(rvt["other_rvt_in_folder"]), "FAIL", basis="Minor",
                  fix="Submit one model; keep other versions and backups out of the submission folder")
    mc = load_json(R("model_counts.json"), {})
    nl = mc.get("OST_RvtLinks")
    O.add("A03-L4", "AUD-A03", "No external links", "model", "0 Revit links",
          "%s Revit links (OST_RvtLinks)" % nl if nl is not None else "not counted",
          "UNCLEAR" if nl is None else ("PASS" if nl == 0 else "FAIL"), cite="%s §4.3(g)" % BIMGBPS,
          method="query_model count saved in model_counts.json", evidence="CAD imports cannot be listed (GAP-03)",
          fix="" if nl == 0 else ("Remove or bind the links" if nl else "Count OST_RvtLinks into model_counts.json"))
    O.add("A03-L4b", "AUD-A03", "No CAD imports", "model", "0", "not listable", "UNCLEAR", cite="%s §4.3(g)" % BIMGBPS,
          basis="GAP-03", fix="Manual SOP man-cad-import")
    O.add("A03-L7", "AUD-A03", "Drawings generated from the model (GEN-01 roll-up)", "%d raster images" % len(rasters),
          "0 raster tables", "%d raster images (%s …)" % (len(rasters), rasters[0]["name"] if rasters else ""),
          "FAIL" if rasters else "PASS", cite="%s §4.2(b)" % BIMGBPS, fix="Rebuild every pictured table from the model")
    O.add("A03-L5", "AUD-A03", "Link hierarchy explained", "model", "only if linked", "single file", "N/A")
    for cid, item in (("A03-L6", "Opens without add-ins"), ("A03-L8", "Exported sheet size equals the title block (A0)"),
                      ("A03-L9", "Submission medium (DVD-ROM / ESH)")):
        O.add(cid, "AUD-A03", item, "submission", "confirmed", "not determinable from the model", "UNCLEAR",
              cite="%s §4.3" % BIMGBPS, basis="manual")

    tasks = list(GROUP)
    per = {}
    for c in O.checks:
        p = per.setdefault(c["task"], {})
        p[c["status"]] = p.get(c["status"], 0) + 1
    tables = {
        "views": {"title": "Views on sheets and annotation counts", "columns": [
            "Sheet", "View ID", "View", "Type", "Scale", "Template", "Grids", "Levels", "Dimensions", "Spot levels",
            "Doors", "Door tags", "Rooms", "Room tags", "Areas", "Area tags", "Text"],
            "rows": [[r["sheet"], int(r["view_id"]), r["view_name"], r["view_type"], props.get(r["view_id"], {}).get("scale", ""),
                      props.get(r["view_id"], {}).get("template", "")] +
                     [n(r["view_id"], c) for c in ("OST_Grids", "OST_Levels", "OST_Dimensions", "OST_SpotElevations",
                                                   "OST_Doors", "OST_DoorTags", "OST_Rooms", "OST_RoomTags", "OST_Areas",
                                                   "OST_AreaTags", "OST_TextNotes")]
                     for r in vos if r["view_id"] in counts]},
        "colours": {"title": "Colour samples", "columns": ["Region", "Sheet", "Table 1 classes (px)", "Pink px", "Grey %",
                                                          "Black %", "Dominant colours"],
                    "rows": [[k, v["sheet"], ", ".join("%s:%d" % kv for kv in v["table1"].items() if kv[1]), v["pink"],
                              v["grey_pct"], v["black_pct"], "; ".join("%s (%d)" % (",".join(map(str, c)), p) for c, p in v["top"][:4])]
                             for k, v in col.items()]},
        "titleblocks": {"title": "Title blocks", "columns": ["Sheet", "Name", "Drawn by", "Issue date", "Date stamp"],
                        "rows": [[t.get("Sheet Number"), t.get("Sheet Name"), t.get("Drawn By"), t.get("Sheet Issue Date"),
                                  t.get("Date/Time Stamp")] for t in sorted(tbs, key=lambda t: t.get("Sheet Number") or "")]},
    }
    O.warnings += [
        "Annotation checks count elements in each view (query_model SpecificView); text content (mPD format, titles, "
        "MSL dimensions) is read from sheet exports where legible, otherwise UNCLEAR.",
        "Colour checks sample pixels of the 1920 px sheet exports (exact RGB match for fills, grey share for halftone).",
        "Revit version is read from the BasicFileInfo text inside the .rvt (needs file access) - GAP-04 closed for this harness.",
    ]
    out = {"project_info": {"project_name": a.project, "model_path": a.model, "group": "G4 drawings", "tasks": tasks,
                            "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "read_only": True,
                            "rules": {"Drawings": "BIMGBPS 2019 §4.2, §4.3, §5.2, §5.5, §6; Table 1 RGB (DK-AUD-004)",
                                      "Windows": "Cap. 123F regs 30, 31, 36 (via S14)"}},
           "checks": O.checks, "tables": tables,
           "summary": {"per_task": per, "checks": len(O.checks), "fail": sum(1 for c in O.checks if c["status"] == "FAIL"),
                       "unclear": sum(1 for c in O.checks if c["status"] == "UNCLEAR"), "data_quality_warnings": O.warnings}}
    out["readings"] = readings.listing(rd, a.raw)
    T.finish(out, wanted, GROUP, gp, TABLE_TASKS)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    T.print_summary(out, "G4 drawings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
