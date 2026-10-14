"""Validate tools/extract/g1_extract.py on real responses (Cursor 2026-10-13 revit-mcp dumps) against our S14 extract.

python -I check_g1_real.py <scratch dir>
1. copy the dumps (+ the 2026-10-14 room boundaries) and run g1_extract
2. compare every extract file with ours row by row (ids, text exactly; numbers within 0.006 - ours kept 2 decimals)
3. run the S14 analyser on the new extract and compare room results with our C14 analysis
"""
import csv
import json
import os
import shutil
import subprocess
import sys

W = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
T = os.path.join(W, "model-audit", "tools")
OURS = os.path.join(W, "model-audit-runs", "audit-2026-10-13-s14", "_raw")
CUR = r"C:\Users\Datech\Desktop\Cursor Projects\HK GBP\model-audit\work\model-audit-runs"
N = "GBP_Revit_Templates_R27-GBPSkills"
S = sys.argv[1]
if os.path.exists(S):
    shutil.rmtree(S)
mcp, raw = os.path.join(S, "mcp"), os.path.join(S, "raw")
shutil.copytree(os.path.join(CUR, "audit-2026-10-13-full", "_raw", "mcp"), mcp)
shutil.copy(os.path.join(CUR, "audit-2026-10-14-s10", "_raw", "mcp", "room_boundaries.json"), mcp)
os.makedirs(raw)
p = subprocess.run([sys.executable, "-I", os.path.join(T, "extract", "g1_extract.py"), "--mcp", mcp, "--out", raw],
                   capture_output=True, text=True)
print(p.stdout, p.stderr)
if p.returncode:
    sys.exit(1)


def rows(path, key="id"):
    with open(path, encoding="utf-8-sig") as f:
        return {r[key]: r for r in csv.DictReader(f, delimiter="\t")}


def same(a, b):
    try:
        return abs(float(a) - float(b)) <= 0.006
    except (TypeError, ValueError):
        return (a or "") == (b or "")


bad = 0
for name, key in (("cw", "id"), ("pn", "id"), ("fs_windows.tsv", "id"), ("doors.tsv", "id"), ("doors_other.tsv", "family"),
                  ("rooms.tsv", "id"), ("pn_bbox_sample.tsv", "id")):
    if name in ("cw", "pn"):
        ours = {}
        for f in sorted(os.listdir(OURS)):
            if f.startswith(name + "_part"):
                ours.update(rows(os.path.join(OURS, f)))
        new = rows(os.path.join(raw, name + "_part1.tsv"))
    else:
        ours, new = rows(os.path.join(OURS, name), key), rows(os.path.join(raw, name), key)
    if name == "pn_bbox_sample.tsv":                       # ours sampled one panel per group; new has every panel
        diff = [i for i in ours if i not in new or not all(same(ours[i][c], new[i][c]) for c in ("minz", "maxz"))]
        print("%-20s ours %3d sampled, new %3d (all panels); sampled panels that differ: %s" % (name, len(ours), len(new), diff))
        bad += bool(diff)
        continue
    only_o, only_n = sorted(set(ours) - set(new)), sorted(set(new) - set(ours))
    cells = []
    for i in set(ours) & set(new):
        for c in ours[i]:
            if c in new[i] and c != "note" and not same(ours[i][c], new[i][c]):
                cells.append((i, c, ours[i][c], new[i][c]))
    print("%-20s ours %3d new %3d | only ours %s | only new %s | differing cells %d %s"
          % (name, len(ours), len(new), only_o[:5], only_n[:5], len(cells), sorted(cells)[:6]))
    bad += bool(only_o or only_n or (cells and name != "rooms.tsv"))

# S14 analysis on the new extract
sched = [f for f in os.listdir(OURS) if f.endswith(".csv") and "S14" in f]
fx = os.path.join(W, "model-audit-runs", "audit-2026-10-13-g2", "_raw", "fixtures.tsv")
out = os.path.join(S, "C14.json")
args = [sys.executable, "-I", os.path.join(T, "s14_lv", "analyze.py"), "--raw", raw, "--project", N, "--model", N + ".rvt",
        "--out", out, "--fixtures", fx] + (["--schedule", os.path.join(OURS, sched[0])] if sched else [])
q = subprocess.run(args, capture_output=True, text=True)
if q.returncode:
    print(q.stderr)
    sys.exit(1)
a = json.load(open(out, encoding="utf-8"))
b = json.load(open(os.path.join(W, "model-audit-runs", "audit-2026-10-13-s14", "C14_analysis_%s.json" % N), encoding="utf-8"))
ka = {r["id"]: r for r in a["rooms_included"]}
kb = {r["id"]: r for r in b["rooms_included"]}
diffs = [(i, kb[i]["name"], (kb[i]["status"], kb[i]["act_light_sqm"], kb[i]["act_vent_sqm"]),
          (ka.get(i, {}).get("status"), ka.get(i, {}).get("act_light_sqm"), ka.get(i, {}).get("act_vent_sqm")))
         for i in kb if i not in ka or (ka[i]["status"], ka[i]["act_light_sqm"], ka[i]["act_vent_sqm"])
         != (kb[i]["status"], kb[i]["act_light_sqm"], kb[i]["act_vent_sqm"])]
for k in ("rooms_included_count", "rooms_excluded_count", "rooms_pending_count", "both_pass_count", "panels_total",
          "panels_openable", "panels_louvre", "openings_unassigned_count"):
    print("  %-28s ours %s new %s" % (k, b["summary"].get(k), a["summary"].get(k)))
print("S14 room results differing: %d" % len(diffs))
for d in diffs[:12]:
    print("  ", d)
sys.exit(1 if bad or diffs else 0)
