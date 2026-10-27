#!/usr/bin/env python3
"""Combine the group analyses into one audit-results.json (templates/audit-results.schema.json) for render_report.py.

Usage:
  python build_results.py --out <run>/audit-results.json --project <name> --model <file> --date YYYY-MM-DD
         [--s14 <S14 run>/audit-results.json] --group <G2 json> <G2 report dir> --group <G3 json> <dir> ...
         [--update <analysis json from a --tasks run>] ... [--decisions <decisions.json>]
         [--crop <png> <task> <caption>] ...
--update: the --tasks run is merged into the --group JSON of the same group (its tasks replace theirs, a copy of the
old file is kept as <name>.prev.json), the group report is rebuilt, then everything is combined as usual - so the
other tasks keep their results.  --decisions: {"decisions": [...], "inputs": [...]} for the AP questions.
Each group's Excel and HTML report are copied to <run>/assets and linked as evidence; every FAIL / Partial / Missing
check becomes part of a finding (one finding per task and rule); UNCLEAR checks go to 'unclear'.  Stdlib only.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
L2 = os.path.normpath(os.path.join(HERE, "..", "..", "L2-Task-Logic"))
L2_RE = r"-C\d|-C-|^S13-C|^V\d\d-C|-LIM$|-ROUTE$|-DV-"
STATUS = {"PASS": "Pass", "FAIL": "Fail", "UNCLEAR": "Unclear", "N/A": "N/A（附条件）", "APPLICABLE": "Unclear"}
ORDER = ["Fail", "Missing", "Partial", "Unclear", "N/A 待声明", "N/A（附条件）", "Pass", "Not judged"]


def card(task):
    """Name, clause and category from the L2 card title line."""
    for p in glob.glob(os.path.join(L2, "*", "%s_*.md" % task)):
        with open(p, encoding="utf-8-sig") as f:
            first = f.readline().strip("# \n")
        m = re.match(r"%s\s+(.*?)\s+·\s+(.*)$" % task, first)
        cat = {"Views": "View", "Schedules": "Schedule", "Assembly": "Assembly"}[os.path.basename(os.path.dirname(p))]
        if m:
            return m.group(1), m.group(2), cat
    return task, "", "Assembly"


def status_of(c):
    st = STATUS.get(c["status"], "Not judged")
    if st == "Fail" and c.get("basis") in ("Partial", "Missing"):
        return c["basis"]
    return st


def worst(sts):
    sts = [s for s in sts if s and s != "Not judged"]
    if not sts:
        return "Not judged"
    if all(s == "N/A（附条件）" for s in sts):
        return "N/A（附条件）"
    sts = [s for s in sts if s != "N/A（附条件）"] or sts
    return min(sts, key=ORDER.index)


def severity(c):
    b = c.get("basis", "")
    if b in ("Blocker", "Major", "Minor"):
        return b
    if b == "Missing":
        return "Major"
    if b == "Partial":
        return "Minor"
    return "Major" if re.search(r"-C\d|C\d-|GEN01|-D-|-W-", c["id"]) else "Minor"


def method_of(fix):
    f = fix or ""
    if re.search(r"\bAP\b|INP-", f):
        return "AP"
    if "Function B" in f or "schedule" in f.lower() or "rebuild" in f.lower():
        return "function-b"
    return "manual"


def group_reports(gdir, gname, ext, tasks=None):
    """The group's full report files, newest first; reports of a --tasks run (GBP_G2_S10_...) are left out.
    tasks: the group JSON is itself a --tasks run (a new audit of a few tasks) - then only its own report
    (GBP_G2_S10-S13_...) counts."""
    want = "-".join(t[4:] for t in tasks) if tasks else None
    out = []
    for p in glob.glob(os.path.join(gdir, "GBP_%s_*.%s" % (gname, ext))):
        parts = os.path.basename(p).split("_")
        if len(parts) > 2 and (parts[2] == want if want else not T.PARTIAL_NAME.match(parts[2])):
            out.append(p)
    return sorted(out, key=os.path.getmtime)


def update_group(path, groups):
    """Merge a --tasks run into its group's JSON (keeping <name>.prev.json) and rebuild that group's report."""
    with open(path, encoding="utf-8") as f:
        part = json.load(f)
    gname = part["project_info"]["group"].split()[0]
    for gjson, gdir in groups:
        with open(gjson, encoding="utf-8") as f:
            full = json.load(f)
        if full["project_info"]["group"].split()[0] != gname:
            continue
        shutil.copyfile(gjson, gjson[:-5] + ".prev.json" if gjson.endswith(".json") else gjson + ".prev")
        T.merge(full, part)
        with open(gjson, "w", encoding="utf-8") as f:
            json.dump(full, f, indent=1, ensure_ascii=False)
        old = group_reports(gdir, gname, "html")
        name = os.path.basename(old[-1]).split("_")[2] if old else ""
        cmd = [sys.executable, "-I", os.path.join(HERE, "task_report.py"), "--analysis", gjson, "--outdir", gdir]
        r = subprocess.run(cmd + (["--name", name] if name else []), capture_output=True, text=True)
        if r.returncode:
            print("ERROR: rebuilding the %s report failed: %s" % (gname, r.stderr.strip()), file=sys.stderr)
            return True
        print("merged %s (%s) into %s; report rebuilt" % (os.path.basename(path), ", ".join(part["project_info"]["tasks"]), gjson))
        return False
    print("ERROR: %s is a %s run; pass that group's full analysis with --group <JSON> <DIR> to update it"
          % (path, gname), file=sys.stderr)
    return True


def load_gate(run_dir, current):
    """The reading review saved by the audit window (<run>/gate-confirmation.json), or None when there is none.
    `current`: {(group, key): (value, sheet, item)} from the group JSONs being combined.  A reviewed reading whose value
    or sheet has changed since, or that is gone, does not count as checked; a current reading the review never saw
    is unreviewed.  A file that cannot be read stops the build (exit 2) rather than producing reports without it."""
    p = os.path.join(run_dir, "gate-confirmation.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            g = json.load(f)
        mode = g["mode"]
        rows = [{k: str(r.get(k) or "") for k in ("group", "key", "sheet", "item", "value", "note", "mark")}
                for r in g["readings"]]
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        print("ERROR: %s: %s" % (p, e))
        sys.exit(2)
    keep = ("group", "key", "sheet", "item", "value", "note")
    out = {"mode": mode, "saved": str(g.get("saved") or ""), "checked": 0, "unreviewed": [], "disputed": [], "stale": 0}
    seen = set()
    for r in rows:
        k = (r["group"], r["key"])
        now = current.get(k)
        if now is None:
            continue
        seen.add(k)
        if (r["value"], r["sheet"]) != now[:2]:
            out["stale"] += 1
            r.update(value=now[0], sheet=now[1], note="")
            out["unreviewed"].append({x: r[x] for x in keep})
        elif r["mark"] == "ok":
            out["checked"] += 1
        elif r["mark"] == "wrong":
            out["disputed"].append({x: r[x] for x in keep})
        else:
            out["unreviewed"].append({x: r[x] for x in keep})
    for (grp, key), (value, sheet, item) in current.items():
        if (grp, key) not in seen:
            out["unreviewed"].append({"group": grp, "key": key, "sheet": sheet, "item": item, "value": value, "note": ""})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--s14")
    ap.add_argument("--group", nargs=2, action="append", default=[], metavar=("JSON", "DIR"))
    ap.add_argument("--update", action="append", default=[], metavar="TASKS_JSON")
    ap.add_argument("--decisions")
    ap.add_argument("--harness", default="not stated")
    ap.add_argument("--crop", nargs=3, action="append", default=[], metavar=("PNG", "TASK", "CAPTION"))
    a = ap.parse_args()
    for upd in a.update:
        if update_group(upd, a.group):
            return 2
    run = os.path.dirname(os.path.abspath(a.out))
    assets = os.path.join(run, "assets")
    os.makedirs(assets, exist_ok=True)
    evidence, tasks, findings, unclear, a1 = [], {}, [], [], []
    if a.s14:
        with open(a.s14, encoding="utf-8") as f:
            S14 = json.load(f)
        s14dir = os.path.dirname(os.path.abspath(a.s14))
        for e in S14["evidence"]:
            src = os.path.join(s14dir, "assets", e["file"])
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(assets, e["file"]))
                evidence.append(e)
        tasks["AUD-S14"] = S14["tasks"][0]
        findings += S14["findings"]
        unclear += S14["unclear"]
    version = "not read"
    group_ev = {}
    current = {}
    partial_tasks = []
    for gjson, gdir in a.group:
        with open(gjson, encoding="utf-8") as f:
            G = json.load(f)
        gname = G["project_info"]["group"].split()[0]
        if G["project_info"].get("partial"):
            partial_tasks += G["project_info"]["tasks"]
        for r in G.get("readings") or []:
            current[(gname, str(r.get("key") or ""))] = (str(r.get("value") or ""), str(r.get("sheet") or ""),
                                                        str(r.get("item") or ""))
        v = next((c for c in G["checks"] if c["id"] == "A03-L3"), None)
        if v and str(v.get("status")) == "PASS":
            version = str(v["actual"])
        evs = []
        for ext, kind in (("xlsx", "table"), ("html", "report")):
            pi = G["project_info"]
            hits = group_reports(gdir, gname, ext, pi["tasks"] if pi.get("partial") else None)
            if hits:
                shutil.copyfile(hits[-1], os.path.join(assets, os.path.basename(hits[-1])))
                eid = "ev-%s-%s" % (gname.lower(), kind)
                evidence.append({"id": eid, "file": os.path.basename(hits[-1]), "kind": kind, "audience": "both",
                                 "task": G["project_info"]["tasks"][0] if G["project_info"]["tasks"][0] != "AUD-A1" else "A1",
                                 "caption": "%s %s: %s" % (gname, "workbook" if kind == "table" else "detailed report",
                                                           ", ".join(t.replace("AUD-", "") for t in G["project_info"]["tasks"]))})
                evs.append(eid)
        by_task = {}
        for c in G["checks"]:
            by_task.setdefault(c["task"], []).append(c)
        for t, cs in by_task.items():
            if t == "AUD-A1":
                ma = {}
                for c in cs:
                    m = re.match(r"^(MA-[1-7]\.\d+)", c["id"])
                    if m:                      # non-MA ids (e.g. G2 door rows) are covered by MA-5.2
                        ma.setdefault(m.group(1), []).append(c)
                for mid, mc in ma.items():
                    a1.append({"id": mid, "title": mc[0]["item"], "result": worst([status_of(c) for c in mc]),
                               "evidence": "; ".join("%s: expected %s, actual %s" % (c["object"], c["expected"], c["actual"])
                                                     for c in mc[:8]),
                               "element_ids": [str(c["object_id"]) for c in mc if c.get("object_id")],
                               "clause": mc[0].get("cite", ""), "gap": None, "audience": "both"})
                continue
            group_ev.setdefault(t, set()).update(evs)
            name, clause, cat = card(t)
            l1 = [status_of(c) for c in cs if not re.search(L2_RE, c["id"])]
            l2 = [status_of(c) for c in cs if re.search(L2_RE, c["id"])]
            T = tasks.setdefault(t, {"id": t, "name": name, "clause": clause, "category": cat,
                                     "applicability": {"applicable": True}, "l1_status": "Not judged",
                                     "l2_status": "Not judged", "checks": [], "calcs": [], "evidence_ids": [],
                                     "finding_ids": [], "fix": [], "summary": ""})
            T["l1_status"] = worst([T["l1_status"]] + l1) if l1 else T["l1_status"]
            T["l2_status"] = worst([T["l2_status"]] + l2) if l2 else T["l2_status"]
            if all(c["status"] == "N/A" for c in cs):
                T["l1_status"] = T["l2_status"] = "N/A（附条件）"
                T["applicability"] = {"applicable": False, "reason": cs[0].get("evidence") or cs[0]["actual"],
                                      "conditions": cs[0].get("fix", ""), "ap_confirmed": None}
            for c in cs:
                row = {"id": c["id"], "item": "%s - %s" % (c["item"], c["object"]), "result": status_of(c),
                       "evidence": "expected %s; actual %s%s" % (c["expected"], c["actual"],
                                                                ("; " + c["evidence"]) if c.get("evidence") else ""),
                       "audience": "both"}
                if c.get("object_id"):
                    row["element_ids"] = [str(c["object_id"])]
                if re.search(L2_RE, c["id"]):
                    T["calcs"].append({"id": c["id"], "formula": "%s - %s" % (c["item"], c["object"]),
                                       "values": "expected %s; actual %s" % (c["expected"], c["actual"]),
                                       "limit": str(c["expected"]), "clause": c.get("cite", ""), "result": status_of(c),
                                       "basis": c.get("basis") or None, "audience": "both"})
                else:
                    T["checks"].append(row)
            groups = {}
            for c in cs:
                if c["status"] == "FAIL":
                    groups.setdefault(c["item"], []).append(c)
                elif c["status"] == "UNCLEAR":
                    src = "source" if re.search(r"missing|FS Code|reconstructed", c.get("cite", "")) else \
                        "data" if re.search(r"INP-|external|AP|manual", c.get("basis", "") + c.get("cite", "")) else "tool"
                    unclear.append({"task": t, "reason_kind": src, "detail": "%s - %s" % (c["item"], c["object"]),
                                    "need": c.get("fix") or c.get("basis") or "-", "gap": None})
            for item, gc in groups.items():
                fid = "F%d" % (max(int(x["id"][1:]) for x in findings if re.match(r"^F\d+$", x["id"])) + 1 if findings else 1)
                sev = max((severity(c) for c in gc), key=["Minor", "Major", "Blocker"].index)
                findings.append({
                    "id": fid, "task": t, "title": "%s: %d object%s" % (item, len(gc), "s" if len(gc) > 1 else ""),
                    "status": worst([status_of(c) for c in gc]), "severity": sev, "clause": gc[0].get("cite") or clause,
                    "evidence": [{"element_id": str(c["object_id"]) if c.get("object_id") else None,
                                  "value": "expected %s; actual %s" % (c["expected"], c["actual"]),
                                  "note": c["object"], "evidence_id": (evs or [None])[-1]} for c in gc[:6]],
                    "label": "FACT" if all(c.get("confidence", "high") == "high" for c in gc) else "INFERENCE",
                    "fix": gc[0].get("fix") or "", "fix_method": method_of(gc[0].get("fix")),
                    "overturn_if": "A reading or association marked medium / low is shown wrong on the drawings.", "gap": None})
                T["finding_ids"].append(fid)
                if gc[0].get("fix") and not any(x["text"] == gc[0]["fix"] for x in T["fix"]):
                    T["fix"].append({"text": gc[0]["fix"], "method": method_of(gc[0]["fix"]), "audience": "both"})
    for t, evs in group_ev.items():
        tasks[t]["evidence_ids"] = sorted(set(tasks[t]["evidence_ids"]) | evs)
    for png, task, cap in a.crop:
        eid = "ev-crop-%d" % (len([e for e in evidence if e["kind"] == "crop"]) + 1)
        shutil.copyfile(png, os.path.join(assets, os.path.basename(png)))
        evidence.append({"id": eid, "file": os.path.basename(png), "kind": "crop", "caption": cap, "task": task, "audience": "both"})
        if task in tasks:
            tasks[task]["evidence_ids"].append(eid)
    for T in tasks.values():
        n = {s: 0 for s in ("Pass", "Fail", "Unclear")}
        for c in T["checks"] + T["calcs"]:
            if c["result"] in n:
                n[c["result"]] += 1
        if not T.get("summary"):
            T["summary"] = "%d checks pass, %d fail, %d cannot be decided; details in the group report." % (n["Pass"], n["Fail"], n["Unclear"])
    blockers = [f for f in findings if f["severity"] == "Blocker"]
    majors = [f for f in findings if f["severity"] == "Major"]
    reasons = [{"text": f["title"] if "title" in f else f["id"], "finding_ids": [f["id"]]} for f in (blockers + majors)[:8]]
    dec = {"decisions": [], "inputs": []}
    if a.decisions:
        with open(a.decisions, encoding="utf-8") as f:
            dec.update(json.load(f))
    results = {
        "meta": {"project": a.project, "model": a.model, "revit_version": version + (" (read from the file header)"
                                                                                    if version != "not read" else ""),
                 "mcp": "revit-mcp (Experimental Technical Preview)", "harness": a.harness, "date": a.date,
                 "round": "Audit by group (G1–G6)%s" % ("; updated: " + ", ".join(
                     os.path.basename(u) for u in a.update) if a.update else ""),
                 "package_version": "Model Audit package 2026-10-14 (executable specs, --tasks)", "filled_by": "script"},
        "verdict": {"submittable": not blockers and not majors and not partial_tasks,
                    "summary": ("Partial audit: only %s checked, so this report cannot say whether the package can be "
                                "submitted. " % ", ".join(t.replace("AUD-", "") for t in partial_tasks) if partial_tasks else "")
                               + "%d tasks audited by measurement; %d findings (%d Blocker, %d Major). Group reports hold every check."
                               % (len(tasks), len(findings), len(blockers), len(majors)),
                    "reasons": reasons},
        "a1": a1, "tasks": sorted(tasks.values(), key=lambda t: t["id"]), "findings": findings,
        "decisions": dec["decisions"],
        "inputs": dec["inputs"],
        "unclear": unclear,
        "evidence": evidence,
    }
    gate = load_gate(os.path.dirname(os.path.abspath(a.out)), current)
    if gate:
        results["gate"] = gate
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("wrote %s: %d tasks, %d findings (%d Blocker, %d Major), %d unclear, %d A1 items, %d evidence"
          % (a.out, len(tasks), len(findings), len(blockers), len(majors), len(unclear), len(a1), len(evidence)))


if __name__ == "__main__":
    sys.exit(main())
