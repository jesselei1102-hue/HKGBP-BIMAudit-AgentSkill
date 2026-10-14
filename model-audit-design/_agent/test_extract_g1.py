"""Tests for tools/extract/g1_extract.py (S14 extract) on small responses in both MCP shapes.

Run: python -I test_extract_g1.py
Real-data check (Cursor 2026-10-13 revit-mcp dumps vs our S14 extract and analysis): check_g1_real.py.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
EXTRACT = os.path.join(PKG, "tools", "extract", "g1_extract.py")


def bb(x0, y0, z0, x1, y1, z1):
    return {"min": {"x": x0, "y": y0, "z": z0}, "max": {"x": x1, "y": y1, "z": z1}}


def el(i, family, typ, level="L1", box=(0, 0, 0, 1, 1, 1), **params):
    e = {"id": i, "family": family, "type": typ, "level": level, "parameters": params}
    if box:
        e["boundingBox"] = bb(*box)
    return e


ROOMS = {"elements": [{"id": 1, "parameters": {"Name": "OFFICE", "Number": "1", "Area": "10.000 m²", "Level": "L1"},
                       "boundingBox": bb(0, 0, 0, 10, 10, 10)}]}
CW = {"elements": [el(10, None, "Glass CW", Area="5.000 m²"), el(11, None, "External Louvre", Area="1.000 m²"),
                   el(12, None, "Generic 200", Area="9.000 m²")]}
PN = {"elements": [el(20, "Louvre_Panel", "30x150", Area="0.400 m²", box=(0, 0, 3, 1, 1, 4)),
                   el(21, "Glazed_Panel", "50x100 top hung", Area="0.500 m²", box=(0, 0, 2, 2, 2, 6)),
                   el(22, "Glazed_Panel", "fixed", Area="1.000 m²"),
                   el(23, "System Panel", "Empty", Area="0.000 m²")]}
WIN = {"elements": [el(30, "FS_Window", "900x500", Area="0.450 m²", Mark="1")]}
DOORS = {"elements": [el(40, "DOR-SGL-Glass", "1000x2100", Area="2.100 m²", Mark="3"),
                      el(41, "DOR-SGL-Wood-w_Glazing", "900x2100", Area="1.890 m²"),
                      el(42, "DOR-ETY", "7900x2500", Area="19.750 m²"), el(43, "DOR-SGL-Wood", "900x2100")]}
ALL = {"rooms.json": ROOMS, "cw.json": CW, "pn.json": PN, "windows.json": WIN, "doors.json": DOORS}


def run(files, *extra, pre=()):
    tmp = tempfile.mkdtemp()
    mcp, out = os.path.join(tmp, "mcp"), os.path.join(tmp, "raw")
    os.makedirs(mcp)
    os.makedirs(out)
    for n, d in files.items():
        json.dump(d, open(os.path.join(mcp, n), "w", encoding="utf-8"))
    for n in pre:
        open(os.path.join(out, n), "w").close()
    p = subprocess.run([sys.executable, "-I", EXTRACT, "--mcp", mcp, "--out", out] + list(extra), capture_output=True, text=True)
    return p, out


def tsv(path):
    with open(path, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f]
    return [dict(zip(rows[0], r)) for r in rows[1:]]


class G1Extract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.out = run(ALL)

    def test_runs(self):
        self.assertEqual(self.p.returncode, 0, self.p.stderr)

    def test_panel_kinds_from_family_and_type(self):
        pn = {r["id"]: r for r in tsv(os.path.join(self.out, "pn_part1.tsv"))}
        self.assertEqual({k: v["kind"] for k, v in pn.items()}, {"20": "L", "21": "H"})
        self.assertEqual((pn["21"]["cx"], pn["21"]["cy"], pn["21"]["cz"]), ("1.0", "1.0", "4.0"))
        self.assertIn("fixed glazing", self.p.stdout)                               # 22 and 23 named, not dropped silently
        self.assertIn("Glazed_Panel / fixed", self.p.stdout)

    def test_every_panel_box_kept(self):
        s = {r["id"]: (r["minz"], r["maxz"]) for r in tsv(os.path.join(self.out, "pn_bbox_sample.tsv"))}
        self.assertEqual(s, {"20": ("3", "4"), "21": ("2", "6")})

    def test_walls_filtered_by_type(self):
        self.assertEqual([r["id"] for r in tsv(os.path.join(self.out, "cw_part1.tsv"))], ["10", "11"])
        self.assertIn("Generic 200", self.p.stdout)

    def test_doors_split(self):
        self.assertEqual([r["id"] for r in tsv(os.path.join(self.out, "doors.tsv"))], ["40", "42"])   # vision panel is not glass
        other = {r["family"]: r["count"] for r in tsv(os.path.join(self.out, "doors_other.tsv"))}
        self.assertEqual(other, {"DOR-SGL-Wood-w_Glazing": "1", "DOR-SGL-Wood": "1"})

    def test_patterns_per_project(self):
        p, out = run(ALL, "--hung-type-pattern", "hung|fixed", "--wall-type-pattern", "glass")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual({r["id"]: r["kind"] for r in tsv(os.path.join(out, "pn_part1.tsv"))}, {"20": "L", "21": "H", "22": "H"})
        self.assertEqual([r["id"] for r in tsv(os.path.join(out, "cw_part1.tsv"))], ["10"])

    def test_stale_parts_stop(self):
        p, out = run(ALL, pre=("cw_part2.tsv",))
        self.assertEqual(p.returncode, 2)
        self.assertIn("cw_part2.tsv", p.stderr)
        self.assertEqual(sorted(os.listdir(out)), ["cw_part2.tsv"])                 # nothing new written

    def test_panel_without_box_stops(self):
        pn = {"elements": PN["elements"] + [el(24, "Glazed_Panel", "top hung", Area="0.5 m²", box=None)]}
        p, _ = run(dict(ALL, **{"pn.json": pn}))
        self.assertEqual(p.returncode, 2)
        self.assertIn("24", p.stderr)

    def test_revit_mcp_shape(self):
        rm = {"results": {"ElementId 30": {"BasicElementInfo": {"familyName": "FS", "typeName": "T", "levelName": "L1",
                                                                "processingStatus": "Success"},
                                           "BoundingBox": {"minXYZ": {"x": 0, "y": 0, "z": 0}, "maxXYZ": {"x": 1, "y": 1, "z": 1}},
                                           "InstanceParameters": [{"name": "Area", "displayValue": "0.450 m²", "value": "4.84"},
                                                                  {"name": "Mark", "displayValue": "7"}]}}}
        p, out = run(dict(ALL, **{"windows.json": rm}))
        self.assertEqual(p.returncode, 0, p.stderr)
        w = tsv(os.path.join(out, "fs_windows.tsv"))[0]
        self.assertEqual((w["id"], w["mark"], w["area_m2"]), ("30", "7", "0.450"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
