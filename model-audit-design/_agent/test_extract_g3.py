"""Tests for tools/extract/g3_extract.py (area schemes) on small responses in both MCP shapes.

Run: python -I test_extract_g3.py
Real data: the script reproduces our areas.tsv / area_schemes.tsv byte for byte from the saved 2026-10-13 responses
(test_real_ours, skipped when the run folder is absent).
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
EXTRACT = os.path.join(PKG, "tools", "extract", "g3_extract.py")
OURS = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit-runs", "audit-2026-10-13-g3", "_raw"))


def rm(eid, cat, name, params, box=True):
    """revit-mcp element; params {name: (display or None, value)}."""
    e = {"BasicElementInfo": {"name": name, "category": cat, "processingStatus": "Success"},
         "InstanceParameters": [dict({"name": k, "value": v}, **({"displayValue": d} if d is not None else {}))
                                for k, (d, v) in params.items()]}
    if box:
        e["BoundingBox"] = {"minXYZ": {"x": 1.234, "y": 2.0, "z": 0}, "maxXYZ": {"x": 3.0, "y": 4.0, "z": 1}}
    return e


SCHEMES = {"results": {"ElementId 100": rm(100, "Area Schemes", "ARC_gbp_gfa", {}, box=False),
                       "ElementId 101": rm(101, "Area Schemes", "ARC_gbp_ufa", {}, box=False),
                       "ElementId 9": rm(9, "Property Lines", "Property", {"Area": ("2000.000 m²", "21527.8")}),
                       "ElementId 8": rm(8, "Property Lines", "Property Line 1", {}, box=False)}}
PART = {"results": {"ElementId 5": rm(5, "Areas", "Area", {"Area Scheme Id": ("100", "100"), "Area": ("50.000 m²", "538.2")},
                                      box=False)}}
FULL = {"results": {"ElementId 5": rm(5, "Areas", "Area", {
    "Area Scheme Id": ("100", "100"), "Level": ("L1", "L1"), "Name": ("TX RM", "TX RM"), "GFA DEDUCT 2.2": (None, "1"),
    "GFA SUMMARY": ("Yes", "1"), "SERVED FACADE": (None, "32.8083989501"), "FRC HEIGHT": (None, "0"),
    "Perimeter": ("30000", "98.4")})}}


def run(files, *extra):
    tmp = tempfile.mkdtemp()
    mcp, out = os.path.join(tmp, "mcp"), os.path.join(tmp, "raw")
    os.makedirs(mcp)
    os.makedirs(out)
    for n, d in files.items():
        json.dump(d, open(os.path.join(mcp, n), "w", encoding="utf-8"))
    p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", mcp, "--out", out] + list(extra), capture_output=True, text=True)
    return p, out


def tsv(path):
    with open(path, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f]
    return {r[0]: dict(zip(rows[0], r)) for r in rows[1:]}


class G3Extract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.out = run({"areas_part1.json": PART, "areas_all_1.json": FULL, "area_schemes.json": SCHEMES})
        cls.a = tsv(os.path.join(cls.out, "areas.tsv"))

    def test_runs(self):
        self.assertEqual(self.p.returncode, 0, self.p.stderr)

    def test_one_row_per_area_merged(self):
        self.assertEqual(sorted(self.a), ["5", "9"])                                # area 5 in two files -> one row
        r = self.a["5"]
        self.assertEqual((r["scheme"], r["level"], r["name"], r["area_m2"]), ("ARC_gbp_gfa", "L1", "TX RM", "50.000"))
        self.assertEqual((r["minx"], r["maxy"]), ("1.23", "4.00"))                  # box from the other file

    def test_yes_no_from_stored_value(self):
        self.assertEqual((self.a["5"]["gfa_summary"], self.a["5"]["d22"], self.a["5"]["d23"]), ("1", "1", "0"))

    def test_length_without_shown_text(self):
        self.assertEqual(self.a["5"]["served_facade_mm"], "10000")                  # 32.808 ft -> 10000 mm
        self.assertEqual(self.a["5"]["frc_height"], "0")
        self.assertEqual(self.a["5"]["perimeter_mm"], "30000")

    def test_property_lines(self):
        self.assertEqual((self.a["9"]["scheme"], self.a["9"]["area_m2"]), ("(property line)", "2000.000"))
        self.assertIn("left out: 8", self.p.stdout)                                 # unplaced line named

    def test_scheme_counts_include_empty(self):
        with open(os.path.join(self.out, "area_schemes.tsv"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "id\tname\tareas\n100\tARC_gbp_gfa\t1\n101\tARC_gbp_ufa\t0\n")

    def test_param_map(self):
        full = json.loads(json.dumps(FULL).replace("SERVED FACADE", "EVA FACADE"))
        m = os.path.join(tempfile.mkdtemp(), "map.json")
        json.dump({"served_facade": "EVA FACADE"}, open(m, "w"))
        p, out = run({"areas_all_1.json": full, "area_schemes.json": SCHEMES}, "--param-map", m)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(tsv(os.path.join(out, "areas.tsv"))["5"]["served_facade_mm"], "10000")

    def test_unknown_scheme_stops(self):
        p, out = run({"areas_all_1.json": FULL, "area_schemes.json": {"results": {"ElementId 101": SCHEMES["results"]["ElementId 101"]}}})
        self.assertEqual(p.returncode, 2)
        self.assertIn("scheme", p.stderr)
        self.assertEqual(os.listdir(out), [])

    def test_rasters_and_completeness(self):
        ras = {"elements": [{"id": 70, "name": "C001 - table.jpg", "category": "Raster Images",
                             "parameters": {"Width": "325", "Height": "460"}}]}
        q = {"results": {"elementIds": [70, 71]}}
        p, _ = run({"areas_all_1.json": FULL, "area_schemes.json": SCHEMES, "rasters.json": ras, "query_rasters.json": q})
        self.assertEqual(p.returncode, 2)
        self.assertIn("71", p.stderr)
        p, out = run({"areas_all_1.json": FULL, "area_schemes.json": SCHEMES, "rasters.json": ras})
        self.assertEqual(tsv(os.path.join(out, "rasters.tsv"))["70"]["width_mm"], "325")

    @unittest.skipUnless(os.path.isdir(os.path.join(OURS, "mcp")), "sample run not here")
    def test_real_ours(self):
        tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(OURS, "mcp"), os.path.join(tmp, "mcp"))
        p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", os.path.join(tmp, "mcp"), "--out", tmp],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        for f in ("areas.tsv", "area_schemes.tsv"):
            with open(os.path.join(tmp, f), "rb") as x, open(os.path.join(OURS, f), "rb") as y:
                self.assertEqual(x.read(), y.read(), f)


if __name__ == "__main__":
    unittest.main(verbosity=1)
