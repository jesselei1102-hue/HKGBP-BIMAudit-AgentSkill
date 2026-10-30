"""Render a Model Audit report (HTML) from audit-results.json.

python render_report.py --results audit-results.json --audience bim|ap --out report-<audience>.html

- Validates the results against templates/audit-results.schema.json (and finding.schema.json).
  Invalid data: prints "INVALID <path>: <reason>" lines, writes nothing, exit 2.
- Every evidence file must exist under <results dir>/assets/. Missing: "MISSING ASSET <file>", exit 3.
- Output is one HTML file that refers to assets/ by relative path; no network, no external CSS / JS / fonts.
- Styling and script come from templates/report-template.html (blocks report-css and report-js).
- Audience "bim" leads with the fix list: every failing object with its location plate (object, kind, sheet, Revit ID),
  Copy ID (for Revit's Select by ID), Copy for agent, and a Fixed mark kept in the browser.
- Audience "ap" omits element IDs, tool-like identifiers, GAP numbers and anything marked audience "bim",
  and puts the decisions and the information to supply right after the verdict.
- Sheet readings are listed as not checked by a person, with their crops.

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
SEV_RANK = {"Blocker": 0, "Major": 1, "Minor": 2, None: 3}
LABELS = {"bim": {"FACT": "FACT", "INFERENCE": "INFERENCE", "GAP": "GAP"},
          "ap": {"FACT": "Verified", "INFERENCE": "Inferred", "GAP": "Not determinable"}}
METHOD_EN = {"manual": "Manual (Revit)", "function-b": "Function B (model preparation)", "AP": "AP decision",
             "external": "External information"}
REASON_EN = {"source": "Source text not available", "data": "Project information not available",
             "tool": "Cannot be read by the tool"}
VIEW_TYPE = re.compile(r"\s*\([A-Z][A-Za-z]+\)$")   # a trailing Revit view-type enum such as "(FloorPlan)"
KIND_EN = {"sheet": "Sheet", "view": "View", "level": "Level", "scheme": "Area scheme", "schedule": "Schedule",
           "room": "Room", "element": "Element", None: "Object"}
ICON_COPY = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5">'
             '<rect x="5.5" y="5.5" width="8" height="8" rx="1.2"/><path d="M10.5 3.5v-.8a1.2 1.2 0 0 0-1.2-1.2H3.7'
             'a1.2 1.2 0 0 0-1.2 1.2v5.6a1.2 1.2 0 0 0 1.2 1.2h.8"/></svg>')
ICON_AGENT = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5">'
              '<path d="M2.5 3.5h11v7h-6l-3 2.5v-2.5h-2z" stroke-linejoin="round"/></svg>')
ICON_ARROW = ('<svg class="arrow" viewBox="0 0 14 10" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8">'
              '<path d="M1 5h11M8.5 1.5L12 5 8.5 8.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')


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
        for i in issues_of(results):
            if i.get("element_id"):
                ids.add(i["element_id"])
        self.ids = sorted((i for i in ids if i), key=len, reverse=True)
        self.tasks = {t["id"]: t for t in results["tasks"]}

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

    def tl(self, task_id):
        return task_id.replace("AUD-", "TL-") if task_id.startswith("AUD-") else task_id


def attr(s):
    return html.escape("" if s is None else str(s), quote=True)


def table(head, rows, sortable=False):
    th = "".join(f'<th{" class=\"sortable\"" if sortable else ""}>{h}</th>' for h in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def task_severity(r, t):
    sev = [f["severity"] for f in r["findings"] if f["id"] in t.get("finding_ids", [])]
    return min(sev, key=lambda s: SEV_RANK[s]) if sev else None


def task_order(task_id):
    m = re.match(r"AUD-([VSA])", task_id)
    return ({"V": 0, "S": 1, "A": 2}[m.group(1)] if m else 3, task_id)


def issues_of(r):
    """The fix list; older results without one get it from the findings' evidence (at most six objects each)."""
    if "issues" in r:
        return r["issues"]
    out = []
    for f in r.get("findings", []):
        for n, e in enumerate(f.get("evidence", [])):
            out.append({"id": "%s-%d" % (f["id"], n + 1), "finding_id": f["id"], "task": f["task"],
                        "tl": f["task"].replace("AUD-", "TL-"), "rule": f.get("title", ""), "action": "fix",
                        "status": f["status"], "severity": f["severity"], "object": e.get("note") or "", "kind": None,
                        "element_id": e.get("element_id"), "sheet": None, "id_from": None, "expected": "",
                        "actual": e.get("value") or "", "fix": f.get("fix") or "", "clause": f.get("clause", ""),
                        "audience": "both"})
    return out


def readings_of(r):
    """Sheet readings, none checked by a person; older results carry them in the old review record."""
    if "readings" in r:
        return r["readings"]
    g = r.get("gate") or {}
    return [{"group": x.get("group", ""), "key": x["key"], "sheet": x["sheet"], "item": x["item"], "value": x["value"],
             "crop": None} for x in g.get("unreviewed", []) + g.get("disputed", [])]


def verdict_state(r):
    v = r["verdict"]
    if (v.get("summary") or "").startswith("Partial audit"):
        return "partial", "Partial audit · readiness not judged"
    return ("ok", "Ready to submit") if v["submittable"] else ("", "Not ready to submit")


def agent_line(i):
    """One instruction the BIM team can paste to the agent: find the object, show it, propose the fix, ask first."""
    kind = KIND_EN.get(i.get("kind"), "Object").lower()
    where = f' (Revit ID {i["element_id"]})' if i.get("element_id") else ""
    on = f' on sheet {i["sheet"]}' if i.get("sheet") and i.get("kind") == "view" else ""
    what = f'expected {i["expected"]}, actual {i["actual"]}' if i.get("expected") or i.get("actual") else i.get("status", "")
    fix = f' Suggested fix: {i["fix"]}' if i.get("fix") else ""
    return (f'In the open Revit model, find the {kind} "{i["object"]}"{where}{on} and show it to me: open it if it is a '
            f'sheet or view, otherwise select it and zoom to it. GBP audit {i["tl"]} "{i["rule"]}": {what}.{fix} '
            f'Ask me before changing the model.')


def plate(i):
    """The street-name plate: object name above, kind · sheet · Revit ID below."""
    bits = [KIND_EN.get(i.get("kind"), "Object")]
    if i.get("sheet") and i.get("kind") == "view":
        bits.append("sheet " + html.escape(i["sheet"]))
    if i.get("element_id"):
        bits.append(f'ID <span class="plate-id">{html.escape(i["element_id"])}</span>')
    else:
        bits.append("no Revit ID · find by name")
    cls = "plate" + ("" if i.get("element_id") else " no-id")
    name = html.escape(VIEW_TYPE.sub("", i["object"] or "") or "—")   # "(FloorPlan)": the line below already says View
    return f'<span class="{cls}" title="{attr(i["object"])}"><span class="plate-name">{name}</span><span class="plate-line">{" · ".join(bits)}</span></span>'


def obj_row(c, i, n):
    """One object to fix or check: Fixed mark, plate, expected → actual, copy actions."""
    exp, act = c.text(i.get("expected")), c.text(i.get("actual"))
    what = (f'<span class="muted">expected</span> {exp} · <span class="muted">found</span> {act}' if exp and act
            else act or exp or c.text(i.get("status")))
    key = f'{i["id"]}#{n}'
    label = f'Mark {html.escape(i["object"] or "this object")} as fixed'
    copy_id = (f'<button type="button" class="btn" data-copy="{attr(i["element_id"])}" data-copied="Revit ID copied">{ICON_COPY}Copy ID</button>'
               if i.get("element_id") else
               f'<button type="button" class="btn" data-copy="{attr(i["object"])}" data-copied="Name copied">{ICON_COPY}Copy name</button>')
    agent = f'<button type="button" class="btn" data-copy="{attr(agent_line(i))}" data-copied="Instruction copied: paste it to the agent">{ICON_AGENT}Copy for agent</button>'
    text = attr(" ".join(str(i.get(k) or "") for k in ("object", "actual", "element_id", "sheet")).lower())
    return (f'<li class="obj" data-key="{attr(key)}" data-id="{attr(i.get("element_id") or "")}" data-kind="{attr(i.get("kind") or "")}" '
            f'data-text="{text}"><input type="checkbox" class="tick" aria-label="{label}">{plate(i)}'
            f'<span class="what">{what}</span><span class="acts">{copy_id}{agent}</span></li>')


def group_issues(issues, action):
    """Issues of one action grouped: by finding where there is one, else by task and rule; worst first."""
    groups = {}
    for n, i in enumerate(issues):
        if i["action"] != action:
            continue
        k = i.get("finding_id") or f'{i["task"]}|{i["tl"]}|{i["rule"]}'
        groups.setdefault(k, []).append((n, i))
    return sorted(groups.values(), key=lambda g: (SEV_RANK[g[0][1].get("severity")], task_order(g[0][1]["task"]), g[0][0]))


def finding_block(c, rows, action):
    head = rows[0][1]
    sev = head.get("severity") if action == "fix" else None
    sev_html = f'<span class="sev sev-{sev}">{sev}</span>' if sev else '<span class="sev sev-check">Check</span>'
    task = head["task"]
    name = c.tasks.get(task, {}).get("name", "")
    code = (f'<a class="code" href="#task-{attr(task)}">{html.escape(head["tl"])}</a>' if task in c.tasks
            else f'<span class="code">{html.escape(head["tl"])}</span>')
    n = len(rows)
    meta = [f'{n} object{"s" if n != 1 else ""}']
    if name:
        meta.append(c.text(name))
    if head.get("clause"):
        meta.append(c.text(head["clause"]))
    if head.get("finding_id"):
        meta.append(html.escape(head["finding_id"]))
    fixes = []
    for _, i in rows:
        if i.get("fix") and i["fix"] not in fixes:
            fixes.append(i["fix"])
    verb = "Fix" if action == "fix" else "Look at"
    fix_html = "".join(f'<p class="f-fix"><b>{verb}:</b> {c.text(f)}</p>' for f in fixes[:3])
    ids_btn = ('<span class="f-actions"><button type="button" class="btn" data-copy-ids>' + ICON_COPY + 'Copy IDs</button></span>'
               if any(i.get("element_id") for _, i in rows) else "")
    text = attr((head["rule"] + " " + " ".join(fixes) + " " + head["tl"]).lower())
    objs = "".join(obj_row(c, i, k) for k, i in rows)
    return (f'<article class="finding" data-sev="{attr(sev or "check")}" data-task="{attr(task)}" data-text="{text}">'
            f'<div class="f-head">{sev_html}<h3>{code} · {c.text(head["rule"])}</h3>{ids_btn}'
            f'<p class="f-meta">{" · ".join(meta)}</p>{fix_html}</div><ul class="objs">{objs}</ul></article>')


def evidence_html(c, ids):
    ev = {e["id"]: e for e in c.r["evidence"]}
    figs, links = [], []
    for i in ids:
        e = ev[i]
        if not c.show(e):
            continue
        href = "assets/" + html.escape(e["file"])
        cap = c.text(e["caption"])
        if e["kind"] in LINK_KINDS:
            links.append(f'<a href="{href}">{cap} ({LINK_KINDS[e["kind"]]})</a>')
        else:
            figs.append(f'<figure><a href="{href}"><img src="{href}" loading="lazy" alt="{cap}"></a><figcaption>{cap}</figcaption></figure>')
    out = ""
    if links:
        out += f'<p class="links">{"".join(links)}</p>'
    if figs:
        out += f'<div class="thumbs">{"".join(figs)}</div>'
    return out


LINK_KINDS = {"csv": "CSV", "table": "Excel workbook", "report": "detailed report"}


# ---------------------------------------------------------------- band (header)
def band(c, nav):
    m = c.r["meta"]
    state, label = verdict_state(c.r)
    sev = {s: sum(1 for f in c.r["findings"] if f["severity"] == s) for s in ("Blocker", "Major", "Minor")}
    count = " · ".join(f"{n} {s}" for s, n in sev.items() if n) or "no findings"
    aud = "AP / client edition" if c.ap else "BIM team edition"
    sub = " · ".join([f"GBP Model Audit · {aud}", c.text(m["date"]), c.text(m["model"])])
    links = "".join(f'<a href="#{sid}">{ICON_ARROW}{name}{f"<span class=num>{n}</span>" if n is not None else ""}</a>'
                    for sid, name, n in nav)
    return (f'<header class="band"><div class="band-in"><div><h1>{c.text(m["project"])}</h1><p class="sub">{sub}</p></div>'
            f'<div class="verdict-sign {state}"><span class="mark" aria-hidden="true"></span>{label}<span class="count">{count}</span></div>'
            f'<nav class="signs" aria-label="Sections">{links}</nav></div></header>')


# ---------------------------------------------------------------- BIM sections
def s_fix(c):
    issues = [i for i in issues_of(c.r) if i["action"] == "fix" and c.show(i)]
    groups = group_issues(issues, "fix")
    if not groups:
        return ('<section id="fix"><h2>Fix list</h2><p class="lead">Nothing failed in this audit. '
                'See <a href="#check">To check</a> for what a person still has to look at.</p></section>')
    by_sev = {s: sum(1 for i in issues if i.get("severity") == s) for s in ("Blocker", "Major", "Minor")}
    seg = (f'<button type="button" data-sev="" aria-pressed="true">All<span class="num">{len(issues)}</span></button>'
           + "".join(f'<button type="button" data-sev="{s}" aria-pressed="false">{s}<span class="num">{n}</span></button>'
                     for s, n in by_sev.items() if n))
    tasks = sorted({i["task"] for i in issues}, key=task_order)
    task_opts = "".join(f'<option value="{attr(t)}">{html.escape(c.tl(t))} {c.text(c.tasks.get(t, {}).get("name", ""))}</option>' for t in tasks)
    kinds = sorted({i.get("kind") for i in issues if i.get("kind")})
    kind_opts = "".join(f'<option value="{attr(k)}">{KIND_EN[k]}</option>' for k in kinds)
    with_id = sum(1 for i in issues if i.get("element_id"))
    bar = (f'<div class="toolbar" role="group" aria-label="Filter the fix list"><span class="seg">{seg}</span>'
           f'<select name="task" aria-label="Task"><option value="">All tasks</option>{task_opts}</select>'
           + (f'<select name="kind" aria-label="Object kind"><option value="">All kinds</option>{kind_opts}</select>' if kinds else "")
           + '<input type="search" name="q" placeholder="Search object, sheet, ID" aria-label="Search the fix list">'
           '<label><input type="checkbox" name="hidefixed">Hide fixed</label><span class="spacer"></span>'
           '<span class="progress" data-fixed-count></span>'
           f'<button type="button" class="btn primary" data-copy-ids>{ICON_COPY}Copy IDs in view</button></div>')
    lead = (f'<p class="lead">{len(issues)} object{"s" if len(issues) != 1 else ""} to fix in {len(groups)} finding'
            f'{"s" if len(groups) != 1 else ""}; {with_id} with a Revit ID. Paste IDs into Revit (Manage › Select by ID, '
            f'several at once separated by “;”), or copy one line for the agent. Fixed marks stay in this browser.</p>')
    body = "".join(finding_block(c, g, "fix") for g in groups)
    return (f'<section id="fix"><h2>Fix list</h2>{lead}{bar}{body}'
            '<p id="fix-empty" class="empty" hidden>Nothing matches these filters.</p></section>')


def readings_block(c):
    rs = readings_of(c.r)
    if not rs:
        return "<h3>Sheet readings</h3><p>No values were read off sheet images in this audit.</p>"
    cards = []
    for x in rs:
        img = (f'<a class="crop" href="assets/{attr(x["crop"])}" title="Open the crop full size">'
               f'<img src="assets/{attr(x["crop"])}" loading="lazy" alt="Crop of sheet {attr(x["sheet"])}: {attr(x["item"])}"></a>'
               if x.get("crop") else '<div class="nocrop">No crop</div>')
        conf = f' · confidence {html.escape(x["confidence"])}' if x.get("confidence") else ""
        key = "" if c.ap else f' · {html.escape(x["key"])}'
        cards.append(f'<figure class="reading">{img}<figcaption class="body"><div class="val num">{c.text(x["value"]) or "—"}</div>'
                     f'<div>{c.text(x["item"] or x["key"])}</div><div class="meta">Sheet {c.text(x["sheet"]) or "—"}{conf}{key}</div>'
                     '</figcaption></figure>')
    n = len(rs)
    return (f'<h3>Sheet readings</h3><p class="notice"><b>{n} value{"s" if n != 1 else ""} read off sheet images, '
            f'not checked by a person.</b> Compare each with its crop before relying on the results that use it.</p>'
            f'<div class="readings">{"".join(cards)}</div>')


def s_check(c):
    issues = [i for i in issues_of(c.r) if i["action"] == "check" and c.show(i)]
    out = ['<section id="check"><h2>To check by eye</h2><p class="lead">What the tool could not decide on its own. '
           'Unclear is not a pass.</p>', readings_block(c)]
    if c.ap:
        n = len(issues)
        out.append(f'<h3>Items the tool could not decide</h3><p>{n} item{"s" if n != 1 else ""}; the BIM team edition lists each with '
                   'what to look at.</p>' if n else "")
    elif issues:
        out.append("<h3>Items the tool could not decide</h3>" + "".join(finding_block(c, g, "check") for g in group_issues(issues, "check")))
    return "".join(out) + "</section>"


def model_health(c):
    rows = []
    for a in c.r["a1"]:
        if not c.show(a) or (c.ap and a["result"] not in ("Fail", "Partial", "Unclear")):
            continue
        row = [html.escape(a["id"]), c.text(a["title"]), c.chip(a["result"]), c.text(a.get("evidence")), c.text(a.get("clause"))]
        if not c.ap:
            row += [html.escape(", ".join(a.get("element_ids", []))), html.escape(a.get("gap") or "")]
        rows.append(row)
    head = ["MA", "Check", "Result", "Evidence", "Clause"] + ([] if c.ap else ["Element IDs", "Gap"])
    return (f'<h3 id="model-health">Model health</h3>' + (table(head, rows) if rows else "<p>No issues.</p>"))


def task_card(c, t):
    r = c.r
    sev = task_severity(r, t)
    parts = []
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
        parts.append("<p>Findings: " + ", ".join(html.escape(f) for f in t["finding_ids"]) + "</p>")
    fixes = [x for x in t.get("fix", []) if c.show(x)]
    if fixes:
        parts.append("<h3>Direction of fix</h3><ul>" + "".join(
            f'<li><span class="badge">{html.escape(METHOD_EN[x["method"]])}</span>{c.text(x["text"])}</li>' for x in fixes) + "</ul>")
    if t.get("overturn_if"):
        parts.append(f'<p class="muted">Would change if: {c.text(t["overturn_if"])}</p>')
    sev_html = f' <span class="sev sev-{sev}">{sev}</span>' if sev else ""
    return (f'<details class="task" id="task-{attr(t["id"])}" data-category="{attr(t["category"])}"><summary>'
            f'<span class="code">{html.escape(c.tl(t["id"]))}</span>'
            f'<span class="name">{c.text(t["name"])} <span class="muted">· {c.text(t["clause"])}</span>{sev_html}</span>'
            f'<span>L1 {c.chip(t["l1_status"])}</span><span>L2 {c.chip(t["l2_status"])}</span></summary>'
            f'<div class="inner">{"".join(parts)}</div></details>')


def s_tasks(c):
    ts = sorted(c.r["tasks"], key=lambda t: task_order(t["id"]))
    return ('<section id="tasks"><h2>Tasks</h2><p class="lead">Every task in this audit with its Layer 1 (presentation) and '
            'Layer 2 (compliance) result. Open a task for its checks, calculations and evidence.</p>'
            + model_health(c) + "<h3>Tasks</h3>" + "".join(task_card(c, t) for t in ts) + "</section>")


def decisions_html(c):
    rows = [(c.text(d["question"]), c.text("; ".join(d.get("options", [])) or "—"), html.escape(", ".join(d["tasks"])))
            for d in c.r["decisions"]]
    return table(["Question", "Options", "Affects"], rows) if rows else "<p>None.</p>"


def inputs_html(c):
    rows = [(c.text(i["item"]), html.escape(", ".join(i["tasks"]))) for i in c.r["inputs"]]
    return table(["Information", "Needed for"], rows) if rows else "<p>None.</p>"


def unclear_html(c):
    rows = [[html.escape(u["task"]), html.escape(REASON_EN[u["reason_kind"]]), c.text(u["detail"]), c.text(u["need"])]
            + ([] if c.ap else [html.escape(u.get("gap") or "")]) for u in c.r["unclear"]]
    head = ["Task", "Why", "Detail", "Needed"] + ([] if c.ap else ["Gap"])
    return table(head, rows) if rows else "<p>None.</p>"


def s_information(c):
    return ('<section id="information"><h2>Information</h2>'
            '<h3 id="decisions">Decisions the AP must make</h3>' + decisions_html(c)
            + '<h3 id="inputs">Information still required</h3>' + inputs_html(c)
            + '<h3 id="not-determinable">Not determinable</h3><p class="muted">Not determinable is not a pass.</p>'
            + unclear_html(c) + "</section>")


def s_na(c):
    rows = [[html.escape(c.tl(t["id"])), c.text(t["clause"]), c.text(t["applicability"].get("reason")),
             c.text(t["applicability"].get("conditions") or "—"), c.text(t["applicability"].get("ap_confirmed") or "pending")]
            for t in sorted(c.r["tasks"], key=lambda t: task_order(t["id"])) if not t["applicability"]["applicable"]]
    return ('<section id="na-table"><h2>Not applicable</h2><p class="lead">Each statement must also appear on the drawings.</p>'
            + (table(["Task", "Clause", "Reason", "Conditions", "AP confirmed"], rows) if rows else "<p>None.</p>") + "</section>")


def s_about(c):
    m = c.r["meta"]
    rows = [("Project", c.text(m["project"])), ("Model", c.text(m["model"])), ("Revit version", c.text(m.get("revit_version", "—"))),
            ("Date", c.text(m["date"])), ("Audit round", c.text(m["round"])),
            ("Method", c.text(m.get("package_version", "Model Audit package")))]
    if not c.ap:
        rows[3:3] = [("MCP", c.text(m.get("mcp", "—"))), ("Harness", c.text(m.get("harness", "—")))]
    note = ("This is a readiness audit of the BIM model against BIMGBPS 2019 and the cited legislation. "
            "It is not an approval by the Buildings Department or the Building Authority.")
    if c.ap:
        note += " It does not replace the professional judgement of the Authorized Person."
    filled = '<p class="muted"><b>Hand-filled from template.</b></p>' if m.get("filled_by") == "template" else ""
    out = [f'<section id="about" class="about"><h2>About this audit</h2><p>{html.escape(note)}</p>{filled}',
           table(["Item", "Value"], rows)]
    g = c.r.get("regression")
    if g:
        rows_ = [[html.escape(i["finding_id"]), c.text(i["before"]), html.escape(i["after"]), c.text(i.get("note"))] for i in g["items"]]
        out.append(f'<h3 id="regression">Compared with {c.text(g["previous_round"])}</h3>'
                   + table(["Finding", "Before", "Now", "Note"], rows_))
    clauses = sorted({t["clause"] for t in c.r["tasks"]} | {f["clause"] for f in c.r["findings"]})
    out.append("<h3>Clauses cited</h3><ul>" + "".join(f"<li>{c.text(x)}</li>" for x in clauses if x) + "</ul>")
    if not c.ap:
        rows_ = [[html.escape(e["id"]), html.escape(e["kind"]), f'<a href="assets/{html.escape(e["file"])}">{html.escape(e["file"])}</a>',
                  c.text(e["caption"]), html.escape(e["task"])] for e in c.r["evidence"]]
        out.append("<h3>Evidence index</h3>" + table(["ID", "Kind", "File", "Caption", "Task"], rows_, sortable=True))
        out.append(f'<h3>All findings</h3>' + findings_table(c))
    return "".join(out) + "</section>"


def findings_table(c):
    rows = []
    for f in sorted(c.r["findings"], key=lambda f: (SEV_RANK[f["severity"]], int(f["id"][1:]) if f["id"][1:].isdigit() else 0)):
        rows.append([f'<span data-key="{attr(f["id"])}">{html.escape(f["id"])}</span>',
                     f'<span class="sev sev-{f["severity"]}" data-key="{SEV_RANK[f["severity"]]}">{f["severity"]}</span>',
                     c.chip(f["status"]), html.escape(", ".join(c.tl(t) for t in [f["task"]] + f.get("tasks", []))),
                     c.text(f.get("title")), html.escape(LABELS[c.aud][f["label"]]), c.text(f.get("fix")),
                     html.escape(METHOD_EN.get(f.get("fix_method"), "—"))])
    head = ["ID", "Severity", "Status", "Tasks", "Finding", "Basis", "Fix", "By"]
    return table(head, rows, sortable=True) if rows else "<p>None.</p>"


# ---------------------------------------------------------------- AP sections
def s_verdict(c):
    v = c.r["verdict"]
    _, label = verdict_state(c.r)
    reasons = "".join(f"<li>{c.text(x['text'])}</li>" for x in v["reasons"][:5])
    return (f'<section id="verdict"><h2>{label}</h2>'
            + (f'<p class="lead">{c.text(v.get("summary"))}</p>' if v.get("summary") else "")
            + (f'<h3>Main reasons</h3><ol class="verdict-list">{reasons}</ol>' if reasons else "") + "</section>")


def s_problems(c):
    rows = []
    for t in sorted(c.r["tasks"], key=lambda t: task_order(t["id"])):
        fs = [f for f in c.r["findings"] if f["id"] in t.get("finding_ids", []) and f["status"] not in ("Pass",)]
        if not fs:
            continue
        what = "<br>".join(f'<span class="sev sev-{f["severity"]}">{f["severity"]}</span> {c.text(f.get("title"))} '
                           f'<span class="muted">({html.escape(LABELS["ap"][f["label"]])})</span>' for f in fs)
        fix = "<br>".join(c.text(x["text"]) for x in t.get("fix", []) if c.show(x)) or "—"
        rows.append([html.escape(c.tl(t["id"])), c.text(t["name"]), what, fix])
    return ('<section id="problems"><h2>Problems by task</h2><p class="lead">What is wrong in the model, task by task, and the '
            'direction of the fix. The BIM team edition lists every object to fix.</p>'
            + (table(["Task", "Name", "What is wrong", "Direction of fix"], rows) if rows else "<p>None.</p>") + "</section>")


# ---------------------------------------------------------------- page
def render(results, audience):
    c = Ctx(results, audience)
    tpl = (TEMPLATES / "report-template.html").read_text(encoding="utf-8-sig")
    css = re.search(r'^<style id="report-css">(.*?)^</style>', tpl, re.S | re.M).group(1)  # tags at line start, not in comments
    js = re.search(r'^<script id="report-js">(.*?)^</script>', tpl, re.S | re.M).group(1)
    issues = [i for i in issues_of(results) if c.show(i)]
    n_fix = sum(1 for i in issues if i["action"] == "fix")
    n_check = sum(1 for i in issues if i["action"] == "check") + len(readings_of(results))
    if c.ap:
        body = [s_verdict(c), f'<section id="decisions"><h2>Decisions required</h2><p class="lead">Decisions that only the AP '
                'can make. Where two bases are possible, both are computed in the task cards.</p>' + decisions_html(c) + "</section>",
                '<section id="inputs"><h2>Information required</h2>' + inputs_html(c) + "</section>",
                s_problems(c), s_check(c),
                '<section id="not-determinable"><h2>Not determinable</h2><p class="lead">Not determinable is not a pass.</p>'
                + unclear_html(c) + "</section>", s_na(c), s_about(c)]
        nav = [("verdict", "Verdict", None), ("decisions", "Decisions", len(results["decisions"]) or None),
               ("inputs", "Information required", len(results["inputs"]) or None), ("problems", "Problems", None),
               ("check", "To check", n_check or None), ("not-determinable", "Not determinable", len(results["unclear"]) or None),
               ("na-table", "N/A", None), ("about", "About", None)]
    else:
        body = [s_fix(c), s_check(c), s_tasks(c), s_information(c), s_na(c), s_about(c)]
        nav = [("fix", "Fix list", n_fix), ("check", "To check", n_check or None), ("tasks", "Tasks", len(results["tasks"])),
               ("information", "Information", None), ("na-table", "N/A", None), ("about", "About", None)]
    title = f'GBP Model Audit · {c.text(results["meta"]["project"])}'
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{title}</title><style>{css}</style></head><body>"
            + band(c, nav) + "<main>" + "".join(body) + f"</main><script>{js}</script></body></html>\n")


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
    missing += [x["crop"] for x in readings_of(results) if x.get("crop") and not (assets / x["crop"]).is_file()]
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
