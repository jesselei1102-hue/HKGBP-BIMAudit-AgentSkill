#!/usr/bin/env python3
"""Write model-audit/tasks.json, the task list the audit window shows (BIMGBPS sections, groups, task numbers, names,
clauses).

Usage:
  python make_tasks_json.py           write tasks.json
  python make_tasks_json.py --check   compare only; exit 1 and print the difference if tasks.json is out of date
Groups: G1 = S14 (tools/s14_lv); G2-G5 = the GROUP list of each analyser (read from the source, not imported).
Names and clauses come from the L2 card title lines, as in build_results.card().  English only.  Stdlib only.
"""
import ast
import difflib
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", ".."))
L2 = os.path.join(PKG, "L2-Task-Logic")
OUT = os.path.join(PKG, "tasks.json")
GROUPS = [("G1", "Lighting and ventilation", None), ("G2", "Room use", "room_use"),
          ("G3", "Area schemes", "area_scheme"), ("G4", "Drawings", "drawings"),
          ("G5", "Lists and model health", "lists_health")]
A1 = {"task": "AUD-A1", "tl": "MA-1 to MA-7", "name": "Model health", "summary": "Roadmap MA-1 to MA-7"}
# How the window lists tasks: by BIMGBPS section, then TL number. The groups above only decide which analysers run.
SECTIONS = [("views", "Views", "BIMGBPS §5.2"), ("schedules", "Schedules", "BIMGBPS §5.3"),
            ("assembly", "Assembly and export", "BIMGBPS §4, §5.5, §6"), ("health", "Model health", "Roadmap MA-1 to MA-7")]


def section(task):
    if task == "AUD-A1":
        return "health"
    return {"V": "views", "S": "schedules", "A": "assembly"}[task[4]]


def group_list(tool):
    if tool is None:
        return ["AUD-S14"]
    with open(os.path.join(PKG, "tools", tool, "analyze.py"), encoding="utf-8") as f:
        for node in ast.parse(f.read()).body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "GROUP":
                return ast.literal_eval(node.value)
    raise SystemExit("ERROR: no GROUP list in tools/%s/analyze.py" % tool)


def card(task):
    """(name, clause) from the card title line '# AUD-S10 Min Exit Doors & Routes · BIMGBPS §5.3.10'."""
    for p in glob.glob(os.path.join(L2, "*", "%s_*.md" % task)):
        with open(p, encoding="utf-8-sig") as f:
            first = f.readline().strip("# \n")
        m = re.match(r"%s\s+(.*?)\s+·\s+(.*)$" % task, first)
        if m:
            return m.group(1), m.group(2).replace("、", ", ")
    raise SystemExit("ERROR: no L2 card title for %s" % task)


def build():
    tasks = {}
    for gid, _, tool in GROUPS:
        for t in group_list(tool):
            if t not in tasks:
                if t == "AUD-A1":
                    tasks[t] = dict(A1, groups=[])
                else:
                    name, clause = card(t)
                    tasks[t] = {"task": t, "tl": "TL-" + t[4:], "name": name, "summary": clause, "groups": []}
            tasks[t]["groups"].append(gid)
    order = [sid for sid, _, _ in SECTIONS]
    for t in tasks.values():
        t["section"] = section(t["task"])
    listed = sorted(tasks.values(), key=lambda t: (order.index(t["section"]), int(re.sub(r"\D", "", t["task"]) or 0)))
    return {"sections": [{"id": i, "name": n, "clause": c} for i, n, c in SECTIONS],
            "groups": [{"id": g, "name": n} for g, n, _ in GROUPS], "tasks": listed}


def main(argv):
    text = json.dumps(build(), ensure_ascii=False, indent=1) + "\n"
    if "--check" in argv:
        try:
            with open(OUT, encoding="utf-8") as f:
                old = f.read()
        except OSError:
            old = ""
        if old != text:
            sys.stdout.writelines(difflib.unified_diff(old.splitlines(True), text.splitlines(True), "tasks.json", "expected"))
            return 1
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
