#!/usr/bin/env python3
"""G2 room-use group: AUD-S13 sanitary fitments, AUD-S10 exit doors, AUD-S11 discharge value,
AUD-S15 refuse storage, AUD-S16 TBE room.  Read-only; works only on the R-G2 extract.

Usage:
  python analyze.py --raw <extract dir> --project <name> --model <path> --out <json> [--use institutional]
Extract (see L3 recipe R-G2): rooms.tsv, room_polygons.json, fixtures.tsv, doors_all.tsv and the model's
schedule CSV exports (S10, S11, S13).  Writes the generic task-analysis JSON (templates/task-analysis.schema.json)
and prints the on-screen summary.  Stdlib only.  Exit 0 = written, 2 = input missing.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from geom import ceil_div, load_rooms, read_schedule_csv, read_tsv, room_at, rooms_touching_box  # noqa: E402
import tasks as T  # noqa: E402

GROUP = ["AUD-S13", "AUD-S10", "AUD-S11", "AUD-S15", "AUD-S16", "AUD-A1"]
_X = "R-G2 step %s (L3-SOP/SOP-AUD-mcp-revit-mcp.md §10)"
NEEDS = {  # (input, required?, how to get it)
    "AUD-S13": [("fixtures.tsv", True, _X % 2), ("GBP S13 schedule CSV", False, _X % 4)],
    "AUD-S10": [("fixtures.tsv", True, _X % 2 + " - UFA excludes rooms with fitments"), ("doors_all.tsv", True, _X % 3),
                ("GBP S10 schedule CSV", False, _X % 4)],
    "AUD-S11": [("fixtures.tsv", True, _X % 2), ("doors_all.tsv", True, _X % 3), ("GBP S10 schedule CSV", True, _X % 4),
                ("GBP S11 schedule CSV", True, _X % 4)],
    "AUD-S15": [("fixtures.tsv", True, _X % 2 + " - UFS excludes rooms with fitments")],
    "AUD-S16": [],
    "AUD-A1": [("doors_all.tsv", True, _X % 3)],
}
TABLE_TASKS = {"fixtures": ["AUD-S13", "AUD-S15"], "ufa": ["AUD-S13", "AUD-S15", "AUD-S10"], "s13": ["AUD-S13"],
               "s10": ["AUD-S10", "AUD-S11"], "s11": ["AUD-S11"], "soil_rooms": ["AUD-S13"]}

CAP123I = "Cap. 123I"
# ---------------------------------------------------------------- rules (L1 LIM-21, LIM-22, LIM-19/20, LIM-18)
UFA_EXCLUDE = [  # Cap. 123I reg 3 'usable floor area' exclusions, matched on room name
    (r"^S-\d+$", "staircase"),
    (r"^FLL$", "lift landing (fireman's lift lobby)"),
    (r"^ELV$", "lift"),
    (r"LAV|TOILET|^Room$", "lavatory (contains sanitary fitments)"),
    (r"^AHU$|^TX RM$|PFWTPR|FSSPRPR|FSWT|SPRWT|^MSR$", "space occupied by machinery or plant for a building service"),
    (r"^ENT HALL$", "public circulation space (entrance hall) [INFERENCE]"),
    (r"^FR$", "roof level 'FR' - flat roof, not a floor [INFERENCE]"),
]
UFA_PENDING = [(r"^ELR$", "abbreviation 'ELR' undefined - machinery room or occupied room; excluded and flagged")]
ASSEMBLY = r"FUNCTION ROOM|ACTIVITY AREA"


def office_req(p):
    """Cap. 123I reg 5 + Tables 5-7 (workplace, office: 1 person / 9 m², male:female 1:1)."""
    m = f = ceil_div(p, 2)
    if p <= 10:
        return {"male_wc": 1, "urinal": 0, "female_wc": 1, "male_basin": 1, "female_basin": 1, "male": m, "female": f,
                "note": "reg 5(3): not more than 10 persons - at least 1 WC and 1 basin"}
    mw = 1 if m <= 10 else ceil_div(m, 25) if m <= 100 else 4 + ceil_div(m - 100, 50)
    mu = 0 if m <= 10 else ceil_div(m, 50) if m <= 100 else 2 + ceil_div(m - 100, 50)
    fw = 1 if f <= 10 else 2 if f <= 25 else 2 + ceil_div(f - 25, 25)
    b = lambda n: ceil_div(n, 25) if n <= 100 else 4 + ceil_div(n - 100, 50)
    return {"male_wc": mw, "urinal": mu, "female_wc": fw, "male_basin": b(m), "female_basin": b(f), "male": m, "female": f,
            "note": "Tables 5, 6, 7"}


def ppe_req(p):
    """Cap. 123I reg 6 + Tables 8-10 (place of public entertainment, assembly area without seating: 1 / 0.5 m², 1:1.5)."""
    m, f = ceil_div(p * 1, 2.5), ceil_div(p * 1.5, 2.5)
    mw = ceil_div(m, 100) if m <= 400 else 4 + ceil_div(m - 400, 250)
    mu = ceil_div(m, 50)
    fw = 2 * ceil_div(f, 50) if f <= 250 else 10 + ceil_div(f - 250, 40)
    return {"male_wc": mw, "urinal": mu, "female_wc": fw, "male_basin": ceil_div(m, 100), "female_basin": ceil_div(f, 100),
            "male": m, "female": f, "note": "Tables 8, 9, 10"}


def add_req(a, b):
    out = {k: a[k] + b[k] for k in ("male_wc", "urinal", "female_wc", "male_basin", "female_basin", "male", "female")}
    out["note"] = "sum of the separate requirements"
    return out


def fitment_kind(fam):
    if "Toilet_Cubicle-Accessible" in fam:
        return "accessible_wc"
    if "Toilet_Cubicle" in fam:
        return "wc"
    if "URN" in fam:
        return "urinal"
    if fam.endswith("PLM-SNK"):
        return "basin"
    if "Flush" in fam or "Grab_Rail" in fam:
        return "accessory"
    if fam.startswith("BD_Plumbing Fixtures"):
        return "counter"
    return "other"


def num(s):
    m = re.search(r"-?\d+(?:\.\d+)?", s or "")
    return float(m.group()) if m else None


class Out:
    def __init__(self):
        self.checks = []
        self.warnings = []

    def check(self, cid, task, item, obj, expected, actual, status, cite="", method="", confidence="high",
              evidence="", fix="", object_id=None, basis=""):
        self.checks.append({"id": cid, "task": task, "item": item, "object": obj, "object_id": object_id,
                            "expected": expected, "actual": actual, "status": status, "cite": cite, "basis": basis,
                            "method": method, "confidence": confidence, "evidence": evidence, "fix": fix})


def find_csv(raw, key):
    hits = glob.glob(os.path.join(raw, "*%s*.csv" % key))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--use", default="institutional", help="building use for APL-03 / APL-04 (AP to confirm)")
    T.add_arg(ap)
    a = ap.parse_args()
    wanted = T.parse(a.tasks, GROUP)
    if not os.path.exists(os.path.join(a.raw, "rooms.tsv")):
        print("ERROR: missing rooms.tsv (every G2 task needs it: R-G2 step 1)", file=sys.stderr)
        return 2
    has = lambda n: os.path.exists(os.path.join(a.raw, n))
    have = {"fixtures.tsv": has("fixtures.tsv"), "doors_all.tsv": has("doors_all.tsv"),
            "GBP S13 schedule CSV": bool(find_csv(a.raw, "GBP S13")), "GBP S10 schedule CSV": bool(find_csv(a.raw, "GBP S10")),
            "GBP S11 schedule CSV": bool(find_csv(a.raw, "GBP S11"))}
    gp = T.gaps(wanted, NEEDS, have)
    rooms = load_rooms(a.raw)
    placed = [r for r in rooms if r.area > 0]
    fixtures = read_tsv(os.path.join(a.raw, "fixtures.tsv")) if have["fixtures.tsv"] else []
    doors = read_tsv(os.path.join(a.raw, "doors_all.tsv")) if have["doors_all.tsv"] else []
    O = Out()
    tables = {}

    # ------------------------------------------------ fixtures -> rooms
    fx_rows = []
    by_room = {}
    for fx in fixtures:
        x, y, z = float(fx["cx"]), float(fx["cy"]), float(fx["z"]) + 1.0
        r = room_at(placed, x, y, z)
        kind = fitment_kind(fx["family"])
        fx["room"] = r
        fx["kind"] = kind
        if r is not None:
            by_room.setdefault(r.id, []).append(fx)
        fx_rows.append([int(fx["id"]), fx["family"], fx["type"], fx["level"] or "(no level)", kind,
                        r.label if r else "(no room)", r.level if r else "",
                        "counted" if kind in ("wc", "urinal", "basin", "accessible_wc") else "not a fitment (%s)" % kind])
    tables["fixtures"] = {"title": "Sanitary fitments by room", "columns": [
        "Fixture ID", "Family", "Type", "Level", "Kind", "Room", "Room level", "Counted"], "rows": fx_rows}
    soil_rooms = {rid for rid, fl in by_room.items() if any(f["kind"] in ("wc", "urinal", "accessible_wc") for f in fl)}
    nolevel = [f for f in fixtures if not f["level"]]
    for f in nolevel:
        r = f["room"]
        O.check("S13-L4-%s" % f["id"], "AUD-S13", "Fixture with no level is classified", "Fixture %s" % f["id"],
                "level set, or explained", "no level; %s inside %s" % (f["family"], r.label if r else "no room"),
                "FAIL", cite="BIMGBPS §5.3.13; AUD-S13 S13-L4", method="centre point in room outline",
                evidence="Geometry: counter-height element over the basins; not a sanitary fitment",
                fix="Host the counter on its level (or move it to Casework) so it does not appear as an unlevelled plumbing fixture",
                object_id=int(f["id"]), basis="Minor")

    # ------------------------------------------------ UFA per level (Cap. 123I reg 3)
    def ufa_class(r):
        for pat, why in UFA_EXCLUDE:
            if re.search(pat, r.name):
                return "excluded", why
        for pat, why in UFA_PENDING:
            if re.search(pat, r.name):
                return "pending", why
        if r.id in soil_rooms:
            return "excluded", "contains sanitary fitments"
        return "included", "usable floor area"

    ufa_rows = []
    levels = sorted({r.level for r in placed}, key=lambda l: min(x.bb[2] for x in placed if x.level == l))
    lv_ufa = {}
    for r in placed:
        c, why = ufa_class(r)
        use = "assembly" if re.search(ASSEMBLY, r.name) else "office-type"
        ufa_rows.append([r.id, r.label, r.level, round(r.area, 3), c, why, use if c == "included" else ""])
        if c == "included":
            d = lv_ufa.setdefault(r.level, {"all": 0.0, "assembly": 0.0, "other": 0.0})
            d["all"] += r.area
            d["assembly" if use == "assembly" else "other"] += r.area
    tables["ufa"] = {"title": "Usable floor area by room (Cap. 123I reg 3)", "columns": [
        "Room ID", "Room", "Level", "Area (m²)", "UFA", "Reason", "Use for S13 basis B"], "rows": ufa_rows}

    # ------------------------------------------------ S13 provided per level
    prov = {}
    for r in placed:
        for f in by_room.get(r.id, []):
            d = prov.setdefault(r.level, {"male_wc": 0, "urinal": 0, "female_wc": 0, "male_basin": 0, "female_basin": 0,
                                          "accessible_wc": 0, "accessible_basin": 0})
            male = "M LAV" in r.name
            female = "F LAV" in r.name
            if f["kind"] == "wc":
                d["male_wc" if male else "female_wc" if female else "accessible_wc"] += 1
            elif f["kind"] == "urinal":
                d["urinal"] += 1
            elif f["kind"] == "accessible_wc":
                d["accessible_wc"] += 1
            elif f["kind"] == "basin":
                d["male_basin" if male else "female_basin" if female else "accessible_basin"] += 1

    # S13 schedule vs model counts (S13-L3)
    s13 = find_csv(a.raw, "GBP S13")
    sched_counts = {}
    if s13:
        _, hdr, data = read_schedule_csv(s13)
        for row in data:
            if len(row) >= 4 and row[1] and row[3].strip().isdigit() and not row[0].endswith(":"):
                k = (row[0], row[1])
                sched_counts[k] = sched_counts.get(k, 0) + int(row[3])
        model_counts = {}
        for f in fixtures:
            if f["kind"] in ("wc", "urinal", "basin", "accessible_wc") and f["level"]:
                k = (f["level"], f["family"])
                model_counts[k] = model_counts.get(k, 0) + 1
        for k in sorted(set(sched_counts) | set(model_counts)):
            t, m = sched_counts.get(k, 0), model_counts.get(k, 0)
            O.check("S13-L3-%s-%s" % (k[0][-3:], k[1].split("-")[-1]), "AUD-S13", "Schedule count equals model count",
                    "%s on %s" % (k[1], k[0]), m, t, "PASS" if t == m else "FAIL", cite="BIMGBPS §5.3.13 (GEN-06)",
                    method="schedule CSV rows vs fixtures counted by family and level",
                    fix="" if t == m else "Re-check the schedule filter / category")
        O.check("S13-L2", "AUD-S13", "Schedule shows UFA, persons and required numbers next to provided",
                "GBP S13 schedule", "UFA, persons, required and provided per sex", "columns: " + ", ".join(hdr), "FAIL",
                cite="BIMGBPS §5.3.13", method="schedule header",
                fix="Add UFA, number of persons, required and provided per fitment type and sex (calculated fields)")
    else:
        O.warnings.append("No S13 schedule CSV in the extract - S13-L2/L3 not checked.")

    # S13 requirement per level, basis A (office) and basis B (assembly as PPE + rest as office)
    req_rows = []
    for lv in levels:
        if lv not in lv_ufa:
            continue
        u = lv_ufa[lv]
        p_a = ceil_div(u["all"], 9)
        A = office_req(p_a)
        pa = ceil_div(u["assembly"], 0.5)
        po = ceil_div(u["other"], 9)
        B = add_req(ppe_req(pa), office_req(po)) if pa else office_req(po)
        pv = prov.get(lv, {})
        for basis, R, persons in (("A office (reg 5)", A, "%d (UFA %.3f / 9)" % (p_a, u["all"])),
                                  ("B assembly as PPE (reg 6) + office", B,
                                   "%d assembly (%.3f / 0.5) + %d office (%.3f / 9)" % (pa, u["assembly"], po, u["other"]))):
            for item, label in (("male_wc", "male WCs"), ("urinal", "urinals"), ("female_wc", "female WCs"),
                                ("male_basin", "male basins"), ("female_basin", "female basins")):
                have = pv.get(item, 0)
                st = "PASS" if have >= R[item] else ("FAIL" if basis[0] == "A" else "UNCLEAR")
                req_rows.append([lv, basis, persons, R["male"], R["female"], label, R[item], have, st])
                O.check("S13-C-%s-%s-%s" % (lv[-3:], basis[0], item), "AUD-S13", "Provided %s >= required" % label,
                        "%s, basis %s" % (lv, basis), R[item], have, st,
                        cite="%s reg %s, %s" % (CAP123I, "5" if basis[0] == "A" else "5 and 6", R["note"]),
                        method="fixtures counted in M LAV / F LAV outlines on the level", basis=basis,
                        confidence="high" if basis[0] == "A" else "medium",
                        fix="" if st == "PASS" else ("Add %d %s on %s" % (R[item] - have, label, lv) if st == "FAIL" else
                                                     "Only if the function rooms / activity areas are a place of public "
                                                     "entertainment: add %d %s on %s. AP to decide the category (INP-12)"
                                                     % (R[item] - have, label, lv)))
        acc = pv.get("accessible_wc", 0)
        req_rows.append([lv, "accessible (not counted to male / female)", "", "", "", "accessible WCs", "", acc, "INFO"])
    tables["s13"] = {"title": "S13 required vs provided per level", "columns": [
        "Level", "Basis", "Persons", "Male", "Female", "Fitment", "Required", "Provided", "Status"], "rows": req_rows}

    # ------------------------------------------------ doors -> rooms
    usable_doors = [d for d in doors if "Access" not in d["family"] and "Lift" not in d["family"]]
    door_rooms = {}
    off_model = []
    xs = [r.bb[0] for r in placed] + [r.bb[3] for r in placed]
    ys = [r.bb[1] for r in placed] + [r.bb[4] for r in placed]
    fp = (min(xs) - 30, min(ys) - 30, max(xs) + 30, max(ys) + 30)
    lowest = min(r.bb[2] for r in placed)
    site_doors = []
    for d in doors:
        bb = [float(d[k]) for k in ("minx", "miny", "minz", "maxx", "maxy", "maxz")]
        if bb[5] < lowest - 1.0:
            off_model.append(d)
            continue
        if bb[3] < fp[0] or bb[0] > fp[2] or bb[4] < fp[1] or bb[1] > fp[3]:
            site_doors.append(d)
            continue
        hits = rooms_touching_box(placed, bb, bb[2] + 1.0, grow=0.5)
        top = max(hits.values()) if hits else 0
        door_rooms[d["id"]] = {r: h for r, h in hits.items() if h >= 0.3 * top}   # drop corner grazes
    if off_model:
        lv = sorted({d["level"] for d in off_model})
        O.check("A1-DOORS-OFF", "AUD-A1", "No doors placed below the building", "%d doors" % len(off_model),
                "0", "%d on %s, x ≈ %.0f ft, z ≈ %.1f ft" % (len(off_model), ", ".join(lv), float(off_model[0]["minx"]),
                                                          float(off_model[0]["minz"])), "FAIL",
                cite="BIMGBPS §4.3 (model health MA-3)", method="door bounding box below the lowest room floor",
                fix="Delete or move the stray doors (Function B, with confirmation)",
                evidence=", ".join(d["id"] for d in off_model[:12]), basis="Minor")
    for d in site_doors:
        O.check("A1-DOOR-SITE-%s" % d["id"], "AUD-A1", "Door outside the building footprint is a site element",
                "Door %s" % d["id"], "site element", "%s %s on %s" % (d["family"], d["type"], d["level"]), "PASS",
                method="bounding box outside the room footprint + 30 ft", basis="info", object_id=int(d["id"]))
    room_doors = {}
    for d in usable_doors:
        for r in door_rooms.get(d["id"], {}):
            room_doors.setdefault(r.id, []).append(d)

    # ------------------------------------------------ S10 exit doors (schedule vs model)
    s10 = find_csv(a.raw, "GBP S10")
    s10_rows, s10_cap = [], {}
    rooms_by_key = {(r.level, r.name): r for r in placed}
    if s10:
        _, hdr, data = read_schedule_csv(s10)
        col = {h: i for i, h in enumerate(hdr)}
        g = lambda row, k: row[col[k]] if k in col and col[k] < len(row) else ""
        listed = set()
        for row in data:
            if not g(row, "Name"):
                continue
            lv, name = g(row, "Level"), g(row, "Name")
            area, factor, cap = num(g(row, "Area")), num(g(row, "FACTOR")), num(g(row, "Room Capacity"))
            n_req = num(g(row, "MIN. NO. OF EXIT DOORS OR EXIT ROUTES REQUIRED"))
            n_prov = num(g(row, "MIN. NO. OF EXIT DOORS OR EXIT ROUTES PROVIDED"))
            w_req = num(g(row, "MIN. WIDTH OF EACH (mm) EXIT DOOR REQUIRED"))
            w_prov = num(g(row, "MIN. WIDTH OF EACH (mm) EXIT DOOR PROVIDED"))
            r = rooms_by_key.get((lv, name))
            s10_cap[lv] = s10_cap.get(lv, 0) + (cap or 0)
            obj = "%s (%s)" % (name, lv)
            if r is None:
                O.check("S10-MATCH-%s-%s" % (lv[-3:], name), "AUD-S10", "Table row matches a model room", obj,
                        "one room", "none", "FAIL", method="level + name")
                continue
            listed.add(r.id)
            ds = room_doors.get(r.id, [])
            widths = [num(d["width_moe_mm"]) for d in ds if d["width_moe_mm"]]
            calc_cap = ceil_div(r.area, factor) if factor else None
            s10_rows.append([r.id, name, lv, area, round(r.area, 3), factor, cap, calc_cap, n_req, n_prov, len(ds),
                             w_req, w_prov, min(widths) if widths else None,
                             ", ".join("%s (%s, %s mm)" % (d["id"], d["type"], d["width_moe_mm"] or "-") for d in ds)])
            O.check("S10-L2-%d" % r.id, "AUD-S10", "Table area equals room area", obj, round(r.area, 3), area,
                    "PASS" if area is not None and abs(area - r.area) < 0.0005 else "FAIL", cite="BIMGBPS §5.3.10 (GEN-06)",
                    method="schedule CSV vs room Area", object_id=r.id)
            O.check("S10-L3-%d" % r.id, "AUD-S10", "Capacity = area / factor, rounded up", obj, calc_cap, cap,
                    "PASS" if cap == calc_cap else "FAIL", cite="BIMGBPS §5.3.10", method="ceil(area / factor)",
                    object_id=r.id, fix="" if cap == calc_cap else "Use a calculated capacity field")
            st = "PASS" if n_prov is not None and len(ds) >= n_prov else ("UNCLEAR" if not ds else "FAIL")
            O.check("S10-D-%d" % r.id, "AUD-S10", "Exit doors claimed in the table exist on the room boundary", obj,
                    n_prov, len(ds), st, cite="BIMGBPS §5.3.10 (GEN-06)",
                    method="grid over the door box (+0.5 ft) falls in the room on the same storey (rooms with < 30 % of the best hits dropped)",
                    confidence="medium", object_id=r.id,
                    evidence=", ".join(d["id"] for d in ds),
                    fix="" if st == "PASS" else ("No door on the room boundary: exits may be open archways - check the plan, "
                                                  "and model or annotate the exit openings" if st == "UNCLEAR"
                                                  else "Correct the provided count, or add the missing exit door"))
            no_w = [d["id"] for d in ds if not d["width_moe_mm"]]
            if no_w:
                O.check("S10-WM-%d" % r.id, "AUD-S10", "Every exit door has a modelled clear width", obj,
                        "width_MOE on each door", "missing on %s (%s)" % (", ".join(no_w), ", ".join(
                            sorted({d["family"] for d in ds if not d["width_moe_mm"]}))), "UNCLEAR",
                        cite="BIMGBPS §5.3.10", method="door parameter width_MOE", object_id=r.id,
                        fix="Use a door family that reports the clear width, or measure the glass doors on plan")
            if widths:
                st = "PASS" if w_prov is not None and min(widths) >= w_prov - 0.5 else "FAIL"
                O.check("S10-W-%d" % r.id, "AUD-S10", "Door width in the table equals the modelled clear width", obj,
                        "%s mm (smallest width_MOE)" % int(min(widths)), "%s mm" % (int(w_prov) if w_prov else "-"), st,
                        cite="BIMGBPS §5.3.10 (GEN-06)", method="door parameter width_MOE (clear width for means of escape)",
                        object_id=r.id,
                        fix="" if st == "PASS" else "Report the clear width (width_MOE), not the leaf size")
                st2 = "PASS" if w_req is not None and min(widths) >= w_req else "FAIL"
                O.check("S10-WR-%d" % r.id, "AUD-S10", "Modelled clear width >= the table's required width", obj,
                        "%s mm (table requirement; FS Code value not verified)" % (int(w_req) if w_req else "-"),
                        "%s mm" % int(min(widths)), st2, cite="FS Code 2011 Part B (LIM-30, source missing)",
                        method="width_MOE vs table", object_id=r.id, confidence="medium")
        O.check("S10-LIM", "AUD-S10", "Occupancy factors, exit numbers and widths meet the FS Code", "all rows",
                "FS Code 2011 Table B1 / B2 values", "table values only", "UNCLEAR",
                cite="FS Code 2011 Part B (LIM-30)", method="source text not in Knowledge",
                fix="Provide FS Code 2011 Part B tables (DK-AUD-006 M-01)")
        O.check("S10-ROUTE", "AUD-S10", "Exit route widths", "all rows", "measured corridor width", "not measurable",
                "UNCLEAR", cite="FS Code 2011 Part B", method="no width / path tool (CAP-MEASURE-PATH)",
                fix="Measure corridor widths on plan (manual SOP)")
        missing = [r for r in placed if r.id not in listed and ufa_class(r)[0] == "included"]
        for r in missing:
            O.check("S10-L1-%d" % r.id, "AUD-S10", "Occupiable room listed in the table", r.label + " (" + r.level + ")",
                    "listed", "not listed", "FAIL", cite="BIMGBPS §5.3.10", method="rooms with usable floor area vs table rows",
                    object_id=r.id, fix="Add the room to the S10 schedule, or state why it is not an occupied room",
                    basis="Minor")
    tables["s10"] = {"title": "S10 table vs model per room", "columns": [
        "Room ID", "Room", "Level", "Table area (m²)", "Model area (m²)", "Factor", "Table capacity", "Calc. capacity",
        "Exits required (table)", "Exits provided (table)", "Doors on boundary (model)", "Width required (table, mm)",
        "Width provided (table, mm)", "Smallest clear width (model, mm)", "Doors (id, type, width_MOE)"], "rows": s10_rows}

    # ------------------------------------------------ S11 discharge values
    s11 = find_csv(a.raw, "GBP S11")
    s11_rows = []
    if s11:
        _, hdr, data = read_schedule_csv(s11)
        col = {h: i for i, h in enumerate(hdr)}
        g = lambda row, k: row[col[k]] if k in col and col[k] < len(row) else ""
        stairs = {}
        for r in placed:
            if re.match(r"^S-\d+$", r.name):
                stairs.setdefault(r.level, set()).add(r.name)
        per_stair_dv = {}
        for row in data:
            lv = g(row, "Level")
            if not lv:
                continue
            for s in ("S-1", "S-2"):
                tc, ns, tt = num(g(row, s + " TOTAL CAPACITY")), num(g(row, s + " NO. OF STAIRCASE")), num(g(row, s + " TOTAL"))
                if tc is None:
                    continue
                exp_tc = s10_cap.get(lv)
                O.check("S11-L2-%s-%s" % (lv[-3:], s), "AUD-S11", "Floor capacity equals the S10 total", "%s, %s" % (lv, s),
                        exp_tc, tc, "PASS" if exp_tc == tc else "FAIL", cite="BIMGBPS §5.3.11 (GEN-06)",
                        method="sum of S10 room capacities on the level")
                n_model = len(stairs.get(lv, ()))
                O.check("S11-N-%s-%s" % (lv[-3:], s), "AUD-S11", "Number of staircases equals the model", "%s, %s" % (lv, s),
                        n_model, ns, "PASS" if n_model == ns else "FAIL", method="staircase rooms (S-n) on the level")
                exp_tt = ceil_div(tc, ns) if ns else None
                O.check("S11-C-%s-%s" % (lv[-3:], s), "AUD-S11", "Persons per staircase = capacity / staircases, rounded up",
                        "%s, %s" % (lv, s), exp_tt, tt, "PASS" if exp_tt == tt else "FAIL", method="ceil(capacity / n)")
                per_stair_dv[s] = per_stair_dv.get(s, 0) + (tt or 0)
                s11_rows.append([lv, s, exp_tc, tc, n_model, ns, exp_tt, tt])
            dv_total, dv_perm = num(g(row, "DV TOTAL PERSON")), num(g(row, "DV PERMISSIBLE S-1"))
            s11_rows.append([lv, "DV total (table)", None, None, None, None, None, dv_total])
        for s, v in sorted(per_stair_dv.items()):
            O.check("S11-DV-%s" % s, "AUD-S11", "Discharge value per staircase <= permissible", s,
                    "%s (table; FS Code B12 value not verified)" % (int(dv_perm) if dv_perm else "-"), v,
                    "UNCLEAR", cite="FS Code 2011 B12 (LIM-30, source missing)",
                    method="sum of persons per staircase over the floors served",
                    evidence="Table 'DV TOTAL PERSON' = %s adds both staircases; per staircase = %d" % (dv_total, v),
                    fix="Provide FS Code Table B12 to confirm the permissible DV; show DV per staircase, not the sum")
    tables["s11"] = {"title": "S11 discharge value check", "columns": [
        "Level", "Staircase", "S10 total capacity", "Table capacity", "Staircases (model)", "Staircases (table)",
        "Persons per stair (calc.)", "Persons per stair (table)"], "rows": s11_rows}

    # ------------------------------------------------ S15 refuse (Cap. 123H), S16 TBE (Cap. 123F reg 28A)
    ufs_low = sum(r.area for r in placed if ufa_class(r)[0] == "included")
    # upper bound: per storey, the plan box enclosing that storey's rooms (any floor space lies inside it);
    # storeys whose rooms are all roof / staircase / lift / plant are left out (not usable floor space).
    upper, ub_rows = 0.0, []
    for lv in levels:
        rs = [r for r in placed if r.level == lv]
        if all(ufa_class(r)[0] != "included" for r in rs):
            ub_rows.append(lv + ": no usable rooms (roof / staircase / lift / plant)")
            continue
        bx = (max(r.bb[3] for r in rs) - min(r.bb[0] for r in rs)) * (max(r.bb[4] for r in rs) - min(r.bb[1] for r in rs)) * 0.09290304
        upper += bx
        ub_rows.append("%s: %.3f m² plan box" % (lv, bx))
    all_rooms = upper
    thr = 3960.0
    st = "N/A" if upper < thr else ("APPLICABLE" if ufs_low >= thr else "UNCLEAR")
    O.check("S15-APL", "AUD-S15", "Refuse storage and material recovery chamber required (Cap. 123H)",
            "building (%s, non-domestic)" % a.use, "UFS >= %.0f m²" % thr,
            "UFS from rooms %.3f m² (lower bound); storey plan boxes %.3f m² (upper bound)" % (ufs_low, upper),
            "N/A" if st == "N/A" else st, cite="Cap. 123H reg 3, Schedule (LIM-19)",
            method="room areas less staircases, lift landings, lavatories and plant (Cap. 123H usable floor space)",
            confidence="medium", basis="conditional",
            evidence="Upper bound by storey: " + "; ".join(ub_rows) + ". Even the gross plan boxes are below the threshold.",
            fix="State N/A on the drawings with the reason (APL-03), or confirm UFS with the area scheme")
    tbe = [r for r in placed if re.search(r"TBE|TELECOM|BROADCAST", r.name, re.I)]
    O.check("S16-APL", "AUD-S16", "TBE room required (Cap. 123F reg 28A)", "building (%s)" % a.use,
            "commercial, industrial, residential or hotel building", a.use, "N/A", cite="Cap. 123F reg 28A (LIM-18)",
            method="building use from the project title (AP to confirm)", confidence="medium", basis="conditional",
            evidence="Rooms named TBE / telecom in the model: %d" % len(tbe),
            fix="AP to confirm the building is not a 'commercial building' (term undefined in Cap. 123); state N/A on drawings")

    # ------------------------------------------------ S14 hand-off: rooms with soil fitments
    soil = [[r.id, r.label, r.level, ", ".join(sorted({f["kind"] for f in by_room[r.id]}))] for r in placed if r.id in soil_rooms]
    tables["soil_rooms"] = {"title": "Rooms with soil fitments (reg 36 applies - used by S14)", "columns": [
        "Room ID", "Room", "Level", "Fitments"], "rows": soil}

    # ------------------------------------------------ summary + output
    tasks = list(GROUP)
    per = {}
    for c in O.checks:
        p = per.setdefault(c["task"], {"PASS": 0, "FAIL": 0, "UNCLEAR": 0, "N/A": 0, "APPLICABLE": 0})
        p[c["status"]] = p.get(c["status"], 0) + 1
    O.warnings += [
        "Fixture and door association to rooms is computed from room outlines / boxes and element boxes "
        "(revit-mcp returns no room for fixtures or doors) - see method and confidence per check.",
        "Accessible WCs are unisex and are not counted towards the male / female numbers.",
        "S13 basis B (function rooms and activity areas as places of public entertainment) is a sensitivity case; "
        "the AP decides the category (INP-12).",
        "FS Code 2011 Part B is not in Knowledge: S10 / S11 limits are reported as UNCLEAR with the table's own values.",
    ]
    out = {
        "project_info": {"project_name": a.project, "model_path": a.model, "group": "G2 room-use",
                         "tasks": tasks, "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "read_only": True, "building_use": a.use,
                         "rules": {"S13": "Cap. 123I reg 3 (UFA), reg 5 Tables 5-7 (office 1/9 m², 1:1), reg 6 Tables 8-10 (PPE 1/0.5 m², 1:1.5)",
                                   "S10/S11": "FS Code 2011 Part B - not in Knowledge (LIM-30 GAP)",
                                   "S15": "Cap. 123H reg 3 and Schedule: non-domestic UFS >= 3,960 m²",
                                   "S16": "Cap. 123F reg 28A"}},
        "checks": O.checks,
        "tables": tables,
        "summary": {"per_task": per, "checks": len(O.checks),
                    "fail": sum(1 for c in O.checks if c["status"] == "FAIL"),
                    "unclear": sum(1 for c in O.checks if c["status"] == "UNCLEAR"),
                    "fixtures": len(fixtures), "doors": len(doors), "rooms": len(placed),
                    "data_quality_warnings": O.warnings},
    }
    T.finish(out, wanted, GROUP, gp, TABLE_TASKS)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print_summary(out)
    return 0


def print_summary(d):
    s = d["summary"]
    print("=" * 78)
    print("G2 room-use (%s) - %s" % (", ".join(t[4:] for t in d["project_info"]["tasks"]), d["project_info"]["project_name"]))
    print("=" * 78)
    print("Extract: %d rooms, %d plumbing fixtures, %d doors | %d checks: %d FAIL, %d UNCLEAR"
          % (s["rooms"], s["fixtures"], s["doors"], s["checks"], s["fail"], s["unclear"]))
    for t, p in s["per_task"].items():
        print("  %-8s %s" % (t, ", ".join("%s %d" % (k, v) for k, v in p.items() if v)))
    print("-" * 78)
    for c in d["checks"]:
        if c["status"] in ("FAIL", "UNCLEAR", "N/A", "APPLICABLE"):
            print("  [%s] %s | %s | expected %s | actual %s" % (c["status"], c["id"], c["object"], c["expected"], c["actual"]))
    print("-" * 78)
    for w in s["data_quality_warnings"]:
        print("! " + w)


if __name__ == "__main__":
    sys.exit(main())
