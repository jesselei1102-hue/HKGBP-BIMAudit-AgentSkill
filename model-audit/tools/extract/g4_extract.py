#!/usr/bin/env python3
"""R-G4 extract: MCP responses saved verbatim -> views_on_sheets.tsv, view_props.tsv, view_counts.json, model_counts.json
for tools/drawings/analyze.py.

Usage:
  python g4_extract.py --mcp <run>/_raw/mcp --out <run>/_raw [--keep-revision-schedules]

Saved responses in <mcp> (revit-mcp):
  sheets*.json             get_sheets (id -> sheet number; revit-mcp sends the list as a JSON string - both are read)
  views_on_sheets*.json    get_views_on_sheets for every sheet
  view_props*.json         get_element_data on the placed views: basic + View Scale, View Template, Title on Sheet
  view_counts_<viewId>.json  one query_model per placed view (searchScope SpecificView, maxResults 1): the response
                           does not name the view, so the file name carries its id
  query_rvtlinks*.json     query_model on OST_RvtLinks (types and instances) - the link count
  titleblocks.json         get_element_data on the title blocks + project information: read as is by the analyser
mcp-servers-for-revit has no get_sheets / get_views_on_sheets; save instead:
  sheets*.json             get_element_data on the OST_Sheets ids (Sheet Number)
  view_props*.json         get_element_data on the OST_Views ids (Sheet Number, View Scale, View Template, Title on Sheet);
                           only views that are on a sheet are written to view_props.tsv
  sheet_viewports_<sheetId>.json  query_model searchScope SpecificView, viewId = the sheet, categories OST_Viewports
  viewports*.json          get_element_data on those viewports (View, View Name): each is matched to its view by view
                           family and name, so a legend placed on several sheets is listed on each
  view_counts_<viewId>.json  as above; byCategory display names are mapped to OST_ names (CATEGORY)
  This MCP returns no viewport outline, so outline_miny / outline_maxy stay empty.

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
from mcp_formats import Out, Stop, elements, files_for, gather, load, pdisp, read_kind  # noqa: E402

REV = re.compile(r"^<\s*revision schedule", re.I)
# mcp-servers-for-revit: view family name -> revit-mcp viewType
VIEW_TYPE = {"Floor Plan": "FloorPlan", "Area Plan": "AreaPlan", "Ceiling Plan": "CeilingPlan",
             "Structural Plan": "EngineeringPlan", "Section": "Section", "Elevation": "Elevation", "Legend": "Legend",
             "Drafting View": "DraftingView", "3D View": "ThreeD", "Detail View": "Detail", "Schedule": "Schedule"}
# mcp-servers-for-revit query_model byCategory display names -> the OST_ names revit-mcp gives (same counts, checked
# on views 2349, 5451 and 1071929 of the sample model on 2026-10-27).  Unmapped names are kept and listed as a warning.
CATEGORY = {"Grids": "OST_Grids", "Levels": "OST_Levels", "Dimensions": "OST_Dimensions",
            "Spot Elevations": "OST_SpotElevations", "Views": "OST_Viewers", "Elevations": "OST_Elev",
            "Doors": "OST_Doors", "Door Tags": "OST_DoorTags", "Rooms": "OST_Rooms", "Room Tags": "OST_RoomTags",
            "Areas": "OST_Areas", "Area Tags": "OST_AreaTags", "Text Notes": "OST_TextNotes", "Callouts": "OST_Callouts",
            "Walls": "OST_Walls", "Wall Tags": "OST_WallTags", "Floors": "OST_Floors", "Windows": "OST_Windows",
            "Window Tags": "OST_WindowTags", "Structural Framing": "OST_StructuralFraming",
            "Structural Columns": "OST_StructuralColumns", "Curtain Panels": "OST_CurtainWallPanels",
            "Curtain Wall Mullions": "OST_CurtainWallMullions", "Curtain Wall Grids": "OST_CurtainGridsWall",
            "Plumbing Fixtures": "OST_PlumbingFixtures", "Specialty Equipment": "OST_SpecialityEquipment",
            "Specialty Equipment Tags": "OST_SpecialityEquipmentTags", "Generic Models": "OST_GenericModel",
            "Generic Annotations": "OST_GenericAnnotation", "Stairs": "OST_Stairs", "Runs": "OST_StairsRuns",
            "Landings": "OST_StairsLandings", "Stair Tags": "OST_StairsTags", "Stair Paths": "OST_StairsPaths",
            "Railings": "OST_StairsRailing", "Top Rails": "OST_RailingTopRail",
            "<Room Separation>": "OST_RoomSeparationLines", "Lines": "OST_Lines", "Detail Items": "OST_DetailComponents",
            "Detail Groups": "OST_IOSDetailGroups", "Cameras": "OST_Cameras", "Parking": "OST_Parking",
            "Parking Tags": "OST_ParkingTags", "Site": "OST_Site", "Property Lines": "OST_SiteProperty",
            "Property Line Segments": "OST_SitePropertyLineSegment", "Floor opening cut": "OST_FloorOpening",
            "<Area Boundary>": "OST_AreaSchemeLines"}
NO_SHEET = ("", "---")


def sheet_numbers(mcp):
    out = {}
    for f in files_for(mcp, "sheets"):
        d = load(f)
        if isinstance(d, dict) and isinstance(d.get("elements"), list):               # mcp-servers-for-revit
            for e in elements(f):
                n = pdisp(e, "Sheet Number")
                if n in (None, ""):
                    raise Stop("%s: sheet %d without a Sheet Number - read it with SpecificParameters"
                               % (os.path.basename(f), e["id"]))
                out[e["id"]] = n
            continue
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


def views_from_viewports(mcp, numbers, views):
    """mcp-servers-for-revit: what is on each sheet, from sheet_viewports_<sheet id>.json + viewports*.json.
    Returns (rows, sheets not queried)."""
    _, ports = gather(mcp, "viewports")
    port = {e["id"]: e for e in ports}
    key = {}
    for v in views:
        key.setdefault((v["family"], v["name"]), []).append(v)
    rows, queried = [], set()
    for f in sorted(glob.glob(os.path.join(mcp, "sheet_viewports_*.json"))):
        m = re.match(r"^sheet_viewports_(\d+)\.json$", os.path.basename(f))
        if not m:
            raise Stop("%s: name it sheet_viewports_<sheet id>.json" % os.path.basename(f))
        sid = int(m.group(1))
        if sid not in numbers:
            raise Stop("%s: sheet %d is not in sheets*.json" % (os.path.basename(f), sid))
        queried.add(sid)
        r = load(f).get("results") or {}
        ids = r.get("elementIds") or [x.get("elementId") for x in r.get("elementRefs", [])]
        total = (r.get("analysis") or {}).get("total")
        if total is not None and int(total) > len(ids):
            raise Stop("%s: query_model result truncated (%d of %d) - use maxResults 0"
                       % (os.path.basename(f), len(ids), int(total)))
        for vp in map(int, ids):
            if vp not in port:
                raise Stop("viewport %d on sheet %s was not read - call get_element_data for it (viewports*.json)"
                           % (vp, numbers[sid]))
            label, name = pdisp(port[vp], "View") or "", pdisp(port[vp], "View Name") or ""
            # 'Area Plan (Block plan): SITE (1/A001)' / 'Section : A (A/A006)': family, optional view type, then name
            lm = re.match(r"^\s*([^(:]+?)\s*(?:\((.*?)\))?\s*:", label)
            family, vtype_name = (lm.group(1), lm.group(2)) if lm else ("", None)
            hit = key.get((family, name), [])
            if len(hit) > 1 and vtype_name:
                hit = [v for v in hit if re.sub(r"[\x00-\x1f]", "", v["type"] or "").strip() == vtype_name]
            if len(hit) != 1:
                raise Stop("viewport %d on sheet %s ('%s'): %s view of that family and name"
                           % (vp, numbers[sid], label, "no" if not hit else "more than one"))
            v = hit[0]
            if v["family"] not in VIEW_TYPE:
                raise Stop("view %d '%s': unknown view family '%s' - add it to VIEW_TYPE in g4_extract.py"
                           % (v["id"], v["name"], v["family"]))
            rows.append({"sheet_id": sid, "view_id": v["id"], "name": v["name"], "type": VIEW_TYPE[v["family"]],
                         "miny": None, "maxy": None})
    return rows, sorted(set(numbers) - queried, key=lambda s: numbers[s])


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
    servers = not vos and bool(glob.glob(os.path.join(a.mcp, "sheet_viewports_*.json")))   # mcp-servers-for-revit
    views = None
    if servers:
        views = read_kind(a.mcp, "view_props", warn, order="file")
        vos, skipped = views_from_viewports(a.mcp, numbers, views)
        warn.append("mcp-servers-for-revit: no viewport outlines - outline_miny / outline_maxy left empty")
        if skipped:
            warn.append("sheets whose viewports were not queried (nothing listed on them): %s"
                        % ", ".join(numbers[s] for s in skipped))
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
    props = views if servers else read_kind(a.mcp, "view_props", warn, required=False, order="file")
    first_sheet = {}
    for r in keep:
        first_sheet.setdefault(r["view_id"], numbers[r["sheet_id"]])
    if servers:                       # every view was read: keep the placed ones, legends / schedules out (R-G4 step 3)
        props = [e for e in props if e["id"] in placed and placed[e["id"]]["type"] not in ("Legend", "Schedule")]
    if props is None:
        warn.append("no view_props*.json - view_props.tsv not written (scales, templates, titles not checked)")
    else:
        rows = []
        for e in props:
            scale = e["params"].get("View Scale") or {}
            sv = str(scale.get("value") if scale.get("value") not in (None, "") else (scale.get("display") or "")).strip()
            sv = "custom" if sv in ("-1", "Custom", "custom") else (re.sub(r".*:\s*", "", sv) if ":" in sv else sv)
            own = pdisp(e, "Sheet Number")
            sheet = own if own not in (None,) + NO_SHEET else first_sheet.get(e["id"], "")
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
        if isinstance(cb, list):                                                       # mcp-servers-for-revit
            odd = sorted({x.get("name") for x in cb} - set(CATEGORY) - {"(none)"})
            if odd:
                warn.append("%s: category names not mapped to OST_ (kept as is, not counted by the checks): %s"
                            % (os.path.basename(f), ", ".join(odd)))
            cb = {CATEGORY.get(x.get("name"), x.get("name")): x.get("count") for x in cb}
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
