"""Build sample-round1/ (audit-results.json + assets) from the round-1 audit of the BD sample model.
Data transcribed from work/gbp-tasks/audit-report.md; screenshots copied from work/gbp-tasks/_agent/.
Not part of the package."""
import json
import shutil
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "gbp-tasks" / "_agent"
OUT = HERE / "sample-round1"
ASSETS = OUT / "assets"


def swatch(path, sampled, standard, w=120, h=60):
    rows = []
    for _ in range(h):
        rows.append(b"\x00" + bytes(sampled) * (w // 2) + bytes(standard) * (w // 2))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


EV = []


def ev(eid, src, kind, caption, task):
    name = f"{eid}.png"
    shutil.copyfile(SRC / src, ASSETS / name)
    EV.append({"id": eid, "file": name, "kind": kind, "caption": caption, "task": task, "audience": "both"})
    return eid


def sw(eid, sampled, standard, caption, task):
    swatch(ASSETS / f"{eid}.png", sampled, standard)
    EV.append({"id": eid, "file": f"{eid}.png", "kind": "swatch", "caption": caption, "task": task, "audience": "both"})
    return eid


def chk(cid, item, result, evidence="", ids=(), audience="both"):
    return {"id": cid, "item": item, "result": result, "evidence": evidence, "element_ids": list(ids), "audience": audience}


def calc(cid, formula, values, limit, clause, result, basis=None):
    return {"id": cid, "formula": formula, "values": values, "limit": limit, "clause": clause, "result": result, "basis": basis, "audience": "both"}


def fx(text, method, audience="both"):
    return {"text": text, "method": method, "audience": audience}


def task(tid, name, clause, cat, l1, l2, checks, ev_ids, f_ids, fixes, calcs=(), na=None, summary=None, overturn=None):
    t = {"id": tid, "name": name, "clause": clause, "category": cat,
         "applicability": {"applicable": True} if na is None else {"applicable": False, "reason": na[0], "conditions": na[1], "ap_confirmed": None},
         "l1_status": l1, "l2_status": l2, "checks": checks, "calcs": list(calcs), "evidence_ids": ev_ids,
         "finding_ids": f_ids, "fix": fixes, "overturn_if": overturn}
    if summary:
        t["summary"] = summary
    return t


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    ASSETS.mkdir(parents=True)
    P1, V06, V02, V01, V03 = "phase1-sheets", "tl-v06-v14-review", "tl-v02-review", "tl-v01-review", "tl-v03-v04-review"
    C001 = f"{P1}/Export_20261012_134819 - Sheet - C001 - SITE COVERAGE, PLOT RATIO AND DEVELOPMENT SCHEDULE.png"
    C003 = f"{P1}/Export_20261012_134820 - Sheet - C003 - SC DIAGRAM AND CALCULATION AND GFA CONCESSION SUMMARY.png"
    C007 = f"{P1}/Export_20261012_134822 - Sheet - C007 - SCHEDULES.png"
    A001 = f"{P1}/Export_20261012_134957 - Sheet - A001 - BLOCK PLAN, NOTES AND LEGEND.png"
    nonres = ("The building is non-domestic (Institutional) with no domestic part; Cap. 123F regulation 25 and the Second Schedule apply to domestic buildings only, so no open space diagram or calculation is required.",
              "AP confirms the use classification.")
    refuse = ("The building is non-domestic (not industrial) and its usable floor space is below the 3 960 m² threshold of the Cap. 123H Schedule (total floor area only 3 944.120 m²); regulation 3A applies to domestic buildings only.",
              "AP confirms the use classification.")
    lift = ("No GFA / SC concession under PNAP APP-89 is applied for (item 18 of the concession list is '-'), and an Institutional building is not a category listed in APP-89 para 5, so no lift shaft schedule is required.",
            "AP confirms no application.")
    tbe = ("The building is Institutional, not a commercial, industrial, residential or hotel building under Cap. 123F regulation 28A, so no telecommunications and broadcasting access facilities are required, nor MAF under PNAP APP-84 note 2.",
           "AP confirms the building is not commercial in the ordinary meaning.")

    tasks = [
        task("AUD-V01", "Block / Key Plan", "BIMGBPS §5.2.2", "View", "Partial", "Unclear", [
            chk("V01-L1", "Scale not smaller than 1:500", "Pass", "Block plan view at 1:500.", ["696470"]),
            chk("V01-L3", "Site area coloured pink", "Fail", "Sampled 230,250,240 (mint green), not pink."),
            chk("V01-L6", "Boundary coordinates and dimensions", "Fail", "Coordinate table is an inserted image; boundary lengths not dimensioned.", ["1513247"]),
            chk("V01-L5", "Specified streets indicated", "Partial", "Street names and widths shown; specified streets not marked."),
            chk("V01-L10", "Spot level format X.XXX mPD", "Fail", "Street levels show two decimals, no mPD.")],
            [ev("v01-1-view", f"{V01}/Export_20261012_161900 - Area Plan (Block plan) - SFL 17-25_TR-F.png", "view", "Block plan as exported", "AUD-V01"),
             sw("v01-2-swatch", (230, 250, 240), (255, 218, 236), "Site fill: sampled (left) vs pink 255,218,236 (right)", "AUD-V01"),
             ev("v01-3-crop", f"{V01}/a001-coord-table-zoom.png", "crop", "Coordinate table is a picture", "AUD-V01")],
            ["F1", "F11"], [fx("Change the block plan site fill to pink.", "function-b"), fx("Replace the coordinate image with spot coordinates and dimension the boundary.", "manual"),
                            fx("Mark which streets are specified streets.", "manual")],
            [calc("V01-C1", "Site class from street widths and frontage", "4 streets 10 m wide; 70.35 % frontage on 3 streets", "LIM-11, LIM-12", "Cap. 123F reg 18A", "Unclear")]),
        task("AUD-V02", "Floor Plans", "BIMGBPS §5.2.3", "View", "Partial", "Not judged", [
            chk("V02-L2", "Grids and column spacing", "Partial", "Main floors have 11 grids; TR/F roof plan has none."),
            chk("V02-L5", "Door marks", "Partial", "Only fire-rated doors tagged (G/F 11 of 30)."),
            chk("V02-L6", "Room, corridor and stair dimensions", "Partial", "Corridor clear widths not dimensioned."),
            chk("V02-L8", "ADM-9 colours", "Pass", "Matches the A001 colour legend."),
            chk("V02-L9", "Spot level format", "Fail", "Two decimals, no mPD.")],
            [ev("v02-1-view", f"{V02}/Export_20261012_162342 - Floor Plan - FFL 0-30 G-F.png", "view", "G/F plan", "AUD-V02")],
            ["F11"], [fx("Tag all doors with a mark-based tag.", "function-b"), fx("Add room sizes, corridor widths and internal wall thickness.", "manual")]),
        task("AUD-V03", "Sections", "BIMGBPS §5.2.4", "View", "Partial", "Unclear", [
            chk("V03-L3", "Levels in X.XXX mPD", "Fail", "Level heads show 'SFL 12.25 m'."),
            chk("V03-L5", "Adjoining street levels", "Partial", "Only section B shows the mean street level."),
            chk("V03-L7", "Height limit line or NIL", "Fail", "No height limit line or note.")],
            [ev("v03-1-view", f"{V03}/Export_20261012_162559 - Section - B.png", "view", "Section B", "AUD-V03"),
             ev("v03-2-crop", f"{V03}/section-b-levels-zoom.png", "crop", "Level heads, two decimals", "AUD-V03")],
            ["F11", "F12"], [fx("Change level heads to X.XXX mPD.", "manual"), fx("Add a height dimension from the mean street level and a height limit line.", "manual")],
            [calc("V03-C1", "Building height from mean street level", "12.150 m", "OZP / lease", "Cap. 123F reg 23(1)", "Unclear", "to main roof"),
             calc("V03-C2", "Building height from mean street level", "17.350 m", "OZP / lease", "Cap. 123F reg 23(1)", "Unclear", "to top roof")]),
        task("AUD-V04", "Elevations", "BIMGBPS §5.2.4", "View", "Partial", "Unclear", [
            chk("V04-L5", "Street levels on elevations", "Partial", "Elevations show no street level."),
            chk("V04-L8", "ADM-9 colours", "Partial", "Roof metal fence drawn stone grey.")],
            [ev("v04-1-view", f"{V03}/Export_20261012_162559 - Elevation - 1.png", "view", "Elevation 1", "AUD-V04")],
            [], [fx("Add street levels; colour the fence as metal.", "manual")]),
        task("AUD-V05", "Typical Details", "BIMGBPS §5.2.5", "View", "Partial", "Not judged", [
            chk("V05-L2", "Typical / non-typical identified", "Fail", "Detail titled 'SECTION' only."),
            chk("V05-L4", "Coverage of required details", "Partial", "Only the atrium balustrade detail exists.")],
            [ev("v05-1-view", "tl-v05-review/Export_20261012_163051 - Section - SECTION.png", "view", "The only detail view", "AUD-V05")],
            [], [fx("Title the detail; AP to confirm which details apply.", "AP")]),
        task("AUD-V06", "EVA Diagram", "BIMGBPS §5.2.6", "View", "Partial", "Pass", [
            chk("V06-L4", "Corresponding calculation", "Fail", "Calculation is an image; served façade value typed in.", ["1512231"]),
            chk("V06-L5", "APP-136 para 4 items", "Partial", "Gradient and paving not stated.")],
            [ev("v06-1-view", f"{V06}/Export_20261012_163407 - Area Plan (ARC_gbp_eva) - SFL 0-25_G-F.png", "view", "EVA diagram G/F", "AUD-V06"),
             ev("v06-2-crop", f"{V06}/c006-calcs-zoom.png", "crop", "EVA calculation as an image", "AUD-V06")],
            ["F1"], [fx("Rebuild the calculation from model geometry; add gradient and paving.", "function-b")],
            [calc("V06-C1", "Served façade / perimeter", "112.4 / 144.0 = 78.056 % (G/F); 41.0 / 57.9 = 70.812 % (R/F)", "≥ 25 %", "PNAP APP-136 para 6", "Pass")],
            summary="Pass on the main APP-136 test, conditional on FS Code Part D values not yet checked."),
        task("AUD-V07", "Open Space Diagram", "BIMGBPS §5.2.7", "View", "N/A 待声明", "N/A（附条件）", [], [], ["F9"],
             [fx("Add the N/A statement to the drawings.", "AP")], na=nonres),
        task("AUD-V08", "Fire Compartment Diagram", "BIMGBPS §5.2.8", "View", "Partial", "Unclear", [
            chk("V08-L2", "Compartment dimensions", "Partial", "1/F view has no dimensions."),
            chk("V08-L4", "Halftone underlay", "Fail", "Walls pure black; grey under 0.3 %.")],
            [ev("v08-1-view", f"{V06}/Export_20261012_163408 - Area Plan (ARC_gbp_comp) - SFL 5-25_1-F.png", "view", "Compartment diagram 1/F", "AUD-V08")],
            ["F8", "F1"], [fx("Set the underlay to halftone in the view template.", "manual")]),
        task("AUD-V09", "Site Area & SC Diagram", "BIMGBPS §5.2.9", "View", "Partial", "Unclear", [
            chk("V09-L3", "Building labels with covered area", "Partial", "Label only, no area figure."),
            chk("V09-L4", "Corresponding calculation", "Fail", "Image.")],
            [ev("v09-1-view", f"{V06}/Export_20261012_163409 - Area Plan (ARC_gbp_sc) - SFL 12-80 R-F.png", "view", "SC diagram", "AUD-V09")],
            ["F1"], [fx("Rebuild as an area schedule; add the covered area to the label.", "manual")]),
        task("AUD-V10", "GFA Diagram", "BIMGBPS §5.2.10", "View", "Partial", "Pass", [
            chk("V10-L3", "Table 1 colours", "Pass", "Sampled 227,100,102 / 191,0,255 / 30,144,255 equal Table 1."),
            chk("V10-L4", "Halftone underlay", "Fail", "No halftone."),
            chk("V10-L6", "Corresponding calculation", "Fail", "Image.", ["1511833", "1511954"])],
            [ev("v10-1-view", "tl-v10-review/Export_20261012_134330 - Area Plan (ARC_gbp_gfa_deduct) - SFL 0-25_G-F.png", "view", "GFA deduction diagram G/F", "AUD-V10"),
             sw("v10-2-swatch", (227, 100, 102), (227, 100, 102), "Accountable non-domestic: sampled (left) vs Table 1 (right)", "AUD-V10")],
            ["F1", "F8", "F10"], [fx("Remove the duplicate deduction set; add halftone; rebuild the table as a schedule.", "function-b")],
            [calc("V10-C1", "Declared GFA = total − uncapped − capped", "3944.120 − 301.959 − 123.080 = 3519.081 m²", "—", "Cap. 123F reg 23(3)(a)", "Pass"),
             calc("V10-C2", "Capped concessions / declared GFA", "123.080 / 3519.081 = 3.498 %", "≤ 10 %", "PNAP APP-151 para 4", "Pass")]),
        task("AUD-V11", "UFA Diagram", "BIMGBPS §5.2.11", "View", "Fail", "Not judged", [
            chk("V11-L2", "Total UFA extent", "Fail", "No fill; both UFA areas unplaced.")],
            [ev("v11-1-view", f"{V06}/Export_20261012_163414 - Area Plan (ARC_gbp_ufa) - SFL 5-25_1-F.png", "view", "UFA diagram 1/F", "AUD-V11")],
            ["F1", "F2"], [fx("Redraw the UFA areas and colour the total UFA.", "manual")]),
        task("AUD-V12", "UFS Diagram", "BIMGBPS §5.2.12", "View", "N/A 待声明", "N/A（附条件）", [], [], ["F9"],
             [fx("Add the N/A statement to the drawings.", "AP")], na=refuse),
        task("AUD-V13", "Prescribed Windows", "BIMGBPS §5.2.13", "View", "Fail", "Unclear", [
            chk("V13-L1", "Prescribed window diagram", "Missing", "No dedicated diagram."),
            chk("V13-L7", "Corresponding calculation", "Fail", "In the C007 image.", ["1512245"])],
            [ev("v13-1-sheet", C007, "sheet", "C007: all schedules in one image", "AUD-V13")],
            ["F1", "F9"], [fx("Prepare the prescribed window diagram.", "manual")]),
        task("AUD-V14", "SBD Compliance", "BIMGBPS §5.2.14", "View", "Partial", "Unclear", [
            chk("V14-L1", "Separation, setback, greenery", "Partial", "Greenery only; SBD areas exist but no view uses them."),
            chk("V14-L2", "Primary / non-primary zones", "Partial", "No primary zone.")],
            [ev("v14-1-view", f"{V06}/Export_20261012_163415 - Area Plan (ARC_gbp_greenery) - SFL 0-25_G-F.png", "view", "Greenery G/F", "AUD-V14")],
            ["F1"], [fx("Define the primary zone; state separation and setback as N/A or show them.", "AP")],
            [calc("V14-C1", "Overall greenery / site area", "957.072 / 3082 = 31.054 %", "≥ 20 %", "PNAP APP-152 Table 2", "Pass")]),
        task("AUD-S01", "List of Drawings", "BIMGBPS §5.3.1", "Schedule", "Fail", "Not judged", [
            chk("S01-L1", "Generated from the model", "Fail", "Image on A001."), chk("S01-L2", "Matches the sheets", "Pass", "16 rows identical.")],
            [ev("s01-1-crop", f"{V01}/a001-drawing-list-zoom.png", "crop", "Drawing list on A001", "AUD-S01")], ["F1"],
            [fx("Create a sheet list schedule.", "manual")]),
        task("AUD-S02", "Site Area Calculation", "BIMGBPS §5.3.2", "Schedule", "Fail", "Unclear", [
            chk("S02-L1", "Generated from the model", "Fail", "Image strip on C003."), chk("S02-L2", "Values agree", "Pass", "3082.000 m² in all three places."),
            chk("S02-L3", "Rounding", "Pass", "To 1 m² (≥ 2 000 m²).")],
            [ev("s02-1-sheet", C003, "sheet", "Sheet C003", "AUD-S02")], ["F1"], [fx("Area schedule of the site scheme.", "manual")]),
        task("AUD-S03", "List of Coordinates", "BIMGBPS §5.3.3", "Schedule", "Fail", "Unclear", [
            chk("S03-L1", "Generated from the model", "Fail", "Picture."), chk("S03-L3", "Bearings and distances", "Fail", "Missing.")],
            [ev("s03-1-crop", f"{V01}/a001-coord-table-zoom.png", "crop", "Coordinate table", "AUD-S03")], ["F1"],
            [fx("Spot coordinates at the corners; bearing and distance labels.", "manual")]),
        task("AUD-S04", "Development Schedule", "BIMGBPS §5.3.4", "Schedule", "Fail", "Unclear", [
            chk("S04-L1", "Generated from the model", "Fail", "Image."), chk("S04-L3", "Height basis", "Partial", "17.35 m here vs 12.15 m on C001.")],
            [ev("s04-1-sheet", C001, "sheet", "Sheet C001", "AUD-S04")], ["F1"], [fx("Rebuild; state both height bases until the AP decides.", "AP")]),
        task("AUD-S05", "Site Classification + SC / PR", "BIMGBPS §5.3.5", "Schedule", "Fail", "Pass", [
            chk("S05-L1", "Generated from the model", "Fail", "Image."), chk("S05-L2", "Supporting information for the site class", "Partial", "Only 'CLASS OF SITE: C'.")],
            [ev("s05-1-sheet", C001, "sheet", "Sheet C001", "AUD-S05")], ["F1"], [fx("Rebuild; add streets, frontage and the specified-street basis.", "manual")],
            [calc("S05-C7", "Site coverage", "1280.000 / 3082.000 = 41.531 %", "100 % / 97.5 %", "Cap. 123F Sch. 1", "Pass", "both height bases"),
             calc("S05-C8", "Plot ratio", "3519.081 / 3082.000 = 1.142", "5 / 5.8", "Cap. 123F Sch. 1", "Pass", "both height bases")],
            summary="Passes under both height bases, conditional on the four streets being specified streets."),
        task("AUD-S06", "Open Space Calculation", "BIMGBPS §5.3.6", "Schedule", "N/A 待声明", "N/A（附条件）", [], [], ["F9"],
             [fx("Add the N/A statement to the drawings.", "AP")], na=nonres),
        task("AUD-S07", "GFA Concession Requirements", "BIMGBPS §5.3.7", "Schedule", "Missing", "Fail", [
            chk("S07-L1", "Pre-requisite table", "Missing", "None."), chk("S07-L3", "BEAM Plus target rating on GBP", "Missing", "None.")],
            [ev("s07-1-crop", "schedules-review/c003-gfa-summary-top.png", "crop", "Concession list without pre-requisites", "AUD-S07")], ["F9"],
            [fx("Add the APP-151 pre-requisite table, or withdraw the AHU and void concessions.", "AP")],
            [calc("S07-C6", "If the 123.080 m² capped concessions are refused", "PR = 3642.161 / 3082.000 = 1.182", "5 / 5.8", "Cap. 123F Sch. 1", "Pass")],
            summary="Capped concessions (123.080 m²) cannot be granted without the pre-requisites; PR still passes without them."),
        task("AUD-S08", "List of GFA Concessions", "BIMGBPS §5.3.8", "Schedule", "Fail", "Pass", [
            chk("S08-L1", "Generated from the model", "Fail", "Images.", ["1508522", "1508515"]), chk("S08-L4", "Item arithmetic", "Pass", "All items agree with model areas.")],
            [ev("s08-1-crop", "schedules-review/c003-gfa-summary-total.png", "crop", "GFA concession totals", "AUD-S08")], ["F1"], [fx("Area schedule of the deduction scheme, split uncapped / capped.", "manual")],
            [calc("S08-C1", "Capped / declared GFA", "123.080 / 3519.081 = 3.498 %", "≤ 10 %", "PNAP APP-151 para 4", "Pass")]),
        task("AUD-S09", "Lift Shaft Schedule", "BIMGBPS §5.3.17", "Schedule", "N/A 待声明", "N/A（附条件）", [], [], ["F9"], [fx("Add the N/A statement to the drawings.", "AP")], na=lift),
        task("AUD-S10", "Min Exit Doors & Routes", "BIMGBPS §5.3.10", "Schedule", "Fail", "Unclear", [
            chk("S10-L1", "Generated from the model", "Fail", "Part of the C007 image.", ["1512245"]),
            chk("S10-L2", "UFA equals room area", "Pass", "e.g. Activity Area 261 = 261.240 m²."),
            chk("S10-L4", "Required column typed in", "Partial", "Typed values, no formula.", audience="bim")],
            [ev("s10-1-sheet", C007, "sheet", "Sheet C007", "AUD-S10")], ["F1"], [fx("Rebuilt schedule to be placed on C007 with formulas.", "manual")],
            [calc("S10-C1", "Persons = ceil(UFA / factor)", "261 / 10 → 27", "FS Code Part B", "LIM-30", "Unclear")]),
        task("AUD-S11", "Discharge Value Schedule", "BIMGBPS §5.3.11", "Schedule", "Fail", "Unclear", [
            chk("S11-L1", "Generated from the model", "Fail", "Image."), chk("S11-L2", "Persons agree with S10", "Pass", "83 and 75.")],
            [ev("s11-1-sheet", C007, "sheet", "Sheet C007", "AUD-S11")], ["F1"], [fx("Place the rebuilt schedule; turn off itemize.", "manual")]),
        task("AUD-S12", "FRR / Compartment Schedule", "BIMGBPS §5.3.12", "Schedule", "Fail", "Unclear", [
            chk("S12-L1", "Generated from the model", "Fail", "Image."), chk("S12-L2", "Areas agree", "Pass", "1184 / 1184 / 938 m².")],
            [ev("s12-1-sheet", C007, "sheet", "Sheet C007", "AUD-S12")], ["F1"], [fx("Area schedule of the compartment scheme with volume.", "manual")]),
        task("AUD-S13", "Sanitary Fitments", "BIMGBPS §5.3.13", "Schedule", "Fail", "Pass", [
            chk("S13-L1", "Generated from the model", "Fail", "Image."), chk("S13-L3", "Provided counts agree with the model", "Pass", "Per floor: WC 10, urinal 6, basin 9 + 1."),
            chk("S13-L4", "Fixtures without a level", "Partial", "Six counter-top fixtures have no level.", ["68162", "716177", "718412", "718498", "719589", "719664"])],
            [ev("s13-1-crop", "schedules-review/c007-s13-zoom.png", "crop", "Sanitary fitment table", "AUD-S13")], ["F1"], [fx("AP to confirm office (reg 5) or place of public entertainment (reg 6).", "AP")],
            [calc("S13-C1", "Office basis: persons = UFA / 9", "2/F 796 → 89; requirements met", "Cap. 123I reg 5", "LIM-21", "Pass", "office"),
             calc("S13-C2", "Public entertainment basis: persons = UFA / 0.5", "2/F 796 → 1592; provision insufficient", "Cap. 123I reg 6", "LIM-22", "Fail", "public entertainment")],
            summary="Pass on the office basis; would fail if classed as a place of public entertainment."),
        task("AUD-S14", "Window Area Calculation", "BIMGBPS §5.3.14", "Schedule", "Fail", "Unclear", [
            chk("S14-L1", "Generated from the model", "Fail", "Image."), chk("S14-L3", "All applicable rooms listed", "Partial", "Only G/F rooms listed.")],
            [ev("s14-1-sheet", C007, "sheet", "Sheet C007", "AUD-S14")], ["F1"], [fx("List 1/F and 2/F rooms; take provided areas from window geometry.", "manual")],
            [calc("S14-C1", "Required window area = floor area / 10", "Office 12.9; provided 13.23", "1/10", "Cap. 123F reg 30(2)(a)(i)", "Unclear")]),
        task("AUD-S15", "Refuse Storage & RMRC", "BIMGBPS §5.3.15", "Schedule", "N/A 待声明", "N/A（附条件）", [], [], ["F9"], [fx("Add the N/A statement to the drawings.", "AP")], na=refuse),
        task("AUD-S16", "TBE Room", "BIMGBPS §5.3.16", "Schedule", "N/A 待声明", "N/A（附条件）", [], [], ["F9"], [fx("Add the N/A statement to the drawings.", "AP")], na=tbe),
        task("AUD-S17", "Lift Shaft Schedule (GFA)", "BIMGBPS §5.3.17", "Schedule", "N/A 待声明", "N/A（附条件）", [], [], ["F9"], [fx("Add the N/A statement to the drawings.", "AP")], na=lift),
        task("AUD-S18", "List of Modifications", "BIMGBPS §5.3.9", "Schedule", "Missing", "Fail", [
            chk("S18-L1", "List exists on the drawings", "Missing", "Modification table image loaded but not placed.")],
            [ev("s18-1-sheet", C003, "sheet", "C003 concession list includes the entrance void", "AUD-S18")], ["F9"],
            [fx("Provide the ADV-33 Appendix A3 Table 1 list, or withdraw the entrance void concession.", "AP")]),
        task("AUD-A01", "Sheet Assembly", "BIMGBPS §4.3(f), §5.5, §6.4", "Assembly", "Partial", "Not judged", [
            chk("A01-L1", "Title block on every sheet", "Pass", "16 sheets, 16 title blocks."),
            chk("A01-L5", "BIM file reference", "Partial", "Software segment R19, file is R27."),
            chk("A01-L6", "Placeholder content", "Fail", "Issue date 'XX-XX-2018', 'Author', 'DATE 1'.")],
            [ev("a01-1-sheet", A001, "sheet", "Sheet A001", "AUD-A01")], ["F6"], [fx("Fill project information and title block fields.", "manual")]),
        task("AUD-A02", "Colour Coding (GFA)", "BIMGBPS §5.1.4, Table 1", "Assembly", "Partial", "Not judged", [
            chk("A02-L1", "Table 1 on the diagram", "Pass", "Equal."), chk("A02-L2", "Table 1 on the legend", "Pass", "All six equal."),
            chk("A02-L4", "Halftone", "Fail", "None.")],
            [ev("a02-1-view", f"{V02}/Export_20261012_122116 - Legend - A001 Colour Indication & Abbreviations.png", "view", "Colour legend", "AUD-A02")],
            ["F8"], [fx("Add halftone underlays.", "manual")]),
        task("AUD-A03", "Export", "BIMGBPS §4, §6", "Assembly", "Partial", "Not judged", [
            chk("A03-L2", "Size ≤ 500 MB", "Pass", "40.4 MB."), chk("A03-L8", "PDF page size", "Partial", "Check export is A3; sheets are A0.")],
            [ev("a03-1-sheet", A001, "sheet", "A001 exported for checking", "AUD-A03")], [], [fx("AP to confirm which file version (R27 or R17) is submitted.", "AP")]),
        task("AUD-A04", "Submission Validation", "BIMGBPS §4.2, §5.2.1, §5.3, §5.5", "Assembly", "Fail", "Not judged", [
            chk("A04-L2", "No typed-in dimensions / areas", "Fail", "11 tables are images."),
            chk("A04-L3", "Areas verifiable", "Fail", "Unplaced areas and rooms; no halftone."),
            chk("A04-L6", "N/A table", "Missing", "Not prepared.")],
            [ev("a04-1-sheet", C007, "sheet", "Example: C007", "AUD-A04")], ["F1", "F9", "F8"], [fx("Resolve F1, F9 and F8 first.", "function-b")]),
    ]

    def F(i, task_, title, status, sev, clause, note, label, fix, method, eid=None, value=None, tasks_=(), gap=None):
        return {"id": f"F{i}", "task": task_, "tasks": list(tasks_), "title": title, "status": status, "severity": sev, "clause": clause,
                "evidence": [{"element_id": eid, "value": value, "note": note, "evidence_id": None}], "label": label,
                "fix": fix, "fix_method": method, "gap": gap}
    findings = [
        F(1, "AUD-A04", "Calculation tables on the drawings are inserted images, not model schedules.", "Fail", "Blocker", "BIMGBPS §4.2(b), §5.1.2",
          "C007 is one 690 × 668 mm image holding five tables; the same on C001–C008.", "FACT", "Rebuild as model schedules and place them on the sheets.", "function-b",
          "1512245", "690 × 668 mm", ["AUD-S01", "AUD-S02", "AUD-S04", "AUD-S05", "AUD-S08", "AUD-S10", "AUD-S11", "AUD-S12", "AUD-S13", "AUD-S14", "AUD-V06", "AUD-V10"]),
        F(2, "A1", "16 areas have zero area (not placed or not enclosed).", "Fail", "Major", "BIMGBPS §4.2(e)(f)", "Two of them have no level.", "FACT",
          "Redraw or delete after confirmation.", "manual", "481205", "0.000 m²"),
        F(3, "A1", "14 rooms have zero area.", "Fail", "Major", "BIMGBPS §4.2(e)", "Rooms on G/F, 1/F, R/F and two without a level.", "FACT",
          "Redraw or delete after confirmation.", "manual", "195108", "0.000 m²"),
        F(4, "A1", "Roof stair room S-2 has an implausible area; boundary probably missing.", "Unclear", "Minor", "—", "844.969 m² for a stair room.", "INFERENCE",
          "Check the room boundary on the roof plan.", "manual", "938715", "844.969 m²"),
        F(5, "A1", "13 raster image types are loaded but not used.", "Fail", "Minor", "BIMGBPS §4.2(g)", "Not placed anywhere.", "FACT", "Purge unused images.", "manual"),
        F(6, "AUD-A01", "Project information contradicts itself and has blank fields.", "Fail", "Minor", "BIMGBPS §5.5.1", "Name says Kowloon, address says TKO.", "FACT",
          "Fill in the real project information.", "manual"),
        F(7, "AUD-V10", "Area names have typos and default names.", "Fail", "Minor", "—", "e.g. 'SWITCH TOOM', 'ABCD'.", "FACT", "Rename.", "function-b", "483310"),
        F(8, "AUD-A02", "Area diagrams have no halftone underlay.", "Fail", "Major", "BIMGBPS §4.2(d)", "Walls pure black; grey under 0.3 % of pixels.", "FACT",
          "Set underlays to halftone in the view templates.", "manual", tasks_=["AUD-V08", "AUD-V10"]),
        F(9, "AUD-A04", "Missing items are not declared N/A; S07 and S18 apply but are missing.", "Fail", "Major", "BIMGBPS §5.2.1, §5.3", "No N/A table.", "FACT",
          "AP decides applicability; add items or N/A statements.", "AP", tasks_=["AUD-V07", "AUD-V12", "AUD-V13", "AUD-S06", "AUD-S07", "AUD-S09", "AUD-S15", "AUD-S16", "AUD-S17", "AUD-S18"]),
        F(10, "AUD-V10", "Two sets of identical G/F deduction areas.", "Fail", "Minor", "BIMGBPS §4.2(e)(f)", "One set has no view and no tags.", "FACT",
          "Delete the leftover set after confirmation.", "function-b", "479931"),
        F(11, "AUD-V02", "Spot levels and level heads use two decimals without mPD.", "Fail", "Minor", "BIMGBPS §5.1.3", "e.g. '5.35', 'SFL 12.25 m'.", "FACT",
          "Change formats to X.XXX mPD.", "manual", tasks_=["AUD-V01", "AUD-V03", "AUD-V04"]),
        F(12, "AUD-V03", "Level datum is inconsistent; displayed levels may be 0.100 m above mPD.", "Unclear", "Major", "BIMGBPS §5.1.3", "Level types are based on the project base point at −100 mm.", "GAP",
          "AP confirms the survey basis; then reset the base point or the elevation base.", "AP", "6844", tasks_=["AUD-V01", "AUD-V02"], gap=None),
    ]
    results = {
        "meta": {"project": "BD Sample – Proposed Institutional Development at Kowloon", "model": "GBP_Revit_Templates_R27.rvt",
                 "revit_version": "2027 (inferred from file name)", "mcp": "revit-mcp (Experimental Technical Preview)", "harness": "Claude Code",
                 "date": "2026-10-12", "round": "Round 1", "package_version": "Model Audit package 2026-10-13", "filled_by": "script"},
        "verdict": {"submittable": False, "summary": "The sample model cannot be submitted as is. All checkable figures agree with the model; the problems are in form.",
                    "reasons": [{"text": "Calculation tables are images, not generated from the model.", "finding_ids": ["F1"]},
                                {"text": "Inapplicable items are not declared N/A, and two applicable items are missing.", "finding_ids": ["F9"]},
                                {"text": "Area diagrams have no halftone underlay.", "finding_ids": ["F8"]}]},
        "a1": [
            {"id": "MA-1.1", "title": "Revit version", "result": "Unclear", "evidence": "Not returned by the tool; file name suggests 2027.", "clause": "BIMGBPS §4.3(c)", "gap": "GAP-04"},
            {"id": "MA-1.3", "title": "File size", "result": "Pass", "evidence": "40.4 MB.", "clause": "BIMGBPS §4.3(b)", "gap": None},
            {"id": "MA-1.5", "title": "Links", "result": "Pass", "evidence": "No Revit links, point clouds or coordination models; CAD imports not checkable.", "clause": "BIMGBPS §4.3(g)", "gap": "GAP-03"},
            {"id": "MA-2.2", "title": "Area units", "result": "Pass", "evidence": "m², three decimals.", "clause": "BIMGBPS §5.1.1", "gap": None},
            {"id": "MA-2.3", "title": "Coordinates", "result": "Pass", "evidence": "Base point within the HK1980 range (inferred).", "clause": "BIMGBPS §5.1.3", "gap": None},
            {"id": "MA-2.4", "title": "Level datum", "result": "Unclear", "evidence": "Elevation base is the project base point at −100 mm.", "element_ids": ["6844", "7388"], "clause": "BIMGBPS §5.1.3", "gap": None},
            {"id": "MA-3.1", "title": "No manual input", "result": "Fail", "evidence": "Calculation tables are images; dimension overrides not readable.", "clause": "BIMGBPS §5.1.2", "gap": "GAP-01"},
            {"id": "MA-3.3", "title": "LOD", "result": "Unclear", "evidence": "No measurable criterion.", "clause": "BIMGBPS §4.4", "gap": "GAP-05"},
            {"id": "MA-3.4", "title": "Irrelevant data", "result": "Partial", "evidence": "Lighting, ceilings, MEP are zero; 13 unused image types.", "clause": "BIMGBPS §4.2(g)", "gap": None},
            {"id": "MA-4.1", "title": "Rooms placed", "result": "Fail", "evidence": "14 of 80 rooms have zero area.", "clause": "—", "gap": None},
            {"id": "MA-4.3", "title": "Areas enclosed", "result": "Fail", "evidence": "16 of 94 areas have zero area; boundary gaps not checkable.", "clause": "BIMGBPS §4.2(e)", "gap": "GAP-02"},
            {"id": "MA-6.2", "title": "Site area", "result": "Pass", "evidence": "3082.000 m², rounded to 1 m².", "clause": "PNAP ADM-21", "gap": None},
            {"id": "MA-7.1", "title": "Title blocks", "result": "Partial", "evidence": "All sheets have one; placeholder values remain.", "clause": "BIMGBPS §5.5.1", "gap": None},
        ],
        "tasks": tasks,
        "findings": findings,
        "decisions": [
            {"id": "INP-11", "question": "Which building height basis applies: to the main roof or to the top roof?", "options": ["12.15 m", "17.35 m"], "tasks": ["AUD-V03", "AUD-V04", "AUD-S04", "AUD-S05"]},
            {"id": "INP-12", "question": "Sanitary fitments: office (Cap. 123I reg 5) or place of public entertainment (reg 6)?", "options": ["Office", "Public entertainment"], "tasks": ["AUD-S13"]},
            {"id": "INP-13", "question": "Keep or withdraw the AHU room (52.380 m²) and entrance void (70.700 m²) concessions?", "options": ["Keep: add pre-requisites and modification list", "Withdraw: GFA 3642.161 m², PR 1.182"], "tasks": ["AUD-S07", "AUD-S08", "AUD-S18"]},
            {"id": "INP-14", "question": "Confirm the N/A items: open space, refuse room / UFS, TBE room, lift shaft.", "options": [], "tasks": ["AUD-V07", "AUD-S06", "AUD-V12", "AUD-S15", "AUD-S16", "AUD-S09", "AUD-S17"]},
            {"id": "INP-15", "question": "Which file is submitted: the 2027 or the 2017 version?", "options": ["R27", "R17"], "tasks": ["AUD-A03", "AUD-A01"]},
            {"id": "INP-16", "question": "Which level datum is correct (project base point at −100 mm or survey point)?", "options": [], "tasks": ["AUD-V01", "AUD-V02", "AUD-V03", "AUD-V04"]},
        ],
        "inputs": [
            {"id": "INP-01", "item": "Lease Plan / Land Survey Plan", "tasks": ["AUD-S02", "AUD-S03", "AUD-V01", "AUD-S05"]},
            {"id": "INP-02", "item": "Specified street status of the four abutting streets", "tasks": ["AUD-S05", "AUD-V01"]},
            {"id": "INP-04", "item": "OZP and lease height limits", "tasks": ["AUD-V03", "AUD-V04"]},
            {"id": "INP-07", "item": "BEAM Plus registration and target rating", "tasks": ["AUD-S07"]},
        ],
        "unclear": [
            {"task": "AUD-S10", "reason_kind": "source", "detail": "Occupancy factors, exit widths not checkable.", "need": "FS Code 2011 Part B", "gap": None},
            {"task": "AUD-S12", "reason_kind": "source", "detail": "Compartment limits not checkable.", "need": "FS Code 2011 Part C", "gap": None},
            {"task": "AUD-S13", "reason_kind": "source", "detail": "Place of public entertainment definition.", "need": "Cap. 172 section 2", "gap": None},
            {"task": "AUD-S02", "reason_kind": "data", "detail": "Site area against the lease.", "need": "Lease Plan / Land Survey Plan", "gap": None},
            {"task": "AUD-A04", "reason_kind": "tool", "detail": "Dimension overrides cannot be read.", "need": "Manual check of key dimensions", "gap": "GAP-01"},
            {"task": "AUD-V10", "reason_kind": "tool", "detail": "Area boundary gaps cannot be read.", "need": "Manual check or BD BIM Area Tool", "gap": "GAP-02"},
        ],
        "evidence": EV,
    }
    (OUT / "audit-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"tasks {len(tasks)}, findings {len(findings)}, evidence {len(EV)}")


if __name__ == "__main__":
    main()
