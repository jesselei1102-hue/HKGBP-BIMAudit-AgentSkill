#!/usr/bin/env python3
"""R-G2 extract: turn MCP responses saved verbatim into rooms.tsv, fixtures.tsv, doors_all.tsv and room_polygons.json.

Usage:
  python g2_extract.py --mcp <run>/_raw/mcp --out <run>/_raw
                       [--width-param width_MOE] [--name-param Name] [--number-param Number] [--area-param Area]
                       [--level-param Level]

Put each MCP response in <mcp> unchanged (one file per call, any number of parts: <kind>.json or <kind>_<part>.json):
  rooms               get_element_data on the rooms: basic info + bounding box + parameters Name, Number, Area, Level
  fixtures            get_element_data on OST_PlumbingFixtures: basic info + bounding box
  doors               get_element_data on OST_Doors: basic info + bounding box + the clear-width parameter, Level
  room_boundaries     get_room_boundaries (optional; MCPs without that tool: leave it out)
  query_rooms, query_fixtures, query_doors   query_model results (optional, used to prove nothing is missing)

Response formats: see mcp_formats.py (revit-mcp and mcp-servers-for-revit are recognised by shape).
Checks (exit 2, nothing written): unknown format; element the MCP failed to read; duplicate id; id missing from or
not in the query_model result; truncated query_model; fixture or door without a bounding box; area or width that
cannot be read in m² / mm.  Warnings (printed, files written): no query_model file; unplaced rooms (no bounding box)
left out; doors without the width parameter; displayed width that disagrees with the internal value.
Stdlib only; reads files, never the model.
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_formats import Out, Stop, area_m2, files_for, length_mm, load, pdisp, read_kind  # noqa: E402


def rooms_rows(mcp, a, warn):
    """rooms.tsv rows (also used by the G1 extract, which shares the rooms with G2)."""
    rooms = read_kind(mcp, "rooms", warn)
    lvl = lambda e: e["level"] or pdisp(e, a.level_param) or ""
    rows, unplaced = [], []
    for e in rooms:
        if not e["bb"]:
            unplaced.append(e["id"])
            continue
        name, num = pdisp(e, a.name_param), pdisp(e, a.number_param)
        if name is None or num is None:
            raise Stop("room %d: no '%s' / '%s' parameter - request them in get_element_data" % (e["id"], a.name_param, a.number_param))
        lo, hi = e["bb"]
        rows.append([e["id"], name, num, lvl(e), area_m2(e["params"].get(a.area_param), "room %d" % e["id"]),
                     lo["x"], lo["y"], lo["z"], hi["x"], hi["y"], hi["z"]])
    if unplaced:
        warn.append("rooms without a bounding box (unplaced, left out): %s" % ", ".join(map(str, unplaced)))
    return rows


ROOM_HEADER = ["id", "name", "number", "level", "area_m2", "minx", "miny", "minz", "maxx", "maxy", "maxz"]


def room_polygons(mcp, warn):
    bfiles = files_for(mcp, "room_boundaries")
    if not bfiles:
        warn.append("no room_boundaries*.json - non-rectangular rooms use their bounding box (lower confidence)")
        return None
    polys = {}
    for f in bfiles:
        for rid, loops in load(f).get("results", {}).items():
            polys[str(rid)] = [[[round(p["x"], 2), round(p["y"], 2)] for p in loop] for loop in loops]
    return polys


def run(a):
    warn, info, out = [], {}, Out(a.out)
    lvl = lambda e: e["level"] or pdisp(e, a.level_param) or ""

    rows = rooms_rows(a.mcp, a, warn)
    out.tsv("rooms.tsv", ROOM_HEADER, rows)
    info["rooms"] = len(rows)

    fx = read_kind(a.mcp, "fixtures", warn, required=False, need_box=True)
    if fx is None:
        warn.append("no fixtures*.json - fixtures.tsv not written (S13, S15 and S10 need it)")
    else:
        out.tsv("fixtures.tsv", ["id", "family", "type", "level", "cx", "cy", "z"],
                [[e["id"], e["family"], e["type"], lvl(e), (e["bb"][0]["x"] + e["bb"][1]["x"]) / 2,
                  (e["bb"][0]["y"] + e["bb"][1]["y"]) / 2, e["bb"][0]["z"]] for e in fx])
        info["fixtures"] = len(fx)
        info["fixture levels"] = dict(Counter(lvl(e) or "(none)" for e in fx))

    doors = read_kind(a.mcp, "doors", warn, required=False, need_box=True)
    if doors is None:
        warn.append("no doors*.json - doors_all.tsv not written (S10, S11 and the stray-door check need it)")
    else:
        drows = [[e["id"], e["family"], e["type"], lvl(e),
                  length_mm(e["params"].get(a.width_param), "door %d width" % e["id"], warn),
                  e["bb"][0]["x"], e["bb"][0]["y"], e["bb"][0]["z"], e["bb"][1]["x"], e["bb"][1]["y"], e["bb"][1]["z"]]
                 for e in doors]
        out.tsv("doors_all.tsv", ["id", "family", "type", "level", "width_moe_mm", "minx", "miny", "minz", "maxx", "maxy",
                                  "maxz"], drows)
        info["doors"] = len(drows)
        nw = [r[0] for r in drows if not r[4]]
        if nw:
            warn.append("%d door(s) without '%s' (their width checks will be UNCLEAR): %s"
                        % (len(nw), a.width_param, ", ".join(map(str, nw[:15])) + (" ..." if len(nw) > 15 else "")))
        info["door families"] = dict(Counter(r[1] for r in drows))

    polys = room_polygons(a.mcp, warn)
    if polys is not None:
        out.json("room_polygons.json", polys)
        info["room polygons"] = len(polys)
    out.commit()
    return info, warn


def add_room_args(ap):
    ap.add_argument("--name-param", default="Name")
    ap.add_argument("--number-param", default="Number")
    ap.add_argument("--area-param", default="Area")
    ap.add_argument("--level-param", default="Level", help="used when the MCP gives no level in the basic info")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mcp", required=True, help="folder with the saved MCP responses")
    ap.add_argument("--out", required=True, help="extract folder (_raw) to write the TSV files into")
    ap.add_argument("--width-param", default="width_MOE", help="door clear-width parameter (default width_MOE)")
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
