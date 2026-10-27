#!/usr/bin/env python3
"""R-G5 extract: MCP responses saved verbatim -> levels.tsv, points.tsv, all_schedules.tsv for tools/lists_health/analyze.py.

Usage:
  python g5_extract.py --mcp <run>/_raw/mcp --out <run>/_raw [--keep-revision-schedules]

Saved responses in <mcp> (<kind>.json or <kind>_<part>.json):
  levels      get_element_data on OST_Levels: basic + Elevation, Building Story
  points      get_element_data on OST_ProjectBasePoint, OST_SharedBasePoint and OST_SiteProperty: basic + bounding box +
              E/W, N/S, Elev, Angle to True North (base points), Area (property line)
  schedules   get_all_schedules ({"schedules": [{"name", "Id"}]} or a plain list)
  query_levels, query_points   query_model results (optional; prove nothing is missing)
The drawing list on A001 is read off the sheet (drawing_list.tsv), not extracted here.

Output:
  levels.tsv         id, name, type, elevation_mm, building_story (1 / 0)
  points.tsv         Survey Point and Project Base Point rows (position in feet, E/W, N/S, Elev in mm, angle in degrees),
                     plus 'Property Line bbox min' / 'max' rows for each placed property line (rectangular-site corners)
  all_schedules.tsv  id, name; title-block revision schedules ('<Revision Schedule>') are left out and counted unless
                     --keep-revision-schedules
Stops (exit 2, nothing written): see mcp_formats.py, plus no Project Base Point, or a level without an elevation.
Stdlib only; reads files, never the model.
"""
import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_formats import Out, Stop, files_for, length_mm, load, number, pdisp, read_kind  # noqa: E402

KINDS = (("Project Base Point", r"project\s*base"), ("Survey Point", r"survey|shared\s*base"),
         ("Property Line", r"property\s*line|site\s*property"))


def yes(e, name):
    p = e["params"].get(name) or {}
    return "1" if str(p.get("display") or "").strip().lower() in ("yes", "true") or str(p.get("value")) in ("1", "True") else "0"


def schedules(mcp):
    out = []
    for f in files_for(mcp, "schedules"):
        d = load(f)
        if isinstance(d, dict) and isinstance(d.get("elements"), list):
            rows = d["elements"]                                          # mcp-servers-for-revit get_element_data
        else:
            rows = d.get("schedules", d.get("results", d)) if isinstance(d, dict) else d
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise Stop("%s: unknown schedule list format - add an adapter in g5_extract.py" % os.path.basename(f))
        for r in rows:
            i = r.get("Id", r.get("id", r.get("ElementId")))
            if i is None or r.get("name") is None:
                raise Stop("%s: schedule without id or name: %s" % (os.path.basename(f), r))
            out.append((int(i), r["name"]))
    return files_for(mcp, "schedules"), out


def run(a):
    warn, info, out = [], {}, Out(a.out)

    lv = read_kind(a.mcp, "levels", warn)
    rows = []
    for e in lv:
        el = length_mm(e["params"].get("Elevation"), "level %d elevation" % e["id"], warn)
        if el == "":
            raise Stop("level %d (%s): no Elevation - request it in get_element_data" % (e["id"], e["name"]))
        rows.append([e["id"], e["name"], e["type"] or "", el, yes(e, "Building Story")])
    out.tsv("levels.tsv", ["id", "name", "type", "elevation_mm", "building_story"], rows)
    info["levels"] = "%d (%d building storeys)" % (len(rows), sum(r[4] == "1" for r in rows))

    pts = read_kind(a.mcp, "points", warn, need_box=True)
    prow, kinds = [], Counter()
    for e in pts:
        kind = next((k for k, pat in KINDS if re.search(pat, e["category"] or "", re.I)), None)
        if kind is None:
            warn.append("element %d (%s) is not a base point or property line - left out" % (e["id"], e["category"]))
            continue
        lo, hi = e["bb"]
        kinds[kind] += 1
        if kind == "Property Line":
            for tag, c in (("min", lo), ("max", hi)):
                prow.append([e["id"], "Property Line bbox " + tag, "%.3f" % c["x"], "%.3f" % c["y"], "%.3f" % c["z"],
                             "", "", "", ""])
            continue
        ang = pdisp(e, "Angle to True North")
        prow.append([e["id"], kind, "%.3f" % lo["x"], "%.3f" % lo["y"], "%.3f" % lo["z"],
                     length_mm(e["params"].get("E/W"), "%s E/W" % kind, warn),
                     length_mm(e["params"].get("N/S"), "%s N/S" % kind, warn),
                     length_mm(e["params"].get("Elev"), "%s Elev" % kind, warn),
                     ("%g" % number(ang)) if number(ang) is not None else ""])
    if not kinds["Project Base Point"]:
        raise Stop("no Project Base Point read - add OST_ProjectBasePoint to the points call")
    if not kinds["Property Line"]:
        warn.append("no property line read - S03 corner checks and MA-6.1 will be UNCLEAR")
    order = {"Survey Point": 0, "Project Base Point": 1}
    prow.sort(key=lambda r: (order.get(r[1], 2), r[0]))                 # stable: bbox min stays before max
    out.tsv("points.tsv", ["id", "kind", "x_ft", "y_ft", "z_ft", "ew_mm", "ns_mm", "elev_mm", "angle_true_north"], prow)
    info["points"] = dict(kinds)

    files, sch = schedules(a.mcp)
    if files:
        rev = [s for s in sch if re.match(r"^<\s*revision schedule", s[1], re.I)]
        keep = sch if a.keep_revision_schedules else [s for s in sch if s not in rev]
        out.tsv("all_schedules.tsv", ["id", "name"], [list(s) for s in sorted(keep)])
        info["schedules"] = "%d listed%s" % (len(keep), "" if a.keep_revision_schedules or not rev else
                                             "; %d title-block revision schedules left out" % len(rev))
    else:
        warn.append("no schedules*.json - all_schedules.tsv not written (S01 sheet-list check UNCLEAR)")
    out.commit()
    return info, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mcp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-revision-schedules", action="store_true")
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
