#!/usr/bin/env python3
"""R-S14 (G1) extract: MCP responses saved verbatim -> rooms.tsv, room_polygons.json, cw_part1.tsv, pn_part1.tsv,
pn_bbox_sample.tsv, fs_windows.tsv, doors.tsv, doors_other.tsv for tools/s14_lv/analyze.py.

Usage:
  python g1_extract.py --mcp <run>/_raw/mcp --out <run>/_raw
        [--wall-type-pattern "glass|louvre"] [--louvre-family-pattern louvre] [--hung-type-pattern hung]
        [--glass-door-pattern "(?<![a-z])glass|\\bETY\\b|entrance"]  [room parameter options as in g2_extract.py]

Saved responses in <mcp> (<kind>.json or <kind>_<part>.json; query_<kind>* optional, proves nothing is missing):
  rooms, room_boundaries   as for G2 (rooms are shared; the same rooms.tsv is written)
  cw        get_element_data on the curtain walls (OST_Walls, type name glass / louvre): basic + bounding box +
            Area, Mark (KeyParameters is enough)
  pn        get_element_data on the curtain panels (OST_CurtainWallPanels): basic + bounding box + Area
  windows   get_element_data on OST_Windows: basic + bounding box + Area, Mark
  doors     get_element_data on OST_Doors: basic + bounding box + Area, Mark (the G2 door responses can be reused)

Rules (all patterns are case-insensitive regular expressions, changeable per project):
  wall kept            type name matches --wall-type-pattern; other walls are left out and counted
  panel kind L         family matches --louvre-family-pattern
  panel kind H         not louvre, type name matches --hung-type-pattern (an openable sash)
  other panels         fixed glazing: left out (their glass is in the curtain-wall area) and counted by family / type
  pn_bbox_sample.tsv   the bounding box of every kept panel (opening top heights; no sampling needed)
  doors.tsv            doors whose family matches --glass-door-pattern (glass leaf or entrance), with area and box
  doors_other.tsv      every other door family with its count
Stops (exit 2, nothing written): see mcp_formats.py, plus panels / walls / windows / doors without a bounding box, and
cw_*.tsv / pn_*.tsv parts in the output folder that this run did not write (stale parts would be read too).
Stdlib only; reads files, never the model.
"""
import argparse
import glob
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_formats import Out, Stop, area_m2, pdisp, read_kind  # noqa: E402
from g2_extract import ROOM_HEADER, add_room_args, room_polygons, rooms_rows  # noqa: E402

BOX = ["minx", "miny", "minz", "maxx", "maxy", "maxz"]


def box(e):
    lo, hi = e["bb"]
    return [lo["x"], lo["y"], lo["z"], hi["x"], hi["y"], hi["z"]]


def run(a):
    warn, info, out = [], {}, Out(a.out)
    stale = [os.path.basename(p) for p in glob.glob(os.path.join(a.out, "cw_*.tsv")) + glob.glob(os.path.join(a.out, "pn_*.tsv"))
             if os.path.basename(p) not in ("cw_part1.tsv", "pn_part1.tsv", "pn_bbox_sample.tsv")]
    if stale:
        raise Stop("older extract parts in %s would be read as well: %s - remove them or use a new folder"
                   % (a.out, ", ".join(sorted(stale))))
    lvl = lambda e: e["level"] or pdisp(e, a.level_param) or ""
    flags = re.I

    rows = rooms_rows(a.mcp, a, warn)
    out.tsv("rooms.tsv", ROOM_HEADER, rows)
    info["rooms"] = len(rows)
    polys = room_polygons(a.mcp, warn)
    if polys is not None:
        out.json("room_polygons.json", polys)
        info["room polygons"] = len(polys)

    walls = read_kind(a.mcp, "cw", warn, need_box=True)
    kept = [e for e in walls if re.search(a.wall_type_pattern, e["type"] or e["name"] or "", flags)]
    other = Counter((e["type"] or e["name"] or "?") for e in walls if e not in kept)
    out.tsv("cw_part1.tsv", ["id", "type", "level", "area_m2", "mark"] + BOX,
            [[e["id"], e["type"] or e["name"], lvl(e), area_m2(e["params"].get("Area"), "wall %d" % e["id"]),
              pdisp(e, "Mark") or ""] + box(e) for e in kept])
    info["curtain walls"] = "%d kept by type %s" % (len(kept), dict(Counter(e["type"] for e in kept)))
    if other:
        warn.append("walls left out (type not matching '%s'): %s" % (a.wall_type_pattern, dict(other)))

    panels = read_kind(a.mcp, "pn", warn, need_box=True)
    pn_rows, sample, fixed = [], [], Counter()
    for e in panels:
        if re.search(a.louvre_family_pattern, e["family"] or "", flags):
            kind = "L"
        elif re.search(a.hung_type_pattern, e["type"] or "", flags):
            kind = "H"
        else:
            fixed["%s / %s" % (e["family"], e["type"])] += 1
            continue
        lo, hi = e["bb"]
        pn_rows.append([e["id"], kind, e["type"], area_m2(e["params"].get("Area"), "panel %d" % e["id"]),
                        (lo["x"] + hi["x"]) / 2, (lo["y"] + hi["y"]) / 2, (lo["z"] + hi["z"]) / 2])
        sample.append([e["id"], lo["z"], hi["z"]])
    out.tsv("pn_part1.tsv", ["id", "kind", "type", "area_m2", "cx", "cy", "cz"], pn_rows)
    out.tsv("pn_bbox_sample.tsv", ["id", "minz", "maxz"], sample)
    info["panels"] = "%d kept: %s" % (len(pn_rows), dict(Counter(r[1] for r in pn_rows)))
    if fixed:
        warn.append("panels left out as fixed glazing (not louvre, type not '%s'): %s" % (a.hung_type_pattern, dict(fixed)))

    wins = read_kind(a.mcp, "windows", warn, need_box=True)
    out.tsv("fs_windows.tsv", ["id", "family", "type", "level", "mark", "area_m2"] + BOX,
            [[e["id"], e["family"], e["type"], lvl(e), pdisp(e, "Mark") or "",
              area_m2(e["params"].get("Area"), "window %d" % e["id"])] + box(e) for e in wins])
    info["windows"] = "%d by family %s" % (len(wins), dict(Counter(e["family"] for e in wins)))

    doors = read_kind(a.mcp, "doors", warn, need_box=True)
    glass = [e for e in doors if re.search(a.glass_door_pattern, e["family"] or "", flags)]
    out.tsv("doors.tsv", ["id", "family", "type", "level", "mark", "area_m2"] + BOX,
            [[e["id"], e["family"], e["type"], lvl(e), pdisp(e, "Mark") or "",
              area_m2(e["params"].get("Area"), "door %d" % e["id"])] + box(e) for e in glass])
    rest = Counter(e["family"] for e in doors if e not in glass)
    out.tsv("doors_other.tsv", ["family", "count", "note"],
            [[f, n, "family not matching the glass / entrance pattern"] for f, n in rest.most_common()])
    info["doors"] = "%d glass / entrance, %d other" % (len(glass), sum(rest.values()))

    out.commit()
    return info, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mcp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wall-type-pattern", default=r"glass|louvre")
    ap.add_argument("--louvre-family-pattern", default=r"louvre")
    ap.add_argument("--hung-type-pattern", default=r"hung")
    ap.add_argument("--glass-door-pattern", default=r"(?<![a-z])glass|\bETY\b|entrance")
    add_room_args(ap)
    a = ap.parse_args()
    try:
        info, warn = run(a)
    except Stop as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    for k, v in info.items():
        print("%-15s %s" % (k, v))
    for w in warn:
        print("! " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
