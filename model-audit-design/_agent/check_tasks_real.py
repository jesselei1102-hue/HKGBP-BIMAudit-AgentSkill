"""Run every task of G2-G5 alone on the saved sample extracts and compare with the group run (read-only on the runs).

python -I check_tasks_real.py <scratch dir>
Prints one line per task: same / DIFF, plus any <task>-INPUT line.  Exit 1 if any task differs.
"""
import json
import os
import subprocess
import sys

W = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
T = os.path.join(W, "model-audit", "tools")
R = os.path.join(W, "model-audit-runs")
N = "GBP_Revit_Templates_R27-GBPSkills"
J = lambda g: os.path.join(R, "audit-2026-10-13-%s" % g, "%s_analysis_%s.json" % (g.upper() if g != "s14" else "C14", N))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
G = {
    "g2": ("room_use", ["--raw", os.path.join(R, "audit-2026-10-13-g2", "_raw")]),
    "g3": ("area_scheme", ["--raw", os.path.join(R, "audit-2026-10-13-g3", "_raw"), "--g2", J("g2")]),
    "g4": ("drawings", ["--raw", os.path.join(R, "audit-2026-10-13-g4", "_raw"), "--s14", J("s14"), "--g3", J("g3")]),
    "g5": ("lists_health", ["--raw", os.path.join(R, "audit-2026-10-13-g5", "_raw"), "--g2", J("g2"), "--g3", J("g3"),
                            "--g4", J("g4"), "--s14", J("s14"), "--g3raw", os.path.join(R, "audit-2026-10-13-g3", "_raw"),
                            "--g4raw", os.path.join(R, "audit-2026-10-13-g4", "_raw"),
                            "--schedules", os.path.join(R, "audit-2026-10-13-g5", "_raw", "all_schedules.tsv")]),
}
key = lambda cs, t: sorted((c["id"], c["status"], str(c["actual"])) for c in cs if c["task"] == t and not c["id"].endswith("-INPUT"))
bad = 0
for g, (tool, args) in G.items():
    full = json.load(open(J(g), encoding="utf-8"))
    for t in full["project_info"].get("group_tasks", full["project_info"]["tasks"]):
        out = os.path.join(OUT, "%s-%s.json" % (g, t))
        p = subprocess.run([sys.executable, "-I", os.path.join(T, tool, "analyze.py"), "--project", N, "--model", N + ".rvt",
                            "--out", out, "--tasks", t[4:]] + args, capture_output=True, text=True)
        if p.returncode:
            print("%s %-8s ERROR %s" % (g, t, p.stderr.strip()[-200:]))
            bad += 1
            continue
        d = json.load(open(out, encoding="utf-8"))
        same = key(d["checks"], t) == key(full["checks"], t)
        bad += not same
        extra = sorted({c["task"] for c in d["checks"]} - {t})
        inp = [c["actual"] for c in d["checks"] if c["id"].endswith("-INPUT")]
        print("%s %-8s %-4s %3d checks%s%s" % (g, t, "same" if same else "DIFF", len(key(d["checks"], t)),
                                             " | other tasks: %s" % extra if extra else "", " | " + inp[0] if inp else ""))
sys.exit(1 if bad else 0)
