#!/usr/bin/env python3
"""R-G3 extract: MCP responses saved verbatim -> areas.tsv, area_schemes.tsv, rasters.tsv for tools/area_scheme/analyze.py.

Usage:
  python g3_extract.py --mcp <run>/_raw/mcp --out <run>/_raw [--param-map map.json]

Saved responses in <mcp> (<kind>.json or <kind>_<part>.json):
  areas          get_element_data on OST_Areas (+ OST_AreaSchemes and OST_SiteProperty may be in the same calls):
                 bounding box + the area parameters below.  The same Area may appear in several files (e.g. one batch
                 with SpecificParameters, one with AllParameters + box): its parameters are merged, never duplicated.
  area_schemes   get_element_data on OST_AreaSchemes (basic) - optional if the schemes are in the areas files
  property_lines get_element_data on OST_SiteProperty with Area - optional if they are in the areas files
  rasters        get_element_data on OST_RasterImages (basic + Width, Height) - for GEN-01 (picture tables)
  query_areas, query_rasters   query_model results (optional; prove nothing is missing)

Area parameters (BD GBP template names; another template: --param-map {"served_facade": "My Served Facade", ...}):
  scheme_id "Area Scheme Id", area "Area", number "Number", name "Name", level "Level", common_area "Common Area",
  gfa_summary "GFA SUMMARY", d22 "GFA DEDUCT 2.2", d23 "GFA DEDUCT 2.3", d21 "GFA DEDUCT 21", d25 "GFA DEDUCT 25",
  d27 "GFA DEDUCT 27", served_facade "SERVED FACADE", frr "FRR minutes", compartment "FRC COMPARTMENT",
  frc_height "FRC HEIGHT", perimeter "Perimeter", area_type "Area Type", raster_width "Width", raster_height "Height"
Yes / No parameters: '1' when shown Yes / True or stored 1.  Stops (exit 2, nothing written): see mcp_formats.py, plus
an Area whose scheme id is not among the schemes read.  Stdlib only; reads files, never the model.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_formats import Out, Stop, check_complete, elements, files_for, length_mm, query_ids  # noqa: E402

PARAMS = {"scheme_id": "Area Scheme Id", "area": "Area", "number": "Number", "name": "Name", "level": "Level",
          "common_area": "Common Area", "gfa_summary": "GFA SUMMARY", "d22": "GFA DEDUCT 2.2", "d23": "GFA DEDUCT 2.3",
          "d21": "GFA DEDUCT 21", "d25": "GFA DEDUCT 25", "d27": "GFA DEDUCT 27", "served_facade": "SERVED FACADE",
          "frr": "FRR minutes", "compartment": "FRC COMPARTMENT", "frc_height": "FRC HEIGHT", "perimeter": "Perimeter",
          "area_type": "Area Type", "raster_width": "Width", "raster_height": "Height"}
HEAD = ["id", "scheme", "level", "name", "area_m2", "number", "common_area", "gfa_summary", "d22", "d23", "d21", "d25", "d27",
        "served_facade_mm", "frr", "compartment", "frc_height", "perimeter_mm", "area_type", "minx", "miny", "maxx", "maxy"]


def merged(mcp, kinds):
    """Elements from several files, merged by id: first non-empty value of each parameter wins; any bounding box."""
    out = {}
    for kind in kinds:
        for f in files_for(mcp, kind):
            for e in elements(f):
                m = out.setdefault(e["id"], dict(e, params={}))
                for k in ("name", "category", "family", "type", "level"):
                    m[k] = m.get(k) or e.get(k)
                m["bb"] = m.get("bb") or e["bb"]
                for k, v in e["params"].items():
                    if k not in m["params"] or (m["params"][k]["display"] in (None, "") and v["display"] not in (None, "")):
                        m["params"][k] = v
    return out


def run(a):
    P = dict(PARAMS)
    if a.param_map:
        with open(a.param_map, encoding="utf-8") as f:
            P.update(json.load(f))
    warn, info, out = [], {}, Out(a.out)
    els = merged(a.mcp, ["areas", "area_schemes", "property_lines"])
    if not els:
        raise Stop("no areas*.json in %s" % a.mcp)
    cat = lambda e, word: re.search(word, e.get("category") or "", re.I)
    schemes = {i: e["name"] for i, e in els.items() if cat(e, r"area\s*scheme")}
    plines = [e for e in els.values() if cat(e, r"property\s*line|site\s*property")]
    areas = [e for e in els.values() if cat(e, r"^areas?$")]
    check_complete("areas", areas, query_ids(a.mcp, "areas"), warn)
    if not schemes:
        raise Stop("no Area Scheme elements read - add OST_AreaSchemes to the calls (basic info)")

    lengths = {"served_facade", "frc_height", "perimeter"}

    def disp(e, key):
        """Shown text; when the MCP gives no shown text, the stored value (a non-zero length is converted ft -> mm)."""
        p = e["params"].get(P[key])
        if not p:
            return ""
        if p["display"] is not None:
            return p["display"]
        v = p.get("value")
        if v in (None, ""):
            return ""
        if key in lengths and re.match(r"^-?[\d.]+$", str(v)) and float(v) != 0:
            return str(round(float(v) * 304.8))
        return str(v)

    num = lambda s: re.sub(r"[^\d.\-]", "", s or "")

    def yes(e, key):
        p = e["params"].get(P[key]) or {}
        return "1" if str(p.get("display") or "").strip().lower() in ("yes", "true") or str(p.get("value")) in ("1", "True") else "0"

    rows, bad = [], []
    for e in areas:
        sid = num(str(disp(e, "scheme_id")))
        if not sid or int(sid) not in schemes:
            bad.append(e["id"])
            continue
        lo, hi = e["bb"] if e["bb"] else ({}, {})
        rows.append([e["id"], schemes[int(sid)], disp(e, "level"), disp(e, "name"), num(disp(e, "area")), disp(e, "number"),
                     disp(e, "common_area"), yes(e, "gfa_summary"), yes(e, "d22"), yes(e, "d23"), yes(e, "d21"),
                     yes(e, "d25"), yes(e, "d27"), num(disp(e, "served_facade")), disp(e, "frr"), disp(e, "compartment"),
                     num(disp(e, "frc_height")), num(disp(e, "perimeter")), disp(e, "area_type"),
                     "%.2f" % lo.get("x", 0), "%.2f" % lo.get("y", 0), "%.2f" % hi.get("x", 0), "%.2f" % hi.get("y", 0)])
    if bad:
        raise Stop("Areas whose scheme is not among the schemes read: %s" % ", ".join(map(str, bad[:20])))
    placed = [e for e in plines if num(disp(e, "area"))]
    if len(placed) < len(plines):
        warn.append("property lines without an area (not placed) left out: %s"
                    % ", ".join(str(e["id"]) for e in plines if e not in placed))
    if not placed:
        warn.append("no property line with an area - S02 site area checks will have nothing to compare with")
    for e in placed:
        rows.append([e["id"], "(property line)", "", "Property", num(disp(e, "area"))] + [""] * 18)
    rows.sort(key=lambda r: r[0])
    out.files["areas.tsv"] = "\t".join(HEAD) + "\n" + "".join("\t".join(str(x) for x in r) + "\n" for r in rows)
    out.files["area_schemes.tsv"] = "id\tname\tareas\n" + "".join(
        "%d\t%s\t%d\n" % (i, n, sum(1 for r in rows if r[1] == n)) for i, n in sorted(schemes.items()))
    info["areas"] = len(areas)
    info["schemes"] = dict(Counter(r[1] for r in rows))
    info["empty schemes"] = sorted(n for n in schemes.values() if not any(r[1] == n for r in rows))

    rfiles = files_for(a.mcp, "rasters")
    if rfiles:
        ras = merged(a.mcp, ["rasters"])
        check_complete("rasters", list(ras.values()), query_ids(a.mcp, "rasters"), warn)
        out.tsv("rasters.tsv", ["id", "name", "width_mm", "height_mm"],
                [[i, e["name"], length_mm(e["params"].get(P["raster_width"]), "raster %d width" % i, warn),
                  length_mm(e["params"].get(P["raster_height"]), "raster %d height" % i, warn)] for i, e in sorted(ras.items())])
        info["raster images"] = len(ras)
    else:
        warn.append("no rasters*.json - rasters.tsv not written; GEN-01 (picture tables) will not be judged")
    out.commit()
    return info, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mcp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--param-map", help="JSON {key: parameter name} overriding the BD template names")
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
