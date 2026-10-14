"""Run some tasks of a group (`--tasks S10,S13`) and say what each task could not use.

Each group analyser declares NEEDS = {task: [(input name, required?, how to get it)]} and which inputs it has.
  - A required input that is missing: the task is not judged on empty data; it gets one UNCLEAR check
    `<task>-INPUT` naming the input and how to extract it, and its other checks are dropped.
  - An optional input that is missing: the task runs; one UNCLEAR check `<task>-INPUT` lists what could not be judged.
The output JSON keeps only the chosen tasks (checks, tables, per-task counts) and records `tasks` / `group_tasks`.
Stdlib only.
"""
import re
import sys


def add_arg(ap):
    ap.add_argument("--tasks", help="only these tasks of the group, e.g. S10,S13 (default: all)")


def parse(arg, group_tasks):
    """'S10, aud-s13' -> ['AUD-S10', 'AUD-S13'] (group order).  Unknown task: exit 2 naming the group's tasks."""
    if not arg:
        return list(group_tasks)
    want = []
    for t in re.split(r"[,\s]+", arg.strip()):
        if not t:
            continue
        t = t.upper()
        t = t if t.startswith("AUD-") else "AUD-" + t
        if t not in group_tasks:
            print("ERROR: %s is not in this group; tasks here: %s" % (t, ", ".join(x[4:] for x in group_tasks)),
                  file=sys.stderr)
            sys.exit(2)
        want.append(t)
    return [t for t in group_tasks if t in want]


def gaps(wanted, needs, have):
    """{task: {"required": [(name, how)], "optional": [(name, how)]}} for inputs the task needs but we do not have."""
    out = {}
    for t in wanted:
        for name, required, how in needs.get(t, []):
            if not have.get(name):
                out.setdefault(t, {"required": [], "optional": []})["required" if required else "optional"].append((name, how))
    return out


def blocked(task, gp):
    return bool(gp.get(task, {}).get("required"))


def finish(out, wanted, group_tasks, gp, table_tasks):
    """Keep the chosen tasks; add the <task>-INPUT checks; recount the summary.  Returns out."""
    checks = [c for c in out["checks"] if c["task"] in wanted and not blocked(c["task"], gp)]
    for t in wanted:
        g = gp.get(t)
        if not g:
            continue
        miss = g["required"] or g["optional"]
        st_text = ("not judged: required input missing" if g["required"]
                   else "judged without: some checks left out")
        checks.append({"id": "%s-INPUT" % t[4:], "task": t, "item": "Inputs for this task", "object": t,
                       "object_id": None, "expected": "all inputs extracted",
                       "actual": "%s - missing %s" % (st_text, ", ".join(n for n, _ in miss)), "status": "UNCLEAR",
                       "cite": "", "basis": "input", "method": "tools/common/tasks.py", "confidence": "high",
                       "evidence": "", "fix": "; ".join("%s: %s" % (n, h) for n, h in miss)})
    out["checks"] = checks
    ok = set(wanted)
    out["tables"] = {k: v for k, v in out.get("tables", {}).items()
                     if set(table_tasks.get(k, group_tasks)) & ok}
    per = {}
    for c in checks:
        p = per.setdefault(c["task"], {})
        p[c["status"]] = p.get(c["status"], 0) + 1
    s = out.setdefault("summary", {})
    s["per_task"] = per
    s["checks"] = len(checks)
    s["fail"] = sum(1 for c in checks if c["status"] == "FAIL")
    s["unclear"] = sum(1 for c in checks if c["status"] == "UNCLEAR")
    pi = out.setdefault("project_info", {})
    pi["group_tasks"] = list(group_tasks)
    pi["tasks"] = list(wanted)
    pi["partial"] = list(wanted) != list(group_tasks)
    return out


PARTIAL_NAME = re.compile(r"^([SVA]\d\d|A1)(-([SVA]\d\d|A1))*$")


def merge(full, part):
    """Put a --tasks run (part) into the group's full analysis: its tasks replace theirs, the rest stays as it was."""
    tasks = set(part["project_info"]["tasks"])
    full["checks"] = [c for c in full["checks"] if c["task"] not in tasks] + part["checks"]
    full.setdefault("tables", {}).update(part.get("tables", {}))
    ws = full.setdefault("summary", {}).setdefault("data_quality_warnings", [])
    ws += [w for w in part.get("summary", {}).get("data_quality_warnings", []) if w not in ws]
    per = {}
    for c in full["checks"]:
        p = per.setdefault(c["task"], {})
        p[c["status"]] = p.get(c["status"], 0) + 1
    s = full["summary"]
    s["per_task"], s["checks"] = per, len(full["checks"])
    s["fail"] = sum(1 for c in full["checks"] if c["status"] == "FAIL")
    s["unclear"] = sum(1 for c in full["checks"] if c["status"] == "UNCLEAR")
    pi = full["project_info"]
    pi["partial"] = False
    pi["updated_tasks"] = sorted(set(pi.get("updated_tasks", [])) | tasks)
    pi["updated"] = part["project_info"].get("analysis_date")
    return full


def print_summary(out, title):
    s = out["summary"]
    print("=" * 78)
    print("%s - %s%s" % (title, out["project_info"].get("project_name", ""),
                         " (tasks: %s)" % ", ".join(t[4:] for t in out["project_info"]["tasks"])
                         if out["project_info"].get("partial") else ""))
    print("=" * 78)
    print("%d checks: %d FAIL, %d UNCLEAR" % (s["checks"], s["fail"], s["unclear"]))
    for t, p in s["per_task"].items():
        print("  %-8s %s" % (t, ", ".join("%s %d" % kv for kv in sorted(p.items()))))
    print("-" * 78)
    for c in out["checks"]:
        if c["status"] != "PASS":
            print("  [%s] %s | %s | expected %s | actual %s" % (c["status"], c["id"], c["object"], c["expected"],
                                                                str(c["actual"])[:90]))
    for w in s.get("data_quality_warnings", []):
        print("! " + w)
    rd = out.get("readings") or []
    if rd:
        print("-" * 78)
        print("Readings to check against their crops before confirming (the report shows each crop):")
        for r in rd:
            print("  %-22s %-12s %-8s %-6s %s | %s" % (r["key"], (r["sheet"] or "")[:12], r["finding"] or "-",
                                                      "crop" if r["crop"] else "NO CROP", str(r["value"])[:60],
                                                      str(r.get("note") or "")[:40]))
