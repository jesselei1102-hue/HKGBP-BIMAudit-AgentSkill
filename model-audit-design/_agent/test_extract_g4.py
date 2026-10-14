"""Tests for tools/extract/g4_extract.py (views on sheets, view properties, per-view counts, link count).

Run: python -I test_extract_g4.py
Real data: fixtures_real/g4_revit_mcp_20261014 (read-only revit-mcp calls, 2026-10-14) must reproduce our view_props.tsv
byte for byte and our views_on_sheets.tsv except the four C007 schedules no longer on that sheet.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
EXTRACT = os.path.join(PKG, "tools", "extract", "g4_extract.py")
REAL = os.path.join(HERE, "fixtures_real", "g4_revit_mcp_20261014")
OURS = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit-runs", "audit-2026-10-13-g4", "_raw"))

OUT = lambda y0, y1: {"minXYZ": {"x": 0, "y": y0, "z": 0}, "maxXYZ": {"x": 1, "y": y1, "z": 0}}
SHEETS = {"sheets": json.dumps([{"Id": 1, "Name": "PLANS", "Number": "A002"}, {"Id": 2, "Name": "BLOCK", "Number": "A001"}])}
VOS = {"results": {"1": [{"viewId": 10, "viewName": "G/F", "viewType": "FloorPlan", "outline": OUT(0.1, 2.5)},
                         {"viewId": 11, "viewName": "A", "viewType": "Section", "outline": OUT(1, 2)},
                         {"viewId": 90, "viewName": "<Revision Schedule> 2", "viewType": "Schedule", "outline": OUT(1, 1.3)}],
                   "2": [{"viewId": 20, "viewName": "SITE", "viewType": "AreaPlan", "outline": OUT(130.1344, 130.8831)}]}}


def rm(eid, name, typ, scale, template, title):
    ps = [{"name": "View Scale", "value": scale[0], "displayValue": scale[1]}, {"name": "View Template", "displayValue": template}]
    if title:
        ps.append({"name": "Title on Sheet", "displayValue": title})
    return {"BasicElementInfo": {"name": name, "category": "Views", "typeName": typ, "processingStatus": "Success"},
            "InstanceParameters": ps}


PROPS = {"results": {"ElementId 20": rm(20, "SITE", "Block plan", ("500", " 1 : 500"), "BD_block", ""),
                     "ElementId 11": rm(11, "A", "\x1e\x1e\x1eARC_gbp", ("-1", "Custom"), "BD_sec", "SECTION"),
                     "ElementId 10": rm(10, "G/F", "Floor Plan (GBP)", ("100", " 1 : 100"), "BD_plan", "")}}
COUNT = {"results": {"analysis": {"totalElements": 9, "categoryBreakdown": {"OST_Grids": 5, "OST_Dimensions": 4}}, "Element Ids": [1]}}
LINKS = {"results": {"analysis": {"totalElements": 0}}}
ALL = {"sheets.json": SHEETS, "views_on_sheets.json": VOS, "view_props.json": PROPS, "view_counts_10.json": COUNT,
       "query_rvtlinks.json": LINKS}


def run(files, *extra):
    tmp = tempfile.mkdtemp()
    mcp, out = os.path.join(tmp, "mcp"), os.path.join(tmp, "raw")
    os.makedirs(mcp)
    os.makedirs(out)
    for n, d in files.items():
        json.dump(d, open(os.path.join(mcp, n), "w", encoding="utf-8"))
    p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", mcp, "--out", out] + list(extra), capture_output=True, text=True)
    return p, out


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n").split("\t") for l in f][1:]


class G4Extract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.out = run(ALL)

    def test_runs(self):
        self.assertEqual(self.p.returncode, 0, self.p.stderr)

    def test_views_on_sheets(self):
        r = rows(os.path.join(self.out, "views_on_sheets.tsv"))
        self.assertEqual([x[1] for x in r], ["A001", "A002", "A002"])                   # by sheet number
        self.assertEqual(r[0], ["2", "A001", "20", "SITE", "AreaPlan", "130.134", "130.883"])
        self.assertNotIn("90", [x[2] for x in r])                                       # revision schedule left out
        self.assertIn("1 title-block revision", self.p.stdout)

    def test_keep_revision_schedules(self):
        p, out = run(ALL, "--keep-revision-schedules")
        self.assertIn("90", [x[2] for x in rows(os.path.join(out, "views_on_sheets.tsv"))])

    def test_view_props(self):
        r = {x[0]: x for x in rows(os.path.join(self.out, "view_props.tsv"))}
        self.assertEqual([x for x in r], ["20", "11", "10"])                            # MCP order kept
        self.assertEqual(r["11"][2:5], ["Section (ARC_gbp)", "A002", "custom"])         # control chars -> view type
        self.assertEqual(r["10"][4], "100")
        self.assertEqual(r["20"][3:6], ["A001", "500", "BD_block"])                     # sheet from views on sheets

    def test_counts_and_links(self):
        with open(os.path.join(self.out, "view_counts.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["10"], {"OST_Grids": 5, "OST_Dimensions": 4})
        with open(os.path.join(self.out, "model_counts.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["OST_RvtLinks"], 0)
        self.assertIn("without counts", self.p.stdout)                                 # views 11, 20 named

    def test_count_for_view_not_on_sheet_stops(self):
        p, out = run(dict(ALL, **{"view_counts_77.json": COUNT}))
        self.assertEqual(p.returncode, 2)
        self.assertIn("77", p.stderr)
        self.assertEqual(os.listdir(out), [])

    def test_no_sheets_stops(self):
        files = dict(ALL)
        del files["sheets.json"]
        p, _ = run(files)
        self.assertEqual(p.returncode, 2)
        self.assertIn("get_sheets", p.stderr)

    @unittest.skipUnless(os.path.isdir(REAL) and os.path.isdir(OURS), "real data not here")
    def test_real_responses(self):
        tmp = tempfile.mkdtemp()
        shutil.copytree(REAL, os.path.join(tmp, "mcp"))
        p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", os.path.join(tmp, "mcp"), "--out", tmp],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(os.path.join(tmp, "view_props.tsv"), "rb") as x, open(os.path.join(OURS, "view_props.tsv"), "rb") as y:
            self.assertEqual(x.read(), y.read())
        ours = [r for r in rows(os.path.join(OURS, "views_on_sheets.tsv"))
                if not (r[1] == "C007" and r[2] in ("1531502", "1531509", "1531516", "1531523"))]
        self.assertEqual(rows(os.path.join(tmp, "views_on_sheets.tsv")), ours)
        with open(os.path.join(tmp, "view_counts.json"), encoding="utf-8") as f, \
                open(os.path.join(OURS, "view_counts.json"), encoding="utf-8") as g:
            new, old = json.load(f), json.load(g)
        for v in (k for k in new if not k.startswith("_")):
            self.assertTrue(all(new[v].get(k) == n for k, n in old[v].items()), v)


if __name__ == "__main__":
    unittest.main(verbosity=1)
