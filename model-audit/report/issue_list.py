"""Write the Excel issue list from audit-results.json: one row per object, for filtering and assigning the fixes.

python issue_list.py --results audit-results.json --out issues.xlsx

Sheets: "Fix list" (every failing object: severity, task, rule, object, kind, sheet, Revit ID, expected, actual, fix,
clause, a Fixed column to fill in, and the one-line instruction for the agent), "To check" (what the tool could not
decide) and "Sheet readings" (values read off sheet images, not checked by a person).  Revit IDs are written as text so
every digit survives.  Same validation as render_report.py (exit 2 on invalid results).  Python 3 standard library only.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools" / "common"))
import render_report as R  # noqa: E402
from xlsx_lite import Cell, Workbook  # noqa: E402

SEV_FILL = {"Blocker": "fail", "Major": "fail", "Minor": "na"}
FIX_HEAD = ["Fixed", "Severity", "Task", "Rule", "Object", "Kind", "Sheet", "Revit ID", "Expected", "Actual", "Fix",
            "Clause", "Finding", "ID from", "For the agent"]
CHECK_HEAD = ["Checked", "Task", "Rule", "Object", "Kind", "Sheet", "Revit ID", "Expected", "Actual", "Look at", "Clause",
              "For the agent"]


def build(results):
    issues = R.issues_of(results)
    order = sorted(range(len(issues)), key=lambda n: (R.SEV_RANK[issues[n].get("severity")], R.task_order(issues[n]["task"]), n))
    wb = Workbook()
    fix = wb.sheet("Fix list", widths=[7, 9, 9, 34, 34, 11, 8, 11, 22, 22, 40, 22, 8, 9, 60])
    fix.row(FIX_HEAD, header=True)
    chk = wb.sheet("To check", widths=[8, 9, 34, 34, 11, 8, 11, 22, 22, 40, 22, 60])
    chk.row(CHECK_HEAD, header=True)
    for n in order:
        i = issues[n]
        kind = R.KIND_EN.get(i.get("kind"), "Object")
        common = [i["tl"], i["rule"], i["object"], kind, i.get("sheet") or "", i.get("element_id") or "", i.get("expected", ""),
                  i.get("actual", "")]
        if i["action"] == "fix":
            sev = i.get("severity") or ""
            fix.row(["", Cell(sev, fill=SEV_FILL.get(sev))] + common
                    + [i.get("fix", ""), i.get("clause", ""), i.get("finding_id") or "", i.get("id_from") or "", R.agent_line(i)])
        else:
            chk.row([""] + common + [i.get("fix", ""), i.get("clause", ""), R.agent_line(i)])
    rd = wb.sheet("Sheet readings", widths=[7, 8, 36, 14, 11, 34, 26])
    rd.row(["Group", "Sheet", "Item", "Value", "Confidence", "Crop (in assets/)", "Checked by a person"], header=True)
    for x in R.readings_of(results):
        rd.row([x.get("group", ""), x["sheet"], x["item"] or x["key"], x["value"], x.get("confidence", ""), x.get("crop") or "",
                Cell("No - not checked by a person", fill="na")])
    return wb, sum(1 for i in issues if i["action"] == "fix"), sum(1 for i in issues if i["action"] == "check")


def main(argv):
    p = argparse.ArgumentParser(description="Write the Excel issue list from audit-results.json.")
    p.add_argument("--results", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        results = R.load_json(a.results)
    except (OSError, json.JSONDecodeError) as e:
        print(f"INVALID $: cannot read results ({e})")
        return 2
    schema = R.load_json(R.TEMPLATES / "audit-results.schema.json")
    errors = R.validate(results, schema, schema) or R.check_semantics(results)
    if errors:
        for e in errors:
            print(f"INVALID {e}")
        return 2
    wb, n_fix, n_check = build(results)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print(f"wrote {a.out}: {n_fix} objects to fix, {n_check} to check")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
