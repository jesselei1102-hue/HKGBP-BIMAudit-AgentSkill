"""Tests for model-audit/report/render_report.py (run: python -I test_render.py)."""
import copy
import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parents[1] / "model-audit" / "report" / "render_report.py"
TOOLS = (HERE / "check_package.py").read_text(encoding="utf-8").split('TOOLS = """')[1].split('"""')[0].split()


def png(path, rgb=(227, 100, 102), size=8):
    raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


SAMPLE = {
    "meta": {"project": "Sample Institutional Development", "model": "Sample_R27.rvt", "revit_version": "2027 (from file name)",
             "mcp": "revit-mcp (Experimental Technical Preview)", "harness": "Claude Code", "date": "2026-10-13",
             "round": "Round 1", "package_version": "Model Audit 2026-10-13", "filled_by": "script"},
    "verdict": {"submittable": False, "summary": "Not submittable as is.",
                "reasons": [{"text": "Calculation tables are images, not model schedules.", "finding_ids": ["F1"]}]},
    "a1": [
        {"id": "MA-3.1", "title": "No manual input", "result": "Fail", "evidence": "Tables are images (sheet 437655).",
         "element_ids": ["437655"], "clause": "BIMGBPS §5.1.2", "gap": "GAP-01", "audience": "both"},
        {"id": "MA-1.3", "title": "File size", "result": "Pass", "evidence": "40.4 MB", "clause": "BIMGBPS §4.3(b)", "gap": None},
    ],
    "tasks": [
        {"id": "AUD-S10", "name": "Min Exit Doors & Routes", "clause": "BIMGBPS §5.3.10", "category": "Schedule",
         "applicability": {"applicable": True}, "l1_status": "Fail", "l2_status": "Unclear", "summary": "Table is an image.",
         "checks": [
             {"id": "S10-L1", "item": "Table generated from the model", "result": "Fail",
              "evidence": "Image 1512245 covers the whole sheet.", "element_ids": ["1512245"], "audience": "both"},
             {"id": "S10-L4", "item": "Required column typed in", "result": "Partial",
              "evidence": "Read with query_model on view 1531502.", "element_ids": ["1531502"], "audience": "bim"}],
         "calcs": [{"id": "S10-C1", "formula": "persons = ceil(UFA / factor)", "values": "261.240 / 10 → 27",
                    "limit": "FS Code Part B", "clause": "LIM-30", "result": "Unclear", "basis": None, "audience": "both"}],
         "evidence_ids": ["ev1"], "finding_ids": ["F1"],
         "fix": [{"text": "Rebuild as a model schedule and place it on sheet C007.", "method": "function-b", "audience": "both"},
                 {"text": "Use modify_element_parameters to rename view 1531502.", "method": "function-b", "audience": "bim"}],
         "overturn_if": "The image is an export of a schedule still in the model."},
        {"id": "AUD-V07", "name": "Open Space Diagram", "clause": "BIMGBPS §5.2.7", "category": "View",
         "applicability": {"applicable": False, "reason": "The building is non-domestic; regulation 25 applies to domestic buildings only.",
                           "conditions": "AP confirms the use classification.", "ap_confirmed": None},
         "l1_status": "N/A 待声明", "l2_status": "N/A（附条件）", "checks": [], "evidence_ids": [], "finding_ids": ["F2"], "fix": []},
        {"id": "AUD-V10", "name": "GFA Diagram", "clause": "BIMGBPS §5.2.10", "category": "View",
         "applicability": {"applicable": True}, "l1_status": "Pass", "l2_status": "Pass",
         "checks": [{"id": "V10-L3", "item": "Table 1 colours", "result": "Pass", "evidence": "Sampled 227,100,102.", "audience": "both"}],
         "evidence_ids": ["ev2"], "finding_ids": ["F3"], "fix": []},
    ],
    "findings": [
        {"id": "F1", "task": "AUD-S10", "title": "Tables are images.", "status": "Fail", "severity": "Blocker",
         "clause": "BIMGBPS §4.2(b)", "evidence": [{"element_id": "1512245", "value": "690 × 668 mm", "note": "One image on C007."}],
         "label": "FACT", "fix": "Rebuild as schedules.", "fix_method": "function-b"},
        {"id": "F2", "task": "AUD-V07", "title": "N/A not declared.", "status": "N/A 待声明", "severity": "Major",
         "clause": "BIMGBPS §5.2.1(g)", "evidence": [{"element_id": None, "value": None, "note": "No N/A note on drawings."}],
         "label": "INFERENCE", "fix": "Add the N/A statement.", "fix_method": "AP"},
        {"id": "F3", "task": "AUD-V10", "title": "Boundary gaps not checked.", "status": "Unclear", "severity": "Minor",
         "clause": "BIMGBPS §4.2(e)", "evidence": [{"element_id": "494030", "value": None, "note": "Tool cannot read boundary end points."}],
         "label": "GAP", "fix": "Check boundaries by hand.", "fix_method": "manual", "gap": "GAP-02"},
    ],
    "decisions": [{"id": "INP-11", "question": "Which building height basis applies?", "options": ["12.15 m", "17.35 m"], "tasks": ["AUD-V03"]}],
    "inputs": [{"id": "INP-04", "item": "OZP and lease height limits", "tasks": ["AUD-V03"]}],
    "unclear": [{"task": "AUD-S10", "reason_kind": "source", "detail": "FS Code Part B not available.", "need": "FS Code 2011 Part B", "gap": None}],
    "regression": {"previous_round": "Round 0", "items": [{"finding_id": "F1", "before": "Fail", "after": "open", "note": "Not yet rebuilt."}]},
    "evidence": [
        {"id": "ev1", "file": "s10-1-sheet.png", "kind": "sheet", "caption": "Sheet C007 exported", "task": "AUD-S10", "audience": "both"},
        {"id": "ev2", "file": "v10-1-swatch.png", "kind": "swatch", "caption": "Sampled vs Table 1 colour", "task": "AUD-V10", "audience": "both"},
    ],
}
ELEMENT_IDS = ["1512245", "1531502", "437655", "494030"]


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "assets").mkdir()
        png(self.dir / "assets" / "s10-1-sheet.png")
        png(self.dir / "assets" / "v10-1-swatch.png")

    def tearDown(self):
        self.tmp.cleanup()

    def run_render(self, data, audience):
        src = self.dir / "audit-results.json"
        src.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        out = self.dir / f"report-{audience}.html"
        if out.exists():
            out.unlink()
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--results", str(src), "--audience", audience, "--out", str(out)],
                           capture_output=True, text=True, encoding="utf-8")
        html = out.read_text(encoding="utf-8") if out.exists() else None
        return r, html

    def test_render_bim_has_all_sections(self):
        r, html = self.run_render(SAMPLE, "bim")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for sid in ["cover", "overview", "decisions", "model-health", "tasks", "findings", "action-plan",
                    "na-table", "not-determinable", "regression", "appendix"]:
            self.assertIn(f'id="{sid}"', html, sid)

    def test_ap_has_no_internal_detail(self):
        r, html = self.run_render(SAMPLE, "ap")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for eid in ELEMENT_IDS:
            self.assertNotIn(eid, html, f"element id {eid}")
        for tool in TOOLS:
            self.assertNotIn(tool, html, f"tool {tool}")
        self.assertNotIn("GAP-0", html)
        self.assertNotIn("Read with", html)          # bim-only check text
        self.assertNotIn("rename view", html)        # bim-only fix text
        for label in ["[FACT]", "[INFERENCE]", "[GAP]"]:
            self.assertNotIn(label, html)

    def test_ap_decisions_first(self):
        r, html = self.run_render(SAMPLE, "ap")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertLess(html.index('id="overview"'), html.index('id="decisions"'))
        self.assertLess(html.index('id="decisions"'), html.index('id="model-health"'))
        self.assertIn('id="inputs"', html)

    def test_labels_translated_for_ap(self):
        r, html = self.run_render(SAMPLE, "ap")
        for word in ["Verified", "Inferred", "Not determinable"]:
            self.assertIn(word, html)

    def test_every_fail_has_evidence(self):
        data = copy.deepcopy(SAMPLE)
        data["tasks"][0]["evidence_ids"] = []
        r, html = self.run_render(data, "bim")
        self.assertEqual(r.returncode, 2)
        self.assertIn("AUD-S10", r.stdout)
        self.assertIsNone(html)

    def test_invalid_results_rejected(self):
        data = copy.deepcopy(SAMPLE)
        del data["verdict"]
        r, html = self.run_render(data, "bim")
        self.assertEqual(r.returncode, 2)
        self.assertIn("INVALID", r.stdout)
        self.assertIsNone(html)

    def test_missing_asset_rejected(self):
        data = copy.deepcopy(SAMPLE)
        data["evidence"][0]["file"] = "does-not-exist.png"
        r, html = self.run_render(data, "bim")
        self.assertEqual(r.returncode, 3)
        self.assertIn("MISSING ASSET does-not-exist.png", r.stdout)
        self.assertIsNone(html)

    def test_offline(self):
        for aud in ("bim", "ap"):
            r, html = self.run_render(SAMPLE, aud)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotRegex(html, r"https?://")

    def test_status_has_text(self):
        r, html = self.run_render(SAMPLE, "bim")
        chips = re.findall(r'<span class="st st-[a-z]+">([^<]*)</span>', html)
        self.assertTrue(chips)
        self.assertTrue(all(c.strip() for c in chips))
        self.assertIn(">Fail<", html)

    def test_template_comments_not_copied(self):
        r, html = self.run_render(SAMPLE, "bim")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("FILL", html)
        self.assertNotIn("Audience rules", html)
        self.assertEqual(html.count("<style"), 1)
        self.assertEqual(html.count("<script"), 1)

    def test_task_report_links_not_images(self):
        data = copy.deepcopy(SAMPLE)
        (self.dir / "assets" / "s14-detail.xlsx").write_bytes(b"PK")
        (self.dir / "assets" / "s14-detail.html").write_text("<p>x</p>", encoding="utf-8")
        data["evidence"] += [
            {"id": "ev3", "file": "s14-detail.xlsx", "kind": "table", "caption": "S14 workbook", "task": "AUD-S10", "audience": "both"},
            {"id": "ev4", "file": "s14-detail.html", "kind": "report", "caption": "S14 detailed report", "task": "AUD-S10", "audience": "both"}]
        data["tasks"][0]["evidence_ids"] += ["ev3", "ev4"]
        r, html = self.run_render(data, "bim")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('href="assets/s14-detail.xlsx"', html)
        self.assertNotIn('src="assets/s14-detail.xlsx"', html)
        self.assertNotIn('src="assets/s14-detail.html"', html)

    def test_accepts_bom(self):
        src = self.dir / "audit-results.json"
        src.write_bytes(b"\xef\xbb\xbf" + json.dumps(SAMPLE, ensure_ascii=False).encode("utf-8"))
        out = self.dir / "bom.html"
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--results", str(src), "--audience", "bim", "--out", str(out)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
