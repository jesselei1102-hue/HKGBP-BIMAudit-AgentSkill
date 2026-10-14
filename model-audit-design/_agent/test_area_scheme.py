"""Tests for tools/area_scheme (G3) on a small synthetic extract.

Run: python -I test_area_scheme.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
ANALYZE = os.path.join(PKG, "tools", "area_scheme", "analyze.py")
HEAD = ("id\tscheme\tlevel\tname\tarea_m2\tnumber\tcommon_area\tgfa_summary\td22\td23\td21\td25\td27\tserved_facade_mm\t"
        "frr\tcompartment\tfrc_height\tperimeter_mm\tarea_type\tminx\tminy\tmaxx\tmaxy\n")


def row(i, scheme, level, name, area, common="", summ="0", d22="0", d23="0", d21="0", d25="0", served="", frr="",
        comp="", per=""):
    return "\t".join(str(x) for x in [i, scheme, level, name, area, "", common, summ, d22, d23, d21, d25, "0", served, frr,
                                      comp, "0", per, "", 0, 0, 0, 0]) + "\n"


AREAS = HEAD + "".join([
    row(1, "(property line)", "", "Property", "2000.000"),
    row(2, "ARC_gbp_site area", "SFL 9_TR/F", "Area", "2000.000"),
    row(10, "ARC_gbp_gfa", "SFL 0.00_G/F", "Area", "1000.000"),
    row(11, "ARC_gbp_gfa", "SFL 4.00_1/F", "Area", "1000.000"),
    row(12, "ARC_gbp_gfa", "SFL 7.50_R/F", "Area", "10.000"),
    row(20, "ARC_gbp_gfa_deduct", "SFL 0.00_G/F", "TX RM", "50.000", "A1", d22="1"),
    row(21, "ARC_gbp_gfa_deduct", "SFL 0.00_G/F", "Area", "950.000", "Non-domestic", summ="1"),
    row(22, "ARC_gbp_gfa_deduct", "SFL 4.00_1/F", "AHU", "30.000", "B1", d23="1"),
    row(23, "ARC_gbp_gfa_deduct", "SFL 4.00_1/F", "Area", "960.000", "", summ="1"),          # unlabelled, and 10 m² short
    row(30, "ARC_gbp_sc", "SFL 9_R/F", "Area", "1000.000"),
    row(40, "ARC_gbp_greenery", "SFL 0.00_G/F", "Area", "500.000"),
    row(50, "ARC_gbp_comp", "SFL 0.00_G/F", "Area", "900.000", "G-A", frr="60", comp="G-A"),
    row(51, "ARC_gbp_comp", "SFL 4.00_1/F", "Area", "990.000", "1-A", frr="60", comp="1-A"),
    row(60, "ARC_gbp_eva", "SFL 0.00_G/F", "Area", "1000.000", served="40000", per="130000"),
])
SCHEMES = "id\tname\tareas\n1\tARC_gbp_ufa\t0\n2\tARC_gbp_gfa\t3\n"
TV_PLAIN = ("key\tsheet\titem\tvalue\tunit\tconfidence\tnote\n"
            "site_area\tC001\tsite\t2000\tm2\thigh\t\nsite_area_c003\tC003\tsite\t2000.000\tm2\thigh\t\n"
            "use\tC001\tuse\tINSTITUTIONAL\ttext\thigh\t\nheight_c001\tC001\th\t12.15\tm\thigh\t\n"
            "height_devsched\tC001\th\t16.00\tm\thigh\t\nperm_sc\tC001\tsc\t100\t%\thigh\t\nperm_pr\tC001\tpr\t5\t-\thigh\t\n"
            "sc_area\tC001\tsc\t1000.000\tm2\thigh\t\nsc_pct\tC001\tsc\t50.000\t%\thigh\t\n"
            "gfa\tC001\tgfa\t1910.000\tm2\thigh\t\npr\tC001\tpr\t0.955\t-\thigh\t\n"
            "gfa_gf\tC002\tgf\t950.000\tm2\thigh\t\ngfa_1f\tC002\t1f\t970.000\tm2\thigh\t\ngfa_total\tC002\tt\t1910.000\tm2\thigh\t\n"
            "grn_gf\tC008\tg\t500.000\tm2\thigh\t\ngrn_pct\tC008\tg\t25.000\t%\thigh\t\ngrn_primary_pct\tC008\tg\t25\t%\thigh\t\n"
            "comp_ga_area\tC005\ta\t900\tm2\thigh\t\ncomp_ga_vol\tC005\tv\t3600\tm3\thigh\t\n"
            "eva_gf_perim\tC006\tp\t130.0\tm\thigh\t\neva_gf_pct\tC006\tp\t30.769\t%\thigh\t\n")
NL, TAB = "\n", "\t"


def with_crops(tv):
    """Every reading backed by a crop of the cell (crops/<key>.png)."""
    lines = tv.strip(NL).split(NL)
    return NL.join([lines[0] + TAB + "crop"] + [l + TAB + "crops/%s.png" % l.split(TAB)[0] for l in lines[1:]]) + NL


TV = with_crops(TV_PLAIN)
RASTERS = "id\tname\twidth_mm\theight_mm\n9\tC002 - GFA DIAGRAMS AND CALCULATIONS.jpg\t600\t125\n"


def run_g3(raw, tmp, tv, crops):
    os.makedirs(os.path.join(raw, "crops"), exist_ok=True)
    for n, body in (("areas.tsv", AREAS), ("area_schemes.tsv", SCHEMES), ("table_values.tsv", tv), ("rasters.tsv", RASTERS)):
        with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
            f.write(body)
    if crops:
        for l in tv.strip(NL).split(NL)[1:]:
            open(os.path.join(raw, "crops", l.split(TAB)[0] + ".png"), "wb").close()
    out = os.path.join(tmp, "G3.json")
    proc = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                           "--out", out], capture_output=True, text=True)
    if not os.path.exists(out):
        return proc, {"checks": [], "summary": {"data_quality_warnings": []}}
    with open(out, encoding="utf-8") as f:
        return proc, json.load(f)


class AreaSchemeRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.proc, cls.d = run_g3(os.path.join(cls.tmp, "_raw"), cls.tmp, TV, crops=True)
        cls.c = {c["id"]: c for c in cls.d["checks"]}

    def test_runs(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertIn("G3 area-scheme", self.proc.stdout)

    def test_gfa_two_paths(self):
        self.assertEqual(self.c["V10-C1-G/F"]["status"], "PASS")          # 1000 - 50 = 950
        self.assertEqual(self.c["V10-C1-1/F"]["status"], "FAIL")          # 1000 - 30 = 970, summary areas 960
        self.assertEqual(self.c["V10-T-1/F"]["status"], "FAIL")           # table 970 vs model 960, crop present

    def test_unlabelled_accountable_area(self):
        self.assertEqual(self.c["V10-L5-23"]["status"], "FAIL")

    def test_cap_percentage(self):
        g = self.d["summary"]["gfa"]
        self.assertEqual((g["no_cap"], g["capped"]), (50.0, 30.0))
        self.assertEqual(self.c["S08-C1"]["status"], "PASS")

    def test_raster_table(self):
        self.assertEqual(self.c["V10-GEN01"]["status"], "FAIL")
        self.assertEqual(self.c["V14-GEN01"]["status"], "PASS")

    def test_first_schedule_both_heights(self):
        self.assertEqual(self.c["S05-C7-height_c001"]["expected"], "≤ 100 %")
        self.assertEqual(self.c["S05-C8-height_devsched"]["expected"], "≤ 5.8")
        self.assertEqual(self.c["S05-HGT"]["status"], "FAIL")

    def test_ufa_scheme_empty(self):
        self.assertEqual(self.c["V11-L2"]["status"], "FAIL")

    def test_compartment_volume_from_levels(self):
        self.assertEqual(self.c["S12-L2-v-G-A"]["expected"], 3600)        # 900 x (4.00 - 0.00)
        self.assertEqual(self.c["S12-L2-v-G-A"]["status"], "PASS")

    def test_eva(self):
        self.assertEqual(self.c["V06-C1-G/F"]["status"], "PASS")          # 40 / 130 = 30.769 %
        self.assertEqual(self.c["V06-TP-G/F"]["status"], "PASS")

    def test_open_space_na(self):
        self.assertEqual(self.c["V07-APL"]["status"], "N/A")

    def test_sheet_observations_never_assumed(self):
        for cid in ("S08-L2", "S07-C4", "S05-L2"):                      # no reading recorded -> UNCLEAR, not FAIL
            self.assertEqual(self.c[cid]["status"], "UNCLEAR", cid)

    def test_pr_sensitivity_computed(self):
        self.assertEqual(self.c["S07-C6"]["expected"], "PR ≤ 5")         # 12.15 m -> First Schedule band ≤ 15 m
        self.assertEqual(self.c["S07-C6"]["status"], "PASS")              # (1910 + 30) / 2000 = 0.970

    def test_frc_height_from_model(self):
        self.assertEqual(self.c["S12-FRC"]["status"], "FAIL")             # fixture FRC HEIGHT = 0


class ReadingProvenance(unittest.TestCase):
    """Sheet readings: a model value is never a reading; a mismatch is FAIL only with a crop of the cell."""

    @classmethod
    def setUpClass(cls):
        tv = (TV_PLAIN
              .replace("gfa_1f\tC002\t1f\t970.000\tm2\thigh\t", "gfa_1f\tC002\t1f\t960.000\tm2\tmedium\tFILLED from model extract")
              .replace("site_area\tC001\tsite\t2000\tm2\thigh\t", "site_area\tC001\tsite\t3000\tm2\tmedium\tC001 sheet OCR")
              .replace("site_area_c003\tC003\tsite\t2000.000\tm2\thigh\t", "site_area_c003\tC003\tsite\t3000\tm2\tmedium\tassume same as C001")
              .replace("height_devsched\tC001\th\t16.00\tm\thigh\t\n", ""))
        cls.tmp = tempfile.mkdtemp()
        cls.proc, cls.d = run_g3(os.path.join(cls.tmp, "_raw"), cls.tmp, tv, crops=False)
        cls.c = {c["id"]: c for c in cls.d["checks"]}

    def test_runs_without_a_height(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertEqual(self.c["S05-HGT"]["status"], "UNCLEAR")

    def test_model_value_is_not_a_reading(self):
        self.assertEqual(self.c["V10-T-1/F"]["status"], "UNCLEAR")        # 960 equals the model, but it was copied from it
        self.assertEqual(self.c["S02-T-site_area_c003"]["status"], "UNCLEAR")
        warn = " ".join(self.d["summary"]["data_quality_warnings"])
        self.assertIn("gfa_1f", warn)
        self.assertIn("site_area_c003", warn)

    def test_mismatch_without_crop_is_unclear(self):
        self.assertEqual(self.c["S02-T-site_area"]["status"], "UNCLEAR")  # 3000 vs 2000, no crop of the cell
        self.assertIn("crop", self.c["S02-T-site_area"]["fix"])

    def test_match_without_crop_passes_at_medium(self):
        self.assertEqual(self.c["V10-T-G/F"]["status"], "PASS")
        self.assertEqual(self.c["V10-T-G/F"]["confidence"], "medium")


class TaskSelectionG3(unittest.TestCase):
    """--tasks on G3: same checks as the group run; a missing raster list is named, never read as 'no picture'."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.full_p, cls.full = run_g3(os.path.join(cls.tmp, "full"), os.path.join(cls.tmp, "f"), TV, crops=True)

    def run_sel(self, name, *extra, drop=()):
        raw = os.path.join(self.tmp, name)
        os.makedirs(os.path.join(raw, "crops"), exist_ok=True)
        for n, body in (("areas.tsv", AREAS), ("area_schemes.tsv", SCHEMES), ("table_values.tsv", TV), ("rasters.tsv", RASTERS)):
            if n not in drop:
                with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                    f.write(body)
        for l in TV.strip(NL).split(NL)[1:]:
            open(os.path.join(raw, "crops", l.split(TAB)[0] + ".png"), "wb").close()
        out = os.path.join(self.tmp, name + ".json")
        p = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                            "--out", out] + list(extra), capture_output=True, text=True)
        return p, (json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None)

    @staticmethod
    def checks(d, task, skip=()):
        return sorted((c["id"], c["status"], str(c["actual"])) for c in d["checks"]
                      if c["task"] == task and not c["id"].endswith("-INPUT") and c["id"] not in skip)

    def test_s05_alone_equals_group(self):
        p, d = self.run_sel("s05", "--tasks", "S05")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual({c["task"] for c in d["checks"]}, {"AUD-S05"})
        self.assertEqual(self.checks(d, "AUD-S05"), self.checks(self.full, "AUD-S05"))

    def test_no_raster_list_is_not_a_pass(self):
        p, d = self.run_sel("s02", "--tasks", "S02", drop=("rasters.tsv",))
        c = {x["id"]: x for x in d["checks"]}
        self.assertNotIn("S02-GEN01", c)                                    # not judged 'no raster found'
        self.assertEqual(c["S02-INPUT"]["status"], "UNCLEAR")
        self.assertIn("rasters.tsv", c["S02-INPUT"]["actual"])
        self.assertEqual(self.checks(d, "AUD-S02"), self.checks(self.full, "AUD-S02", skip=("S02-GEN01",)))

    def test_v12_needs_g2(self):
        p, d = self.run_sel("v12", "--tasks", "V12")
        self.assertEqual([c["id"] for c in d["checks"]], ["V12-INPUT"])
        self.assertIn("G2", d["checks"][0]["actual"])


class ObservationEvidence(unittest.TestCase):
    """A sheet judgement that something IS there (PASS) needs a crop; 'not there' (FAIL) names the sheets looked at.
    Every reading is listed for the operator, with its crop, in the analysis, the screen summary and the report."""

    @classmethod
    def setUpClass(cls):
        tmp = cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(tmp, "_raw")
        os.makedirs(os.path.join(raw, "crops"))
        head = "key\tsheet\titem\tvalue\tunit\tconfidence\tnote\tfinding\tcrop\n"
        rows = "".join(l + "\t\t\n" for l in TV_PLAIN.strip(NL).split(NL)[1:])
        rows += ("appendices\tC003\tApp A G H\tall three tables\ttext\thigh\t\tPASS\t\n"
                 "site_class_info\tC001\tsite class\tstreets and widths shown\ttext\thigh\t\tPASS\tcrops/site.png\n"
                 "beam_target_rating\tC001-C008\tBEAM\tnot found\ttext\thigh\t\tFAIL\t\n")
        for n, body in (("areas.tsv", AREAS), ("area_schemes.tsv", SCHEMES), ("table_values.tsv", head + rows),
                        ("rasters.tsv", RASTERS)):
            with open(os.path.join(raw, n), "w", encoding="utf-8") as f:
                f.write(body)
        with open(os.path.join(raw, "crops", "site.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nfake")
        cls.out = os.path.join(tmp, "G3.json")
        cls.p = subprocess.run([sys.executable, "-I", ANALYZE, "--raw", raw, "--project", "T", "--model", "t.rvt",
                                "--out", cls.out], capture_output=True, text=True)
        cls.d = json.load(open(cls.out, encoding="utf-8"))
        cls.c = {c["id"]: c for c in cls.d["checks"]}

    def test_pass_without_crop_is_unclear(self):
        self.assertEqual(self.c["S08-L2"]["status"], "UNCLEAR")
        self.assertIn("crop", self.c["S08-L2"]["fix"])

    def test_pass_with_crop_and_fail_with_sheets(self):
        self.assertEqual(self.c["S05-L2"]["status"], "PASS")
        self.assertEqual(self.c["S07-C4"]["status"], "FAIL")

    def test_readings_listed_with_crops(self):
        r = {x["key"]: x for x in self.d["readings"]}
        self.assertTrue(r["site_class_info"]["crop"].endswith("site.png") and os.path.exists(r["site_class_info"]["crop"]))
        self.assertIsNone(r["appendices"]["crop"])
        self.assertEqual(r["appendices"]["finding"], "PASS")
        self.assertIn("Readings to check", self.p.stdout)
        self.assertIn("appendices", self.p.stdout)

    def test_report_shows_readings_with_crops(self):
        out = os.path.join(self.tmp, "rep")
        p = subprocess.run([sys.executable, "-I", os.path.join(PKG, "tools", "common", "task_report.py"), "--analysis",
                            self.out, "--outdir", out, "--date", "20260101"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        html = open([os.path.join(out, f) for f in os.listdir(out) if f.endswith(".html")][0], encoding="utf-8").read()
        self.assertIn("Sheet readings to check", html)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("no crop", html)


CROPPER = os.path.join(PKG, "tools", "common", "crop_readings.py")


class CropReadings(unittest.TestCase):
    """crop_readings.py cuts each `box` out of its sheet export and fills the `crop` column."""

    def test_crops_written(self):
        from PIL import Image
        raw = os.path.join(tempfile.mkdtemp(), "_raw")
        os.makedirs(os.path.join(raw, "sheets"))
        Image.new("RGB", (200, 100), (255, 255, 255)).save(os.path.join(raw, "sheets", "Export - Sheet - C001 - SC.png"))
        with open(os.path.join(raw, "table_values.tsv"), "w", encoding="utf-8") as f:
            f.write("key\tsheet\titem\tvalue\tunit\tconfidence\tnote\tbox\n"
                    "site_area\tC001\ts\t3082\tm2\thigh\t\t10,10,60,30\npr\tC001\tp\t1.142\t-\thigh\t\t\n")
        p = subprocess.run([sys.executable, "-I", CROPPER, "--raw", raw], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.exists(os.path.join(raw, "crops", "site_area.png")))
        with open(os.path.join(raw, "table_values.tsv"), encoding="utf-8") as f:
            rows = [l.rstrip("\n").split("\t") for l in f]
        head = rows[0]
        self.assertIn("crop", head)
        by = {r[0]: dict(zip(head, r + [""] * (len(head) - len(r)))) for r in rows[1:]}
        self.assertEqual(by["site_area"]["crop"], "crops/site_area.png")
        self.assertEqual(by["pr"]["crop"], "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
