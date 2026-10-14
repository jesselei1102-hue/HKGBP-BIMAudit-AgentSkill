#!/usr/bin/env python3
"""TL-S14 report: Excel (6 sheets) + self-contained HTML, from the analysis JSON only.

Never queries Revit. Usage:
  python report.py --analysis C14_analysis_<project>.json --outdir <dir> [--date YYYYMMDD]
Writes GBP_TL-S14_LV_Compliance_<project>_<date>.xlsx and .html.
Stdlib only. Exit 0 = written, 2 = analysis JSON missing or invalid.
"""
import argparse
import datetime
import html
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from xlsx_lite import Cell, Workbook  # noqa: E402

REQUIRED = ["project_info", "level_correspondence", "rooms_included", "rooms_excluded", "rooms_pending",
            "rooms_no_area", "openings_all", "openings_unassigned", "openings_fire_service", "summary"]
DISCLAIMER = ("Automated pre-check generated from the Revit model for internal review. "
              "It is not a Building Authority approval and does not replace the Authorized Person's own verification.")


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        print("ERROR: cannot read analysis JSON: %s" % e, file=sys.stderr)
        sys.exit(2)
    miss = [k for k in REQUIRED if k not in d]
    if miss:
        print("ERROR: analysis JSON missing sections: %s" % ", ".join(miss), file=sys.stderr)
        sys.exit(2)
    return d


def pf(v):
    """Pass / Fail / N/A cell."""
    if v is True:
        return Cell("Pass", fill="pass")
    if v is False:
        return Cell("Fail", fill="fail")
    return Cell("N/A", fill="na")


def status_cell(s):
    return Cell(s, fill={"PASS": "pass", "FAIL": "fail", "FAIL*": "fail"}.get(s, "na"))


def r3(v):
    return None if v is None else round(float(v), 3)


def type_key(o):
    return o["type"]


def build_rows(d):
    """All table content, shared by Excel and HTML (one source of truth)."""
    T = {}
    # 1 Room L&V Compliance
    head = ["Room ID", "Room", "No.", "Level", "Area (m²)", "Rule", "Light ratio", "Req. light (m²)",
            "Act. light (m²)", "Light margin (m²)", "Light", "Vent ratio", "Req. vent (m²)", "Act. vent (m²)",
            "Vent margin (m²)", "Vent", "Louvre, not counted (m²)", "Overall", "Basis"]
    rows = []
    for r in d["rooms_included"]:
        rows.append([r["id"], r["name"], r["number"], r["level"], r3(r["area_sqm"]), r["rule_cite"],
                     r["light_ratio"], r3(r["req_light_sqm"]), r3(r["act_light_sqm"]), r3(r["light_margin_sqm"]),
                     r["light_pass"], r["vent_ratio"], r3(r["req_vent_sqm"]), r3(r["act_vent_sqm"]),
                     r3(r["vent_margin_sqm"]), r["vent_pass"], r3(r["act_louvre_sqm"]), r["status"],
                     r["classification_reason"]])
    for r in d["rooms_pending"]:
        rows.append([r["id"], r["name"], r["number"], r["level"], r3(r["area_sqm"]), "Pending", "", None, None,
                     None, None, "", None, None, None, None, None, "N/A", r["classification_reason"]])
    T["compliance"] = (head, rows)

    # 2 Opening Detail (walls, their panels, fire-service windows)
    head = ["Opening ID", "Host wall", "Category", "Type", "Mark", "Level", "Area (m²)", "Classification",
            "Facing", "Glass (m²)", "Openable (m²)", "Louvre (m²)", "Top above FFL (m)", "Counted light",
            "Counted vent", "Matched room", "Match method", "Confidence", "Note"]
    rows = []
    for o in d["openings_all"]:
        rows.append([o["id"], "", o["category"], o["type"], o["mark"], o["level"], r3(o["area_sqm"]),
                     o["classification"], o["facing"], r3(o["glass_sqm"]), r3(o["openable_sqm"]),
                     r3(o["louvre_sqm"]), None, o["counted_lighting"], o["counted_ventilation"],
                     o["matched_room_name"] or ("; ".join(o["adjacent_room_names"]) and
                                                "adjacent: " + "; ".join(o["adjacent_room_names"])) or "",
                     o["match_method"], o["match_confidence"] or "", o["assumption_note"]])
        for p in o["panels"]:
            rows.append([p["id"], o["id"], "Curtain Panels", p["type"], "", o["level"], r3(p["area_sqm"]),
                         p["kind"], o["facing"], None, r3(p["area_sqm"]) if p["kind"].startswith("openable") else None,
                         r3(p["area_sqm"]) if p["kind"] == "louvre" else None, r3(p["top_above_ffl_m"]), None,
                         p["counted_ventilation"], o["matched_room_name"] or "", "centre inside host wall bbox",
                         "", p["top_source"]])
    for f in d["openings_fire_service"]:
        rows.append([f["id"], "", f["category"], f["family"] + " " + f["type"], f["mark"], f["level"],
                     r3(f["area_sqm"]), f["classification"], "", None, None, None, None, False, False, "", "",
                     "", f["assumption_note"]])
    T["openings"] = (head, rows)

    # 3 Room Opening Breakdown
    head = ["Room ID", "Room", "Level", "Opening ID", "Type", "Mark", "Facing", "Share", "Glass (m²)",
            "Counted light (m²)", "Counted vent (m²)", "Louvre (m²)", "Counted", "Method", "Confidence"]
    rows = []
    for r in d["rooms_included"]:
        if not r["matched_openings"]:
            rows.append([r["id"], r["name"] + " " + r["number"], r["level"], "(none)", "No opening found next to this room",
                         "", "", None, 0.0, 0.0, 0.0, 0.0, False, "", ""])
        for m in r["matched_openings"]:
            rows.append([r["id"], r["name"] + " " + r["number"], r["level"], m["id"], m["type"], m["mark"],
                         m["facing"], r3(m["share"]), r3(m["glass_sqm"]), r3(m["counted_light_sqm"]),
                         r3(m["counted_vent_sqm"]), r3(m["louvre_sqm"]), m["counted"], m["match_method"],
                         m["match_confidence"] or ""])
    T["breakdown"] = (head, rows)

    # 4 Opening Type Summary
    groups = {}
    for o in d["openings_all"]:
        g = groups.setdefault(("Curtain wall", o["type"]), [0, 0.0, 0, 0.0, 0.0])
        g[0] += 1
        g[1] += o["area_sqm"]
        if o["counted_lighting"]:
            g[2] += 1
            g[3] += o["glass_sqm"]
        for p in o["panels"]:
            k = ("Panel - " + p["kind"], p["type"])
            g2 = groups.setdefault(k, [0, 0.0, 0, 0.0, 0.0])
            g2[0] += 1
            g2[1] += p["area_sqm"]
            if p["counted_ventilation"]:
                g2[2] += 1
                g2[4] += p["area_sqm"]
    for f in d["openings_fire_service"]:
        g = groups.setdefault(("Window - fire service", f["type"]), [0, 0.0, 0, 0.0, 0.0])
        g[0] += 1
        g[1] += f["area_sqm"]
    head = ["Kind", "Type", "Count", "Total area (m²)", "Counted (count)", "Counted light (m²)", "Counted vent (m²)"]
    rows = [[k[0], k[1], v[0], r3(v[1]), v[2], r3(v[3]), r3(v[4])] for k, v in sorted(groups.items())]
    T["types"] = (head, rows)

    # 5 Summary
    s, pi = d["summary"], d["project_info"]
    rows = [["Project", pi["project_name"]], ["Model", pi["model_path"]], ["Analysis date", pi["analysis_date"]],
            ["Rule - reg 30", pi["rules"]["reg30"]], ["Rule - reg 36", pi["rules"]["reg36"]],
            ["Rule - opening top", pi["rules"]["opening_top"]], ["Erratum", pi["rules"]["erratum"]]]
    for k, v in s.items():
        if k != "data_quality_warnings":
            rows.append([k.replace("_", " "), v])
    for i, w in enumerate(s["data_quality_warnings"], 1):
        rows.append(["Warning %d" % i, w])
    for lc in d["level_correspondence"]:
        rows.append(["Level correspondence", "%s -> %s" % (lc["room_level"] or "(no room level)",
                                                           ", ".join(lc["opening_levels_matched_by_geometry"]) or "(none)")])
    rows.append(["Disclaimer", DISCLAIMER])
    T["summary"] = (["Item", "Value"], rows)

    # 6 Excluded Rooms (+ no area)
    head = ["Room ID", "Room", "No.", "Level", "Area (m²)", "Group", "Reason"]
    rows = [[r["id"], r["name"], r["number"], r["level"], r3(r["area_sqm"]), "Excluded", r["classification_reason"]]
            for r in d["rooms_excluded"]]
    rows += [[r["id"], r["name"], r["number"], r["level"], r3(r["area_sqm"]), "No area", r["classification_reason"]]
             for r in d["rooms_no_area"]]
    T["excluded"] = (head, rows)

    # 7 Schedule vs Model (only when the analysis carries a schedule comparison)
    sc = d.get("schedule_comparison")
    if sc:
        head = ["Level", "Room", "Room ID", "Window mark", "Table area (m²)", "Notional area", "Table req. glass (m²)",
                "Exact req. glass (m²)", "Table req. openable (m²)", "Exact req. openable (m²)", "Table provided",
                "Measured glass (m²)", "Measured openable (m²)", "Model status", "Issues"]
        rows = [[r["level"], r["name"], r["room_id"], r["window_mark"], r3(r["table_area_sqm"]),
                 r["table_notional_area"] or "", r3(r["table_req_light_sqm"]), r3(r["exact_req_light_sqm"]),
                 r3(r["table_req_vent_sqm"]), r3(r["exact_req_vent_sqm"]), r["table_provided_text"],
                 r3(r["measured_light_sqm"]), r3(r["measured_vent_sqm"]), r["model_status"] or "",
                 "; ".join(r["issues"])] for r in sc["rows"]]
        rows += [[m["level"], m["name"] + " " + m["number"], m["id"], "", None, "", None, None, None, None,
                  "(not in table)", None, None, m["status"], "Assessed room missing from the model schedule"]
                 for m in sc["missing_rooms"]]
        T["schedule"] = (head, rows)
    return T


SHEETS = [("compliance", "Room L&V Compliance", [10, 18, 6, 15, 10, 22, 8, 11, 11, 11, 8, 8, 11, 11, 11, 8, 12, 9, 50]),
          ("openings", "Opening Detail", [10, 10, 16, 28, 6, 15, 9, 30, 12, 9, 9, 9, 9, 8, 8, 18, 40, 9, 60]),
          ("breakdown", "Room Opening Breakdown", [10, 20, 15, 10, 26, 6, 12, 7, 9, 10, 10, 9, 8, 40, 10]),
          ("types", "Opening Type Summary", [22, 30, 8, 12, 12, 12, 12]),
          ("summary", "Summary", [32, 110]),
          ("excluded", "Excluded Rooms", [10, 18, 6, 15, 10, 10, 70]),
          ("schedule", "Schedule vs Model", [14, 20, 10, 8, 10, 16, 10, 10, 10, 10, 30, 10, 10, 10, 90])]


def write_xlsx(T, path):
    wb = Workbook()
    for key, name, widths in SHEETS:
        if key not in T:
            continue
        head, rows = T[key]
        ws = wb.sheet(name, widths)
        ws.row(head, header=True)
        for row in rows:
            out = []
            for h, v in zip(head, row):
                if h in ("Light", "Vent", "Counted light", "Counted vent", "Counted"):
                    out.append(pf(v))
                elif h in ("Overall", "Model status"):
                    out.append(status_cell(v))
                else:
                    out.append(v)
            ws.row(out)
    wb.save(path)


def h(v):
    return html.escape("" if v is None else str(v))


def cell_html(head, v):
    if head in ("Light", "Vent", "Counted light", "Counted vent", "Counted"):
        t = "Pass" if v is True else "Fail" if v is False else "N/A"
        if head.startswith("Counted"):
            t = "Yes" if v is True else "No" if v is False else "-"
        return '<td class="%s">%s</td>' % ("p" if v is True else "f" if v is False else "n", t)
    if head in ("Overall", "Model status"):
        return '<td class="%s">%s</td>' % ({"PASS": "p", "FAIL": "f", "FAIL*": "f"}.get(v, "n"), h(v))
    if isinstance(v, float):
        return '<td class="num" data-v="%r">%.3f</td>' % (v, v)
    if isinstance(v, int) and not isinstance(v, bool):
        return '<td class="num" data-v="%d">%d</td>' % (v, v)
    return "<td>%s</td>" % h(v)


def table_html(head, rows, tid):
    out = ['<div class="tw"><table class="sortable" id="%s"><thead><tr>' % tid]
    out += ['<th data-col="%d">%s</th>' % (i, h(c)) for i, c in enumerate(head)]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(cell_html(hd, v) for hd, v in zip(head, r)) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--mut:#5f5f5a;--line:#deded8;--pass:#c6efce;--passi:#0b5d1e;
--fail:#ffc7ce;--faili:#8a1020;--na:#ffeb9c;--nai:#6b5200;--acc:#1f4e79}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--card:#1f1f1e;--ink:#ececE8;
--mut:#a5a59f;--line:#3a3a37;--pass:#173d22;--passi:#a6e3b5;--fail:#4a1d22;--faili:#ffb3bd;--na:#463c12;--nai:#f3dc8a;--acc:#8ab4e0}}
:root[data-theme="dark"]{--bg:#161615;--card:#1f1f1e;--ink:#ecece8;--mut:#a5a59f;--line:#3a3a37;--pass:#173d22;
--passi:#a6e3b5;--fail:#4a1d22;--faili:#ffb3bd;--na:#463c12;--nai:#f3dc8a;--acc:#8ab4e0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 48px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px}
.sub{color:var(--mut);margin:0 0 18px}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}.card b{display:block;font-size:24px}
.card span{color:var(--mut);font-size:12px}.card.p b{color:var(--passi)}.card.f b{color:var(--faili)}.card.n b{color:var(--nai)}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:12.5px}th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card);cursor:pointer;white-space:nowrap;user-select:none}th:after{content:" \\2195";color:var(--mut);font-size:10px}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}td.p{background:var(--pass);color:var(--passi);font-weight:600}
td.f{background:var(--fail);color:var(--faili);font-weight:600}td.n{background:var(--na);color:var(--nai)}
details{margin-top:10px}summary{cursor:pointer;font-weight:600;padding:6px 0}ul.w{padding-left:18px}ul.w li{margin:4px 0}
.bar{display:flex;height:14px;border-radius:7px;overflow:hidden;border:1px solid var(--line);margin:6px 0 2px}
.bar i{display:block}.bar .p{background:var(--passi)}.bar .f{background:var(--faili)}.bar .n{background:var(--nai)}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--line);color:var(--mut);font-size:12px}
.tools{float:right}.tools button{font:inherit;font-size:12px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:3px 8px;cursor:pointer}
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
document.getElementById('theme').addEventListener('click',function(){var r=document.documentElement;
var d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme: dark)').matches);r.dataset.theme=d?'light':'dark'});
"""


def write_html(d, T, path):
    s, pi = d["summary"], d["project_info"]
    inc = s["rooms_included_count"]
    bp, lf, vf = s["both_pass_count"], s["lighting_fail_count"], s["ventilation_fail_count"]
    fail_rooms = [r for r in d["rooms_included"] if r["status"] != "PASS"]
    nfail = len(fail_rooms)
    npend = s["rooms_pending_count"]
    tot = inc + npend or 1
    cards = [("p", bp, "rooms pass both (of %d assessed)" % inc), ("f", nfail, "rooms fail"),
             ("n", npend, "rooms pending classification"), ("", s["rooms_excluded_count"], "rooms excluded"),
             ("", s["total_openings_glazing_louvre"], "curtain-wall openings"),
             ("", s["openings_counted_lighting"], "counted for lighting"),
             ("n", s["openings_unassigned_count"], "openings not assigned"),
             ("", s["openings_fire_service_count"], "fire-service windows (excluded)")]
    o = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>S14 Lighting Ventilation</title><style>%s</style></head><body><main>" % CSS,
         '<div class="tools"><button id="theme" type="button">Light / dark</button></div>',
         "<h1>TL-S14 Lighting &amp; Ventilation check</h1>",
         '<p class="sub">%s &middot; analysed %s &middot; %s</p>' % (h(pi["project_name"]), h(pi["analysis_date"]),
                                                                    "reg 30: glass 1/10, openable 1/16 &middot; reg 36: glass 1/10, openable 1/10"),
         '<div class="cards">' + "".join('<div class="card %s"><b>%s</b><span>%s</span></div>' % (c, h(v), h(t))
                                          for c, v, t in cards) + "</div>",
         '<div class="bar" title="pass / fail / pending"><i class="p" style="width:%.1f%%"></i><i class="f" style="width:%.1f%%"></i>'
         '<i class="n" style="width:%.1f%%"></i></div><span class="sub">%d pass &middot; %d fail &middot; %d pending '
         "(lighting fails %d, ventilation fails %d)</span>"
         % (100 * bp / tot, 100 * nfail / tot, 100 * npend / tot, bp, nfail, npend, lf, vf)]
    if fail_rooms:
        o.append("<h2>What fails and why</h2><ul class=\"w\">")
        for r in fail_rooms:
            why = []
            if not r["light_pass"]:
                why.append("glass %.3f m² vs %.3f m² required" % (r["act_light_sqm"], r["req_light_sqm"]))
            if not r["vent_pass"]:
                why.append("openable %.3f m² vs %.3f m² required" % (r["act_vent_sqm"], r["req_vent_sqm"]))
            ext = [m for m in r["matched_openings"] if m["facing"] == "external"]
            hint = ("no external window found next to the room" if not ext else
                    "external openings found but not enough area")
            internal = [m["id"] for m in r["matched_openings"] if m["facing"].startswith("internal")]
            if internal:
                hint += "; internal glazing %s is not a window to external air" % internal
            near = r.get("glazing_beyond_boundary") or []
            if near:
                hint += ("; fix direction: external glazing %s (%.3f m² glass, %.3f m² openable) lies about %.1f m "
                         "beyond the room boundary with no room in between - check whether the room boundary stops "
                         "short of the facade, or whether that strip is a separate space"
                         % ([n["id"] for n in near], sum(n["glass_sqm"] for n in near),
                            sum(n["openable_sqm"] for n in near), max(n["distance_m"] for n in near)))
            elif not ext and r["rule"] == "reg36":
                hint += ("; fix direction: reg 36(1) requires a window or lantern light for a room with soil fitments - "
                         "provide one, or the AP seeks a modification (s.42) relying on mechanical ventilation")
            elif not ext:
                hint += "; fix direction: provide external windows, or confirm with the AP that reg 30 does not apply to this use"
            o.append("<li><b>%s %s</b> (%s, %.3f m²): %s &mdash; %s.</li>"
                     % (h(r["name"]), h(r["number"]), h(r["level"]), r["area_sqm"], h("; ".join(why)), h(hint)))
        o.append("</ul>")
    if "schedule" in T:
        sc = d["schedule_comparison"]
        o.append("<h2>Model schedule vs measured geometry</h2>")
        o.append('<p class="sub">%s %d of %d table rows have issues; %d assessed rooms are not in the table.</p>'
                 % (h(sc["note"]), sum(1 for r in sc["rows"] if r["issues"]), len(sc["rows"]), len(sc["missing_rooms"])))
        o.append(table_html(*T["schedule"], tid="t-sched"))
    o.append("<h2>Room compliance</h2>")
    o.append(table_html(*T["compliance"], tid="t-comp"))
    o.append("<h2>Openings per room</h2>")
    o.append(table_html(*T["breakdown"], tid="t-break"))
    o.append("<h2>Opening types</h2>")
    o.append(table_html(*T["types"], tid="t-types"))
    o.append("<details><summary>Opening detail &mdash; %d rows (walls, their panels, fire-service windows)</summary>"
             % len(T["openings"][1]))
    o.append(table_html(*T["openings"], tid="t-open"))
    o.append("</details>")
    o.append("<details><summary>Excluded rooms &mdash; %d</summary>" % len(T["excluded"][1]))
    o.append(table_html(*T["excluded"], tid="t-exc"))
    o.append("</details>")
    o.append("<h2>Method, limits and warnings</h2><ul class=\"w\">")
    for w in s["data_quality_warnings"]:
        o.append("<li>%s</li>" % h(w))
    o.append("<li>%s</li>" % h(pi["rules"]["erratum"]))
    o.append("</ul>")
    o.append("<footer>%s Source data: %s.</footer>" % (h(DISCLAIMER), h(os.path.basename(pi["model_path"]))))
    o.append("<script>%s</script></main></body></html>" % JS)
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--date")
    a = ap.parse_args()
    d = load(a.analysis)
    T = build_rows(d)
    date = a.date or datetime.date.today().strftime("%Y%m%d")
    base = "GBP_TL-S14_LV_Compliance_%s_%s" % (d["project_info"]["project_name"], date)
    os.makedirs(a.outdir, exist_ok=True)
    xp = os.path.join(a.outdir, base + ".xlsx")
    hp = os.path.join(a.outdir, base + ".html")
    write_xlsx(T, xp)
    write_html(d, T, hp)
    print("wrote %s" % xp)
    print("wrote %s" % hp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
