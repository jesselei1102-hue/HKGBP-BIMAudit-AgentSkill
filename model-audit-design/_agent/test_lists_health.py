"""Tests for tools/lists_health (G5 lists, G6 model health, A04 roll-up) on synthetic inputs.

Run: python -I test_lists_health.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
ANALYZE = os.path.join(PKG, "tools", "lists_health", "analyze.py")


def chk(cid, task, status, basis="", item="x", actual="y"):
    return {"id": cid, "task": task, "item": item, "object": "o", "expected": "e", "actual": actual, "status": status,
            "basis": basis, "evidence": "", "fix": "f"}


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if isinstance(text, str) else json.dumps(text))


class ListsHealthRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t = cls.tmp = tempfile.mkdtemp()
        g5, g3r, g4r = os.path.join(t, "g5"), os.path.join(t, "g3"), os.path.join(t, "g4")
        w(os.path.join(g5, "levels.tsv"), "id\tname\ttype\televation_mm\tbuilding_story\n"
          "1\tSFL 0.25_G/F\tL\t250\t1\n2\tSFL 12.25_R/F\tL\t12250\t1\n3\tSFL 17.25_TR/F\tL\t17250\t1\n"
          "4\tMEAN STREET LEVEL\tL\t100\t1\n5\tFFL 0.30 G/I\tL\t20000\t1\n")
        w(os.path.join(g5, "points.tsv"), "id\tkind\tx_ft\ty_ft\tz_ft\tew_mm\tns_mm\telev_mm\tangle_true_north\n"
          "2\tProject Base Point\t0\t100\t0\t800000000\t800000000\t-100\t0\n"
          "3\tProperty Line bbox min\t0\t0\t0\t\t\t\t\n3\tProperty Line bbox max\t100\t100\t0\t\t\t\t\n")
        w(os.path.join(g5, "drawing_list.tsv"), "number\trev\ttitle\nA001\tA\tBLOCK PLAN\nA002\tA\tG/F PLAN\n")
        w(os.path.join(g5, "all_schedules.tsv"), "id\tname\n1\tGBP S10\n")
        w(os.path.join(g3r, "table_values.tsv"), "key\tsheet\titem\tvalue\tunit\tconfidence\tnote\tcrop\n"
          "gfa\tC001\tg\t1000.000\tm2\thigh\t\t\nsc_pct\tC001\ts\t50.000\t%\thigh\t\t\nsc_area\tC001\ts\t500.000\tm2\thigh\t\t\n"
          "site_area\tC001\ts\t1000\tm2\thigh\t\t\ngreenery_devsched\tC001\tg\t20.000\t%\tmedium\tFILLED from model extract\t\n"
          "carpark\tC001\tc\t9\tnos\tmedium\tC001 OCR\t\n"
          "height_c001\tC001\th\t12.15\tm\thigh\t\tcrops/h1.png\nheight_devsched\tC001\th\t17.35\tm\thigh\t\tcrops/h2.png\n")
        for n_ in ("h1", "h2"):
            w(os.path.join(g3r, "crops", n_ + ".png"), "")
        w(os.path.join(g3r, "rasters.tsv"), "id\tname\twidth_mm\theight_mm\n1\tC001 - x.jpg\t1\t1\n")
        # A rectangle 100 ft x 100 ft; base point at (0, 100) = E 800000.000, N 800000.000
        w(os.path.join(g4r, "coords.tsv"), "point\tE_m\tN_m\tsource\nA\t800000.000\t800000.000\tx\n"
          "B\t800030.480\t800000.000\tx\nC\t800030.480\t799969.520\tx\nD\t800000.000\t799969.520\tx\n")
        w(os.path.join(g4r, "readings.tsv"), "key\tsheet\titem\tvalue\tconfidence\tnote\tfinding\n"
          "coords_table\tA001\tc\traster image\thigh\t\t\n"
          "coords_format\tA001\tc\tHK1980, 3 dp\thigh\t\tPASS\n"
          "modification_list\tA001\tm\tno List of Modifications on any sheet\thigh\t\tFAIL\n")
        w(os.path.join(g4r, "rvt_info.json"), {"file": "m.rvt", "size_mb": 40, "format": "2027", "build": "b"})
        g2dir = os.path.join(t, "g2run")
        w(os.path.join(g2dir, "_raw", "Export - Schedule - PARKING SCHEDULE.csv"), '"PARKING"\n"Grand total","","6"\n')
        cls.files = {
            "g2": (os.path.join(g2dir, "G2.json"), {"checks": [chk("A1-DOORS-OFF", "AUD-A1", "FAIL"),
                                                               chk("S13-L4-1", "AUD-S13", "FAIL")]}),
            "g3": (os.path.join(t, "G3.json"), {"checks": [chk("V14-C1", "AUD-V14", "PASS", actual="20.000 %"),
                                                           dict(chk("S02-L2-1", "AUD-S02", "PASS"), expected=929.030),
                                                           chk("V11-L2", "AUD-V11", "FAIL"),
                                                           chk("S02-GEN01", "AUD-S02", "FAIL")],
                                                "summary": {"gfa": {"accountable": 1000.0}},
                                                "tables": {"concessions": {"rows": [["25", "subject to cap", "1/F", 1, 70.7, "B7 VOID"]]}}}),
            "g4": (os.path.join(t, "G4.json"), {"checks": [chk("V13-L1", "AUD-V13", "FAIL", basis="Missing"),
                                                           chk("A03-L4", "AUD-A03", "PASS", actual="0 Revit links"),
                                                           chk("A01-L1", "AUD-A01", "PASS"),
                                                           chk("V07-APL", "AUD-V07", "N/A")],
                                                "tables": {"titleblocks": {"rows": [["A001", "BLOCK PLAN"], ["A002", "G/F PLAN"],
                                                                                    ["A003", "1/F PLAN"]]}}}),
            "s14": (os.path.join(t, "S14.json"), {"summary": {"both_pass_count": 5, "rooms_included_count": 6,
                                                              "rooms_pending_count": 1, "data_quality_warnings": []}}),
        }
        for p, d in cls.files.values():
            w(p, d)
        cls.out = os.path.join(t, "G5.json")
        args = [sys.executable, "-I", ANALYZE, "--raw", g5, "--project", "T", "--model", "m.rvt", "--out", cls.out,
                "--g3raw", g3r, "--g4raw", g4r, "--schedules", os.path.join(g5, "all_schedules.tsv")]
        for k, (p, _) in cls.files.items():
            args += ["--" + k, p]
        cls.args = args
        cls.proc = subprocess.run(args, capture_output=True, text=True)
        with open(cls.out, encoding="utf-8") as f:
            cls.c = {c["id"]: c for c in json.load(f)["checks"]}

    def test_runs(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)

    def test_parking_count_read(self):
        self.assertEqual(self.c["S04-L2-carpark"]["expected"], 6)                    # comma export

    def test_parking_count_tab_delimited(self):
        tabdir = os.path.join(self.tmp, "g2tab")
        os.makedirs(os.path.join(tabdir, "_raw"), exist_ok=True)
        w(os.path.join(tabdir, "_raw", "PARKING SCHEDULE_1.csv"), '"PARKING"\n"Grand total"\t""\t"6"\n')
        w(os.path.join(tabdir, "G2.json"), self.files["g2"][1])
        out = os.path.join(self.tmp, "G5tab.json")
        args = [x for x in self.args]
        args[args.index("--out") + 1] = out
        args[args.index("--g2") + 1] = os.path.join(tabdir, "G2.json")
        p = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        c = {x["id"]: x for x in json.load(open(out, encoding="utf-8"))["checks"]}
        self.assertEqual(c["S04-L2-carpark"]["expected"], 6)                           # mcp-servers-for-revit export

    def test_drawing_list(self):
        self.assertEqual(self.c["S01-L1"]["status"], "FAIL")              # no sheet-list schedule
        self.assertEqual(self.c["S01-L2-A001"]["status"], "PASS")
        self.assertEqual(self.c["S01-L2-miss-A003"]["status"], "FAIL")    # sheet not in the list

    def test_coordinates_from_base_point(self):
        for p in "ABCD":
            self.assertEqual(self.c["S03-L4-" + p]["status"], "PASS", self.c["S03-L4-" + p])

    def test_development_schedule(self):
        self.assertEqual(self.c["S04-L2-gfa"]["status"], "PASS")
        self.assertEqual(self.c["S04-L3"]["status"], "FAIL")              # 12.15 vs 17.35, both with crops

    def test_reading_provenance(self):
        self.assertEqual(self.c["S04-L2-carpark"]["status"], "UNCLEAR")   # 9 vs 6 but no crop of the cell
        self.assertEqual(self.c["S04-L2-greenery_devsched"]["status"], "UNCLEAR")   # model value, not a reading
        with open(self.out, encoding="utf-8") as f:
            warn = " ".join(json.load(f)["summary"]["data_quality_warnings"])
        self.assertIn("greenery_devsched", warn)

    def test_modification_list(self):
        self.assertEqual(self.c["S18-C1"]["status"], "FAIL")              # reader's finding: no list on any sheet

    def test_sheet_observations(self):
        self.assertEqual(self.c["S03-L2"]["status"], "UNCLEAR")           # PASS read without a crop of the table
        self.assertIn("crop", self.c["S03-L2"]["fix"])
        self.assertEqual(self.c["S03-L3"]["status"], "UNCLEAR")

    def test_computed_health(self):
        self.assertEqual(self.c["MA-6.1"]["status"], "PASS")              # 30.48 m square = 929.030 m²
        self.assertEqual(self.c["MA-1.5"]["status"], "PASS")              # from G4 A03-L4
        self.assertEqual(self.c["MA-1.3"]["status"], "PASS")
        self.assertEqual(self.c["A04-L2"]["status"], "FAIL")              # one raster table

    def test_level_name_vs_elevation(self):
        self.assertEqual(self.c["MA-4.6-5"]["status"], "FAIL")            # 'FFL 0.30 G/I' at 20.000 m
        self.assertNotIn("MA-4.6-1", self.c)

    def test_rollup(self):
        self.assertEqual(self.c["A04-L4"]["status"], "FAIL")              # V13 missing
        self.assertEqual(self.c["A04-L3"]["status"], "FAIL")              # V11-L2


class TaskSelectionG5(ListsHealthRun):
    """--tasks on G5: S03 needs only points and the G4 extract; S04 without G3 is named; A04 alone = group run."""

    def sel(self, tasks, groups=("g2", "g3", "g4", "s14")):
        t = self.tmp
        out = os.path.join(t, "sel-%s.json" % tasks)
        args = [sys.executable, "-I", ANALYZE, "--raw", os.path.join(t, "g5"), "--project", "T", "--model", "m.rvt",
                "--out", out, "--g3raw", os.path.join(t, "g3"), "--g4raw", os.path.join(t, "g4"),
                "--schedules", os.path.join(t, "g5", "all_schedules.tsv"), "--tasks", tasks]
        for k in groups:
            args += ["--" + k, self.files[k][0]]
        p = subprocess.run(args, capture_output=True, text=True)
        return p, (json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None)

    def same(self, d, task):
        k = lambda x: sorted((c["id"], c["status"], str(c["actual"])) for c in x if c["task"] == task
                             and not c["id"].endswith("-INPUT"))
        self.assertEqual(k(d["checks"]), k(self.c.values()))

    def test_s03_without_group_jsons(self):
        p, d = self.sel("S03", groups=())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.same(d, "AUD-S03")

    def test_s04_needs_g3(self):
        p, d = self.sel("S04", groups=("g2", "g4", "s14"))
        self.assertEqual([c["id"] for c in d["checks"]], ["S04-INPUT"])
        self.assertIn("G3", d["checks"][0]["actual"])

    def test_a04_alone_equals_group(self):
        p, d = self.sel("A04")
        self.assertEqual({c["task"] for c in d["checks"]}, {"AUD-A04"})
        self.same(d, "AUD-A04")

    def test_lift_shaft_not_assumed(self):
        self.assertEqual(self.c["S09-APL"]["status"], "UNCLEAR")            # no 'lift_shaft_concession' reading


if __name__ == "__main__":
    unittest.main(verbosity=1)
