#!/usr/bin/env python3
"""R-G4 extract: MCP responses saved verbatim -> views_on_sheets.tsv, view_props.tsv, view_counts.json, model_counts.json
for tools/drawings/analyze.py.

Usage:
  python g4_extract.py --mcp <run>/_raw/mcp --out <run>/_raw [--keep-revision-schedules]

Saved responses in <mcp>:
  sheets*.json             get_sheets (id -> sheet number; revit-mcp sends the list as a JSON string - both are read)
  views_on_sheets*.json    get_views_on_sheets for every sheet
  view_props*.json         get_element_data on the placed views: basic + View Scale, View Template, Title on Sheet
  view_counts_<viewId>.json  one query_model per placed view (searchScope SpecificView, maxResults 1): the response
                           does not name the view, so the file name carries its id
  query_rvtlinks*.json     query_model on OST_RvtLinks (types and instances) - the link count
  titleblocks.json         get_element_data on the title blocks + project information: read as is by the analyser

Output rules:
  views_on_sheets.tsv  sheet_id, sheet number, view_id, view name, view type, outline min / max y (sheet feet, 3 dp);
                       title-block revision schedules ('<Revision Schedule>') left out unless --keep-revision-schedules
  view_props.tsv       view_id, name, view type name, sheet, scale (1:n -> n, custom scale -> 'custom'), template,
                       title on sheet.  Type names that Revit stores with leading control characters (system section /
                       elevation types) are cleaned and prefixed with the view type, e.g. 'Section (ARC_gbp)'.
  view_counts.json     {view id: categoryBreakdown} for every view_counts_<id> file
  model_counts.json    {"OST_RvtLinks": n}
Stops (exit 2, nothing written): see mcp_formats.py, plus a view_counts file whose view is not on any sheet, a placed
view (not legend / schedule) with no properties read.  Stdlib only; reads files, never the model.
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_formats import Out, Stop, files_for, load, pdisp, read_kind  # noqa: E402

REV = re.compile(r"^<\s*revision schedule", re.I)


def sheet_numbers(mcp):
    out = {}
    for f in files_for(mcp, "sheets"):
        d = load(f)
        rows = d.get("sheets", d) if isinstance(d, dict) else d
        if isinstance(rows, str):
            rows = json.loads(rows)
        if not isinstance(rows, list):
            raise Stop("%s: unknown sheet list format - add an adapter in g4_extract.py" % os.path.basename(f))
        for r in rows:
            i, n = r.get("Id", r.get("id")), r.get("Number", r.get("number", r.get("sheetNumber")))
            if i is None or n is None:
                raise Stop("%s: sheet without id or number: %s" % (os.path.basename(f), r))
            out[int(i)] = n
    return out


def views_on_sheets(mcp):
    rows = []
    for f in files_for(mcp, "views_on_sheets"):
        res = load(f).get("results")
        if not isinstance(res, dict):
            raise Stop("%s: unknown views-on-sheets format - add an adapter in g4_extract.py" % os.path.basename(f))
        for sid, views in res.items():
            for v in views:
                o = v.get("outline") or {}
                lo, hi = o.get("minXYZ") or o.get("min") or {}, o.get("maxXYZ") or o.get("max") or {}
                rows.append({"sheet_id": int(sid), "view_id": int(v["viewId"]), "name": v.get("viewName", ""),
                             "type": v.get("viewType", ""), "miny": lo.get("y"), "maxy": hi.get("y")})
    return rows


def clean_type(name, view_type):
    raw = name or ""
    stripped = re.sub(r"[\x00-\x1f]", "", raw).strip()
    if re.search(r"[\x00-\x1f]", raw) and view_type:          # (str.strip() would eat \x1c-\x1f too)
        return "%s (%s)" % (view_type, stripped)
    return stripped


def run(a):
    warn, info, out = [], {}, Out(a.out)
    numbers = sheet_numbers(a.mcp)
    if not numbers:
        raise Stop("no sheets*.json in %s - call get_sheets" % a.mcp)
    vos = views_on_sheets(a.mcp)
    if not vos:
        raise Stop("no views_on_sheets*.json in %s - call get_views_on_sheets for every sheet" % a.mcp)
    unknown = sorted({r["sheet_id"] for r in vos} - set(numbers))
    if unknown:
        raise Stop("views on sheets not in the sheet list: %s" % ", ".join(map(str, unknown)))
    rev = [r for r in vos if REV.match(r["name"] or "")]
    keep = vos if a.keep_revision_schedules else [r for r in vos if r not in rev]
    keep = sorted(keep, key=lambda r: numbers[r["sheet_id"]])          # by sheet number; views keep their order
    f3 = lambda x: "%.3f" % x if isinstance(x, (int, float)) else ""
    out.tsv("views_on_sheets.tsv", ["sheet_id", "sheet", "view_id", "view_name", "view_type", "outline_miny", "outline_maxy"],
            [[r["sheet_id"], numbers[r["sheet_id"]], r["view_id"], r["name"], r["type"], f3(r["miny"]), f3(r["maxy"])]
             for r in keep])
    info["sheets"] = len(numbers)
    info["views on sheets"] = "%d%s" % (len(keep), "" if a.keep_revision_schedules or not rev else
                                         " (%d title-block revision schedules left out)" % len(rev))

    vtype = {r["view_id"]: r["type"] for r in vos}
    placed = {r["view_id"]: r for r in vos}
    props = read_kind(a.mcp, "view_props", warn, required=False, order="file")
    if props is None:
        warn.append("no view_props*.json - view_props.tsv not written (scales, templates, titles not checked)")
    else:
        rows = []
        for e in props:
            scale = e["params"].get("View Scale") or {}
            sv = str(scale.get("value") if scale.get("value") not in (None, "") else (scale.get("display") or "")).strip()
            sv = "custom" if sv in ("-1", "Custom", "custom") else (re.sub(r".*:\s*", "", sv) if ":" in sv else sv)
            sheet = pdisp(e, "Sheet Number") or (numbers.get(placed[e["id"]]["sheet_id"]) if e["id"] in placed else "")
            rows.append([e["id"], e["name"], clean_type(e["type"], vtype.get(e["id"])), sheet, sv,
                         pdisp(e, "View Template") or "", pdisp(e, "Title on Sheet") or ""])
        out.tsv("view_props.tsv", ["view_id", "name", "view_type_name", "sheet", "scale", "template", "title_on_sheet"], rows)
        info["view properties"] = len(rows)
        missing = sorted(v for v, r in placed.items() if r["type"] not in ("Legend", "Schedule") and v not in {x[0] for x in rows})
        if missing:
            warn.append("placed views without properties read (their scale / template checks will be skipped): %s"
                        % ", ".join(map(str, missing[:15])) + (" ..." if len(missing) > 15 else ""))

    counts = {}
    for f in sorted(glob.glob(os.path.join(a.mcp, "view_counts_*.json"))):
        m = re.match(r"^view_counts_(\d+)\.json$", os.path.basename(f))
        if not m:
            raise Stop("%s: name it view_counts_<view id>.json" % os.path.basename(f))
        vid = int(m.group(1))
        if vid not in placed:
            raise Stop("%s: view %d is not on any sheet" % (os.path.basename(f), vid))
        r = load(f).get("results", {})
        an = r.get("analysis") or {}
        cb = an.get("categoryBreakdown") or an.get("byCategory")
        if isinstance(cb, list):
            cb = {x.get("name"): x.get("count") for x in cb}
        if cb is None:
            raise Stop("%s: no category counts in the query_model result" % os.path.basename(f))
        counts[str(vid)] = cb
    if counts:
        out.json("view_counts.json", dict({"_note": "query_model searchScope SpecificView, maxResults 1; "
                                           "analysis.categoryBreakdown per view (g4_extract.py)"}, **counts), indent=1)
        info["view counts"] = len(counts)
        todo = sorted(v for v, r in placed.items() if r["type"] not in ("Legend", "Schedule") and str(v) not in counts)
        if todo:
            warn.append("placed views without counts (grid / dimension / tag checks skipped for them): %s"
                        % ", ".join(map(str, todo[:15])) + (" ..." if len(todo) > 15 else ""))
    else:
        warn.append("no view_counts_<id>.json - view_counts.json not written (V02-V05 / V08 / V10 / V11 counts not checked)")

    lf = files_for(a.mcp, "query_rvtlinks")
    if lf:
        n = 0
        for f in lf:
            an = (load(f).get("results") or {}).get("analysis") or {}
            n += int(an.get("totalElements", an.get("total", 0)) or 0)
        out.json("model_counts.json", {"OST_RvtLinks": n, "_source": "query_model OST_RvtLinks (g4_extract.py)"})
        info["Revit links"] = n
    else:
        warn.append("no query_rvtlinks*.json - model_counts.json not written (A03-L4 / MA-1.5 UNCLEAR)")
    if not os.path.exists(os.path.join(a.mcp, "titleblocks.json")):
        warn.append("no titleblocks.json in the MCP folder - A01 title-block checks need it")
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
        print("%-17s %s" % (k, v))
    for w in warn:
        print("! " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
