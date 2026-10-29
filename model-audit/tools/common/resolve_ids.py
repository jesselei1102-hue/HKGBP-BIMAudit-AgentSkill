#!/usr/bin/env python3
"""Fill in the Revit ID of each check's object from the run's extracts, so the reports can say where to fix it.

  python resolve_ids.py <analysis.json> [<raw dir> ...]      (default raw dir: <analysis dir>/_raw)

A check whose object names something in the model - a sheet ("C003 site area calculation"), a view
("A002 FFL 0.30 G/F (FloorPlan)"), a level, an area scheme, a schedule, a room number or a raster image - gets
object_id, object_kind ("sheet", "view", "level", "scheme", "schedule", "room", "element"), sheet (the sheet a view sits
on) and id_from ("analysis" when the analyser recorded the ID, "lookup" when it came from here).  An ID the analyser
recorded always wins.  Text that matches nothing, or more than one thing, is left alone: no guessing.
build_results.py calls fill() for every group; the command line is for checking one file.  Stdlib only.
"""
import csv
import glob
import json
import os
import re
import sys

SHEET_NO = re.compile(r"^([A-Z]\d{3})\b\s*(.*)$")
SHEET_FILE = re.compile(r"_(\d+) - Sheet - ([A-Z0-9-]+) - ")
VIEW_TYPE = re.compile(r"\s*\([^()]*\)\s*$")


def _rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class Index:
    def __init__(self):
        self.sheets = {}                      # number -> id
        self.views = {}                       # name -> {(id, sheet)}
        self.named = {k: {} for k in ("level", "scheme", "schedule", "room")}   # name -> {id}
        self.rasters = {}                     # file name -> id

    def add(self, kind, name, ident):
        name, ident = (name or "").strip(), str(ident or "").strip()
        if name and ident:
            self.named[kind].setdefault(name, set()).add(ident)


def build_index(raw_dirs):
    ix = Index()
    for raw in raw_dirs:
        for r in _rows(os.path.join(raw, "views_on_sheets.tsv")):
            if r.get("sheet") and r.get("sheet_id"):
                ix.sheets[r["sheet"].strip()] = r["sheet_id"].strip()
            if r.get("view_name") and r.get("view_id"):
                ix.views.setdefault(r["view_name"].strip(), set()).add((r["view_id"].strip(), (r.get("sheet") or "").strip() or None))
        for r in _rows(os.path.join(raw, "view_props.tsv")):
            if r.get("name") and r.get("view_id"):
                ix.views.setdefault(r["name"].strip(), set()).add((r["view_id"].strip(), (r.get("sheet") or "").strip() or None))
        for p in glob.glob(os.path.join(raw, "sheets", "*")):
            m = SHEET_FILE.search(os.path.basename(p))
            if m:
                ix.sheets.setdefault(m.group(2), m.group(1))
        for r in _rows(os.path.join(raw, "levels.tsv")):
            ix.add("level", r.get("name"), r.get("id"))
        for r in _rows(os.path.join(raw, "area_schemes.tsv")):
            ix.add("scheme", r.get("name"), r.get("id"))
        for r in _rows(os.path.join(raw, "all_schedules.tsv")):
            ix.add("schedule", r.get("name"), r.get("id"))
        for r in _rows(os.path.join(raw, "rooms.tsv")):
            ix.add("room", r.get("number"), r.get("id"))
            ix.add("room", r.get("name"), r.get("id"))
        for r in _rows(os.path.join(raw, "rasters.tsv")):
            if r.get("name") and r.get("id"):
                ix.rasters.setdefault(r["name"].strip(), set()).add(r["id"].strip())
    # a view listed by both tables with and without its sheet counts once
    for name, hits in ix.views.items():
        with_sheet = {i for i, s in hits if s}
        ix.views[name] = {(i, s) for i, s in hits if s or i not in with_sheet}
    return ix


def _one(hits):
    return next(iter(hits)) if hits and len(hits) == 1 else None


def _view(ix, name, sheet=None):
    hits = ix.views.get(name, set())
    if sheet:
        hits = {h for h in hits if h[1] == sheet} or {h for h in hits if h[1] is None}
    hit = _one(hits)
    return (hit[0], "view", hit[1] or sheet) if hit else None


def _level(ix, text):
    exact = _one(ix.named["level"].get(text))
    if exact:
        return exact
    tail = {i for name, ids in ix.named["level"].items() if name.endswith("_" + text) for i in ids}
    return _one(tail)


def resolve(text, ix):
    """(id, kind, sheet) for the model object the text names, or (None, None, None)."""
    t = (text or "").strip()
    if not t:
        return None, None, None
    bare = VIEW_TYPE.sub("", t)
    for name in (t, bare):
        hit = _view(ix, name)
        if hit:
            return hit
    m = SHEET_NO.match(bare)
    if m:
        number, rest = m.group(1), m.group(2).strip()
        if rest:
            hit = _view(ix, rest, number)
            if hit:
                return hit
        if number in ix.sheets:
            return ix.sheets[number], "sheet", number
    lv = _level(ix, t)
    if lv:
        return lv, "level", None
    for kind in ("scheme", "schedule", "room"):
        hit = _one(ix.named[kind].get(t))
        if hit:
            return hit, kind, None
    rasters = {i for name, ids in ix.rasters.items() if len(name) >= 8 and name in t for i in ids}
    hit = _one(rasters)
    if hit:
        return hit, "element", None
    return None, None, None


def fill(checks, ix):
    """Add object_id / object_kind / sheet / id_from to the checks in place; returns how many IDs were looked up."""
    n = 0
    for c in checks:
        ident, kind, sheet = resolve(c.get("object"), ix)
        if c.get("object_id") not in (None, ""):
            c.setdefault("id_from", "analysis")     # a second run keeps "lookup"
            if kind and not c.get("object_kind"):
                c["object_kind"] = kind
            if sheet and not c.get("sheet"):
                c["sheet"] = sheet
            continue
        if ident:
            c.update(object_id=ident, object_kind=kind, id_from="lookup")
            if sheet:
                c["sheet"] = sheet
            n += 1
    return n


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    path = argv[0]
    raws = argv[1:] or [os.path.join(os.path.dirname(os.path.abspath(path)), "_raw")]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    checks = data.get("checks", [])
    n = fill(checks, build_index(raws))
    empty = sum(1 for c in checks if c.get("status") in ("FAIL", "UNCLEAR") and c.get("object_id") in (None, ""))
    print("%s: %d IDs looked up; %d failing or undecided checks still without an ID" % (os.path.basename(path), n, empty))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
