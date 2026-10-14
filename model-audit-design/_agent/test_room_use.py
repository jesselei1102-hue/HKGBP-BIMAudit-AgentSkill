"""Tests for tools/room_use (G2) and tools/common/task_report on a small synthetic extract.

Run: python -I test_room_use.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
ANALYZE = os.path.join(PKG, "tools", "room_use", "analyze.py")
REPORT = os.path.join(PKG, "tools", "common", "task_report.py")
FT2 = 0.09290304

spec = importlib.util.spec_from_file_location("room_use_analyze", ANALYZE)
RU = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.join(PKG, "tools", "common"))
spec.loader.exec_module(RU)

L = "SFL 0_G/F"
# OFFICE 0-30 x 0-30 (900 ft2), M LAV 30-40 x 0-10, F LAV 30-40 x 10-20, Room (accessible) 30-40 x 20-25, S-1 30-40 x 25-30
ROOMS = "id\tname\tnumber\tlevel\tarea_m2\tminx\tminy\tminz\tmaxx\tmaxy\tmaxz\n" + "".join(
    "%d\t%s\t%s\t%s\t%.3f\t%s\t%s\t0\t%s\t%s\t12\n" % (i, n, no, L, a * FT2, x0, y0, x1, y1)
    for i, n, no, a, x0, y0, x1, y1 in [
        (1, "OFFICE", "1", 900, 0, 0, 30, 30), (2, "M LAV", "2", 100, 30, 0, 40, 10),
        (3, "F LAV", "3", 100, 30, 10, 40, 20), (4, "Room", "4", 50, 30, 20, 40, 25), (5, "S-1", "5", 50, 30, 25, 40, 30)])
WC, URN, SNK, ACC, FT = ("BD_PLM-WCS-AEC-Toilet_Cubicle-Wall_Mounted", "BD_PLM-URN-AEC-Wall_Hung", "BD_PLM-SNK",
                         "BD_PLM-WCS-AEC-Toilet_Cubicle-Accessible", "BD_PLM-WCS-Flush_Tank")
FIX = "id\tfamily\ttype\tlevel\tcx\tcy\tz\n" + "".join(
    "%d\t%s\tT\t%s\t%s\t%s\t0\n" % r for r in [
        (101, WC, L, 32, 5), (102, URN, L, 35, 5), (103, SNK, L, 38, 5), (104, FT, L, 32, 6),
        (111, WC, L, 32, 15), (112, SNK, L, 38, 15), (121, ACC, L, 35, 22), (131, "BD_Plumbing Fixtures 1", "", 37, 15)])
# door 201: office <-> corridor-free outside (x 10-13, y -3..3); door 202: office <-> M LAV (x 29..31? use wall at x=30)
DOORS = ("id\tfamily\ttype\tlevel\twidth_moe_mm\tminx\tminy\tminz\tmaxx\tmaxy\tmaxz\n"
         "201\tBD_DOR-SGL-AEC-Wood\t900x2100\tFFL\t850\t10\t-3\t0.2\t13\t3\t7\n"
         "202\tBD_DOR-SGL-AEC-Wood\t900x2100\tFFL\t850\t27\t3\t0.2\t33\t6\t7\n"
         "203\tBD_DOR-SGL-AEC-Wood\t900x2100\tDoor Level\t850\t-90\t3\t-17\t-87\t9\t-10\n")
S10 = ('"GBP S10"\n"Level","Name","Area","FACTOR","Room Capacity","MIN. NO. OF EXIT DOORS OR EXIT ROUTES REQUIRED",'
       '"MIN. NO. OF EXIT DOORS OR EXIT ROUTES PROVIDED","MIN. WIDTH OF EACH (mm) EXIT DOOR REQUIRED",'
       '"MIN. WIDTH OF EACH (mm) EXIT DOOR PROVIDED"\n"","","","","","","","",""\n'
       '"%s","OFFICE","%.3f m²","9","9","1","3","750","900"\n' % (L, 900 * FT2))
S13 = ('"GBP S13"\n"Level","Family","Type","Count"\n"","","",""\n'
       '"%s","%s","T","1"\n"%s","%s","T","1"\n"%s","%s","T","1"\n"%s","%s","T","1"\n' % (L, WC, L, WC, L, URN, L, URN))


def write(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


class Cap123ITables(unittest.TestCase):
    def test_office_small(self):
        r = RU.office_req(8)
        self.assertEqual((r["male_wc"], r["female_wc"], r["male_basin"]), (1, 1, 1))

    def test_office_table5_6_7(self):
        r = RU.office_req(51)            # 26 male, 26 female
        self.assertEqual((r["male"], r["female"]), (26, 26))
        self.assertEqual((r["male_wc"], r["urinal"], r["female_wc"], r["male_basin"], r["female_basin"]), (2, 1, 3, 2, 2))

    def test_office_over_100(self):
        r = RU.office_req(240)           # 120 male: WC 4 + ceil(20/50) = 5, urinals 2 + 1 = 3, basins 4 + 1 = 5
        self.assertEqual((r["male_wc"], r["urinal"], r["male_basin"]), (5, 3, 5))
        self.assertEqual(r["female_wc"], 2 + 4)                 # 120 female: 2 + ceil(95/25)

    def test_ppe_tables8_9_10(self):
        r = RU.ppe_req(1000)             # 400 male, 600 female
        self.assertEqual((r["male"], r["female"]), (400, 600))
        self.assertEqual((r["male_wc"], r["urinal"]), (4, 8))
        self.assertEqual(r["female_wc"], 10 + 9)                # 10 + ceil(350/40)
        self.assertEqual((r["male_basin"], r["female_basin"]), (4, 6))


class RoomUseRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(cls.tmp, "_raw")
        os.makedirs(raw)
        for n, t in (("rooms.tsv", ROOMS), ("fixtures.tsv", FIX), ("doors_all.tsv", DOORS),
                     ("Export - Schedule - GBP S10 - X.csv", S10), ("Export - Schedule - GBP S13 - X.csv", S13)):
            write(raw, n, t)
        cls.out = os.path.join(cls.tmp, "G2.json")
        cls.proc = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                                   "--out", cls.out], capture_output=True, text=True)
        with open(cls.out, encoding="utf-8") as f:
            cls.d = json.load(f)
        cls.c = {c["id"]: c for c in cls.d["checks"]}

    def test_runs(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertIn("G2 room-use", self.proc.stdout)
        schema = json.load(open(os.path.join(PKG, "templates", "task-analysis.schema.json"), encoding="utf-8"))
        for k in schema["required"]:
            self.assertIn(k, self.d)

    def test_fixtures_assigned_by_room(self):
        rows = {r[0]: r for r in self.d["tables"]["fixtures"]["rows"]}
        self.assertEqual(rows[101][5], "M LAV 2")
        self.assertEqual(rows[121][5], "Room 4")
        self.assertTrue(rows[104][7].startswith("not a fitment"))      # flush tank

    def test_soil_rooms_handed_to_s14(self):
        names = [r[1] for r in self.d["tables"]["soil_rooms"]["rows"]]
        self.assertEqual(sorted(names), ["F LAV 3", "M LAV 2", "Room 4"])

    def test_s13_office_basis(self):
        # UFA = OFFICE only (lavatories, accessible WC and staircase excluded): 83.613 m2 -> 10 persons -> reg 5(3)
        c = self.c["S13-C-G/F-A-female_wc"]
        self.assertEqual((c["expected"], c["actual"], c["status"]), (1, 1, "PASS"))

    def test_s13_schedule_counts(self):
        self.assertEqual(self.c["S13-L3-G/F-Wall_Mounted"]["status"], "PASS")     # table 2, model 2
        self.assertEqual(self.c["S13-L3-G/F-Wall_Hung"]["status"], "FAIL")        # table 2 urinals, model 1
        self.assertEqual(self.c["S13-L4-131"]["status"], "FAIL")                  # no-level counter

    def test_s10_doors_and_width(self):
        self.assertEqual(self.c["S10-D-1"]["actual"], 2)
        self.assertEqual(self.c["S10-D-1"]["status"], "FAIL")                     # table claims 3
        self.assertEqual(self.c["S10-W-1"]["status"], "FAIL")                     # 900 claimed, 850 modelled
        self.assertEqual(self.c["S10-L3-1"]["status"], "FAIL")                    # ceil(83.613 / 9) = 10, table says 9

    def test_stray_door(self):
        self.assertEqual(self.c["A1-DOORS-OFF"]["status"], "FAIL")

    def test_report(self):
        outdir = os.path.join(self.tmp, "rep")
        r = subprocess.run([sys.executable, "-I", REPORT, "--analysis", self.out, "--outdir", outdir, "--date", "20260101"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        x = os.path.join(outdir, "GBP_G2_RoomUse_T_20260101.xlsx")
        with zipfile.ZipFile(x) as z:
            wb = z.read("xl/workbook.xml").decode()
            self.assertIn("Task Summary", wb)
            self.assertIn("Checks", wb)
        with open(os.path.join(outdir, "GBP_G2_RoomUse_T_20260101.html"), encoding="utf-8") as f:
            h = f.read()
        self.assertIn("not a Building Authority approval", h)
        self.assertIn('id="t-checks"', h)

    def test_report_rejects_bad_json(self):
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w") as f:
            json.dump({"project_info": {}, "checks": [{"id": "x"}], "tables": {}, "summary": {}}, f)
        r = subprocess.run([sys.executable, "-I", REPORT, "--analysis", bad, "--outdir", self.tmp], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


def run_g2(files, *extra):
    tmp = tempfile.mkdtemp()
    raw = os.path.join(tmp, "_raw")
    os.makedirs(raw)
    for n, t in files:
        write(raw, n, t)
    out = os.path.join(tmp, "G2.json")
    p = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt", "--out", out]
                       + list(extra), capture_output=True, text=True)
    d = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None
    return p, d


ALL_G2 = [("rooms.tsv", ROOMS), ("fixtures.tsv", FIX), ("doors_all.tsv", DOORS),
          ("Export - Schedule - GBP S10 - X.csv", S10), ("Export - Schedule - GBP S13 - X.csv", S13)]
key = lambda c: (c["id"], c["status"], str(c["actual"]))


class TabDelimitedSchedules(unittest.TestCase):
    """mcp-servers-for-revit exports schedules tab-delimited: same results as the comma export."""

    def test_same_checks(self):
        tab = lambda t: t.replace('","', '"\t"')
        files = [(n, tab(t) if n.endswith(".csv") else t) for n, t in ALL_G2]
        p, d = run_g2(files)
        self.assertEqual(p.returncode, 0, p.stderr)
        _, full = run_g2(ALL_G2)
        k = lambda x: sorted((c["id"], c["status"], str(c["actual"])) for c in x["checks"])
        self.assertEqual(k(d), k(full))


class TaskSelectionG2(unittest.TestCase):
    """--tasks: one task alone gives the same checks as in the group run; missing inputs are named, never judged as 0."""

    @classmethod
    def setUpClass(cls):
        cls.full_p, cls.full = run_g2(ALL_G2)

    def checks(self, d, task):
        return sorted(key(c) for c in d["checks"] if c["task"] == task and not c["id"].endswith("-INPUT"))

    def test_s10_alone(self):
        p, d = run_g2([f for f in ALL_G2 if "S13" not in f[0]], "--tasks", "S10")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(d["project_info"]["tasks"], ["AUD-S10"])
        self.assertTrue(d["project_info"]["partial"])
        self.assertEqual({c["task"] for c in d["checks"]}, {"AUD-S10"})
        self.assertEqual(self.checks(d, "AUD-S10"), self.checks(self.full, "AUD-S10"))

    def test_s16_with_rooms_only(self):
        p, d = run_g2([ALL_G2[0]], "--tasks", "S16")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.checks(d, "AUD-S16"), self.checks(self.full, "AUD-S16"))
        self.assertNotIn("S16-INPUT", [c["id"] for c in d["checks"]])

    def test_required_input_missing(self):
        for t in ("S13", "S10"):                                            # both need fixtures (UFA excludes toilets)
            p, d = run_g2([f for f in ALL_G2 if f[0] != "fixtures.tsv"], "--tasks", t)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual([c["id"] for c in d["checks"]], ["%s-INPUT" % t])   # not judged on zero fixtures
            self.assertEqual(d["checks"][0]["status"], "UNCLEAR")
            self.assertIn("fixtures.tsv", d["checks"][0]["actual"])

    def test_optional_schedule_missing_is_named(self):
        c = {x["id"]: x for x in self.full["checks"]}
        self.assertEqual(c["S11-INPUT"]["status"], "UNCLEAR")              # no S11 schedule export in the fixture
        self.assertIn("S11", c["S11-INPUT"]["actual"])

    def test_partial_report_named_by_task(self):
        tmp = tempfile.mkdtemp()
        an = os.path.join(tmp, "G2.json")
        p, d = run_g2([ALL_G2[0]], "--tasks", "S16")
        json.dump(d, open(an, "w", encoding="utf-8"))
        r = subprocess.run([sys.executable, "-I", REPORT, "--analysis", an, "--outdir", tmp, "--name", "RoomUse",
                            "--date", "20260101"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(tmp, "GBP_G2_S16_T_20260101.html")), os.listdir(tmp))

    def test_unknown_task(self):
        p, d = run_g2(ALL_G2, "--tasks", "S99")
        self.assertEqual(p.returncode, 2)
        self.assertIn("S13", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
