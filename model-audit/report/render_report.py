"""Render a Model Audit report (HTML) from audit-results.json.

python render_report.py --results audit-results.json --audience bim|ap --out report-<audience>.html

- Validates the results against templates/audit-results.schema.json (and finding.schema.json).
  Invalid data: prints "INVALID <path>: <reason>" lines, writes nothing, exit 2.
- Every evidence file must exist under <results dir>/assets/. Missing: "MISSING ASSET <file>", exit 3.
- Output is one HTML file that refers to assets/ by relative path; no network, no external CSS / JS / fonts.
- Styling and script come from templates/report-template.html (blocks report-css and report-js).
- Audience "ap" omits element IDs, tool-like identifiers, GAP numbers and anything marked audience "bim",
  and puts "Decisions required" right after the Overview. See spec section 4.8 / README.

Python 3 standard library only.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
TEMPLATES = PKG / "templates"

STATUS_CLASS = {"Pass": "pass", "Partial": "partial", "Fail": "fail", "Missing": "missing", "N/A（附条件）": "na",
                "N/A 待声明": "na", "Unclear": "unclear", "Not judged": "nj"}
STATUS_EN = {"N/A（附条件）": "N/A (conditional)", "N/A 待声明": "N/A (not declared)"}
STATUS_ORDER = ["Pass", "Partial", "Fail", "Missing", "N/A（附条件）", "N/A 待声明", "Unclear", "Not judged"]
SEV_RANK = {"Blocker": 0, "Major": 1, "Minor": 2, None: 3}
LABELS = {"bim": {"FACT": "FACT", "INFERENCE": "INFERENCE", "GAP": "GAP"},
          "ap": {"FACT": "Verified", "INFERENCE": "Inferred", "GAP": "Not determinable"}}
METHOD_EN = {"manual": "Manual (Revit)", "function-b": "Function B (model preparation)", "AP": "AP decision",
             "external": "External information"}
REASON_EN = {"source": "Source text not available", "data": "Project information not available",
             "tool": "Cannot be read by the tool"}


# ---------------------------------------------------------------- validation
def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _type_ok(value, t):
    types = t if isinstance(t, list) else [t]
    checks = {"string": lambda v: isinstance(v, str), "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
              "integer": lambda v: isinstance(v, int) and not isinstance(v, bool), "boolean": lambda v: isinstance(v, bool),
              "array": lambda v: isinstance(v, list), "object": lambda v: isinstance(v, dict), "null": lambda v: v is None}
    return any(checks[x](value) for x in types)


def validate(value, schema, root, path="$", errors=None):
    """Subset of JSON Schema used by the package: type, required, enum, pattern, items, properties,
    additionalProperties (false), $ref (#/$defs/… or a sibling schema file)."""
    errors = [] if errors is None else errors
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/"):
            target = root
            for part in ref[2:].split("/"):
                target = target[part]
            return validate(value, target, root, path, errors)
        other = load_json(TEMPLATES / ref)
        return validate(value, other, other, path, errors)
    if "type" in schema and not _type_ok(value, schema["type"]):
        errors.append(f"{path}: expected {schema['type']}")
        return errors
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not one of {schema['enum']}")
    if "pattern" in schema and isinstance(value, str) and not re.match(schema["pattern"], value):
        errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                validate(sub, props[key], root, f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected field '{key}'")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            validate(item, schema["items"], root, f"{path}[{i}]", errors)
    return errors


def check_semantics(r):
    errors = []
    ev_ids = {e["id"] for e in r.get("evidence", [])}
    f_ids = {f["id"] for f in r.get("findings", [])}
    for i, t in enumerate(r.get("tasks", [])):
        if {t.get("l1_status"), t.get("l2_status")} & {"Fail", "Partial"} and not t.get("evidence_ids"):
            errors.append(f"$.tasks[{i}] ({t.get('id')}): status Fail/Partial but no evidence_ids")
        for e in t.get("evidence_ids", []):
            if e not in ev_ids:
                errors.append(f"$.tasks[{i}] ({t.get('id')}): evidence '{e}' not in evidence[]")
        for f in t.get("finding_ids", []):
            if f not in f_ids:
                errors.append(f"$.tasks[{i}] ({t.get('id')}): finding '{f}' not in findings[]")
    for i, reason in enumerate(r.get("verdict", {}).get("reasons", [])):
        for f in reason.get("finding_ids", []):
            if f not in f_ids:
                errors.append(f"$.verdict.reasons[{i}]: finding '{f}' not in findings[]")
    return errors


# ---------------------------------------------------------------- rendering helpers
class Ctx:
    def __init__(self, results, audience):
        self.r, self.aud = results, audience
        ids = set()
        for a in results["a1"]:
            ids.update(a.get("element_ids", []))
        for t in results["tasks"]:
            for c in t.get("checks", []):
                ids.update(c.get("element_ids", []))
        for f in results["findings"]:
            ids.update(e["element_id"] for e in f["evidence"] if e.get("element_id"))
        self.ids = sorted((i for i in ids if i), key=len, reverse=True)

    @property
    def ap(self):
        return self.aud == "ap"

    def show(self, item):
        return not (self.ap and item.get("audience") == "bim")

    def text(self, s):
        s = "" if s is None else str(s)
        if self.ap:
            for i in self.ids:
                s = re.sub(rf"(?<![0-9A-Za-z]){re.escape(i)}(?![0-9A-Za-z])", "—", s)
            s = re.sub(r"\bGAP-\d{2}\b", "", s)
            s = re.sub(r"\b[a-z]+(?:_[a-z0-9]+)+\b", "…", s)   # tool-like identifiers
        return html.escape(s)

    def chip(self, status):
        return f'<span class="st st-{STATUS_CLASS.get(status, "nj")}">{html.escape(STATUS_EN.get(status, status or "—"))}</span>'


def table(head, rows, sortable=False):
    th = "".join(f'<th{" class=\"sortable\"" if sortable else ""}>{h}</th>' for h in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def task_severity(r, t):
    sev = [f["severity"] for f in r["findings"] if f["id"] in t.get("finding_ids", [])]
    return min(sev, key=lambda s: SEV_RANK[s]) if sev else None


def task_order(t):
    return ({"V": 0, "S": 1, "A": 2}[t["id"][4]], t["id"])


# ---------------------------------------------------------------- sections
def s_cover(c):
    m = c.r["meta"]
    rows = [("Model", c.text(m["model"])), ("Revit version", c.text(m.get("revit_version", "—"))),
            ("Date", c.text(m["date"])), ("Audit round", c.text(m["round"])),
            ("Method", c.text(m.get("package_version", "Model Audit package")))]
    if not c.ap:
        rows[2:2] = [("MCP", c.text(m.get("mcp", "—"))), ("Harness", c.text(m.get("harness", "—")))]
    note = ("This is a readiness audit of the BIM model against BIMGBPS 2019 and the cited legislation. "
            "It is not an approval by the Buildings Department or the Building Authority.")
    if c.ap:
        note += " It does not replace the professional judgement of the Authorized Person."
    filled = '<p class="muted"><b>Hand-filled from template.</b></p>' if m.get("filled_by") == "template" else ""
    aud = "AP / client edition" if c.ap else "BIM team edition"
    return (f'<section id="cover"><h1>{c.text(m["project"])}</h1><p class="muted">GBP Model Audit report · {aud}</p>'
            + table(["Item", "Value"], rows) + f"<p>{html.escape(note)}</p>{filled}</section>")


def s_overview(c):
    r, v = c.r, c.r["verdict"]
    ok = v["submittable"]
    reasons = "".join(f"<li>{c.text(x['text'])}"
                      + (f' <span class="muted">({", ".join(map(html.escape, x.get("finding_ids", [])))})</span>' if x.get("finding_ids") else "")
                      + "</li>" for x in v["reasons"][:3])
    out = [f'<section id="overview"><h2>Overview</h2><div class="verdict{" ok" if ok else ""}">'
           f'<b>Can be submitted as is: {"Yes" if ok else "No"}</b>'
           f'{"<p>" + c.text(v.get("summary")) + "</p>" if v.get("summary") else ""}<ol>{reasons}</ol></div>']
    for layer, key in (("Layer 1 (presentation)", "l1_status"), ("Layer 2 (compliance)", "l2_status")):
        counts = {s: sum(1 for t in r["tasks"] if t[key] == s) for s in STATUS_ORDER}
        cards = "".join(f'<div class="card">{c.chip(s)}<div class="n">{n}</div></div>' for s, n in counts.items() if n)
        out.append(f"<h3>{layer}</h3><div class=\"cards\">{cards}</div>")
    sev = {s: sum(1 for f in r["findings"] if f["severity"] == s) for s in ("Blocker", "Major", "Minor")}
    out.append('<h3>Findings by severity</h3><div class="cards">'
               + "".join(f'<div class="card"><span class="sev sev-{s}">{s}</span><div class="n">{n}</div></div>' for s, n in sev.items())
               + "</div>")
    cells = "".join(f'<a class="cell" href="#task-{t["id"]}"><b>{t["id"]}</b>{c.text(t["name"])}<br>'
                    f'L1 {c.chip(t["l1_status"])} L2 {c.chip(t["l2_status"])}</a>'
                    for t in sorted(r["tasks"], key=task_order))
    out.append(f'<h3>All tasks</h3><div class="grid">{cells}</div>')
    blockers = [f for f in r["findings"] if f["severity"] == "Blocker"]
    if blockers:
        out.append("<h3>Blockers</h3><ul>" + "".join(
            f'<li><b>{f["id"]}</b> {c.text(f.get("title", ""))} <span class="muted">({", ".join([f["task"]] + f.get("tasks", []))})</span></li>'
            for f in blockers) + "</ul>")
    out.append(gate_note(c))
    return "".join(out) + "</section>"


NOT_REVIEWED = {"failures": "failures", "check_yourself": "items to check yourself", "inputs": "missing inputs"}


def gate_note(c):
    """Review state from the audit window: the sheet readings, and review lists not looked at; nothing without it."""
    g = c.r.get("gate")
    if not g:
        return ""
    skipped = [NOT_REVIEWED[k] for k in g.get("not_reviewed", []) if k in NOT_REVIEWED]
    extra = ("<p><b>Not looked at before the reports: %s.</b></p>" % html.escape(", ".join(skipped))) if skipped else ""
    return readings_note(c) + extra


def readings_note(c):
    """Sheet readings part of the review state."""
    g = c.r.get("gate")
    if not g:
        return ""
    unrev, disp = g["unreviewed"], g["disputed"]
    plural = lambda n: "reading was" if n == 1 else "readings were"
    row = lambda x: (html.escape(x["item"] or x["key"]), html.escape(x["sheet"]), html.escape(x["value"]),
                     html.escape(x["key"]))
    if not unrev and not disp and not g["checked"]:
        return "<h3>Sheet readings</h3><p>No sheet readings were taken in this audit.</p>"
    if not unrev and not disp:
        return (f'<h3>Sheet readings</h3><p>All {g["checked"]} sheet {"reading was" if g["checked"] == 1 else "readings were"}'
                f' checked by the operator ({html.escape(g["saved"])}).</p>')
    out = ['<h3>Sheet readings</h3><div class="verdict">']
    if unrev:
        stale = g.get("stale", 0)
        out.append(f"<p><b>{len(unrev)} sheet {plural(len(unrev))} not checked by a person.</b> "
                   + (f"{stale} {'reading' if stale == 1 else 'readings'} changed after the review. " if stale else "")
                   + "Check these values on the sheets before relying on the results that use them.</p>"
                   + table(["Item", "Sheet", "Value", "Key"], [row(x) for x in unrev]))
    if disp:
        out.append("<p><b>Marked wrong by the operator</b></p>"
                   + table(["Item", "Sheet", "Value", "Key", "Operator note"],
                           [row(x) + (html.escape(x["note"]) or "—",) for x in disp]))
    return "".join(out) + "</div>"


def s_decisions(c):
    rows = [(c.text(d["question"]), c.text("; ".join(d.get("options", [])) or "—"), html.escape(", ".join(d["tasks"])))
            for d in c.r["decisions"]]
    intro = ("Decisions that only the AP can make. Where two bases are possible, both are computed in the task cards."
             if c.ap else "Open AP decisions (project input list).")
    return (f'<section id="decisions"><h2>Decisions required</h2><p class="muted">{intro}</p>'
            + (table(["Question", "Options", "Affects"], rows) if rows else "<p>None.</p>") + "</section>")


def s_inputs(c):
    rows = [(c.text(i["item"]), html.escape(", ".join(i["tasks"]))) for i in c.r["inputs"]]
    return ('<section id="inputs"><h2>Information required</h2>'
            + (table(["Information", "Needed for"], rows) if rows else "<p>None.</p>") + "</section>")


def s_model_health(c):
    rows = []
    for a in c.r["a1"]:
        if not c.show(a) or (c.ap and a["result"] not in ("Fail", "Partial", "Unclear")):
            continue
        row = [html.escape(a["id"]), c.text(a["title"]), c.chip(a["result"]), c.text(a.get("evidence")), c.text(a.get("clause"))]
        if not c.ap:
            row += [html.escape(", ".join(a.get("element_ids", []))), html.escape(a.get("gap") or "")]
        rows.append(row)
    head = ["MA", "Check", "Result", "Evidence", "Clause"] + ([] if c.ap else ["Element IDs", "Gap"])
    note = '<p class="muted">Only items that failed or could not be determined are listed.</p>' if c.ap else ""
    return f'<section id="model-health"><h2>Model health</h2>{note}' + (table(head, rows) if rows else "<p>No issues.</p>") + "</section>"


LINK_KINDS = {"csv": "CSV", "table": "Excel workbook", "report": "detailed report"}


def evidence_html(c, ids):
    ev = {e["id"]: e for e in c.r["evidence"]}
    figs = []
    for i in ids:
        e = ev[i]
        if not c.show(e):
            continue
        href = "assets/" + html.escape(e["file"])
        cap = c.text(e["caption"])
        if e["kind"] in LINK_KINDS:
            figs.append(f'<figure><a href="{href}">{cap} ({LINK_KINDS[e["kind"]]})</a></figure>')
        else:
            figs.append(f'<figure><a href="{href}"><img src="{href}" loading="lazy" alt="{cap}"></a><figcaption>{cap}</figcaption></figure>')
    return f'<div class="thumbs">{"".join(figs)}</div>' if figs else ""


def s_tasks(c):
    r = c.r
    out = ['<section id="tasks"><h2>Task breakdown</h2><div class="filters">'
           '<select name="category"><option value="">All categories</option><option>View</option><option>Schedule</option><option>Assembly</option></select>'
           '<select name="status"><option value="">All statuses</option>'
           + "".join(f'<option value="{STATUS_CLASS[s]}">{html.escape(STATUS_EN.get(s, s))}</option>' for s in STATUS_ORDER if s != "N/A 待声明")
           + '</select><select name="severity"><option value="">All severities</option><option>Blocker</option><option>Major</option><option>Minor</option></select></div>']
    for t in sorted(r["tasks"], key=task_order):
        sev = task_severity(r, t)
        st = f'{STATUS_CLASS[t["l1_status"]]} {STATUS_CLASS[t["l2_status"]]}'
        parts = [f'<div class="task" id="task-{t["id"]}" data-category="{t["category"]}" data-status="{st}" data-severity="{sev or ""}">'
                 f'<h3>{t["id"]} {c.text(t["name"])} <span class="muted">· {c.text(t["clause"])}</span></h3>'
                 f'<p>L1 {c.chip(t["l1_status"])} L2 {c.chip(t["l2_status"])}'
                 + (f' <span class="sev sev-{sev}">{sev}</span>' if sev else "") + "</p>"]
        if t.get("summary"):
            parts.append(f"<p>{c.text(t['summary'])}</p>")
        ap_ = t["applicability"]
        if not ap_["applicable"]:
            parts.append(f'<p><b>Not applicable.</b> {c.text(ap_.get("reason"))} '
                         f'<span class="muted">Conditions: {c.text(ap_.get("conditions") or "—")}</span></p>')
        checks = [x for x in t.get("checks", []) if c.show(x)]
        if checks:
            head = ["Check", "Item", "Result", "Evidence"] + ([] if c.ap else ["Element IDs"])
            rows = [[html.escape(x["id"]), c.text(x["item"]), c.chip(x["result"]), c.text(x.get("evidence"))]
                    + ([] if c.ap else [html.escape(", ".join(x.get("element_ids", [])))]) for x in checks]
            parts.append("<h3>Layer 1 checks</h3>" + table(head, rows))
        calcs = [x for x in t.get("calcs", []) if c.show(x)]
        if calcs:
            rows = [[c.text(x["formula"]), c.text(x.get("values")), c.text(x.get("limit")), c.text(x.get("clause")),
                     c.chip(x["result"]), c.text(x.get("basis") or "—")] for x in calcs]
            parts.append("<h3>Layer 2 calculations</h3>" + table(["Formula", "Values", "Limit", "Clause", "Result", "Basis"], rows))
        ev = evidence_html(c, t.get("evidence_ids", []))
        if ev:
            parts.append("<h3>Evidence</h3>" + ev)
        if t.get("finding_ids"):
            parts.append("<p>Findings: " + ", ".join(f'<a href="#finding-{html.escape(f)}">{html.escape(f)}</a>' for f in t["finding_ids"]) + "</p>")
        fixes = [x for x in t.get("fix", []) if c.show(x)]
        if fixes:
            parts.append("<h3>Direction of fix</h3><ul>" + "".join(
                f'<li><span class="badge">{html.escape(METHOD_EN[x["method"]])}</span>{c.text(x["text"])}</li>' for x in fixes) + "</ul>")
        if t.get("overturn_if"):
            parts.append(f'<p class="muted">Would change if: {c.text(t["overturn_if"])}</p>')
        out.append("".join(parts) + "</div>")
    return "".join(out) + "</section>"


def s_findings(c):
    rows = []
    for f in sorted(c.r["findings"], key=lambda f: (SEV_RANK[f["severity"]], int(f["id"][1:]))):
        ev = "; ".join(" ".join(x for x in ([e.get("element_id")] if not c.ap else []) + [e.get("value"), e.get("note")] if x)
                       for e in f["evidence"])
        rows.append([f'<span id="finding-{f["id"]}" data-key="{int(f["id"][1:]):04d}">{f["id"]}</span>',
                     f'<span class="sev sev-{f["severity"]}" data-key="{SEV_RANK[f["severity"]]}">{f["severity"]}</span>',
                     c.chip(f["status"]), html.escape(", ".join([f["task"]] + f.get("tasks", []))), c.text(f.get("title")),
                     c.text(ev), html.escape(LABELS[c.aud][f["label"]]), c.text(f.get("fix")),
                     html.escape(METHOD_EN.get(f.get("fix_method"), "—"))])
    head = ["ID", "Severity", "Status", "Tasks", "Finding", "Evidence", "Basis", "Fix", "By"]
    return '<section id="findings"><h2>Findings</h2>' + (table(head, rows, sortable=True) if rows else "<p>None.</p>") + "</section>"


def s_action_plan(c):
    r = c.r
    items = []
    for t in r["tasks"]:
        for x in t.get("fix", []):
            if c.show(x):
                items.append((SEV_RANK[task_severity(r, t)], t["id"], x))
    items.sort(key=lambda i: (i[0], i[1]))

    def group(title, methods):
        lis = "".join(f'<li><b>{tid}</b> {c.text(x["text"])}</li>' for _, tid, x in items if x["method"] in methods)
        return f"<h3>{title}</h3><ul>{lis}</ul>" if lis else ""

    out = ['<section id="action-plan"><h2>Action plan</h2><p class="muted">Ordered by severity within each group.</p>']
    if c.ap:
        out += [group("AP decisions", {"AP"}), '<p>See also <a href="#decisions">Decisions required</a>.</p>',
                group("External information", {"external"}), '<p>See also <a href="#inputs">Information required</a>.</p>',
                group("Model corrections by the BIM team", {"manual", "function-b"})]
    else:
        out += [group("Manual (Revit)", {"manual"}), group("Function B (model preparation)", {"function-b"}),
                group("AP decisions", {"AP"}), s_decisions(c), group("External information", {"external"})]
    return "".join(out) + "</section>"


def s_na(c):
    rows = [[html.escape(t["id"]), c.text(t["clause"]), c.text(t["applicability"].get("reason")),
             c.text(t["applicability"].get("conditions") or "—"), c.text(t["applicability"].get("ap_confirmed") or "pending")]
            for t in sorted(c.r["tasks"], key=task_order) if not t["applicability"]["applicable"]]
    return ('<section id="na-table"><h2>N/A table</h2><p class="muted">Each statement must also appear on the drawings.</p>'
            + (table(["Task", "Clause", "Reason", "Conditions", "AP confirmed"], rows) if rows else "<p>None.</p>") + "</section>")


def s_unclear(c):
    rows = [[html.escape(u["task"]), html.escape(REASON_EN[u["reason_kind"]]), c.text(u["detail"]), c.text(u["need"])]
            + ([] if c.ap else [html.escape(u.get("gap") or "")]) for u in c.r["unclear"]]
    head = ["Task", "Why", "Detail", "Needed"] + ([] if c.ap else ["Gap"])
    out = ['<section id="not-determinable"><h2>Not determinable</h2><p class="muted">Not determinable is not a pass.</p>'
           + (table(head, rows) if rows else "<p>None.</p>")]
    if not c.ap and c.r["inputs"]:
        out.append("<h3>Project information still required</h3>"
                   + table(["Input", "Information", "Needed for"],
                           [[html.escape(i["id"]), c.text(i["item"]), html.escape(", ".join(i["tasks"]))] for i in c.r["inputs"]]))
    return "".join(out) + "</section>"


def s_regression(c):
    g = c.r.get("regression")
    if not g:
        return ""
    rows = [[html.escape(i["finding_id"]), c.text(i["before"]), html.escape(i["after"]), c.text(i.get("note"))] for i in g["items"]]
    return (f'<section id="regression"><h2>Regression comparison</h2><p class="muted">Against {c.text(g["previous_round"])}.</p>'
            + table(["Finding", "Before", "Now", "Note"], rows) + "</section>")


def s_appendix(c):
    clauses = sorted({t["clause"] for t in c.r["tasks"]} | {f["clause"] for f in c.r["findings"]})
    out = ['<section id="appendix"><h2>Appendix</h2><h3>Clauses cited</h3><ul>'
           + "".join(f"<li>{c.text(x)}</li>" for x in clauses) + "</ul>"]
    if not c.ap:
        rows = [[html.escape(e["id"]), html.escape(e["kind"]), f'<a href="assets/{html.escape(e["file"])}">{html.escape(e["file"])}</a>',
                 c.text(e["caption"]), html.escape(e["task"])] for e in c.r["evidence"]]
        out.append("<h3>Evidence index</h3>" + table(["ID", "Kind", "File", "Caption", "Task"], rows, sortable=True))
        out.append(f'<p class="muted">Method: {c.text(c.r["meta"].get("package_version", "—"))}; '
                   f'capability binding: {c.text(c.r["meta"].get("mcp", "—"))}.</p>')
    return "".join(out) + "</section>"


def render(results, audience):
    c = Ctx(results, audience)
    tpl = (TEMPLATES / "report-template.html").read_text(encoding="utf-8-sig")
    css = re.search(r'^<style id="report-css">(.*?)^</style>', tpl, re.S | re.M).group(1)  # tags at line start, not in comments
    js = re.search(r'^<script id="report-js">(.*?)^</script>', tpl, re.S | re.M).group(1)
    if c.ap:
        body = [s_cover(c), s_overview(c), s_decisions(c), s_inputs(c), s_model_health(c), s_tasks(c), s_findings(c),
                s_action_plan(c), s_na(c), s_unclear(c), s_regression(c), s_appendix(c)]
        nav = ["cover", "overview", "decisions", "inputs", "model-health", "tasks", "findings", "action-plan", "na-table", "not-determinable"]
    else:
        body = [s_cover(c), s_overview(c), s_model_health(c), s_tasks(c), s_findings(c), s_action_plan(c), s_na(c),
                s_unclear(c), s_regression(c), s_appendix(c)]
        nav = ["cover", "overview", "model-health", "tasks", "findings", "action-plan", "na-table", "not-determinable"]
    if results.get("regression"):
        nav.append("regression")
    nav.append("appendix")
    names = {"cover": "Cover", "overview": "Overview", "decisions": "Decisions", "inputs": "Information required",
             "model-health": "Model health", "tasks": "Tasks", "findings": "Findings", "action-plan": "Action plan",
             "na-table": "N/A", "not-determinable": "Not determinable", "regression": "Regression", "appendix": "Appendix"}
    title = f'GBP Model Audit · {c.text(results["meta"]["project"])}'
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{title}</title><style>{css}</style></head><body>"
            "<header class=\"top\"><nav>" + "".join(f'<a href="#{n}">{names[n]}</a>' for n in nav) + "</nav></header>"
            "<main>" + "".join(body) + f"</main><script>{js}</script></body></html>\n")


# ---------------------------------------------------------------- main
def main(argv):
    p = argparse.ArgumentParser(description="Render a Model Audit report from audit-results.json.")
    p.add_argument("--results", required=True)
    p.add_argument("--audience", required=True, choices=["bim", "ap"])
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        results = load_json(a.results)
    except (OSError, json.JSONDecodeError) as e:
        print(f"INVALID $: cannot read results ({e})")
        return 2
    schema = load_json(TEMPLATES / "audit-results.schema.json")
    errors = validate(results, schema, schema)
    if not errors:
        errors = check_semantics(results)
    if errors:
        for e in errors:
            print(f"INVALID {e}")
        return 2
    assets = Path(a.results).resolve().parent / "assets"
    missing = [e["file"] for e in results["evidence"] if not (assets / e["file"]).is_file()]
    if missing:
        for m in missing:
            print(f"MISSING ASSET {m}")
        return 3
    out = Path(a.out)
    out.write_text(render(results, a.audience), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
