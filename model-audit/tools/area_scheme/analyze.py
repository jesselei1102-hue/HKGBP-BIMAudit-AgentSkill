#!/usr/bin/env python3
"""G3 area-scheme group: AUD-S02 site area, AUD-V09 / S05 SC and PR, AUD-V10 / S08 / S07 GFA and concessions,
AUD-V11 UFA, AUD-V12 UFS, AUD-V14 SBD greenery, AUD-V06 EVA, AUD-V08 / S12 compartments, AUD-V07 / S06 open space.
Read-only; works only on the R-G3 extract.

Usage:
  python analyze.py --raw <extract dir> --project <name> --model <path> --out <json> [--g2 <G2 analysis json>]
Extract: areas.tsv + area_schemes.tsv (parsed from verbatim MCP outputs by parse_areas.py), table_values.tsv (values read
from the exported calculation sheets, each with confidence), rasters.tsv, rooms.tsv.  Stdlib only.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from geom import read_tsv  # noqa: E402
import readings  # noqa: E402
import tasks as T  # noqa: E402

GROUP = ["AUD-S02", "AUD-V09", "AUD-S05", "AUD-V10", "AUD-S08", "AUD-S07", "AUD-V11", "AUD-V12", "AUD-V14",
         "AUD-V06", "AUD-V08", "AUD-S12", "AUD-V07", "AUD-S06"]
_X = "R-G3 step %s (L3-SOP/SOP-AUD-mcp-revit-mcp.md §10)"
_TV = ("table_values.tsv", False, _X % 6 + " - values read off C001-C008 / A001")
_RA = ("rasters.tsv", False, _X % 5 + " - without it GEN-01 (picture tables) is not judged")
NEEDS = {t: [_TV, _RA] for t in GROUP}
NEEDS["AUD-V11"] = [_TV, _RA, ("G2 analysis JSON", False, "run G2 first, pass --g2 (room UFA per floor)")]
NEEDS["AUD-V12"] = [("G2 analysis JSON", True, "run G2 first (S15 UFS bounds), pass --g2")]
NEEDS["AUD-S07"] = [_TV]
NEEDS["AUD-V07"] = NEEDS["AUD-S06"] = [_TV]
TABLE_TASKS = {"gfa": ["AUD-V10", "AUD-S08", "AUD-S05", "AUD-S07"], "concessions": ["AUD-S08", "AUD-S07", "AUD-V10"],
               "compartments": ["AUD-V08", "AUD-S12"]}

# Cap. 123F First Schedule, non-domestic columns (Knowledge, reconstructed table - DK-AUD-006 M-11): (max height m, SC %, PR)
SCHED1_NONDOM = [(15, 100, 5), (18, 97.5, 5.8), (21, 95, 6.7), (24, 92, 7.4), (27, {"A": 89, "B": 90, "C": 90}, {"A": 8.0, "B": 8.1, "C": 8.1})]
# APP-151 Appendix A item flags in the model -> (item, subject to the 10 % cap?) ; mapping confirmed against the C003 table columns
CONCESSION = {"d22": ("2.2", False), "d21": ("21", False), "d23": ("2.3", True), "d25": ("25", True), "d27": ("27", None)}
TOL = 0.0005


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def lvl_elev(name):
    m = re.search(r"(?:SFL|FFL)\s*(-?\d+(?:\.\d+)?)", name or "")
    return float(m.group(1)) if m else None


def short(lv):
    m = re.search(r"(G/F|\d/F|R/F|TR/F)", lv or "")
    return m.group(1) if m else lv


class Out:
    def __init__(self):
        self.checks, self.warnings = [], []

    def add(self, cid, task, item, obj, expected, actual, status, cite="", method="", confidence="high", evidence="",
            fix="", basis="", object_id=None):
        self.checks.append({"id": cid, "task": task, "item": item, "object": obj, "object_id": object_id,
                            "expected": expected, "actual": actual, "status": status, "cite": cite, "basis": basis,
                            "method": method, "confidence": confidence, "evidence": evidence, "fix": fix})

    def eq(self, cid, task, item, obj, model, table, cite, tv=None, fix="", tol=TOL, **kw):
        ok = model is not None and table is not None and abs(model - table) <= tol
        if tv is None:                                   # model vs model
            conf, st = "high", ("UNCLEAR" if table is None else ("PASS" if ok else "FAIL"))
        else:                                            # model vs a sheet reading
            conf, st = readings.confidence(tv), readings.status(ok, tv)
            if st == "UNCLEAR":
                fix = readings.CROP_FIX
        if table is None:
            st, fix = "UNCLEAR", "Read this value from the sheet into table_values.tsv"
        ev = (tv or {}).get("note", "")
        if tv and tv.get("verified"):
            ev = ("crop %s; " % tv["crop"]) + ev
        self.add(cid, task, item, obj, round(model, 3) if model is not None else None, table, st,
                 cite=cite, method="model Areas vs value read from the sheet image%s" % (
                     " (%s)" % tv["sheet"] if tv else ""), confidence=conf,
                 evidence=ev, fix="" if st == "PASS" else fix, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--g2", help="G2 analysis JSON (for UFA / UFS cross-checks)")
    T.add_arg(ap)
    a = ap.parse_args()
    wanted = T.parse(a.tasks, GROUP)
    have = {"table_values.tsv": os.path.exists(os.path.join(a.raw, "table_values.tsv")),
            "rasters.tsv": os.path.exists(os.path.join(a.raw, "rasters.tsv")),
            "G2 analysis JSON": bool(a.g2 and os.path.exists(a.g2))}
    gp = T.gaps(wanted, NEEDS, have)
    for need in ("areas.tsv", "area_schemes.tsv"):
        if not os.path.exists(os.path.join(a.raw, need)):
            print("ERROR: missing " + need, file=sys.stderr)
            return 2
    A = read_tsv(os.path.join(a.raw, "areas.tsv"))
    S = {r["name"]: int(r["areas"]) for r in read_tsv(os.path.join(a.raw, "area_schemes.tsv"))}
    TV, rejected = readings.load(os.path.join(a.raw, "table_values.tsv"), a.raw)
    tv = lambda k: f(TV[k]["value"]) if k in TV else None
    tvs = lambda k: TV[k]["value"] if k in TV else "(not read)"
    rasters = read_tsv(os.path.join(a.raw, "rasters.tsv")) if os.path.exists(os.path.join(a.raw, "rasters.tsv")) else []
    g2 = None
    if a.g2 and os.path.exists(a.g2):
        with open(a.g2, encoding="utf-8") as fh:
            g2 = json.load(fh)
    O = Out()
    tables = {}
    sch = lambda name: [r for r in A if r["scheme"] == name]
    area = lambda r: f(r["area_m2"]) or 0.0

    # ------------------------------------------------------------ GEN-01: tables are raster images
    def imgs(*keys):
        return sorted({r["name"] for r in rasters for k in keys if k in r["name"]})
    for task, obj, keys in (("AUD-S02", "C003 site area calculation", ("C003 - SC DIAGRAM",)),
                            ("AUD-V09", "C003 SC calculation", ("C003 - SC DIAGRAM",)),
                            ("AUD-S05", "C001 SC / PR calculation and Development Schedule", ("C001 -", "Development Schedule")),
                            ("AUD-V10", "C002 GFA calculations", ("C002 -",)),
                            ("AUD-S08", "C003 GFA concession tables", ("GFA Concessions App H", "APP-151 Table")),
                            ("AUD-V11", "C004 UFA calculation", ("C004 -",)),
                            ("AUD-V08", "C005 compartment calculation", ("C005 -",)),
                            ("AUD-S12", "C005 compartment calculation", ("C005 -",)),
                            ("AUD-V06", "C006 EVA calculation", ("C006 -",)),
                            ("AUD-V14", "C008 greenery calculation", ("C008 -",))):
        if not have["rasters.tsv"]:
            continue
        found = imgs(*keys)
        O.add("%s-GEN01" % task.split("-")[1], task, "Calculation table is generated from the model (GEN-01)", obj,
              "schedule / model-generated text", "raster image: " + "; ".join(found) if found else "no raster found",
              "FAIL" if found else "PASS", cite="BIMGBPS §4.2(b), §5.1.2 (GEN-01)",
              method="Raster Images in the model, named after the sheet",
              fix="Rebuild the table as a schedule or calculated text from the area scheme (Function B)")

    # ------------------------------------------------------------ S02 site area
    site_rows = [r for r in A if r["scheme"] in ("(property line)", "ARC_gbp_site area", "Block plan", "Location Plan")]
    site = area(next(r for r in A if r["scheme"] == "(property line)"))
    for r in site_rows:
        O.eq("S02-L2-%s" % r["id"], "AUD-S02", "Site area equals the property line", r["scheme"], area(r), site,
             "BIMGBPS §5.3.2 (GEN-06)", fix="Re-draw the area to the property line", object_id=int(r["id"]))
    for k in ("site_area", "site_area_c003"):
        O.eq("S02-T-%s" % k, "AUD-S02", "Table site area equals the model", TV.get(k, {}).get("sheet", k), site, tv(k),
             "BIMGBPS §5.3.2 (GEN-06)", tv=TV.get(k), fix="Correct the table")
    rounded = round(site) if site >= 2000 else round(site, 1)
    O.add("S02-L3", "AUD-S02", "Site area rounded per ADM-21 (≥ 2,000 m² to 1 m²)", "site area", rounded, site,
          "PASS" if abs(rounded - site) < TOL else "FAIL", cite="PNAP ADM-21; BIMGBPS §5.1.1 (LIM-02)",
          method="property line Area")
    O.add("S02-C1", "AUD-S02", "Site area agrees with the lease plan / land survey", "site area", "lease plan figure",
          site, "UNCLEAR", cite="Cap. 123F reg 23(2) (LIM-14)", method="needs INP-01", basis="external input",
          fix="Provide the lease plan / LSP site area (INP-01)")

    # ------------------------------------------------------------ V10 / S08 / S07 GFA
    gross = {}
    for r in sch("ARC_gbp_gfa"):
        gross[short(r["level"])] = gross.get(short(r["level"]), 0) + area(r)
    ded = {}
    acc = {}
    items = {}
    for r in sch("ARC_gbp_gfa_deduct"):
        lv = short(r["level"])
        flags = [k for k in CONCESSION if r[k] == "1"]
        if r["gfa_summary"] == "1":
            acc[lv] = acc.get(lv, 0) + area(r)
        if len(flags) > 1:
            O.add("V10-L7-%s" % r["id"], "AUD-V10", "Each deduction area has one concession item", r["name"],
                  "1 item", ", ".join(flags), "FAIL", object_id=int(r["id"]))
        for k in flags:
            ded[lv] = ded.get(lv, 0) + area(r)
            items.setdefault(k, {}).setdefault(lv, []).append(r)
        if not flags and r["gfa_summary"] != "1":
            O.add("V10-L7-%s" % r["id"], "AUD-V10", "Every area in the deduction scheme is classified", r["name"],
                  "accountable or one concession item", "neither", "FAIL", object_id=int(r["id"]),
                  fix="Set GFA SUMMARY or one GFA DEDUCT flag")
        if r["gfa_summary"] == "1" and not r["common_area"]:
            O.add("V10-L5-%s" % r["id"], "AUD-V10", "Accountable area has a label that the table can refer to",
                  "%s %s m² on %s" % (r["name"], r["area_m2"], lv), "label (e.g. Non-domestic)", "no label", "FAIL",
                  basis="Minor", object_id=int(r["id"]), method="Common Area parameter",
                  fix="Label the area (domestic / non-domestic) so it maps to Table 1 class 1 or 2")
    gfa_rows = []
    tot_g = tot_d = tot_a = 0.0
    for lv in sorted(gross, key=lambda s: ["G/F", "1/F", "2/F", "R/F"].index(s) if s in ["G/F", "1/F", "2/F", "R/F"] else 9):
        g, d, ac = gross[lv], ded.get(lv, 0.0), acc.get(lv, 0.0)
        tot_g, tot_d, tot_a = tot_g + g, tot_d + d, tot_a + ac
        key = {"G/F": "gf", "1/F": "1f", "2/F": "2f", "R/F": "rf"}.get(lv)
        O.add("V10-C1-%s" % lv, "AUD-V10", "Gross − deductions = accountable areas (two independent sums)", lv,
              round(g - d, 3), round(ac, 3), "PASS" if abs(g - d - ac) < 0.002 else "FAIL",
              cite="Cap. 123F reg 23(3)(a) (LIM-15)", method="ARC_gbp_gfa total − flagged deductions vs GFA SUMMARY areas",
              fix="Close the gap: an area is missing or double-counted in the deduction scheme")
        if key:
            O.eq("V10-T-%s" % lv, "AUD-V10", "Table GFA per floor equals the model", lv, ac, tv("gfa_" + key),
                 "BIMGBPS §5.2.10(f) (GEN-06)", tv=TV.get("gfa_" + key), fix="Correct the table")
            O.eq("V10-TD-%s" % lv, "AUD-V10", "Table deduction per floor equals the model", lv, d, tv("ded_" + key),
                 "BIMGBPS §5.2.10(f) (GEN-06)", tv=TV.get("ded_" + key), fix="Correct the table")
        gfa_rows.append([lv, round(g, 3), round(d, 3), round(g - d, 3), round(ac, 3)])
    gfa_rows.append(["Total", round(tot_g, 3), round(tot_d, 3), round(tot_g - tot_d, 3), round(tot_a, 3)])
    tables["gfa"] = {"title": "GFA by floor (model)", "columns": ["Floor", "Gross (ARC_gbp_gfa)", "Deductions (flagged)",
                                                                  "Gross − deductions", "Accountable (GFA SUMMARY)"], "rows": gfa_rows}
    O.eq("V10-T-total", "AUD-V10", "Table total accountable GFA equals the model", "total", tot_a, tv("gfa_total"),
         "BIMGBPS §5.2.10 (GEN-06)", tv=TV.get("gfa_total"))
    nocap = sum(area(r) for k, (it, cap) in CONCESSION.items() if cap is False for rs in items.get(k, {}).values() for r in rs)
    capd = sum(area(r) for k, (it, cap) in CONCESSION.items() if cap for rs in items.get(k, {}).values() for r in rs)
    item_rows = []
    for k, (it, cap) in CONCESSION.items():
        for lv, rs in sorted(items.get(k, {}).items()):
            item_rows.append([it, "subject to cap" if cap else "no cap" if cap is False else "?", lv, len(rs),
                              round(sum(area(r) for r in rs), 3), ", ".join("%s %s" % (r["common_area"], r["name"]) for r in rs)])
    tables["concessions"] = {"title": "GFA concessions by APP-151 item (model)", "columns": [
        "Item", "Cap", "Floor", "Areas", "Area (m²)", "Areas (code, name)"], "rows": item_rows}
    for k, key in (("d22", "c22_nocap"), ("d21", "c21_nocap"), ("d23", "c23_cap"), ("d25", "c25_cap")):
        mv = sum(area(r) for rs in items.get(k, {}).values() for r in rs)
        O.eq("S08-L4-%s" % CONCESSION[k][0], "AUD-S08", "Concession item total equals the model", "item " + CONCESSION[k][0],
             mv, tv(key), "BIMGBPS §5.3.8 (GEN-06)", tv=TV.get(key))
    for lv, key in (("G/F", "c22_gf"), ("1/F", "c22_1f"), ("2/F", "c22_2f"), ("R/F", "c22_rf")):
        mv = sum(area(r) for r in items.get("d22", {}).get(lv, []))
        O.eq("S08-L4-2.2-%s" % lv, "AUD-S08", "Concession item per floor equals the model", "item 2.2, " + lv, mv, tv(key),
             "BIMGBPS §5.3.8 (GEN-06)", tv=TV.get(key))
    O.eq("S08-L4-nocap", "AUD-S08", "Total no-cap concessions equal the model", "no cap", nocap, tv("nocap_total"),
         "BIMGBPS §5.3.8 (GEN-06)", tv=TV.get("nocap_total"))
    O.eq("S08-L4-cap", "AUD-S08", "Total capped concessions equal the model", "subject to cap", capd, tv("cap_total"),
         "BIMGBPS §5.3.8 (GEN-06)", tv=TV.get("cap_total"))
    pct = capd / tot_a * 100 if tot_a else None
    shown = ("%.3f %% (%.3f / %.3f)" % (pct, capd, tot_a) if pct is not None
             else "no accountable GFA (GFA SUMMARY total 0)")
    O.add("S08-C1", "AUD-S08", "Capped concessions ≤ 10 % of total GFA (non-domestic)", "development", "≤ 10 %",
          shown, "PASS" if pct is not None and pct <= 10 else "FAIL",
          cite="PNAP APP-151 ¶4 (LIM-23)", method="model sums", basis="arithmetic only; item eligibility in S07")
    O.eq("S08-T-pct", "AUD-S08", "Table concession % equals the model", "% of GFA concession",
         round(pct, 3) if pct is not None else None, tv("cap_pct"),
         "BIMGBPS §5.3.8 (GEN-06)", tv=TV.get("cap_pct"), tol=0.0006)
    st, txt, cf = readings.observation(TV, "appendices", a.raw)
    O.add("S08-L2", "AUD-S08", "Tables (a): APP-151 Appendix A list, ADM-2 Appendix G and H present", "C003",
          "A, G and H", txt, st, basis="Partial" if st == "FAIL" else "", confidence=cf,
          method="sheet export read (table_values key 'appendices')",
          fix={"PASS": "", "FAIL": "Add the missing appendix table(s)",
               "UNCLEAR": readings.obs_fix(TV, "appendices", a.raw, "Read C003 for Appendix A, G and H; record key 'appendices' with a finding")}[st])
    O.add("S07-C3", "AUD-S07", "BEAM Plus NB registration confirmation (APP-151 ¶6(c))", "submission", "letter on file",
          "not in the model", "UNCLEAR", cite="PNAP APP-151 ¶6(c) (LIM-24)", basis="external input",
          fix="Provide the BEAM Plus registration letter (INP-07)")
    st, txt, cf = readings.observation(TV, "beam_target_rating", a.raw)
    O.add("S07-C4", "AUD-S07", "BEAM Plus target rating stated on the GBP (APP-151 ¶6(d))", "C001–C008, A001",
          "statement on the plans", txt, st, cite="PNAP APP-151 ¶6(d) (LIM-24)", confidence=cf,
          method="sheet exports read (table_values key 'beam_target_rating')",
          fix={"PASS": "", "FAIL": "Add the target-rating statement (template ADV-33 Appendix A4 drawing C042); without it "
               "the %.3f m² capped concessions cannot be granted" % capd,
               "UNCLEAR": readings.obs_fix(TV, "beam_target_rating", a.raw, "Read every C sheet and A001 for the target rating; record key 'beam_target_rating'")}[st])
    h_c = tv("height_c001")
    band = next((b for b in SCHED1_NONDOM if h_c is not None and h_c <= b[0]), None)
    ppr_c = (band[2] if not isinstance(band[2], dict) else band[2]["C"]) if band else None
    pr_up = (tot_a + capd) / site
    O.add("S07-C6", "AUD-S07", "Sensitivity: PR still within the limit if capped concessions are refused", "development",
          "PR ≤ %s" % ppr_c if ppr_c else "PR ≤ permitted (height not read)",
          "%.3f / %.3f = %.3f" % (tot_a + capd, site, pr_up),
          "UNCLEAR" if ppr_c is None else ("PASS" if pr_up <= ppr_c else "FAIL"),
          cite="APP-151 ¶6; Cap. 123F First Schedule", method="model sums; First Schedule band from the C001 height",
          basis="sensitivity", confidence="medium")

    # ------------------------------------------------------------ V09 / S05 SC and PR
    sc_area = sum(area(r) for r in sch("ARC_gbp_sc"))
    O.eq("V09-T-area", "AUD-V09", "Table covered area equals the SC Area", "C001", sc_area, tv("sc_area"),
         "BIMGBPS §5.2.9 (GEN-06)", tv=TV.get("sc_area"))
    sc_pct = sc_area / site * 100
    O.eq("S05-T-sc", "AUD-S05", "Table SC % equals covered area ÷ site area", "C001", round(sc_pct, 3), tv("sc_pct"),
         "BIMGBPS §5.3.5 (GEN-06)", tv=TV.get("sc_pct"), tol=0.0006)
    pr = tot_a / site
    O.eq("S05-T-pr", "AUD-S05", "Table PR equals GFA ÷ site area", "C001", round(pr, 3), tv("pr"),
         "BIMGBPS §5.3.5 (GEN-06)", tv=TV.get("pr"), tol=0.0006)
    O.eq("S05-T-gfa", "AUD-S05", "Table GFA equals the model", "C001", tot_a, tv("gfa"), "BIMGBPS §5.3.5 (GEN-06)", tv=TV.get("gfa"))
    gf_gross = gross.get("G/F", 0)
    if gross:
        O.add("V09-C0", "AUD-V09", "Covered area is not smaller than the largest floor plate", "SC Area vs G/F gross",
              "≥ %.3f" % max(gross.values()), round(sc_area, 3), "PASS" if sc_area >= max(gross.values()) - TOL else "UNCLEAR",
              method="ARC_gbp_sc vs ARC_gbp_gfa", confidence="medium",
              evidence="G/F gross %.3f m² is %.3f m² larger than the SC area" % (gf_gross, gf_gross - sc_area),
              fix="Check which outline the SC area follows (external wall vs projection)")
    else:
        O.add("V09-C0", "AUD-V09", "Covered area is not smaller than the largest floor plate", "SC Area vs GFA",
              "ARC_gbp_gfa floors", "no ARC_gbp_gfa areas in the model", "UNCLEAR",
              method="ARC_gbp_sc vs ARC_gbp_gfa",
              fix="This model has no ARC_gbp_gfa scheme, so the floor-plate comparison was not made")
    for basis, hkey in (("C001 height", "height_c001"), ("Development Schedule height", "height_devsched")):
        h = tv(hkey)
        if h is None:
            O.add("S05-H-%s" % hkey, "AUD-S05", "Building height readable for the First Schedule band", basis,
                  "height read from the sheet", "not read", "UNCLEAR", cite="Cap. 123F First Schedule (LIM-16)",
                  fix="Read the height into table_values.tsv")
            continue
        band = next((b for b in SCHED1_NONDOM if h <= b[0]), None)
        if band is None:
            continue
        psc = band[1] if not isinstance(band[1], dict) else band[1]["C"]
        ppr = band[2] if not isinstance(band[2], dict) else band[2]["C"]
        O.add("S05-C7-%s" % hkey, "AUD-S05", "SC within the First Schedule (non-domestic, class C)", "%s %.2f m" % (basis, h),
              "≤ %s %%" % psc, "%.3f %%" % sc_pct, "PASS" if sc_pct <= psc else "FAIL",
              cite="Cap. 123F reg 20, First Schedule col 10 (LIM-16; reconstructed table, check e-Legislation)",
              confidence="medium", basis="conditional: class C (INP-02), non-domestic use")
        O.add("S05-C8-%s" % hkey, "AUD-S05", "PR within the First Schedule (non-domestic, class C)", "%s %.2f m" % (basis, h),
              "≤ %s" % ppr, "%.3f" % pr, "PASS" if pr <= ppr else "FAIL",
              cite="Cap. 123F reg 21, First Schedule col 13 (LIM-16; reconstructed table)", confidence="medium",
              basis="conditional: class C (INP-02), non-domestic use")
        if hkey == "height_c001":
            O.add("S05-T-perm", "AUD-S05", "Table permissible SC / PR equal the First Schedule for the stated height",
                  "C001", "%s %% / %s" % (psc, ppr), "%s %% / %s" % (tvs("perm_sc"), tvs("perm_pr")),
                  "UNCLEAR" if tv("perm_sc") is None or tv("perm_pr") is None else readings.status(
                      tv("perm_sc") == psc and tv("perm_pr") == ppr, TV.get("perm_sc"), TV.get("perm_pr")),
                  cite="First Schedule (LIM-16)", confidence=readings.confidence(TV.get("perm_sc"), TV.get("perm_pr")))
    h1, h2 = tv("height_c001"), tv("height_devsched")
    st = "UNCLEAR" if h1 is None or h2 is None else readings.status(abs(h1 - h2) < 0.005, TV.get("height_c001"),
                                                                     TV.get("height_devsched"))
    O.add("S05-HGT", "AUD-S05", "One building height used throughout", "C001 calculation vs Development Schedule",
          "same height", "%s m vs %s m" % (tvs("height_c001"), tvs("height_devsched")), st,
          cite="Cap. 123F reg 23(1) (LIM-13)", basis="Major" if st == "FAIL" else "", method="sheet readings",
          confidence=readings.confidence(TV.get("height_c001"), TV.get("height_devsched")),
          fix="" if st == "PASS" else ("AP to fix the height basis (INP-11); SC / PR pass on both, so only the statement "
                                       "changes" if st == "FAIL" else "Read both heights, with crops, into table_values.tsv"))
    st, txt, cf = readings.observation(TV, "site_class_info", a.raw)
    O.add("S05-L2", "AUD-S05", "Supporting information for the site classification", "C001",
          "streets, widths, frontage proportion", txt, st, basis="Partial" if st == "FAIL" else "", confidence=cf,
          cite="BIMGBPS §5.3.5(a); Cap. 123F reg 18A (LIM-11, LIM-12)",
          fix={"PASS": "", "FAIL": "State the specified streets and frontage (INP-02)",
               "UNCLEAR": readings.obs_fix(TV, "site_class_info", a.raw, "Read C001 for the site-class basis; record key 'site_class_info'")}[st])

    # ------------------------------------------------------------ V11 UFA
    n_ufa = S.get("ARC_gbp_ufa", 0)
    O.add("V11-L2", "AUD-V11", "UFA scheme holds placed areas (total UFA extent)", "ARC_gbp_ufa", "> 0 areas",
          "%d areas" % n_ufa, "PASS" if n_ufa else "FAIL", cite="BIMGBPS §5.2.11(b)", method="Areas per scheme",
          fix="" if n_ufa else "Create UFA Areas (or use the room outlines) so the UFA diagram and table come from the model")
    if g2:
        lv_rooms = {}
        for row in g2["tables"]["ufa"]["rows"]:
            if row[4] == "included":
                lv_rooms.setdefault(short(row[2]), []).append(row)
        for lv, key in (("G/F", "ufa_gf"), ("1/F", "ufa_1f"), ("2/F", "ufa_2f")):
            rs = lv_rooms.get(lv, [])
            tot = sum(r[3] for r in rs)
            no_fcc = sum(r[3] for r in rs if not r[1].startswith("FCC"))
            st = "UNCLEAR" if tv(key) is None else readings.status(round(no_fcc) == tv(key), TV.get(key))
            O.add("V11-T-%s" % lv, "AUD-V11", "Table UFA per floor equals the room areas", lv, round(no_fcc, 3), tv(key),
                  st, cite="BIMGBPS §5.2.11 (GEN-06)", method="rooms with usable floor area (G2), table rounded to 1 m²",
                  evidence="G2 UFA incl. FCC = %.3f m²; the table leaves out FCC and shows whole m²" % tot,
                  confidence="medium", fix={"PASS": "Show UFA to 3 decimals; decide whether FCC counts (it is in S13's UFA)",
                                            "FAIL": "Correct the table; show UFA to 3 decimals",
                                            "UNCLEAR": readings.CROP_FIX if tv(key) is not None else
                                            "Read this value from the sheet into table_values.tsv"}[st])
    # ------------------------------------------------------------ V12 UFS
    if g2:
        s15 = next((c for c in g2["checks"] if c["id"] == "S15-APL"), None)
        if s15:
            O.add("V12-C1", "AUD-V12", "UFS diagram required (refuse chamber threshold)", "building", s15["expected"],
                  s15["actual"], s15["status"], cite=s15["cite"], method="G2 S15 bounds", basis="conditional",
                  evidence="Gross GFA %.3f m² (≥ any UFS) also < 3,960 m²" % tot_g if tot_g < 3960 else "",
                  fix="State N/A with the APL-03 reason on the drawings")
    # ------------------------------------------------------------ V14 greenery
    grn = sch("ARC_gbp_greenery")
    gt = sum(area(r) for r in grn)
    gpct = gt / site * 100
    O.eq("V14-T-gf", "AUD-V14", "Table G/F greenery equals the model", "C008",
         sum(area(r) for r in grn if short(r["level"]) == "G/F"), tv("grn_gf"), "BIMGBPS §5.2.14 (GEN-06)", tv=TV.get("grn_gf"))
    O.eq("V14-T-rf", "AUD-V14", "Table R/F greenery equals the model", "C008",
         sum(area(r) for r in grn if short(r["level"]) == "R/F"), tv("grn_rf"), "BIMGBPS §5.2.14 (GEN-06)", tv=TV.get("grn_rf"))
    O.eq("V14-T-pct", "AUD-V14", "Table greenery % equals the model", "C008", round(gpct, 3), tv("grn_pct"),
         "BIMGBPS §5.2.14 (GEN-06)", tv=TV.get("grn_pct"), tol=0.0006)
    O.add("V14-C1", "AUD-V14", "Overall greenery ≥ 20 % (site 1,000–20,000 m²)", "site", "≥ 20 %", "%.3f %%" % gpct,
          "PASS" if gpct >= 20 else "FAIL", cite="PNAP APP-152 Table 2 (LIM-29)", method="greenery Areas ÷ site area")
    O.add("V14-C2", "AUD-V14", "Primary-zone greenery ≥ 10 %", "primary zone", "≥ 10 % of site in the primary zone",
          "C008 claims %s %% using all G/F greenery; no primary zone defined in the model" % tvs("grn_primary_pct"),
          "UNCLEAR", cite="PNAP APP-152 Table 2 (LIM-29)", basis="needs zone",
          fix="Define the primary zone (APP-152) and show which greenery lies in it")
    n_sbd = S.get("ARC_gbp_sbd", 0)
    O.add("V14-C3", "AUD-V14", "Building separation / setback applicability (site < 20,000 m²: Lp ≥ 60 m?)", "building",
          "Lp from the plans", "SBD scheme has %d areas; Lp not stated" % n_sbd, "UNCLEAR", cite="PNAP APP-152 ¶3 (LIM-28)",
          fix="State the continuous projected façade length Lp and, if ≥ 60 m, show separation and setback")

    # ------------------------------------------------------------ V06 EVA
    eva = sch("ARC_gbp_eva")
    for lv in sorted({short(r["level"]) for r in eva}):
        rs = [r for r in eva if short(r["level"]) == lv]
        per = sum(f(r["perimeter_mm"]) or 0 for r in rs) / 1000
        served = sorted({f(r["served_facade_mm"]) for r in rs})
        sv = sum(served) / 1000 if len(served) == 1 and len(rs) == 1 else (served[0] / 1000 if len(served) == 1 else sum(served) / 1000)
        pc = sv / per * 100 if per else 0
        key = "eva_gf" if lv == "G/F" else "eva_rf"
        O.add("V06-C1-%s" % lv, "AUD-V06", "Served façade ≥ 1/4 of the building perimeter", lv, "≥ 25 %",
              "%.3f %% (%.1f / %.1f m)" % (pc, sv, per), "PASS" if pc >= 25 else "FAIL", cite="PNAP APP-136 ¶6 (LIM-26)",
              method="EVA Areas: Perimeter and SERVED FACADE parameters", basis="conditional: V06-C2 not checked")
        O.eq("V06-T-%s" % lv, "AUD-V06", "Table perimeter equals the model", lv, per, tv(key + "_perim"),
             "BIMGBPS §5.2.6 (GEN-06)", tv=TV.get(key + "_perim"), tol=0.05)
        O.eq("V06-TP-%s" % lv, "AUD-V06", "Table % equals the model", lv, round(pc, 3), tv(key + "_pct"),
             "BIMGBPS §5.2.6 (GEN-06)", tv=TV.get(key + "_pct"), tol=0.0006)
    typed = [r for r in eva if f(r["served_facade_mm"])]
    if typed:
        O.add("V06-L4", "AUD-V06", "Served façade length is measured, not typed (GEN-02)", "EVA Areas", "measured from geometry",
              "typed parameter SERVED FACADE on %d EVA Area(s)" % len(typed), "FAIL", basis="Minor",
              cite="BIMGBPS §5.1.2 (GEN-02)", fix="Measure the served façade on the plan (dimension or model line) and show it")
    O.add("V06-C2", "AUD-V06", "EVA width, headroom, loading, gradient, distance to façade", "EVA", "FS Code Part D",
          "not checked", "UNCLEAR", cite="FS Code 2011 Part D (LIM-31, source missing)")

    # ------------------------------------------------------------ V08 / S12 compartments
    comp = sch("ARC_gbp_comp")
    lv_elev = sorted({(lvl_elev(r["level"]), short(r["level"])) for r in A if r["level"] and r["scheme"] == "ARC_gbp_gfa"})
    heights = {}
    for i, (e, lv) in enumerate(lv_elev[:-1]):
        heights[lv] = round(lv_elev[i + 1][0] - e, 3)
    comp_rows = []
    for r in comp:
        lv = short(r["level"])
        h = heights.get(lv)
        vol = area(r) * h if h else None
        comp_rows.append([r["compartment"], lv, round(area(r), 3), r["frr"], h, round(vol, 3) if vol else None, r["frc_height"]])
        key = {"G-A": "comp_ga", "1-A": "comp_1a", "2": "comp_2"}.get(r["compartment"])
        if key:
            O.eq("S12-L2-a-%s" % r["compartment"], "AUD-S12", "Table compartment area equals the model (table in whole m²)",
                 r["compartment"], area(r), tv(key + "_area"), "BIMGBPS §5.3.12 (GEN-06)", tv=TV.get(key + "_area"), tol=0.5)
            tvol = tv(key + "_vol")
            exp = round(tv(key + "_area") * h) if tv(key + "_area") and h else None
            st = "UNCLEAR" if exp is None or tvol is None else readings.status(
                exp == tvol, TV.get(key + "_vol"), TV.get(key + "_area"))
            O.add("S12-L2-v-%s" % r["compartment"], "AUD-S12", "Table volume = area × storey height", r["compartment"],
                  exp, tvol, st, cite="BIMGBPS §5.3.12 (GEN-06)",
                  method="storey height from level elevations (%s m); model volume %s m³" % (
                      "%.2f" % h if h else "?", "%.3f" % vol if vol else "?"), confidence="medium",
                  fix={"PASS": "", "FAIL": "Correct the table volume",
                       "UNCLEAR": "Read area and volume, with crops, into table_values.tsv"}[st])
        else:
            O.add("V08-L5-%s" % r["compartment"], "AUD-V08", "Every modelled compartment is on the diagram and in the table",
                  "compartment %s (%s, %.3f m²)" % (r["compartment"], lv, area(r)), "shown on C005", "not shown", "FAIL",
                  cite="BIMGBPS §5.2.8 / §5.3.12", object_id=int(r["id"]), fix="Add the R/F compartment to C005")
        if not f(r["frc_height"]):
            pass
    tables["compartments"] = {"title": "Compartments (model)", "columns": [
        "Compartment", "Floor", "Area (m²)", "FRR (min)", "Storey height (m)", "Volume (m³)", "FRC HEIGHT param"], "rows": comp_rows}
    for lv, g in gross.items():
        c = sum(area(r) for r in comp if short(r["level"]) == lv)
        if c < g - 1:
            O.add("V08-COV-%s" % lv, "AUD-V08", "Compartments cover the floor", lv, "≈ %.3f m² (gross)" % g,
                  "%.3f m² in compartments" % c, "UNCLEAR", confidence="medium",
                  evidence="%.3f m² of the floor is in no compartment Area (plant rooms may be separate compartments not drawn)" % (g - c),
                  fix="Show every compartment on the floor (or state that the rest is not a compartment)")
    O.add("S12-C1", "AUD-S12", "Compartment size / volume / FRR within limits", "all", "FS Code Part C", "not checked",
          "UNCLEAR", cite="FS Code 2011 Part C (LIM-32, source missing)")
    zero = [r["compartment"] for r in comp if not f(r["frc_height"])]
    if comp:
        O.add("S12-FRC", "AUD-S12", "Compartment height held in the model", "FRC HEIGHT parameter", "> 0",
              ("0 on all compartments" if len(zero) == len(comp) else "0 on " + ", ".join(zero)) if zero else "filled",
              "FAIL" if zero else "PASS", basis="Minor" if zero else "", method="Area parameter FRC HEIGHT",
              fix="Fill FRC HEIGHT (or compute it from levels) so volumes are model values" if zero else "")

    # ------------------------------------------------------------ V07 / S06 open space
    O.add("V07-APL", "AUD-V07", "Open space required (domestic buildings only)", "building",
          "domestic building", "%s (non-domestic)" % tvs("use"), "N/A", cite="Cap. 123F reg 25(1)(a) (LIM-17)",
          basis="conditional: use confirmed by AP", fix="State N/A with the reason on the drawings (APL-02)")
    O.add("S06-APL", "AUD-S06", "Open space calculation required", "building", "domestic building", "non-domestic", "N/A",
          cite="Cap. 123F reg 25 (LIM-17)", basis="conditional")
    # ------------------------------------------------------------ scheme inventory
    tables["schemes"] = {"title": "Area schemes in the model", "columns": ["Scheme", "Areas"],
                         "rows": [[k, v] for k, v in sorted(S.items())]}
    tables["areas"] = {"title": "Areas (model)", "columns": ["ID", "Scheme", "Level", "Name", "Area (m²)", "Label",
                                                            "Accountable", "Items"],
                       "rows": [[int(r["id"]), r["scheme"], r["level"], r["name"], f(r["area_m2"]), r["common_area"],
                                 r["gfa_summary"], ", ".join(CONCESSION[k][0] for k in CONCESSION if r.get(k) == "1")] for r in A]}
    tables["readings"] = {"title": "Values read from the sheet images", "columns": ["Key", "Sheet", "Item", "Value", "Unit",
                                                                                  "Confidence", "Crop", "Note"],
                          "rows": [[r["key"], r["sheet"], r["item"], r["value"], r["unit"], r["confidence"],
                                    r.get("crop", "") if r["verified"] else "none", r["note"]] for r in TV.values()]
                          + [[k, "", "", "", "", "rejected", "", why] for k, why in rejected]}

    tasks = list(GROUP)
    per = {}
    for c in O.checks:
        p = per.setdefault(c["task"], {})
        p[c["status"]] = p.get(c["status"], 0) + 1
    O.warnings += [
        "Every G3 calculation table is a raster image: table values were read from the exported sheets (1920 px); "
        "each reading carries a confidence in table_values.tsv. A medium reading is cross-checked by the table's own totals.",
        "APP-151 item mapping (2.2 / 21 no cap; 2.3 / 25 subject to cap) is the model's GFA DEDUCT flags matched to the C003 columns.",
        "First Schedule values come from the reconstructed table in Knowledge (DK-AUD-006 M-11): confirm against e-Legislation.",
        "FS Code 2011 Parts C and D are not in Knowledge: compartment and EVA limits are UNCLEAR.",
    ]
    if rejected:
        O.warnings.insert(0, readings.warning(rejected))
    unver = sorted(k for k, r in TV.items() if not r["verified"])
    if unver:
        O.warnings.insert(0, "Readings without a crop of the cell (%d): %s. They can PASS (medium confidence) but a "
                             "mismatch stays UNCLEAR until a crop is saved." % (len(unver), ", ".join(unver)))
    out = {"project_info": {"project_name": a.project, "model_path": a.model, "group": "G3 area-scheme", "tasks": tasks,
                            "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "read_only": True,
                            "building_use": tvs("use"),
                            "rules": {"GFA": "Cap. 123F reg 23(3)(a); PNAP APP-151 ¶4 (10 % cap)",
                                      "SC / PR": "Cap. 123F regs 20, 21, First Schedule (non-domestic)",
                                      "Site": "Cap. 123F reg 23(2); PNAP ADM-21 rounding",
                                      "Greenery": "PNAP APP-152 Table 2", "EVA": "PNAP APP-136 ¶6",
                                      "Compartments": "FS Code 2011 Part C (missing)"}},
           "checks": O.checks, "tables": tables,
           "summary": {"per_task": per, "checks": len(O.checks),
                       "fail": sum(1 for c in O.checks if c["status"] == "FAIL"),
                       "unclear": sum(1 for c in O.checks if c["status"] == "UNCLEAR"),
                       "gfa": {"gross": round(tot_g, 3), "deductions": round(tot_d, 3), "accountable": round(tot_a, 3),
                               "no_cap": round(nocap, 3), "capped": round(capd, 3),
                               "capped_pct": round(pct, 3) if pct is not None else None},
                       "data_quality_warnings": O.warnings}}
    out["readings"] = readings.listing(TV, a.raw, rejected=rejected)
    T.finish(out, wanted, GROUP, gp, TABLE_TASKS)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    T.print_summary(out, "G3 area-scheme")
    print("GFA gross %.3f - deductions %.3f = accountable %.3f m² | no cap %.3f, capped %.3f (%s) | site %.3f m²"
          % (tot_g, tot_d, tot_a, nocap, capd, ("%.3f %%" % pct) if pct is not None else "n/a", site))
    return 0


if __name__ == "__main__":
    sys.exit(main())
