"""Shared reading of MCP responses saved verbatim (used by every tools/extract/g*_extract.py).

Formats are recognised by shape, not by MCP name:
  - revit-mcp: get_element_data -> {"results": {"ElementId <n>": {BasicElementInfo, BoundingBox, InstanceParameters}}}
               query_model      -> {"results": {"Element Ids": [...], "analysis": {"totalElements": n, ...}}}
  - mcp-servers-for-revit: get_element_data -> {"elements": [{id, name, category, family, type, level,
               boundingBox{min,max}, parameters{name: value}}]};  query_model -> {"results": {"elementIds": [...]}}
Anything else raises Stop: add an adapter here rather than hand-copying values.

Outputs are collected in an Out object and written only when every check has passed (Out.commit), so a stopped run
never leaves half an extract behind.  Stdlib only; reads files, never the model.
"""
import csv
import glob
import json
import os
import re
from io import StringIO

SQFT = 0.09290304
FT_MM = 304.8


class Stop(Exception):
    pass


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def elements(path):
    """Normalise one get_element_data response into [{id, name, category, family, type, level, bb, params}].
    params: {name: {"display": shown text, "value": internal value or None}}."""
    doc = load(path)
    out = []
    res = doc.get("results") if isinstance(doc, dict) else None
    if isinstance(res, dict) and res and all(str(k).startswith("ElementId ") for k in res):          # revit-mcp
        for key, el in res.items():
            info = el.get("BasicElementInfo") or {}
            if info.get("processingStatus") not in (None, "Success"):
                raise Stop("%s: %s could not be read (%s)" % (os.path.basename(path), key, info.get("processingStatus")))
            params = {}
            for p in el.get("InstanceParameters") or []:
                params.setdefault(p.get("name"), {"display": p.get("displayValue"), "value": p.get("value")})
            for p in el.get("TypeParameters") or []:
                params.setdefault(p.get("name"), {"display": p.get("displayValue"), "value": p.get("value")})
            bb = el.get("BoundingBox") or {}
            out.append({"id": int(str(key).split()[-1]), "name": info.get("name"), "category": info.get("category"),
                        "family": info.get("familyName"), "type": info.get("typeName"), "level": info.get("levelName"),
                        "bb": (bb["minXYZ"], bb["maxXYZ"]) if bb.get("minXYZ") and bb.get("maxXYZ") else None,
                        "params": params})
        return out
    rows = doc.get("elements") if isinstance(doc, dict) else doc
    if isinstance(rows, list) and all(isinstance(e, dict) and "id" in e for e in rows):             # mcp-servers-for-revit
        for e in rows:
            if e.get("error"):
                raise Stop("%s: element %s could not be read (%s)" % (os.path.basename(path), e["id"], e["error"]))
            bb = e.get("boundingBox") or {}
            out.append({"id": int(e["id"]), "name": e.get("name"), "category": e.get("category"),
                        "family": e.get("family"), "type": e.get("type"), "level": e.get("level"),
                        "bb": (bb["min"], bb["max"]) if bb.get("min") and bb.get("max") else None,
                        "params": {k: {"display": v, "value": None} for k, v in (e.get("parameters") or {}).items()}})
        return out
    raise Stop("%s: unknown MCP response format - add an adapter in tools/extract/mcp_formats.py" % os.path.basename(path))


def files_for(mcp, kind):
    """Files of one kind: '<kind>.json' or '<kind>_<part>.json' (so 'rooms' never picks up 'room_boundaries')."""
    return sorted(f for f in glob.glob(os.path.join(mcp, "%s*.json" % kind))
                  if re.match(r"^%s(_[^.]*)?\.json$" % re.escape(kind), os.path.basename(f)))


def gather(mcp, kind, order="id"):
    """All elements of one kind; sorted by id, or in the order the MCP returned them (order='file')."""
    files = files_for(mcp, kind)
    seen, out = set(), []
    for f in files:
        for e in elements(f):
            if e["id"] in seen:
                raise Stop("%s: element %d appears twice" % (kind, e["id"]))
            seen.add(e["id"])
            out.append(e)
    return files, (out if order == "file" else sorted(out, key=lambda e: e["id"]))


def query_ids(mcp, kind):
    """Element ids from saved query_model responses (either MCP), or None when none was saved."""
    files = files_for(mcp, "query_" + kind)
    if not files:
        return None
    ids = set()
    for f in files:
        d = load(f)
        r = d.get("results", d) if isinstance(d, dict) else {}
        got = r.get("elementIds") or r.get("Element Ids") or r.get("ElementIds") or \
            [x.get("elementId") for x in r.get("elementRefs", [])]
        an = r.get("analysis") or {}
        total = an.get("totalElements", an.get("total"))
        if total is not None and int(total) == 0:
            continue
        if not got:
            raise Stop("%s: no element ids in the query_model result (revit-mcp returns none with maxResults 0 - "
                       "use a large maxResults, e.g. 10000; mcp-servers-for-revit: 0 = all)" % os.path.basename(f))
        if total is not None and int(total) > len(got):
            raise Stop("%s: query_model result truncated (%d of %d ids) - save it with maxResults 0 / large enough"
                       % (os.path.basename(f), len(got), int(total)))
        ids |= {int(x) for x in got}
    return ids


def check_complete(kind, rows, qids, warn):
    if qids is None:
        warn.append("%s: no query_%s*.json saved - completeness not checked" % (kind, kind))
        return
    have = {e["id"] for e in rows}
    missing, extra = sorted(qids - have), sorted(have - qids)
    if missing:
        raise Stop("%s: %d element(s) from query_model were not read: %s - call get_element_data for them"
                   % (kind, len(missing), ", ".join(map(str, missing[:20]))))
    if extra:
        raise Stop("%s: %d element(s) not in the query_model result: %s" % (kind, len(extra), ", ".join(map(str, extra[:20]))))


def read_kind(mcp, kind, warn, required=True, need_box=False, order="id"):
    """gather + completeness + optional bounding-box check.  Returns None when nothing was saved and not required."""
    files, rows = gather(mcp, kind, order)
    if not files:
        if required:
            raise Stop("no %s*.json in %s" % (kind, mcp))
        return None
    check_complete(kind, rows, query_ids(mcp, kind), warn)
    if need_box:
        nobb = [e["id"] for e in rows if not e["bb"]]
        if nobb:
            raise Stop("%s without a bounding box: %s" % (kind, ", ".join(map(str, nobb[:20]))))
    return rows


# ---------------------------------------------------------------- values
def number(text):
    m = re.match(r"\s*(-?[\d,]*\.?\d+)", str(text or ""))
    return float(m.group(1).replace(",", "")) if m else None


def first_token(text):
    return str(text).split()[0] if text not in (None, "") and str(text).split() else ""


def pdisp(e, name):
    return (e["params"].get(name) or {}).get("display")


def area_m2(p, what):
    """Area as displayed in m² (text kept as shown, e.g. '129.340'); other units converted from the internal value."""
    if not p:
        raise Stop("%s: no area parameter" % what)
    disp = str(p["display"] or "")
    if re.search(r"m²|m2|sq\.?\s*m", disp) or (number(disp) is not None and not re.search(r"[A-Za-z²']", disp)):
        return first_token(disp)
    if p.get("value") not in (None, ""):                        # internal value is square feet
        return "%.3f" % (float(p["value"]) * SQFT)
    if re.search(r"ft²|ft2|SF|sq\.?\s*ft", disp, re.I) and number(disp) is not None:
        return "%.3f" % (number(disp) * SQFT)
    raise Stop("%s: area '%s' is not in m² and has no internal value" % (what, disp))


FEET_INCHES = re.compile(r"""^\s*(?:(-?\d+(?:\.\d+)?)\s*')?\s*-?\s*(?:(\d+(?:\.\d+)?)?(?:\s*(\d+)/(\d+))?\s*")?\s*$""")


def feet_inches_mm(text):
    """Revit feet-inches text (1' - 9 11/16", 0' - 4", 5 1/2") in mm, or None when it is not that."""
    m = FEET_INCHES.match(str(text or ""))
    if not m or not any(m.groups()):
        return None
    ft, inch, num_, den = m.groups()
    inches = float(inch or 0) + (float(num_) / float(den) if den and float(den) else 0)
    return round((abs(float(ft or 0)) * 12 + inches) * 25.4) * (-1 if (ft or "").startswith("-") else 1)


def length_mm(p, what, warn):
    """Length in mm as displayed; checked against the internal value (feet) when the MCP gives one."""
    if not p or p["display"] in (None, ""):
        return ""
    disp = str(p["display"])
    shown = number(disp) if not re.search(r"['\"]|ft|in\b", disp) else feet_inches_mm(disp)
    internal = round(float(p["value"]) * FT_MM) if p.get("value") not in (None, "") and number(p["value"]) is not None else None
    if shown is not None and internal is not None and abs(shown - internal) > 1:
        warn.append("%s: shows %s but the internal value is %d mm - internal value used" % (what, disp, internal))
        return str(internal)
    if shown is not None:
        return first_token(disp) if not re.search(r"['\"]", disp) else str(shown)
    if internal is not None:
        return str(internal)
    raise Stop("%s: '%s' cannot be read in mm" % (what, disp))


# ---------------------------------------------------------------- output (written only after all checks)
class Out:
    def __init__(self, folder):
        self.folder, self.files = folder, {}

    def tsv(self, name, header, rows):
        buf = StringIO()
        w = csv.writer(buf, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        self.files[name] = buf.getvalue()

    def json(self, name, data, **kw):
        self.files[name] = json.dumps(data, ensure_ascii=False, **kw)

    def commit(self):
        os.makedirs(self.folder, exist_ok=True)
        for name, text in self.files.items():
            with open(os.path.join(self.folder, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        return sorted(self.files)
