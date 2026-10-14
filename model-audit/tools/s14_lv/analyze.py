#!/usr/bin/env python3
"""TL-S14 lighting & ventilation analysis (Cap. 123F reg 30 / reg 36).

Read-only. Works only on the extract files listed in L3-SOP recipe R-S14
(rooms.tsv, room_polygons.json, cw_*.tsv, pn_*.tsv, pn_bbox_sample.tsv,
fs_windows.tsv, doors.tsv, doors_other.tsv). Never queries Revit, never
invents values: anything the extract does not carry is reported as a gap.

Usage:
  python analyze.py --raw <extract dir> --project <name> --model <path> --out <json>
                    [--rules rules.json] [--previous <old analysis json>]
Stdlib only. Exit 0 = written, 2 = input missing/invalid.
"""
import argparse
import csv
import datetime
import glob
import json
import os
import re
import sys

FT = 0.3048
SQFT = FT * FT

# --- default rules (L1 DK-AUD-002 LIM-xx; overridable with --rules) ---------
DEFAULT_RULES = {
    "reg30": {"light": 1 / 10, "vent": 1 / 16, "cite": "Cap. 123F reg 30(2)(a)(i),(ii)"},
    "reg36": {"light": 1 / 10, "vent": 1 / 10, "cite": "Cap. 123F reg 36(2)(a),(b)"},
    "opening_top_min_m": 2.0,          # reg 30(2)(a)(ii), reg 36(3)
    "ffl_over_sfl_m": 0.05,            # level names SFL 0.25 / FFL 0.30
    "probe_extra_ft": 1.0,             # probe distance beyond wall face
    "probe_samples": 9,
    "min_z_overlap_ft": 1.0,
    "rect_ratio": 1.04,                # bbox/area above this = non-rectangular room
    # name rules: first match wins; (regex, group, reason)
    "room_rules": [
        [r"\bLAV\b|TOILET|WC\b|BATH|SHOWER", "reg36",
         "Contains soil fitments (lavatory) - reg 36 applies: glass >= 1/10 and openable >= 1/10"],
        [r"^OFFICE$|CONFERENCE", "reg30",
         "Office use - reg 30(1) applies directly"],
        [r"^RECEPTION$", "reg30",
         "Staffed reception (office-type use) - reg 30 applied"],
        [r"FUNCTION ROOM|ACTIVITY AREA", "reg30",
         "Occupied room - reg 30 applied by the operator's occupied-room rule; reg 30(1) scope is habitation/office/kitchen, AP to confirm use class"],
        [r"^TX RM$|^AHU$|PFWTPR|FSSPRPR|FSWT|SPRWT|^MSR$|^FCC$", "excluded",
         "Plant / building-services / fire-service room - not habitation, office or kitchen"],
        [r"^STORE$", "excluded", "Store - not habitation, office or kitchen"],
        [r"^ENT HALL$|^FLL$|^ELV$|^S-\d+$", "excluded",
         "Circulation (entrance hall, fireman's lift lobby, lift shaft, staircase)"],
        [r"^ELR$", "excluded", "Electric room (A001 abbreviation legend: 'ELR - ELECTRIC ROOM'; GFA scheme deducts it as "
                               "essential plant, item 2.2) - not habitation, office or kitchen"],
        [r"^ROOM$", "pending", "Unnamed room ('Room') - use unknown, cannot classify"],
        [r"^GUARD ROOM$", "pending",
         "Guard room may be a staffed office-type room - AP to confirm whether reg 30 applies"],
        [r"^FR$", "excluded",
         "Flat roof (A001 abbreviation legend reads 'FR - FLAT'; roof level, 1,148 m2) - not a room [INFERENCE: 'flat roof']"],
    ],
}


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(2)


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_parts(raw, pattern):
    files = sorted(glob.glob(os.path.join(raw, pattern)))
    if not files:
        die("no files match " + pattern)
    rows = []
    for p in files:
        rows += read_tsv(p)
    return rows


def fnum(r, k):
    return float(r[k])


def point_in_poly(x, y, loop):
    inside = False
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


class Room:
    def __init__(self, r, polys, rules):
        self.id = int(r["id"])
        self.name = r["name"]
        self.number = r["number"]
        self.level = r["level"]
        self.area = fnum(r, "area_m2")
        self.bb = [fnum(r, k) for k in ("minx", "miny", "minz", "maxx", "maxy", "maxz")]
        self.poly = polys.get(str(self.id))
        bbox_area = (self.bb[3] - self.bb[0]) * (self.bb[4] - self.bb[1]) * SQFT
        self.rect = self.area > 0 and bbox_area / self.area <= rules["rect_ratio"]
        self.shape_source = ("polygon" if self.poly else
                             "bbox (rectangular)" if self.rect else "bbox (non-rectangular)")

    def contains_xy(self, x, y):
        b = self.bb
        if not (b[0] <= x <= b[3] and b[1] <= y <= b[4]):
            return False
        if self.poly:
            if not point_in_poly(x, y, self.poly[0]):
                return False
            return not any(point_in_poly(x, y, h) for h in self.poly[1:])
        return True

    def z_overlap(self, z0, z1):
        return min(z1, self.bb[5]) - max(z0, self.bb[2])


def classify_room(room, rules):
    if room.area <= 0:
        return "no_area", "Room has no area (unplaced or unbounded)"
    for pat, grp, why in rules["room_rules"]:
        if re.search(pat, room.name.strip(), re.I):
            return grp, why
    return "pending", "Name '%s' not covered by the classification rules" % room.name


def _num(text):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*m²\s*$", text or "")
    return float(m.group(1)) if m else None


def compare_schedule(path, rooms, inc, warnings, pen=()):
    """Compare the model's S14 schedule (CSV export) with the measured results, row by row."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = [l for l in text.splitlines() if l.strip()]
    probe = lines[1] if len(lines) > 1 else ""                 # revit-mcp exports commas, mcp-servers-for-revit tabs
    rows = list(csv.reader(text.splitlines(), delimiter="\t" if probe.count("\t") > probe.count(",") else ","))
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "Level")
    hdr = rows[hdr_i]
    col = {h: i for i, h in enumerate(hdr)}
    by_key = {}
    for d in list(inc) + list(pen):
        by_key.setdefault((d["level"], d["name"]), []).append(d)
    out, seen = [], set()
    for r in rows[hdr_i + 1:]:
        if not any(r):
            continue
        g = lambda k: r[col[k]] if k in col and col[k] < len(r) else ""
        level, name = g("Level"), g("Name")
        area = _num(g("Area"))
        req_l = _num(g("10% OF WINDOW AREA"))
        req_v = _num(g("6.25% OF OPENABLE AREA")) or _num(g("10% OF OPENABLE AREA"))
        prov_txt = g("PROVIDED WINDOW AND OPENABLE AREA")
        prov = _num(prov_txt)
        notional = g("NOTIONAL AREA")
        cands = by_key.get((level, name), [])
        rec = {"level": level, "name": name, "window_mark": g("WINDOW MARK"), "table_area_sqm": area,
               "table_notional_area": None if notional in ("", "-") else notional,
               "table_req_light_sqm": req_l, "table_req_vent_sqm": req_v,
               "table_provided_text": prov_txt, "table_provided_sqm": prov,
               "room_id": None, "exact_req_light_sqm": None, "exact_req_vent_sqm": None,
               "measured_light_sqm": None, "measured_vent_sqm": None, "model_status": None, "issues": []}
        if len(cands) != 1:
            rec["issues"].append("No single room matches level + name (%d found)" % len(cands))
        elif cands[0]["classification"] == "pending":
            d = cands[0]
            seen.add(d["id"])
            gl = sum(o["glass_sqm"] for o in d.get("openings_found", []) if o["facing"] == "external")
            vt = sum(o["vent_sqm"] for o in d.get("openings_found", []) if o["facing"] == "external")
            rec.update({"room_id": d["id"], "measured_light_sqm": round(gl, 3), "measured_vent_sqm": round(vt, 3),
                        "model_status": "PENDING"})
            rec["issues"].append("Room is pending in this analysis (%s); the table treats it as applicable - "
                                 "measured external glass %.3f, openable %.3f" % (d["classification_reason"], gl, vt))
            if re.search(r"[x×*]", prov_txt):
                rec["issues"].append("Provided area is a typed formula, not a model value")
        else:
            d = cands[0]
            seen.add(d["id"])
            rec.update({"room_id": d["id"], "exact_req_light_sqm": d["req_light_sqm"],
                        "exact_req_vent_sqm": d["req_vent_sqm"], "measured_light_sqm": d["act_light_sqm"],
                        "measured_vent_sqm": d["act_vent_sqm"], "model_status": d["status"]})
            if req_l is not None and req_l + 1e-9 < d["req_light_sqm"]:
                why = ("rounded down" if not rec["table_notional_area"] and d["req_light_sqm"] - req_l < 0.1
                       else "different basis")
                rec["issues"].append("Required glass %.3f in the table is below the exact %.3f (%s)"
                                     % (req_l, d["req_light_sqm"], why))
            if req_v is not None and req_v + 1e-9 < d["req_vent_sqm"]:
                rec["issues"].append("Required openable %.3f in the table is below the exact %.3f"
                                     % (req_v, d["req_vent_sqm"]))
            if rec["table_notional_area"]:
                rec["issues"].append("Requirement computed on a notional area (%s) instead of the floor area %.3f m²"
                                     % (rec["table_notional_area"], d["area_sqm"]))
            if re.search(r"[x×*]", prov_txt):
                rec["issues"].append("Provided area is a typed formula, not a model value")
            if prov is not None and abs(prov - d["act_light_sqm"]) > 0.05:
                rec["issues"].append("Table provided %.3f differs from the measured glass %.3f (openable %.3f)"
                                     % (prov, d["act_light_sqm"], d["act_vent_sqm"]))
        out.append(rec)
    missing = [{"id": d["id"], "name": d["name"], "number": d["number"], "level": d["level"], "status": d["status"]}
               for d in inc if d["id"] not in seen]
    if missing:
        warnings.append("%d assessed rooms are not in the model's S14 schedule (it lists rooms with a WINDOW MARK only)."
                        % len(missing))
    return {"source": os.path.basename(path), "rows": out, "missing_rooms": missing,
            "note": "The schedule is a room schedule filtered on WINDOW MARK; its provided column is typed text."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rules")
    ap.add_argument("--previous")
    ap.add_argument("--revit-instance", default="")
    ap.add_argument("--schedule", help="CSV export of the model's S14 schedule (optional)")
    ap.add_argument("--fixtures", help="fixtures.tsv from R-G2 (optional): rooms holding a WC or urinal are reg 36 rooms")
    a = ap.parse_args()

    rules = dict(DEFAULT_RULES)
    if a.rules:
        with open(a.rules, encoding="utf-8-sig") as f:
            rules.update(json.load(f))
    raw = a.raw
    for need in ("rooms.tsv", "fs_windows.tsv"):
        if not os.path.exists(os.path.join(raw, need)):
            die("missing " + need)

    polys = {}
    pp = os.path.join(raw, "room_polygons.json")
    if os.path.exists(pp):
        with open(pp, encoding="utf-8-sig") as f:
            polys = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    rooms = [Room(r, polys, rules) for r in read_tsv(os.path.join(raw, "rooms.tsv"))]
    walls = read_parts(raw, "cw_*.tsv")
    panels = read_parts(raw, "pn_*.tsv")
    panels = [p for p in panels if "kind" in p]          # skip pn_bbox_sample.tsv
    bad = [p["id"] for p in panels if p["kind"] not in ("H", "L")]
    if bad:
        die("panel kind must be H (hung, from Glazed_Panel family) or L (Louvre_Panel family); got other values for "
            "%d panel(s): %s. Re-extract with the family name (R-S14 step 4)." % (len(bad), ", ".join(bad[:10])))
    samples = {}
    sp = os.path.join(raw, "pn_bbox_sample.tsv")
    if os.path.exists(sp):
        samples = {int(r["id"]): (fnum(r, "minz"), fnum(r, "maxz")) for r in read_tsv(sp)}
    fsw = read_tsv(os.path.join(raw, "fs_windows.tsv"))
    doors = read_tsv(os.path.join(raw, "doors.tsv")) if os.path.exists(os.path.join(raw, "doors.tsv")) else []
    doors_other = read_tsv(os.path.join(raw, "doors_other.tsv")) if os.path.exists(os.path.join(raw, "doors_other.tsv")) else []

    warnings = []
    # building footprint = extent of all bounded rooms
    placed = [r for r in rooms if r.area > 0]
    fp = (min(r.bb[0] for r in placed), min(r.bb[1] for r in placed),
          max(r.bb[3] for r in placed), max(r.bb[4] for r in placed))

    def outside_fp(x, y):
        return x < fp[0] or x > fp[2] or y < fp[1] or y > fp[3]

    # ---------------- rooms: classification ----------------
    for r in rooms:
        r.group, r.reason = classify_room(r, rules)
    if a.fixtures:
        soil = {}
        for fx in read_tsv(a.fixtures):
            if not re.search(r"Toilet_Cubicle|URN", fx["family"]):
                continue
            x, y, z = float(fx["cx"]), float(fx["cy"]), float(fx["z"]) + 1.0
            hits = [r for r in rooms if r.area > 0 and r.bb[2] - 0.05 <= z < r.bb[5] and r.contains_xy(x, y)]
            if hits:
                soil.setdefault(min(hits, key=lambda r: r.area).id, []).append(fx["id"])
        for r in rooms:
            if r.id in soil and r.group != "reg36":
                r.group, r.reason = "reg36", ("Contains soil fitments (fixtures %s) - reg 36 applies: glass >= 1/10 and "
                                              "openable >= 1/10; classified by fixture evidence, not by name"
                                              % ", ".join(soil[r.id][:3]))
    for r in rooms:
        if r.group == "excluded" and re.match(r"^S-\d+$", r.name) and r.area > 200:
            warnings.append("Room %d '%s %s' on %s is a staircase name with %.3f m2 - implausible; "
                            "check whether it is a roof area mis-named (excluded either way)."
                            % (r.id, r.name, r.number, r.level, r.area))

    # ---------------- walls: association by side probes ----------------
    W = {}
    for w in walls:
        wid = int(w["id"])
        bb = [fnum(w, k) for k in ("minx", "miny", "minz", "maxx", "maxy", "maxz")]
        W[wid] = {"row": w, "bb": bb, "panels": []}

    # typical bbox thickness of the curtain-wall types (mode of the smaller plan extent)
    mins = [round(min(w["bb"][3] - w["bb"][0], w["bb"][4] - w["bb"][1]), 2) for w in W.values()]
    t_typ = max(set(mins), key=mins.count)

    def probe_wall(bb):
        dx, dy = bb[3] - bb[0], bb[4] - bb[1]
        tx, ty = abs(dx - t_typ) < 0.05, abs(dy - t_typ) < 0.05
        if tx != ty:                 # exactly one extent equals the type thickness -> that is the normal
            return probe_axis(bb, "x" if tx else "y")
        if abs(dx - dy) < 0.1:      # square bbox: normal = axis nearer the footprint edge
            cx, cy = (bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2
            ex = min(abs(cx - fp[0]), abs(cx - fp[2]))
            ey = min(abs(cy - fp[1]), abs(cy - fp[3]))
            axis = "x" if ex <= ey else "y"
        else:
            axis = "x" if dx < dy else "y"
        return probe_axis(bb, axis)

    def probe_axis(bb, axis, extra=None):
        t = (bb[3] - bb[0]) if axis == "x" else (bb[4] - bb[1])
        n = rules["probe_samples"]
        off = t / 2 + (rules["probe_extra_ft"] if extra is None else extra)
        sides = {"-": [], "+": []}
        for s, sign in (("-", -1), ("+", 1)):
            for i in range(n):
                f = (i + 0.5) / n
                if axis == "x":
                    x = (bb[0] + bb[3]) / 2 + sign * off
                    y = bb[1] + f * (bb[4] - bb[1])
                else:
                    y = (bb[1] + bb[4]) / 2 + sign * off
                    x = bb[0] + f * (bb[3] - bb[0])
                best, bz = None, rules["min_z_overlap_ft"]
                for r in placed:
                    zo = r.z_overlap(bb[2], bb[5])
                    if zo >= bz and r.contains_xy(x, y):
                        best, bz = r, zo
                sides[s].append((best, outside_fp(x, y)))
        return axis, sides

    rooms_by_id = {r.id: r for r in rooms}
    for wid, w in W.items():
        axis, sides = probe_wall(w["bb"])
        info = {}
        for s in ("-", "+"):
            hits = [h for h, _ in sides[s] if h]
            ids = {}
            for h in hits:
                ids[h.id] = ids.get(h.id, 0) + 1
            info[s] = {"ids": ids, "n_hit": len(hits),
                       "outside": all(o for h, o in sides[s] if not h) and len(hits) < len(sides[s]),
                       "all_outside": all(o for _, o in sides[s])}
        w["axis"] = axis
        a_, b_ = info["-"], info["+"]
        n = rules["probe_samples"]
        if a_["n_hit"] and b_["n_hit"]:
            ra = max(a_["ids"], key=a_["ids"].get)
            rb = max(b_["ids"], key=b_["ids"].get)
            w["facing"] = "internal-same-room" if ra == rb else "internal"
            w["adjacent"] = sorted(set(a_["ids"]) | set(b_["ids"]))
            w["assign"] = {}
        elif a_["n_hit"] or b_["n_hit"]:
            room_side, other = (a_, b_) if a_["n_hit"] else (b_, a_)
            w["facing"] = "external" if other["all_outside"] else "unroomed"
            w["adjacent"] = sorted(room_side["ids"])
            tot = room_side["n_hit"]
            w["assign"] = {rid: c / tot for rid, c in room_side["ids"].items()}
            w["hit_ratio"] = tot / n
        else:
            w["facing"] = "none"
            w["adjacent"] = []
            w["assign"] = {}
            w["all_outside"] = a_["all_outside"] and b_["all_outside"]
            w["nearest"] = None
            for ext in (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0):
                _, sd = probe_axis(w["bb"], axis, ext)
                found = [h for s_ in sd.values() for h, _o in s_ if h]
                if found:
                    nr = max(set(found), key=found.count)
                    w["nearest"] = (nr, round(ext * FT, 2))
                    break

    # ---------------- panels -> host wall ----------------
    tol = 0.2
    orphan_panels = []
    for p in panels:
        cx, cy, cz = fnum(p, "cx"), fnum(p, "cy"), fnum(p, "cz")
        cands = [(wid, w) for wid, w in W.items()
                 if w["bb"][0] - tol <= cx <= w["bb"][3] + tol
                 and w["bb"][1] - tol <= cy <= w["bb"][4] + tol
                 and w["bb"][2] - tol <= cz <= w["bb"][5] + tol]
        if not cands:
            orphan_panels.append(p)
            continue
        wid, w = min(cands, key=lambda c: (c[1]["bb"][3] - c[1]["bb"][0]) * (c[1]["bb"][4] - c[1]["bb"][1]))
        w["panels"].append(p)
        p["host"] = wid

    # half-heights from sampled bboxes, grouped by (type, cz)
    half = {}
    pid = {int(p["id"]): p for p in panels}
    for sid, (z0, z1) in samples.items():
        if sid in pid:
            p = pid[sid]
            half[(p["type"], round(fnum(p, "cz"), 1))] = ((z1 - z0) / 2, sid)
    unmeasured = set()
    for p in panels:
        key = (p["type"], round(fnum(p, "cz"), 1))
        if key in half:
            h, sid = half[key]
            p["top_z"] = fnum(p, "cz") + h
            p["top_src"] = "bbox sample %d (same type, same centre height)" % sid
        else:
            p["top_z"] = None
            p["top_src"] = "not measured"
            if p["kind"] == "H":
                unmeasured.add(key)
    if unmeasured:
        warnings.append("Opening-top height not measured for panel groups %s - 2 m test shown as unknown."
                        % sorted(unmeasured))

    # ---------------- per-wall amounts and opening records ----------------
    min_top_ft = rules["opening_top_min_m"] / FT
    ffl_ft = rules["ffl_over_sfl_m"] / FT
    openings_all, unassigned = [], []
    room_hits = {r.id: [] for r in rooms}
    for wid, w in sorted(W.items()):
        row, bb = w["row"], w["bb"]
        area = fnum(row, "area_m2")
        typ = row["type"]
        is_louvre_wall = "louvre" in typ.lower()
        louv = [p for p in w["panels"] if p["kind"] == "L"]
        hung = [p for p in w["panels"] if p["kind"] == "H"]
        louvre_sqm = sum(fnum(p, "area_m2") for p in louv)
        glass_sqm = 0.0 if is_louvre_wall else max(area - louvre_sqm, 0.0)
        hung_sqm = sum(fnum(p, "area_m2") for p in hung)
        if is_louvre_wall:
            cls = "louvre (needs review)"
        elif hung and louv:
            cls = "glazing with openable hung panels and louvre panels"
        elif hung:
            cls = "glazing with openable hung panels"
        elif louv:
            cls = "glazing with louvre panels (needs review)"
        else:
            cls = "fixed glazing"
        facing = w["facing"]
        counted = facing == "external" and bool(w["assign"])
        # floor of the (main) assigned room, for the 2 m test
        main_room = rooms_by_id[max(w["assign"], key=w["assign"].get)] if w["assign"] else None
        panel_recs = []
        for p in w["panels"]:
            top_m = None
            ok2m = None
            if main_room is not None and p["top_z"] is not None:
                top_m = (p["top_z"] - (main_room.bb[2] + ffl_ft)) * FT
                ok2m = top_m >= rules["opening_top_min_m"] - 1e-9
            vent_ok = counted and p["kind"] == "H" and ok2m is not False
            panel_recs.append({
                "id": int(p["id"]), "kind": "openable (hung)" if p["kind"] == "H" else "louvre",
                "type": p["type"], "area_sqm": round(fnum(p, "area_m2"), 3),
                "top_above_ffl_m": None if top_m is None else round(top_m, 3),
                "top_ge_2m": ok2m, "top_source": p["top_src"],
                "counted_ventilation": vent_ok,
            })
        vent_counted = sum(pr["area_sqm"] for pr in panel_recs if pr["counted_ventilation"])
        hung_below_2m = [pr["id"] for pr in panel_recs if pr["kind"].startswith("openable") and pr["top_ge_2m"] is False]
        # match description
        if facing == "external":
            share = w["assign"]
            nonrect = any(not rooms_by_id[i].rect and not rooms_by_id[i].poly for i in share)
            if len(share) > 1:
                conf, meth = "medium", "side probe (%d samples), area split by probe hits" % rules["probe_samples"]
            elif w.get("hit_ratio", 1) < 0.5 or nonrect:
                conf, meth = "medium", "side probe (%d samples), partial or non-rectangular room bbox" % rules["probe_samples"]
            else:
                conf, meth = "high", "side probe (%d samples): room on one side, outside the building footprint on the other" % rules["probe_samples"]
        elif facing == "unroomed":
            conf, meth = "low", "side probe: room on one side, unroomed space inside the footprint on the other"
        elif facing.startswith("internal"):
            conf, meth = "high", "side probe: rooms on both sides"
        else:
            conf, meth = None, "side probe: no room on either side"
        notes = []
        notes.append("Glass area = curtain wall Area (model-computed) minus louvre panels in it; mullion/frame not deducted (overstates glass slightly).")
        if hung:
            notes.append("Openable area = full area of each hung panel (Glazed_Panel '... hung'); actual sash opening not modelled.")
        if louv or is_louvre_wall:
            notes.append("Louvre is not glass and not an openable window; free area not modelled - shown separately, not counted.")
        if facing.startswith("internal"):
            notes.append("Internal glazing between rooms - not a prescribed window facing external air (reg 30(2)(b)); not counted.")
        if facing == "unroomed":
            notes.append("Faces unroomed space inside the building footprint (void / roof / shaft) - facing external air not proven; not counted, AP to confirm.")
        if facing == "none":
            notes.append("No room on either side at this height%s." % (
                " - element is outside the building footprint (site structure)" if w.get("all_outside") else ""))
            if w.get("nearest"):
                nr, dist = w["nearest"]
                notes.append("Hint only: nearest room is %s %s (%s), about %.1f m beyond the wall face; the space between has no room, so not counted."
                             % (nr.name, nr.number, nr.level, dist))
        if hung_below_2m:
            notes.append("Hung panels %s have opening top below 2 m above FFL - not counted (reg 30(2)(a)(ii)/36(3))." % hung_below_2m)
        rec = {
            "id": wid, "category": "Walls (Curtain Wall)", "family": "Curtain Wall", "type": typ,
            "mark": row.get("mark", ""), "level": row["level"], "area_sqm": round(area, 3),
            "classification": cls, "facing": facing,
            "glass_sqm": round(glass_sqm, 3), "openable_sqm": round(hung_sqm, 3),
            "louvre_sqm": round(louvre_sqm if not is_louvre_wall else area, 3),
            "counted_lighting": counted and glass_sqm > 0,
            "counted_ventilation": vent_counted > 0,
            "panel_vent_sqm": round(vent_counted, 3),
            "data_source": "query_model OST_Walls (curtain) + get_element_data Area/boundingBox; panels via OST_CurtainWallPanels centre-in-host-bbox",
            "assumption_note": " ".join(notes),
            "matched_room_id": None, "matched_room_name": None,
            "adjacent_room_ids": w["adjacent"],
            "adjacent_room_names": ["%s %s" % (rooms_by_id[i].name, rooms_by_id[i].number) for i in w["adjacent"]],
            "match_method": meth, "match_confidence": conf,
            "nearest_room_id": w["nearest"][0].id if w.get("nearest") else None,
            "nearest_room_distance_m": w["nearest"][1] if w.get("nearest") else None,
            "panels": panel_recs,
        }
        if w["assign"]:
            mr = max(w["assign"], key=w["assign"].get)
            rec["matched_room_id"] = mr
            rec["matched_room_name"] = "%s %s" % (rooms_by_id[mr].name, rooms_by_id[mr].number)
            rec["room_shares"] = {str(k): round(v, 3) for k, v in w["assign"].items()}
            for rid, sh in w["assign"].items():
                room_hits[rid].append((rec, sh))
        else:
            unassigned.append(rec)
        for rid in w["adjacent"]:
            if facing.startswith("internal") or facing == "unroomed":
                if rid not in w["assign"]:
                    room_hits[rid].append((rec, 0.0))
        openings_all.append(rec)

    for p in orphan_panels:
        warnings.append("Panel %s (%s) is not inside any curtain wall bbox - not used." % (p["id"], p["type"]))

    # ---------------- per-room compliance ----------------
    def room_rec(r):
        d = {"id": r.id, "name": r.name, "number": r.number, "level": r.level,
             "area_sqm": round(r.area, 3), "classification": r.group,
             "classification_reason": r.reason, "shape_source": r.shape_source}
        if r.group not in ("reg30", "reg36"):
            return d
        rule = rules[r.group]
        req_l = r.area * rule["light"]
        req_v = r.area * rule["vent"]
        act_l = act_v = louv = 0.0
        mo = []
        for rec, sh in room_hits[r.id]:
            cl = rec["glass_sqm"] * sh if rec["counted_lighting"] else 0.0
            cv = rec["panel_vent_sqm"] * sh
            act_l += cl
            act_v += cv
            louv += rec["louvre_sqm"] * sh if rec["facing"] == "external" else 0.0
            mo.append({"id": rec["id"], "type": rec["type"], "mark": rec["mark"], "level": rec["level"],
                       "classification": rec["classification"], "facing": rec["facing"],
                       "share": round(sh, 3),
                       "glass_sqm": round(rec["glass_sqm"] * sh, 3),
                       "counted_light_sqm": round(cl, 3), "counted_vent_sqm": round(cv, 3),
                       "louvre_sqm": round(rec["louvre_sqm"] * sh, 3) if rec["facing"] == "external" else 0.0,
                       "match_method": rec["match_method"], "match_confidence": rec["match_confidence"],
                       "counted": cl > 0 or cv > 0})
        near = [{"id": o["id"], "type": o["type"], "glass_sqm": o["glass_sqm"], "openable_sqm": o["openable_sqm"],
                 "distance_m": o["nearest_room_distance_m"]}
                for o in unassigned if o.get("nearest_room_id") == r.id]
        lp = act_l >= req_l - 1e-9
        vp = act_v >= req_v - 1e-9
        vpl = act_v + louv >= req_v - 1e-9
        d.update({
            "rule": r.group, "rule_cite": rule["cite"],
            "light_ratio": "1/%d" % round(1 / rule["light"]), "vent_ratio": "1/%d" % round(1 / rule["vent"]),
            "req_light_sqm": round(req_l, 3), "req_vent_sqm": round(req_v, 3),
            "act_light_sqm": round(act_l, 3), "act_vent_sqm": round(act_v, 3),
            "act_louvre_sqm": round(louv, 3),
            "light_margin_sqm": round(act_l - req_l, 3), "vent_margin_sqm": round(act_v - req_v, 3),
            "light_pass": lp, "vent_pass": vp, "both_pass": lp and vp,
            "vent_pass_if_louvre_counted": vpl,
            "status": "PASS" if lp and vp else ("FAIL*" if lp and not vp and vpl else "FAIL"),
            "matched_openings": mo,
            "glazing_beyond_boundary": near,
        })
        return d

    inc = [room_rec(r) for r in rooms if r.group in ("reg30", "reg36")]
    exc = [room_rec(r) for r in rooms if r.group == "excluded"]
    pen = [room_rec(r) for r in rooms if r.group == "pending"]
    noa = [room_rec(r) for r in rooms if r.group == "no_area"]
    # pending rooms: show what openings they would have (information only)
    for d in pen:
        hits = room_hits[d["id"]]
        d["openings_found"] = [{"id": rec["id"], "type": rec["type"], "facing": rec["facing"],
                                "glass_sqm": round(rec["glass_sqm"] * sh, 3),
                                "vent_sqm": round(rec["panel_vent_sqm"] * sh, 3)} for rec, sh in hits]

    # ---------------- level correspondence ----------------
    lc = {}
    for rec in openings_all:
        for rid in rec["adjacent_room_ids"]:
            rl = rooms_by_id[rid].level
            lc.setdefault(rl, set()).add(rec["level"])
    room_levels = sorted({r.level for r in rooms}, key=lambda s: min(x.bb[2] for x in rooms if x.level == s))
    level_corr = []
    for rl in room_levels:
        ol = sorted(lc.get(rl, []))
        level_corr.append({"room_level": rl,
                           "opening_levels_matched_by_geometry": ol,
                           "opening_level_same_name_found": rl in ol,
                           "floor_z_ft": round(min(x.bb[2] for x in rooms if x.level == rl), 2)})
    wall_levels = sorted({rec["level"] for rec in openings_all})
    used = set().union(*lc.values()) if lc else set()
    for wl in wall_levels:
        if wl not in used:
            level_corr.append({"room_level": None, "opening_levels_matched_by_geometry": [wl],
                               "opening_level_same_name_found": False,
                               "note": "Openings hosted on this level touch no room"})

    fire = [{"id": int(f["id"]), "category": "Windows", "family": f["family"], "type": f["type"],
             "mark": f["mark"], "level": f["level"], "area_sqm": float(f["area_m2"]),
             "classification": "fire service installation window", "counted_lighting": False,
             "counted_ventilation": False,
             "assumption_note": "Fire-service access/installation window (family name) - excluded from L&V by rule."}
            for f in fsw]
    doors_out = [{"id": int(d["id"]), "family": d["family"], "type": d["type"], "level": d["level"],
                  "mark": d["mark"], "area_sqm": float(d["area_m2"]),
                  "note": ("Glazed door inside a curtain wall - its area is already part of the host wall area; not added again."
                           if any(W[w]["bb"][0] - 1 <= (float(d["minx"]) + float(d["maxx"])) / 2 <= W[w]["bb"][3] + 1
                                  and W[w]["bb"][1] - 1 <= (float(d["miny"]) + float(d["maxy"])) / 2 <= W[w]["bb"][4] + 1
                                  and W[w]["bb"][2] - 1 <= float(d["minz"]) <= W[w]["bb"][5]
                                  for w in W)
                           else "Door outside the building footprint (site entrance) - not a window of any room.")}
                 for d in doors]

    sched = compare_schedule(a.schedule, rooms, inc, warnings, pen) if a.schedule else None

    n_inc30 = sum(1 for d in inc if d["rule"] == "reg30")
    n_inc36 = sum(1 for d in inc if d["rule"] == "reg36")
    summary = {
        "total_rooms": len(rooms),
        "rooms_included_count": len(inc), "rooms_included_reg30": n_inc30, "rooms_included_reg36": n_inc36,
        "rooms_excluded_count": len(exc), "rooms_pending_count": len(pen), "rooms_no_area_count": len(noa),
        "total_openings_glazing_louvre": len(openings_all),
        "openings_counted_lighting": sum(1 for o in openings_all if o["counted_lighting"]),
        "openings_internal_glazing": sum(1 for o in openings_all if o["facing"].startswith("internal")),
        "openings_unassigned_count": len(unassigned),
        "openings_fire_service_count": len(fire),
        "panels_total": len(panels),
        "panels_openable": sum(1 for p in panels if p["kind"] == "H"),
        "panels_louvre": sum(1 for p in panels if p["kind"] == "L"),
        "doors_reviewed": len(doors) + sum(int(x["count"]) for x in doors_other),
        "lighting_pass_count": sum(1 for d in inc if d["light_pass"]),
        "ventilation_pass_count": sum(1 for d in inc if d["vent_pass"]),
        "both_pass_count": sum(1 for d in inc if d["both_pass"]),
        "lighting_fail_count": sum(1 for d in inc if not d["light_pass"]),
        "ventilation_fail_count": sum(1 for d in inc if not d["vent_pass"]),
        "pass_only_if_louvre_counted": sum(1 for d in inc if d["status"] == "FAIL*"),
        "data_quality_warnings": warnings + [
            "Wall-to-room association is computed by the agent from room polygons/bboxes and wall bboxes "
            "(revit-mcp has no IsPointInRoom / FromRoom-ToRoom for curtain walls) - see match_method and confidence.",
            "All 12 Windows-category elements are fire-service installation windows - listed separately, not counted.",
            "Reg 31 (prescribed window faces a street >= 4.5 m or a 21 m2 rectangular horizontal plane) is not "
            "computed - needs site boundary and neighbour geometry; 'external' here means only 'outside the building footprint'.",
            "No room has zero area in this model copy; rooms_no_area is empty.",
        ],
    }

    out = {
        "project_info": {
            "project_name": a.project, "model_path": a.model,
            "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "revit_instance_id": a.revit_instance,
            "task": "TL-S14 Lighting & Ventilation",
            "rules": {"reg30": "glass >= floor area x 1/10; openable >= floor area x 1/16 (Cap. 123F reg 30(2)(a))",
                      "reg36": "glass >= floor area x 1/10; openable >= floor area x 1/10 (Cap. 123F reg 36(2))",
                      "opening_top": "top of each counted opening >= 2 m above floor (reg 30(2)(a)(ii), reg 36(3))",
                      "erratum": "Training prompt / Knowledge TL-S14 gives 1/8 for lighting; legislation text (1/10) is used."},
            "read_only": True,
        },
        "level_correspondence": level_corr,
        "rooms_included": inc,
        "rooms_excluded": exc,
        "rooms_pending": pen,
        "rooms_no_area": noa,
        "openings_all": openings_all,
        "openings_unassigned": unassigned,
        "openings_fire_service": fire,
        "doors_reviewed": {"glazed_or_entrance": doors_out,
                           "other_families": doors_other,
                           "rule": "Doors are not windows under reg 30/36 unless glazed and facing external air; "
                                   "glazed doors found are either inside a counted curtain wall or outside the building."},
        "summary": summary,
    }
    if sched is not None:
        out["schedule_comparison"] = sched
        summary["schedule_rows"] = len(sched["rows"])
        summary["schedule_rows_with_issues"] = sum(1 for r in sched["rows"] if r["issues"])
        summary["assessed_rooms_missing_from_schedule"] = len(sched["missing_rooms"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print_summary(out, a.previous)
    return 0


def print_summary(d, previous):
    s = d["summary"]
    print("=" * 78)
    print("TL-S14 Lighting & Ventilation - %s" % d["project_info"]["project_name"])
    print("=" * 78)
    print("Rooms: %d total | included %d (reg30 %d, reg36 %d) | excluded %d | pending %d | no area %d"
          % (s["total_rooms"], s["rooms_included_count"], s["rooms_included_reg30"], s["rooms_included_reg36"],
             s["rooms_excluded_count"], s["rooms_pending_count"], s["rooms_no_area_count"]))
    print("Openings: %d curtain walls (%d counted for lighting, %d internal glazing, %d unassigned) | "
          "%d panels (%d hung, %d louvre) | %d fire-service windows | %d doors reviewed"
          % (s["total_openings_glazing_louvre"], s["openings_counted_lighting"], s["openings_internal_glazing"],
             s["openings_unassigned_count"], s["panels_total"], s["panels_openable"], s["panels_louvre"],
             s["openings_fire_service_count"], s["doors_reviewed"]))
    print("Results (included rooms): lighting pass %d / fail %d | ventilation pass %d / fail %d | both pass %d | "
          "pass only if louvre counted %d"
          % (s["lighting_pass_count"], s["lighting_fail_count"], s["ventilation_pass_count"],
             s["ventilation_fail_count"], s["both_pass_count"], s["pass_only_if_louvre_counted"]))
    print("-" * 78)
    print("%-9s %-18s %-14s %8s %4s %8s %8s %8s %8s %6s" % ("id", "room", "level", "area", "rule",
                                                             "reqL", "actL", "reqV", "actV", "status"))
    for r in d["rooms_included"]:
        print("%-9d %-18s %-14s %8.3f %4s %8.3f %8.3f %8.3f %8.3f %6s"
              % (r["id"], (r["name"] + " " + r["number"])[:18], r["level"][:14], r["area_sqm"], r["rule"][-2:],
                 r["req_light_sqm"], r["act_light_sqm"], r["req_vent_sqm"], r["act_vent_sqm"], r["status"]))
    print("-" * 78)
    print("Pending:", ", ".join("%s %s (%s)" % (r["name"], r["number"], r["level"]) for r in d["rooms_pending"]))
    print("Unassigned openings:", ", ".join("%d[%s]" % (o["id"], o["facing"]) for o in d["openings_unassigned"]))
    for w in s["data_quality_warnings"]:
        print("! " + w)
    sc = d.get("schedule_comparison")
    if sc:
        print("-" * 78)
        print("Model schedule vs measured (%s): %d rows, %d with issues, %d assessed rooms missing"
              % (sc["source"], len(sc["rows"]), s["schedule_rows_with_issues"], len(sc["missing_rooms"])))
        for r in sc["rows"]:
            print("  %-14s %-16s table req %s / prov %s | exact %s | measured %s | %s"
                  % (r["level"][:14], r["name"][:16], r["table_req_light_sqm"], r["table_provided_sqm"],
                     r["exact_req_light_sqm"], r["measured_light_sqm"], "; ".join(r["issues"]) or "ok"))
    alt = sum(1 for r in d["rooms_included"] if r["rule"] == "reg30" and r["act_light_sqm"] >= r["area_sqm"] / 8 - 1e-9)
    n30 = sum(1 for r in d["rooms_included"] if r["rule"] == "reg30")
    print("Reconciliation only: at the erroneous 1/8 lighting ratio, %d of %d reg-30 rooms would pass lighting." % (alt, n30))
    if previous and os.path.exists(previous):
        with open(previous, encoding="utf-8-sig") as f:
            p = json.load(f)["summary"]
        print("-" * 78)
        print("Compared with previous run (%s):" % os.path.basename(previous))
        for k in ("rooms_included_count", "rooms_excluded_count", "rooms_pending_count", "rooms_no_area_count",
                  "total_openings_glazing_louvre", "openings_unassigned_count", "openings_fire_service_count",
                  "lighting_pass_count", "ventilation_pass_count", "both_pass_count"):
            print("  %-32s previous %-5s now %s" % (k, p.get(k), s.get(k)))


if __name__ == "__main__":
    sys.exit(main())
