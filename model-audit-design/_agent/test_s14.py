"""Tests for tools/s14_lv (analysis + report) on a small synthetic extract.

Run: python -I test_s14.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
ANALYZE = os.path.join(PKG, "tools", "s14_lv", "analyze.py")
REPORT = os.path.join(PKG, "tools", "s14_lv", "report.py")
FT2 = 0.09290304

# Plan (feet): OFFICE 0-20 x 0-20 ; M LAV 20-30 x 0-10 ; ENT HALL 20-30 x 10-20 ; floor z 0, ceiling 12.
ROOMS = """id\tname\tnumber\tlevel\tarea_m2\tminx\tminy\tminz\tmaxx\tmaxy\tmaxz
1\tOFFICE\t1\tSFL 0_G/F\t%.3f\t0\t0\t0\t20\t20\t12
2\tM LAV\t2\tSFL 0_G/F\t%.3f\t20\t0\t0\t30\t10\t12
3\tENT HALL\t3\tSFL 0_G/F\t%.3f\t20\t10\t0\t30\t20\t12
4\tSTORE\t4\tSFL 0_G/F\t%.3f\t0\t20\t0\t10\t25\t12
5\tRoom\t5\tSFL 0_G/F\t%.3f\t10\t20\t0\t20\t25\t12
""" % (400 * FT2, 100 * FT2, 100 * FT2, 50 * FT2, 50 * FT2)
# 101 west facade of OFFICE ; 102 internal OFFICE|HALL ; 103 east facade of M LAV ; 104 site glazing ; 105 louvre wall on LAV
CW = """id\ttype\tlevel\tarea_m2\tmark\tminx\tminy\tminz\tmaxx\tmaxy\tmaxz
101\tBD_free grid clear glass\tSFL 0_G/F\t5.000\tW1\t-1.64\t2\t3\t1.64\t18\t10
102\tBD_free grid clear glass\tSFL 0_G/F\t4.000\t\t18.36\t12\t0\t21.64\t18\t8
103\tBD_free grid clear glass\tSFL 0_G/F\t2.000\tW2\t28.36\t2\t3\t31.64\t8\t10
104\tBD_free grid clear glass\tSFL 0_G/F\t9.000\t\t60\t60\t0\t63.28\t70\t8
105\tBD_external louvre\tSFL 0_G/F\t0.300\t\t28.36\t8.2\t3\t31.64\t9.8\t6
"""
# panels: 201 hung in 101 (top 9.5 ft = 2.9 m) ; 202 louvre in 103 ; 203 hung in 103 (top 6 ft = 1.83 m < 2 m) ; 204 hung in 103 (top 9.5)
PN = """id\tkind\ttype\tarea_m2\tcx\tcy\tcz
201\tH\t50x100 top hung\t0.800\t0.5\t10\t7.5
202\tL\t30x150\t0.200\t30\t3\t8
203\tH\t50x100 left side hung\t0.500\t30\t5\t4.5
204\tH\t50x100 right side hung\t0.600\t30\t7\t7.5
"""
SAMPLE = """id\tminz\tmaxz
201\t5.5\t9.5
202\t7.5\t8.5
203\t3.0\t6.0
204\t5.5\t9.5
"""
FSW = """id\tfamily\ttype\tlevel\tmark\tarea_m2\tminx\tminy\tminz\tmaxx\tmaxy\tmaxz
301\tBD_WDW-OTR-Fire_Service_Installation\t900x500\tSFL 0_G/F\t1\t0.535\t-1\t1\t2\t1\t2\t4
"""


SCHED = """"S14"
"Level","Name","Area","NOTIONAL AREA","10% OF WINDOW AREA","10% OF OPENABLE AREA","6.25% OF OPENABLE AREA","PROVIDED WINDOW AND OPENABLE AREA","WINDOW MARK"
"","","","","","","","",""
"SFL 0_G/F","OFFICE","37.161 m²","-","3.700 m²","","2.322 m²","1.4 x 2 = 2.8 m²","W1"
"""


def write(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


class S14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(cls.tmp, "_raw")
        os.makedirs(raw)
        for n, t in (("rooms.tsv", ROOMS), ("cw_part1.tsv", CW), ("pn_part1.tsv", PN),
                     ("pn_bbox_sample.tsv", SAMPLE), ("fs_windows.tsv", FSW)):
            write(raw, n, t)
        cls.out = os.path.join(cls.tmp, "C14.json")
        cls.proc = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                                  "--out", cls.out], capture_output=True, text=True)
        cls.d = json.load(open(cls.out, encoding="utf-8")) if cls.proc.returncode == 0 else None

    def room(self, rid):
        for k in ("rooms_included", "rooms_excluded", "rooms_pending", "rooms_no_area"):
            for r in self.d[k]:
                if r["id"] == rid:
                    return k, r
        raise KeyError(rid)

    def opening(self, oid):
        return [o for o in self.d["openings_all"] if o["id"] == oid][0]

    def test_runs_and_prints_summary(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertIn("TL-S14 Lighting & Ventilation", self.proc.stdout)
        self.assertIn("Rooms: 5 total", self.proc.stdout)

    def test_required_sections(self):
        schema = json.load(open(os.path.join(PKG, "templates", "s14-analysis.schema.json"), encoding="utf-8"))
        for k in schema["required"]:
            self.assertIn(k, self.d)

    def test_room_classification(self):
        self.assertEqual(self.room(1)[1]["classification"], "reg30")
        self.assertEqual(self.room(2)[1]["classification"], "reg36")
        self.assertEqual(self.room(3)[0], "rooms_excluded")
        self.assertEqual(self.room(4)[0], "rooms_excluded")
        self.assertEqual(self.room(5)[0], "rooms_pending")

    def test_external_facade_assigned_high(self):
        o = self.opening(101)
        self.assertEqual(o["facing"], "external")
        self.assertEqual(o["matched_room_id"], 1)
        self.assertEqual(o["match_confidence"], "high")

    def test_internal_glazing_not_counted(self):
        o = self.opening(102)
        self.assertEqual(o["facing"], "internal")
        self.assertFalse(o["counted_lighting"])
        self.assertIn(o, self.d["openings_unassigned"])

    def test_site_glazing_unassigned(self):
        o = self.opening(104)
        self.assertEqual(o["facing"], "none")
        self.assertIsNone(o["matched_room_id"])

    def test_office_amounts_reg30(self):
        r = self.room(1)[1]
        self.assertAlmostEqual(r["req_light_sqm"], round(400 * FT2 / 10, 3))
        self.assertAlmostEqual(r["req_vent_sqm"], round(400 * FT2 / 16, 3))
        self.assertAlmostEqual(r["act_light_sqm"], 5.0)
        self.assertAlmostEqual(r["act_vent_sqm"], 0.8)
        self.assertTrue(r["light_pass"])
        self.assertFalse(r["vent_pass"])                      # 0.8 < 37.161 / 16 = 2.323
        self.assertEqual(r["status"], "FAIL")

    def test_lav_reg36_louvre_deducted_and_2m_rule(self):
        r = self.room(2)[1]
        self.assertEqual(r["vent_ratio"], "1/10")
        self.assertAlmostEqual(r["act_light_sqm"], 1.8)       # 2.000 wall - 0.200 louvre panel
        self.assertAlmostEqual(r["act_vent_sqm"], 0.6)        # 203 top 1.83 m < 2 m not counted
        p203 = [p for p in self.opening(103)["panels"] if p["id"] == 203][0]
        self.assertFalse(p203["top_ge_2m"])
        self.assertFalse(p203["counted_ventilation"])

    def test_fire_service_window_separate(self):
        self.assertEqual([f["id"] for f in self.d["openings_fire_service"]], [301])
        self.assertFalse(any(o["id"] == 301 for o in self.d["openings_all"]))

    def test_report_xlsx_and_html(self):
        outdir = os.path.join(self.tmp, "rep")
        r = subprocess.run([sys.executable, "-I", REPORT, "--analysis", self.out, "--outdir", outdir, "--date", "20260101"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        x = os.path.join(outdir, "GBP_TL-S14_LV_Compliance_T_20260101.xlsx")
        with zipfile.ZipFile(x) as z:
            wb = z.read("xl/workbook.xml").decode()
            for name in ("Room L&amp;V Compliance", "Opening Detail", "Room Opening Breakdown",
                         "Opening Type Summary", "Summary", "Excluded Rooms"):
                self.assertIn(name, wb)
            self.assertIn('state="frozen"', z.read("xl/worksheets/sheet1.xml").decode())
            self.assertIn('formatCode="0.000"', z.read("xl/styles.xml").decode())
        h = open(os.path.join(outdir, "GBP_TL-S14_LV_Compliance_T_20260101.html"), encoding="utf-8").read()
        self.assertIn("not a Building Authority approval", h)
        self.assertIn("class=\"sortable\"", h)
        self.assertIn("<details>", h)

    def test_schedule_comparison(self):
        raw = os.path.join(self.tmp, "_raw")
        csvp = os.path.join(self.tmp, "sched.csv")
        write(self.tmp, "sched.csv", SCHED)
        out = os.path.join(self.tmp, "C14s.json")
        r = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                            "--out", out, "--schedule", csvp], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            sc = json.load(f)["schedule_comparison"]
        row = sc["rows"][0]
        self.assertEqual(row["room_id"], 1)
        issues = " | ".join(row["issues"])
        self.assertIn("rounded down", issues)                 # 3.700 < 3.716
        self.assertIn("typed formula", issues)
        self.assertIn("differs from the measured glass", issues)
        self.assertEqual([m["id"] for m in sc["missing_rooms"]], [2])   # M LAV assessed but not in the table

    def test_schedule_comparison_tab_delimited(self):
        raw = os.path.join(self.tmp, "_raw")
        csvp = os.path.join(self.tmp, "sched_tab.csv")
        write(self.tmp, "sched_tab.csv", SCHED.replace('","', '"\t"'))          # mcp-servers-for-revit export
        out = os.path.join(self.tmp, "C14t.json")
        r = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                            "--out", out, "--schedule", csvp], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            sc = json.load(f)["schedule_comparison"]
        self.assertEqual(sc["rows"][0]["room_id"], 1)
        self.assertEqual([m["id"] for m in sc["missing_rooms"]], [2])

    def test_report_rejects_incomplete_json(self):
        bad = os.path.join(self.tmp, "bad.json")
        json.dump({"project_info": {}}, open(bad, "w"))
        r = subprocess.run([sys.executable, "-I", REPORT, "--analysis", bad, "--outdir", self.tmp],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


class PanelKindGuard(unittest.TestCase):
    """A panel whose kind is not H (hung) or L (louvre) stops the run: louvre area must never be counted as glass."""

    def test_unknown_kind_stops(self):
        tmp = tempfile.mkdtemp()
        raw = os.path.join(tmp, "_raw")
        os.makedirs(raw)
        for n, t in (("rooms.tsv", ROOMS), ("cw_part1.tsv", CW), ("pn_part1.tsv", PN.replace("202\tL\t", "202\t?\t")),
                     ("pn_bbox_sample.tsv", SAMPLE), ("fs_windows.tsv", FSW)):
            write(raw, n, t)
        p = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                            "--out", os.path.join(tmp, "C14.json")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("202", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(tmp, "C14.json")))


if __name__ == "__main__":
    unittest.main(verbosity=1)
