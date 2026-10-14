"""Tests for tools/extract/g5_extract.py (levels, base points, property line, schedule list).

Run: python -I test_extract_g5.py
Real data: fixtures_real/g5_revit_mcp_20261014 (revit-mcp responses saved 2026-10-14, read-only calls) must give our
levels.tsv / all_schedules.tsv byte for byte and points.tsv value for value.
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
EXTRACT = os.path.join(PKG, "tools", "extract", "g5_extract.py")
REAL = os.path.join(HERE, "fixtures_real", "g5_revit_mcp_20261014")
OURS = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit-runs", "audit-2026-10-13-g5", "_raw"))


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


BB = lambda x, y, z: {"min": {"x": x, "y": y, "z": z}, "max": {"x": x + 1, "y": y + 2, "z": z}}
LEVELS = {"elements": [{"id": 1, "name": "L1", "type": "Lv", "category": "Levels", "parameters": {"Elevation": "0", "Building Story": "Yes"}},
                       {"id": 2, "name": "L2", "type": "Lv", "category": "Levels", "parameters": {"Elevation": "3500", "Building Story": "No"}}]}
POINTS = {"elements": [{"id": 5, "category": "Project Base Point", "boundingBox": BB(10, 20, 0),
                        "parameters": {"E/W": "836000000", "N/S": "818000000", "Elev": "0", "Angle to True North": "12.50°"}},
                       {"id": 6, "category": "Survey Point", "boundingBox": BB(0, 0, 0), "parameters": {}},
                       {"id": 7, "category": "Property Lines", "boundingBox": BB(1, 2, 0), "parameters": {"Area": "2.000 m²"}}]}
SCHED = {"schedules": [{"name": "GBP S10", "Id": 30}, {"name": "<Revision Schedule> 2", "Id": 31}, {"name": "Sheet List", "Id": 29}]}


class G5Extract(unittest.TestCase):
    def test_mcp_servers_for_revit_shape(self):
        p, out = run({"levels.json": LEVELS, "points.json": POINTS, "schedules.json": SCHED})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(rows(os.path.join(out, "levels.tsv")), [["1", "L1", "Lv", "0", "1"], ["2", "L2", "Lv", "3500", "0"]])
        pts = rows(os.path.join(out, "points.tsv"))
        self.assertEqual([r[1] for r in pts], ["Survey Point", "Project Base Point", "Property Line bbox min", "Property Line bbox max"])
        self.assertEqual(pts[1][5:], ["836000000", "818000000", "0", "12.5"])
        self.assertEqual(pts[3][2:4], ["2.000", "4.000"])
        self.assertEqual(rows(os.path.join(out, "all_schedules.tsv")), [["29", "Sheet List"], ["30", "GBP S10"]])
        self.assertIn("1 title-block revision", p.stdout)

    def test_keep_revision_schedules(self):
        p, out = run({"levels.json": LEVELS, "points.json": POINTS, "schedules.json": SCHED}, "--keep-revision-schedules")
        self.assertEqual(len(rows(os.path.join(out, "all_schedules.tsv"))), 3)

    def test_no_base_point_stops(self):
        pts = {"elements": [POINTS["elements"][1]]}
        p, out = run({"levels.json": LEVELS, "points.json": pts})
        self.assertEqual(p.returncode, 2)
        self.assertIn("Project Base Point", p.stderr)
        self.assertEqual(os.listdir(out), [])

    def test_query_without_ids_explains_max_results(self):
        q = {"results": {"analysis": {"totalElements": 2}}}                         # revit-mcp with maxResults 0
        p, _ = run({"levels.json": LEVELS, "points.json": POINTS, "query_levels.json": q})
        self.assertEqual(p.returncode, 2)
        self.assertIn("maxResults", p.stderr)

    def test_internal_value_wins_for_coordinates(self):
        rm = {"results": {"ElementId 5": {"BasicElementInfo": {"category": "Project Base Point", "processingStatus": "Success"},
                                          "BoundingBox": {"minXYZ": {"x": 0, "y": 0, "z": 0}, "maxXYZ": {"x": 0, "y": 0, "z": 0}},
                                          "InstanceParameters": [{"name": "E/W", "value": "2771719.744094", "displayValue": "844820.178"}]}}}
        p, out = run({"levels.json": LEVELS, "points.json": rm})                    # project shown in metres
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(rows(os.path.join(out, "points.tsv"))[0][5], "844820178")
        self.assertIn("internal value used", p.stdout)

    def test_level_without_elevation_stops(self):
        lv = {"elements": [{"id": 1, "name": "L1", "type": "Lv", "category": "Levels", "parameters": {}}]}
        p, _ = run({"levels.json": lv, "points.json": POINTS})
        self.assertEqual(p.returncode, 2)
        self.assertIn("Elevation", p.stderr)

    @unittest.skipUnless(os.path.isdir(REAL) and os.path.isdir(OURS), "real data not here")
    def test_real_responses_reproduce_our_extract(self):
        tmp = tempfile.mkdtemp()
        shutil.copytree(REAL, os.path.join(tmp, "mcp"))
        p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", os.path.join(tmp, "mcp"), "--out", tmp],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        for f in ("levels.tsv", "all_schedules.tsv"):
            with open(os.path.join(tmp, f), "rb") as x, open(os.path.join(OURS, f), "rb") as y:
                self.assertEqual(x.read(), y.read(), f)
        new, ours = rows(os.path.join(tmp, "points.tsv")), rows(os.path.join(OURS, "points.tsv"))
        self.assertEqual(len(new), len(ours))
        for a, b in zip(new, ours):
            for u, v in zip(a, b):
                try:
                    self.assertAlmostEqual(float(u), float(v), places=6)
                except ValueError:
                    self.assertEqual(u, v)


if __name__ == "__main__":
    unittest.main(verbosity=1)
