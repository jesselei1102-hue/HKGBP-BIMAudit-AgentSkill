"""Tests for tools/extract/g2_extract.py: both MCP formats, no project-specific numbers, every stop condition.

Run: python -I test_extract_g2.py
The two real-data tests use the Cursor runs of 2026-10-14 (revit-mcp and mcp-servers-for-revit) and are skipped when
those folders are not on this machine.
"""
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
EXTRACT = os.path.join(PKG, "tools", "extract", "g2_extract.py")
CURSOR = r"C:\Users\Datech\Desktop\Cursor Projects\HK GBP\model-audit\work\model-audit-runs"


def run(mcp_files, *extra):
    tmp = tempfile.mkdtemp()
    mcp, out = os.path.join(tmp, "mcp"), os.path.join(tmp, "raw")
    os.makedirs(mcp)
    os.makedirs(out)
    for name, data in mcp_files.items():
        with open(os.path.join(mcp, name), "w", encoding="utf-8") as f:
            f.write(data if isinstance(data, str) else json.dumps(data))
    p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", mcp, "--out", out] + list(extra),
                       capture_output=True, text=True)
    return p, out


def tsv(path):
    with open(path, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f]
    return [dict(zip(rows[0], r)) for r in rows[1:]]


BB = lambda x0, y0, z0, x1, y1, z1: {"minXYZ": {"x": x0, "y": y0, "z": z0}, "maxXYZ": {"x": x1, "y": y1, "z": z1}}
BB2 = lambda x0, y0, z0, x1, y1, z1: {"min": {"x": x0, "y": y0, "z": z0}, "max": {"x": x1, "y": y1, "z": z1}}


def rm_el(eid, info, bb, params):
    return {"BasicElementInfo": dict({"processingStatus": "Success"}, **info), "BoundingBox": bb,
            "InstanceParameters": [{"name": k, "value": v[1], "displayValue": v[0]} for k, v in params.items()]}


ROOMS_RM = {"outcome": "ok", "results": {
    "ElementId 2": rm_el(2, {"levelName": "L1"}, BB(0, 0, 0, 10, 10, 10),
                         {"Name": ("OFFICE", "OFFICE"), "Number": ("1", "1"), "Area": ("1,076.391 SF", "1076.391")}),
    "ElementId 1": rm_el(1, {"levelName": "L1"}, BB(0, 0, 0, 5, 5, 10),
                         {"Name": ("WC", "WC"), "Number": ("2", "2"), "Area": ("2.323 m²", "25")}),
    "ElementId 3": {"BasicElementInfo": {"levelName": "L1", "processingStatus": "Success"},
                    "InstanceParameters": [{"name": "Name", "displayValue": "UNPLACED"}, {"name": "Number", "displayValue": "9"},
                                           {"name": "Area", "displayValue": "0 m²"}]}}}
FIX_RM = {"results": {"ElementId 11": rm_el(11, {"familyName": "WC", "typeName": "T", "levelName": "L1"},
                                            BB(1, 1, 0, 3, 3, 2), {})}}
DOORS_RM = {"results": {
    "ElementId 21": rm_el(21, {"familyName": "D", "typeName": "900", "levelName": "L1"}, BB(4, 0, 0, 6, 1, 7),
                          {"ClearW": ("850", "2.788713910761")}),
    "ElementId 22": rm_el(22, {"familyName": "D", "typeName": "1800", "levelName": "L1"}, BB(7, 0, 0, 9, 1, 7),
                          {"ClearW": ("900", "5.413385826772")}),                        # shows 900, model 1650
    "ElementId 23": rm_el(23, {"familyName": "G", "typeName": "glass", "levelName": "L1"}, BB(0, 9, 0, 1, 10, 7), {})}}


class Generic(unittest.TestCase):
    def test_revit_mcp_shape_and_options(self):
        p, out = run({"rooms_1.json": ROOMS_RM, "fixtures_1.json": FIX_RM, "doors_1.json": DOORS_RM},
                     "--width-param", "ClearW")
        self.assertEqual(p.returncode, 0, p.stderr)
        rooms = tsv(os.path.join(out, "rooms.tsv"))
        self.assertEqual([r["id"] for r in rooms], ["1", "2"])                     # sorted, unplaced room 3 left out
        self.assertEqual(rooms[1]["area_m2"], "100.000")                           # 1,076.391 ft² -> m² from internal value
        self.assertEqual(rooms[0]["area_m2"], "2.323")                             # m² kept as shown
        doors = {d["id"]: d for d in tsv(os.path.join(out, "doors_all.tsv"))}
        self.assertEqual(doors["21"]["width_moe_mm"], "850")
        self.assertEqual(doors["22"]["width_moe_mm"], "1650")                      # internal value wins, warned
        self.assertEqual(doors["23"]["width_moe_mm"], "")
        fx = tsv(os.path.join(out, "fixtures.tsv"))[0]
        self.assertEqual((fx["cx"], fx["cy"], fx["z"]), ("2.0", "2.0", "0"))
        for w in ("unplaced", "door 22", "without 'ClearW'", "completeness not checked", "room_boundaries"):
            self.assertIn(w, p.stdout)

    def test_mcp_servers_for_revit_shape(self):
        rooms = {"elements": [{"id": 5, "parameters": {"Name": "A", "Number": "1", "Area": "10.000 m²", "Level": "L2"},
                               "boundingBox": BB2(0, 0, 0, 3, 3, 3)}]}
        doors = {"elements": [{"id": 7, "family": "D", "type": "T", "level": "L2", "parameters": {"Level": "L2", "W": "800"},
                               "boundingBox": BB2(0, 0, 0, 1, 1, 7)}]}
        p, out = run({"rooms.json": rooms, "doors.json": doors, "query_rooms.json": {"results": {"elementIds": [5]}},
                      "query_doors.json": {"results": {"elementIds": [7]}}}, "--width-param", "W")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(tsv(os.path.join(out, "rooms.tsv"))[0]["level"], "L2")   # level from the Level parameter
        self.assertEqual(tsv(os.path.join(out, "doors_all.tsv"))[0]["width_moe_mm"], "800")
        self.assertIn("no fixtures", p.stdout)

    def test_missing_element_stops(self):
        p, out = run({"rooms_1.json": ROOMS_RM, "doors_1.json": DOORS_RM,
                      "query_doors.json": {"results": {"elementIds": [21, 22, 23, 24]}}})
        self.assertEqual(p.returncode, 2)
        self.assertIn("24", p.stderr)
        self.assertEqual(os.listdir(out), [])                                      # nothing written, not even rooms.tsv

    def test_truncated_query_stops(self):
        q = {"outcome": "Found 3 elements, but returning only first 1", "results": {
            "analysis": {"totalElements": 3}, "Element Ids": [21]}}                    # revit-mcp shape, maxResults hit
        p, _ = run({"rooms_1.json": ROOMS_RM, "doors_1.json": DOORS_RM, "query_doors.json": q})
        self.assertEqual(p.returncode, 2)
        self.assertIn("truncated", p.stderr)

    def test_revit_mcp_query_shape(self):
        q = {"results": {"analysis": {"totalElements": 3}, "Element Ids": [21, 22, 23]}}
        p, _ = run({"rooms_1.json": ROOMS_RM, "doors_1.json": DOORS_RM, "query_doors.json": q}, "--width-param", "ClearW")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("doors: no query", p.stdout)

    def test_failed_read_stops(self):
        bad = {"results": {"ElementId 11": {"BasicElementInfo": {"processingStatus": "Failed"}}}}
        p, _ = run({"rooms_1.json": ROOMS_RM, "fixtures_1.json": bad})
        self.assertEqual(p.returncode, 2)
        self.assertIn("could not be read", p.stderr)

    def test_unknown_format_stops(self):
        p, _ = run({"rooms_1.json": {"data": [1, 2]}})
        self.assertEqual(p.returncode, 2)
        self.assertIn("adapter", p.stderr)

    def test_fixture_without_box_stops(self):
        fx = {"elements": [{"id": 9, "family": "WC", "type": "T", "level": "L1"}]}
        p, _ = run({"rooms_1.json": ROOMS_RM, "fixtures.json": fx})
        self.assertEqual(p.returncode, 2)
        self.assertIn("bounding box", p.stderr)

    def test_duplicate_stops(self):
        p, _ = run({"rooms_1.json": ROOMS_RM, "fixtures_1.json": FIX_RM, "fixtures_2.json": FIX_RM})
        self.assertEqual(p.returncode, 2)
        self.assertIn("twice", p.stderr)


@unittest.skipUnless(os.path.isdir(CURSOR), "Cursor runs not on this machine")
class SameAsCursorRuns(unittest.TestCase):
    """The package script reproduces both Cursor extractions byte for byte (one revit-mcp, one mcp-servers-for-revit)."""

    def check(self, run_name, files):
        src = os.path.join(CURSOR, run_name, "_raw")
        tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(src, "mcp"), os.path.join(tmp, "mcp"))
        os.makedirs(os.path.join(tmp, "raw"))
        p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", os.path.join(tmp, "mcp"), "--out",
                            os.path.join(tmp, "raw")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        for f in files:
            self.assertTrue(filecmp.cmp(os.path.join(tmp, "raw", f), os.path.join(src, f), shallow=False), f)
        return p

    def test_revit_mcp_run(self):
        self.check("audit-2026-10-14-s10", ["rooms.tsv", "fixtures.tsv", "doors_all.tsv", "room_polygons.json"])

    def test_mcp_servers_for_revit_run(self):
        p = self.check("audit-2026-10-14-s10-mcp2", ["rooms.tsv", "fixtures.tsv", "doors_all.tsv"])
        self.assertNotIn("completeness not checked", p.stdout)                     # query_model saved: checked


if __name__ == "__main__":
    unittest.main(verbosity=1)
