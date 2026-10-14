"""Tests for tools/drawings (G4) on a small synthetic extract.

Run: python -I test_drawings.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
ANALYZE = os.path.join(PKG, "tools", "drawings", "analyze.py")

VOS = ("sheet_id\tsheet\tview_id\tview_name\tview_type\toutline_miny\toutline_maxy\n"
       "1\tA001\t10\tSITE\tAreaPlan\t0\t1\n1\tA001\t11\tA001 Abbreviation & Legend\tLegend\t0\t1\n"
       "1\tA001\t12\tA001 Fs Notes\tLegend\t0\t1\n2\tA002\t20\tG/F\tFloorPlan\t0\t1\n"
       "3\tA006\t30\tA\tSection\t0\t1\n3\tA006\t31\tB\tSection\t0\t1\n4\tA007\t40\t1\tElevation\t0\t1\n"
       "5\tC005\t50\tCOMP G/F\tAreaPlan\t0\t1\n6\tC007\t60\tGBP S14 - WINDOW AREA CALCULATIONS\tSchedule\t0\t1\n")
PROPS = ("view_id\tname\tview_type_name\tsheet\tscale\ttemplate\ttitle_on_sheet\n"
         "10\tSITE\tBlock plan\tA001\t500\tT\t\n20\tG/F\tFloor Plan (GBP)\tA002\t100\tBD_gbp_color\t\n"
         "30\tA\tSection\tA006\t100\tS\t\n31\tB\tSection\tA006\t100\tS\t\n40\t1\tElevation\tA007\t100\tE\t\n")
COUNTS = {"20": {"OST_Grids": 5, "OST_Dimensions": 3, "OST_Viewers": 2, "OST_Doors": 10, "OST_DoorTags": 4,
                 "OST_Rooms": 5, "OST_RoomTags": 5},
          "30": {"OST_Grids": 2, "OST_Levels": 3, "OST_Dimensions": 1, "OST_SpotElevations": 2},
          "31": {"OST_Grids": 2, "OST_Levels": 3, "OST_Dimensions": 1},
          "40": {"OST_Grids": 2, "OST_Levels": 3, "OST_Dimensions": 1},
          "50": {"OST_Grids": 4, "OST_Areas": 1}}
COLOURS = {"block_plan_site": {"sheet": "A001", "box": [0, 0, 1, 1], "pixels": 100, "table1": {}, "pink": 0,
                               "grey_pct": 0, "black_pct": 5, "top": [[[230, 250, 240], 90]]},
           "gfa_gf": {"sheet": "C002", "box": [0, 0, 1, 1], "pixels": 100, "table1": {"2": 50, "3a": 5}, "pink": 0,
                      "grey_pct": 0.1, "black_pct": 20, "top": [[[227, 100, 102], 50]]},
           "legend_table1": {"sheet": "A001", "box": [0, 0, 1, 1], "pixels": 100,
                             "table1": {"1": 1, "2": 1, "3a": 1, "3b": 1, "4a": 1, "4b": 1}, "pink": 0,
                             "grey_pct": 0, "black_pct": 0, "top": [[[255, 255, 255], 90]]}}
RVT = {"file": "m.rvt", "size_mb": 40.0, "format": "2027", "build": "x", "other_rvt_in_folder": ["old.rvt"]}
READ = ("key\tsheet\titem\tvalue\tconfidence\tnote\n"
        "level_heads\tA007\tlevels\tSFL 0.25 m\thigh\t\nelevation_streets\tA007\tstreets\tnone near ground\thigh\t\n"
        "section_streets\tA006\tstreets\tstreet names on both sides\tmedium\t\n")


class DrawingsRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(cls.tmp, "_raw")
        os.makedirs(raw)
        files = {"views_on_sheets.tsv": VOS, "view_props.tsv": PROPS, "readings.tsv": READ,
                 "view_counts.json": json.dumps(COUNTS), "colour_samples.json": json.dumps(COLOURS),
                 "rvt_info.json": json.dumps(RVT), "rasters.tsv": "id\tname\twidth_mm\theight_mm\n1\tC001 - x.jpg\t1\t1\n"}
        for n, t in files.items():
            with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                f.write(t)
        cls.out = os.path.join(cls.tmp, "G4.json")
        cls.proc = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                                   "--out", cls.out], capture_output=True, text=True)
        with open(cls.out, encoding="utf-8") as f:
            cls.c = {c["id"]: c for c in json.load(f)["checks"]}

    def test_runs(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)

    def test_block_plan(self):
        self.assertEqual(self.c["V01-L1"]["status"], "PASS")
        self.assertEqual(self.c["V01-L3"]["status"], "FAIL")              # green, not pink

    def test_plan_counts(self):
        self.assertEqual(self.c["V02-L2-20"]["status"], "PASS")
        self.assertEqual(self.c["V02-L5-20"]["status"], "FAIL")           # 4 of 10 doors tagged
        self.assertEqual(self.c["V02-L10-20"]["status"], "PASS")

    def test_readings_scoped_to_read_sheets(self):
        self.assertEqual(self.c["V04-L5-40"]["status"], "FAIL")           # A007 read: no streets
        self.assertEqual(self.c["V03-L5-30"]["status"], "PASS")           # A006 read: both sides
        self.assertEqual(self.c["V04-L3"]["status"], "FAIL")              # SFL … m, not mPD

    def test_colours(self):
        self.assertEqual(self.c["A02-L1"]["status"], "PASS")
        self.assertEqual(self.c["A02-L2"]["status"], "PASS")
        self.assertEqual(self.c["V10-L4"]["status"], "FAIL")              # no halftone

    def test_file(self):
        self.assertEqual(self.c["A03-L3"]["status"], "PASS")
        self.assertEqual(self.c["A03-FOLDER"]["status"], "FAIL")
        self.assertEqual(self.c["A03-L7"]["status"], "FAIL")

    def test_window_schedule_is_not_a_diagram(self):
        self.assertEqual(self.c["V13-L1"]["status"], "FAIL")

    def test_compartment_dims(self):
        self.assertEqual(self.c["V08-DIM-50"]["status"], "FAIL")

    def test_reading_marked_not_read_is_not_a_fail(self):
        tmp = tempfile.mkdtemp()
        raw = os.path.join(tmp, "_raw")
        os.makedirs(raw)
        read = READ.replace("street names on both sides\tmedium", "not read\tlow")
        files = {"views_on_sheets.tsv": VOS, "view_props.tsv": PROPS, "readings.tsv": read,
                 "view_counts.json": json.dumps(COUNTS), "colour_samples.json": json.dumps(COLOURS),
                 "rvt_info.json": json.dumps(RVT), "rasters.tsv": "id\tname\twidth_mm\theight_mm\n"}
        for n, t in files.items():
            with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                f.write(t)
        out = os.path.join(tmp, "G4.json")
        subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt", "--out", out],
                       capture_output=True, text=True)
        c = {x["id"]: x for x in json.load(open(out, encoding="utf-8"))["checks"]}
        self.assertNotEqual(c["V03-L5-30"]["status"], "FAIL")                      # 'not read' is not a reading

    def test_links_need_a_count(self):
        self.assertEqual(self.c["A03-L4"]["status"], "UNCLEAR")           # no model_counts.json: never assume 0


class TaskSelectionG4(unittest.TestCase):
    """--tasks on G4: A03 runs from the file header alone; V13 without the S14 analysis is named, not judged."""

    FILES = {"views_on_sheets.tsv": VOS, "view_props.tsv": PROPS, "readings.tsv": READ,
             "view_counts.json": json.dumps(COUNTS), "colour_samples.json": json.dumps(COLOURS),
             "rvt_info.json": json.dumps(RVT), "rasters.tsv": "id\tname\twidth_mm\theight_mm\n1\tC001 - x.jpg\t1\t1\n"}

    def run_sel(self, names, *extra):
        tmp = tempfile.mkdtemp()
        raw = os.path.join(tmp, "_raw")
        os.makedirs(raw)
        for n in names:
            with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                f.write(self.FILES[n])
        out = os.path.join(tmp, "G4.json")
        p = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                            "--out", out] + list(extra), capture_output=True, text=True)
        return p, (json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None)

    @staticmethod
    def checks(d, task):
        return sorted((c["id"], c["status"], str(c["actual"])) for c in d["checks"]
                      if c["task"] == task and not c["id"].endswith("-INPUT"))

    @classmethod
    def setUpClass(cls):
        cls.full_p, cls.full = cls.run_sel(cls, list(cls.FILES))

    def test_a03_from_file_header_only(self):
        p, d = self.run_sel(["rvt_info.json", "rasters.tsv"], "--tasks", "A03")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.checks(d, "AUD-A03"), self.checks(self.full, "AUD-A03"))

    def test_v02_alone_equals_group(self):
        p, d = self.run_sel(list(self.FILES), "--tasks", "V02")
        self.assertEqual({c["task"] for c in d["checks"]}, {"AUD-V02"})
        self.assertEqual(self.checks(d, "AUD-V02"), self.checks(self.full, "AUD-V02"))

    def test_v13_without_s14(self):
        p, d = self.run_sel(list(self.FILES), "--tasks", "V13")
        c = {x["id"]: x for x in d["checks"]}
        self.assertIn("V13-L1", c)                                          # diagram check needs no S14
        self.assertNotIn("V13-C1", c)                                       # glass / openable need S14
        self.assertEqual(c["V13-INPUT"]["status"], "UNCLEAR")
        self.assertIn("S14", c["V13-INPUT"]["actual"])


SAMPLER = os.path.join(PKG, "tools", "drawings", "sample_colours.py")


class WholeSheetColours(unittest.TestCase):
    """No regions.json: sample_colours.py counts colours over each sheet; the analyser judges what a whole sheet can show."""

    @classmethod
    def setUpClass(cls):
        from PIL import Image
        cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(cls.tmp, "_raw")
        sheets = os.path.join(raw, "sheets")
        os.makedirs(sheets)
        a = Image.new("RGB", (400, 300), (255, 255, 255))                 # A001: green site, Table 1 legend
        a.paste((230, 250, 240), (40, 40, 120, 120))
        for i, rgb in enumerate([(255, 164, 25), (227, 100, 102), (191, 0, 255), (222, 184, 135), (30, 144, 255),
                                 (144, 214, 236)]):
            a.paste(rgb, (200 + 15 * i, 40, 210 + 15 * i, 50))
        a.save(os.path.join(sheets, "Export - Sheet - A001 - BLOCK PLAN.png"))
        c = Image.new("RGB", (400, 300), (255, 255, 255))                 # C002: exact class 2 fill
        c.paste((227, 100, 102), (40, 40, 200, 200))
        c.save(os.path.join(sheets, "Export - Sheet - C002 - GFA.png"))
        cls.sample = subprocess.run([sys.executable, "-I", SAMPLER, "--sheets", sheets, "--out",
                                     os.path.join(raw, "colour_samples.json")], capture_output=True, text=True)
        with open(os.path.join(raw, "colour_samples.json"), encoding="utf-8") as f:
            cls.col = json.load(f)
        files = {"views_on_sheets.tsv": VOS, "view_props.tsv": PROPS, "readings.tsv": READ,
                 "view_counts.json": json.dumps(COUNTS), "rvt_info.json": json.dumps(RVT),
                 "rasters.tsv": "id\tname\twidth_mm\theight_mm\n"}
        for n, t in files.items():
            with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                f.write(t)
        out = os.path.join(cls.tmp, "G4.json")
        cls.proc = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                                   "--out", out], capture_output=True, text=True)
        with open(out, encoding="utf-8") as f:
            cls.c = {c["id"]: c for c in json.load(f)["checks"]}

    def test_sampler_whole_sheet(self):
        self.assertEqual(self.sample.returncode, 0, self.sample.stderr)
        self.assertIn("sheet_A001", self.col)
        self.assertEqual(self.col["sheet_A001"]["pink"], 0)
        self.assertGreater(self.col["sheet_C002"]["table1"]["2"], 0)

    def test_no_pink_anywhere_fails(self):
        self.assertEqual(self.c["V01-L3"]["status"], "FAIL")

    def test_table1_exact(self):
        self.assertEqual(self.c["A02-L1"]["status"], "PASS")
        self.assertEqual(self.c["A02-L2"]["status"], "PASS")

    def test_halftone_needs_regions(self):
        self.assertEqual(self.c["V10-L4"]["status"], "UNCLEAR")


if __name__ == "__main__":
    unittest.main(verbosity=1)
