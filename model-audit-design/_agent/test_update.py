"""Tests for running one task and updating the combined results (build_results.py --update).

Run: python -I test_update.py
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "model-audit"))
TOOLS = os.path.join(PKG, "tools")
sys.path.insert(0, HERE)
import test_room_use as RU  # noqa: E402  (G2 fixture)

PY = [sys.executable, "-I"]


def run(*args):
    p = subprocess.run(PY + list(args), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return p


class UpdateOneTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t = cls.tmp = tempfile.mkdtemp()
        g2 = cls.g2 = os.path.join(t, "g2")
        raw = os.path.join(g2, "_raw")
        os.makedirs(raw)
        for n, body in RU.ALL_G2:
            RU.write(raw, n, body)
        cls.gjson = os.path.join(g2, "G2.json")
        run(os.path.join(TOOLS, "room_use", "analyze.py"), "--raw", raw, "--project", "T", "--model", "t.rvt", "--out", cls.gjson)
        run(os.path.join(TOOLS, "common", "task_report.py"), "--analysis", cls.gjson, "--outdir", g2, "--name", "RoomUse",
            "--date", "20260101")
        cls.full = os.path.join(t, "full")
        os.makedirs(cls.full)
        cls.res = os.path.join(cls.full, "audit-results.json")
        base = [os.path.join(TOOLS, "common", "build_results.py"), "--out", cls.res, "--project", "T", "--model", "t.rvt",
                "--date", "2026-01-01", "--group", cls.gjson, g2]
        run(*base)
        cls.before = json.load(open(cls.res, encoding="utf-8"))
        cls.g2_before = json.load(open(cls.gjson, encoding="utf-8"))
        # one task re-run; pretend the model changed so S16 now fails
        part = os.path.join(t, "G2-S16.json")
        run(os.path.join(TOOLS, "room_use", "analyze.py"), "--raw", raw, "--project", "T", "--model", "t.rvt", "--out", part,
            "--tasks", "S16")
        d = json.load(open(part, encoding="utf-8"))
        for c in d["checks"]:
            c["status"], c["actual"] = "FAIL", "changed"
        json.dump(d, open(part, "w", encoding="utf-8"))
        cls.part = part
        run(*(base + ["--update", part]))
        cls.after = json.load(open(cls.res, encoding="utf-8"))
        cls.g2_after = json.load(open(cls.gjson, encoding="utf-8"))

    def task(self, d, tid):
        return next(t for t in d["tasks"] if t["id"] == tid)

    def test_only_s16_changes(self):
        ids = {t["id"] for t in self.before["tasks"]}
        for tid in ids - {"AUD-S16"}:
            self.assertEqual(self.task(self.after, tid)["checks"], self.task(self.before, tid)["checks"], tid)
            self.assertEqual(self.task(self.after, tid)["l1_status"], self.task(self.before, tid)["l1_status"], tid)
        self.assertEqual(self.task(self.after, "AUD-S16")["l1_status"], "Fail")

    def test_group_json_merged_on_disk(self):
        keep = lambda d: [c for c in d["checks"] if c["task"] != "AUD-S16"]
        self.assertEqual(keep(self.g2_after), keep(self.g2_before))
        self.assertTrue(all(c["status"] == "FAIL" for c in self.g2_after["checks"] if c["task"] == "AUD-S16"))
        self.assertFalse(self.g2_after["project_info"].get("partial"))
        self.assertIn("AUD-S16", self.g2_after["project_info"]["updated_tasks"])
        self.assertTrue(os.path.exists(self.gjson.replace(".json", ".prev.json")))

    def test_group_report_rebuilt_and_linked(self):
        ev = [e["file"] for e in self.after["evidence"] if e["id"].startswith("ev-g2")]
        self.assertTrue(ev and all("RoomUse" in f for f in ev), ev)

    def test_meta_from_arguments(self):
        self.assertEqual(self.after["meta"]["project"], "T")

    def test_update_needs_matching_group(self):
        p = subprocess.run(PY + [os.path.join(TOOLS, "common", "build_results.py"), "--out", self.res, "--project", "T",
                                 "--model", "t.rvt", "--date", "2026-01-01", "--update", self.part],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("--group", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
