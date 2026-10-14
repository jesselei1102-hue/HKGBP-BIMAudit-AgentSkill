#!/usr/bin/env python3
"""Generic task-group report: Excel + self-contained HTML from a task-analysis JSON (templates/task-analysis.schema.json).

Never queries Revit.  Usage:
  python task_report.py --analysis <G?_analysis.json> --outdir <dir> [--name RoomUse] [--date YYYYMMDD]
Writes GBP_<group>_<name>_<project>_<date>.xlsx and .html.  Stdlib only.  Exit 0 = written, 2 = invalid JSON.
"""
import argparse
import base64
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx_lite import Cell, Workbook  # noqa: E402

REQUIRED = ["project_info", "checks", "tables", "summary"]
CHECK_FIELDS = ["id", "task", "item", "object", "expected", "actual", "status"]
STATUS_FILL = {"PASS": "pass", "FAIL": "fail", "UNCLEAR": "na", "N/A": "na", "APPLICABLE": "na", "INFO": "na"}
STATUS_CLS = {"PASS": "p", "FAIL": "f"}
DISCLAIMER = ("Automated pre-check generated from the Revit model for internal review. "
              "It is not a Building Authority approval and does not replace the Authorized Person's own verification.")


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        die("cannot read analysis JSON: %s" % e)
    miss = [k for k in REQUIRED if k not in d]
    if miss:
        die("analysis JSON missing sections: " + ", ".join(miss))
    for i, c in enumerate(d["checks"]):
        m = [k for k in CHECK_FIELDS if k not in c]
        if m:
            die("check %d (%s) missing fields: %s" % (i, c.get("id"), ", ".join(m)))
    return d


def task_status(cs):
    st = {c["status"] for c in cs}
    for s in ("FAIL", "UNCLEAR", "APPLICABLE", "N/A"):
        if s in st:
            return s
    return "PASS"


def by_task(d):
    out = {}
    for c in d["checks"]:
        out.setdefault(c["task"], []).append(c)
    return out


def val(v):
    if isinstance(v, float):
        return round(v, 3)
    return v


CHECK_HEAD = ["Task", "Check ID", "Item", "Object", "Expected", "Actual", "Status", "Severity / basis", "Clause",
              "Method", "Confidence", "Evidence", "Fix direction"]


def check_row(c):
    return [c["task"], c["id"], c["item"], c["object"], val(c["expected"]), val(c["actual"]), c["status"],
            c.get("basis", ""), c.get("cite", ""), c.get("method", ""), c.get("confidence", ""),
            c.get("evidence", ""), c.get("fix", "")]


def write_xlsx(d, path):
    wb = Workbook()
    bt = by_task(d)
    ws = wb.sheet("Task Summary", [12, 12, 8, 8, 10, 8, 60])
    ws.row(["Task", "Status", "PASS", "FAIL", "UNCLEAR", "N/A", "First failing item"], header=True)
    for t, cs in bt.items():
        st = task_status(cs)
        cnt = lambda s: sum(1 for c in cs if c["status"] == s)
        first = next((c for c in cs if c["status"] == "FAIL"), None)
        ws.row([t, Cell(st, fill=STATUS_FILL.get(st)), cnt("PASS"), cnt("FAIL"), cnt("UNCLEAR"), cnt("N/A"),
                "%s: %s" % (first["object"], first["item"]) if first else ""])
    ws = wb.sheet("Checks", [10, 18, 34, 30, 22, 22, 9, 12, 26, 34, 9, 34, 50])
    ws.row(CHECK_HEAD, header=True)
    for c in d["checks"]:
        r = check_row(c)
        r[6] = Cell(c["status"], fill=STATUS_FILL.get(c["status"]))
        ws.row(r)
    for key, t in d["tables"].items():
        ws = wb.sheet(t["title"][:31], [max(8, min(40, len(str(h)) + 4)) for h in t["columns"]])
        ws.row(t["columns"], header=True)
        for row in t["rows"]:
            ws.row([Cell(v, fill=STATUS_FILL[v]) if isinstance(v, str) and v in STATUS_FILL else val(v) for v in row])
    if d.get("readings"):
        ws = wb.sheet("Readings", [22, 14, 40, 9, 11, 40, 50])
        ws.row(["Key", "Sheet", "Value read", "Finding", "Confidence", "Note", "Crop file"], header=True)
        for r in d["readings"]:
            ws.row([r["key"], r.get("sheet", ""), r.get("value", ""), r.get("finding") or "-", r.get("confidence", ""),
                    r.get("note", ""), r.get("crop") or "no crop"])
    ws = wb.sheet("Summary", [30, 110])
    ws.row(["Item", "Value"], header=True)
    pi = d["project_info"]
    for k in ("project_name", "model_path", "group", "analysis_date", "building_use"):
        if k in pi:
            ws.row([k.replace("_", " "), pi[k]])
    for k, v in pi.get("rules", {}).items():
        ws.row(["Rule - " + k, v])
    for i, w in enumerate(d["summary"].get("data_quality_warnings", []), 1):
        ws.row(["Warning %d" % i, w])
    ws.row(["Disclaimer", DISCLAIMER])
    wb.save(path)


def h(v):
    return html.escape("" if v is None else str(val(v)))


def td(v, head=""):
    if head == "Status" or (isinstance(v, str) and v in STATUS_FILL and head in ("Status", "")):
        return '<td class="%s">%s</td>' % (STATUS_CLS.get(v, "n"), h(v))
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return '<td class="num" data-v="%r">%s</td>' % (v, h(v))
    return "<td>%s</td>" % h(v)


def table_html(head, rows, tid):
    o = ['<div class="tw"><table class="sortable" id="%s"><thead><tr>' % tid]
    o += ['<th data-col="%d">%s</th>' % (i, h(c)) for i, c in enumerate(head)]
    o.append("</tr></thead><tbody>")
    for r in rows:
        o.append("<tr>" + "".join(td(v, hd) for hd, v in zip(head, r)) + "</tr>")
    o.append("</tbody></table></div>")
    return "".join(o)


CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--mut:#5f5f5a;--line:#deded8;--pass:#c6efce;--passi:#0b5d1e;
--fail:#ffc7ce;--faili:#8a1020;--na:#ffeb9c;--nai:#6b5200}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--card:#1f1f1e;--ink:#ecece8;
--mut:#a5a59f;--line:#3a3a37;--pass:#173d22;--passi:#a6e3b5;--fail:#4a1d22;--faili:#ffb3bd;--na:#463c12;--nai:#f3dc8a}}
:root[data-theme="dark"]{--bg:#161615;--card:#1f1f1e;--ink:#ecece8;--mut:#a5a59f;--line:#3a3a37;--pass:#173d22;
--passi:#a6e3b5;--fail:#4a1d22;--faili:#ffb3bd;--na:#463c12;--nai:#f3dc8a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 48px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:30px 0 10px}
h3{font-size:15px;margin:18px 0 6px}.sub{color:var(--mut);margin:0 0 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--line);border-radius:8px;padding:10px 12px}
.card.f{border-left-color:var(--faili)}.card.p{border-left-color:var(--passi)}.card.n{border-left-color:var(--nai)}
.card b{display:block;font-size:16px}.card span{color:var(--mut);font-size:12px}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:12.5px}th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card);cursor:pointer;white-space:nowrap;user-select:none}th:after{content:" \\2195";color:var(--mut);font-size:10px}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}td.p{background:var(--pass);color:var(--passi);font-weight:600}
td.f{background:var(--fail);color:var(--faili);font-weight:600}td.n{background:var(--na);color:var(--nai)}
details{margin-top:10px}summary{cursor:pointer;font-weight:600;padding:6px 0}ul.w{padding-left:18px}ul.w li{margin:4px 0}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0}.filters select,.tools button{font:inherit;font-size:12px;border:1px solid var(--line);
background:var(--card);color:var(--ink);border-radius:6px;padding:3px 8px}.tools{float:right}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--line);color:var(--mut);font-size:12px}
"""

JS = """
document.querySelectorAll('table.sortable th').forEach(function(th){th.addEventListener('click',function(){
var t=th.closest('table'),b=t.tBodies[0],i=+th.dataset.col,asc=th.dataset.dir!=='asc';
t.querySelectorAll('th').forEach(function(x){delete x.dataset.dir});th.dataset.dir=asc?'asc':'desc';
var rows=[].slice.call(b.rows);rows.sort(function(a,c){var x=a.cells[i],y=c.cells[i];
var xv=x.dataset.v!==undefined?+x.dataset.v:x.textContent.trim(),yv=y.dataset.v!==undefined?+y.dataset.v:y.textContent.trim();
if(xv===''&&yv!=='')return 1;if(yv===''&&xv!=='')return -1;
if(typeof xv==='number'&&typeof yv==='number')return asc?xv-yv:yv-xv;return asc?String(xv).localeCompare(yv):String(yv).localeCompare(xv)});
rows.forEach(function(r){b.appendChild(r)})})});
function flt(){var t=document.getElementById('ft').value,s=document.getElementById('fs').value;
document.querySelectorAll('#t-checks tbody tr').forEach(function(r){var ok=(!t||r.cells[0].textContent===t)&&(!s||r.cells[6].textContent===s);
r.style.display=ok?'':'none'})}
['ft','fs'].forEach(function(i){var e=document.getElementById(i);if(e)e.addEventListener('change',flt)});
document.getElementById('theme').addEventListener('click',function(){var r=document.documentElement;
var d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme: dark)').matches);r.dataset.theme=d?'light':'dark'});
"""


def write_html(d, path, title):
    pi, s = d["project_info"], d["summary"]
    bt = by_task(d)
    o = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>%s</title><style>%s</style></head><body><main>" % (h(title), CSS),
         '<div class="tools"><button id="theme" type="button">Light / dark</button></div>',
         "<h1>%s</h1>" % h(title),
         '<p class="sub">%s &middot; analysed %s &middot; %d checks</p>' % (h(pi["project_name"]), h(pi["analysis_date"]),
                                                                          len(d["checks"])),
         '<div class="cards">']
    for t, cs in bt.items():
        st = task_status(cs)
        cls = {"PASS": "p", "FAIL": "f"}.get(st, "n")
        cnt = lambda x: sum(1 for c in cs if c["status"] == x)
        o.append('<div class="card %s"><b>%s</b><span>%s &middot; %d pass, %d fail, %d unclear</span></div>'
                 % (cls, h(t), h(st), cnt("PASS"), cnt("FAIL"), cnt("UNCLEAR")))
    o.append("</div>")
    o.append("<h2>What fails or cannot be decided, and how to fix it</h2>")
    for t, cs in bt.items():
        bad = [c for c in cs if c["status"] in ("FAIL", "UNCLEAR")]
        na = [c for c in cs if c["status"] in ("N/A", "APPLICABLE")]
        if not bad and not na:
            continue
        o.append("<h3>%s</h3><ul class=\"w\">" % h(t))
        groups = {}
        for c in bad + na:
            groups.setdefault((c["status"], c["item"], c.get("fix", "")), []).append(c)
        for (st, item, fix), cs2 in groups.items():
            objs = ", ".join(sorted({c["object"] for c in cs2}))
            ex = cs2[0]
            o.append("<li><b>[%s] %s</b> &mdash; %s. <i>Expected</i> %s; <i>actual</i> %s.%s%s</li>"
                     % (h(st), h(item), h(objs[:400] + (" …" if len(objs) > 400 else "")), h(ex["expected"]), h(ex["actual"]),
                        (" <i>Fix:</i> " + h(fix)) if fix else "",
                        (" <i>Evidence:</i> " + h(ex.get("evidence"))) if ex.get("evidence") else ""))
        o.append("</ul>")
    rd = d.get("readings") or []
    if rd:
        o.append("<h2>Sheet readings to check</h2><p class=\"sub\">Values and judgements read off the sheet images. "
                 "Compare each with its crop before accepting the result: a PASS judgement with no crop is not used, "
                 "and a value that disagrees with the model is FAIL only with a crop.</p>")
        rows_html = []
        for r in rd:
            img = "no crop"
            if r.get("crop") and os.path.exists(r["crop"]):
                with open(r["crop"], "rb") as f:
                    img = '<img alt="%s" style="max-width:360px;max-height:180px;border:1px solid #888" ' \
                          'src="data:image/png;base64,%s">' % (h(r["key"]), base64.b64encode(f.read()).decode("ascii"))
            rows_html.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                             % (h(r["key"]), h(r.get("sheet")), h(r.get("value")), h(r.get("finding") or "-"),
                                h(r.get("confidence")), h(r.get("note")), img))
        o.append('<div class="tw"><table><thead><tr><th>Key</th><th>Sheet</th><th>Value read</th><th>Finding</th>'
                 '<th>Confidence</th><th>Note</th><th>Crop</th></tr></thead><tbody>%s</tbody></table></div>'
                 % "".join(rows_html))
    o.append("<h2>All checks</h2>")
    o.append('<div class="filters"><select id="ft"><option value="">All tasks</option>%s</select>'
             '<select id="fs"><option value="">All statuses</option>%s</select></div>'
             % ("".join("<option>%s</option>" % h(t) for t in bt),
                "".join("<option>%s</option>" % h(x) for x in ("PASS", "FAIL", "UNCLEAR", "N/A"))))
    o.append(table_html(CHECK_HEAD, [check_row(c) for c in d["checks"]], "t-checks"))
    for key, t in d["tables"].items():
        o.append("<details><summary>%s &mdash; %d rows</summary>" % (h(t["title"]), len(t["rows"])))
        o.append(table_html(t["columns"], t["rows"], "t-" + re.sub(r"\W", "", key)))
        o.append("</details>")
    o.append("<h2>Method, limits and warnings</h2><ul class=\"w\">")
    for k, v in pi.get("rules", {}).items():
        o.append("<li><b>%s</b>: %s</li>" % (h(k), h(v)))
    for w in s.get("data_quality_warnings", []):
        o.append("<li>%s</li>" % h(w))
    o.append("</ul><footer>%s Source data: %s.</footer>" % (h(DISCLAIMER), h(os.path.basename(pi["model_path"]))))
    o.append("<script>%s</script></main></body></html>" % JS)
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--date")
    a = ap.parse_args()
    d = load(a.analysis)
    pi = d["project_info"]
    grp = pi.get("group", "G").split()[0]
    name = a.name or re.sub(r"\W+", "", " ".join(pi.get("group", "").split()[1:]).title()) or "Audit"
    if pi.get("partial"):                       # run with --tasks: the file says which tasks it holds
        name = "-".join(t[4:] for t in pi["tasks"])
    date = a.date or datetime.date.today().strftime("%Y%m%d")
    base = "GBP_%s_%s_%s_%s" % (grp, name, pi["project_name"], date)
    os.makedirs(a.outdir, exist_ok=True)
    xp, hp = os.path.join(a.outdir, base + ".xlsx"), os.path.join(a.outdir, base + ".html")
    write_xlsx(d, xp)
    title = "%s %s check" % (grp, " / ".join(t.replace("AUD-", "") for t in pi.get("tasks", [])))
    write_html(d, hp, title)
    print("wrote " + xp)
    print("wrote " + hp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
