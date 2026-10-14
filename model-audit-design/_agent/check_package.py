"""Check the Model Audit package against the plan's structural rules.

python -I check_package.py [--layer L1|L2|L3|L4|templates|top|all]
Prints PASS/FAIL lines; exit 1 if any FAIL.
"""
import json
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
PKG = WS / "work" / "model-audit"
REPO = WS / "knowledge" / "hk-gbp-submission" / "hk-gbp-kb-text"
PNAP_PDF = WS / "knowledge" / "hk-gbp-pdf-sources" / "hk-gbp-pdfs" / "PNAP"
LEGIS = WS / "knowledge"

L1 = ["DK-AUD-001_Hard_Requirements.md", "DK-AUD-002_Limits_Index.md", "DK-AUD-003_Applicability.md",
      "DK-AUD-004_Colour_Standards.md", "DK-AUD-005_Errata.md", "DK-AUD-006_Missing_Sources.md"]
VIEWS = ["V01_Block_Key_Plan", "V02_Floor_Plans", "V03_Sections", "V04_Elevations", "V05_Details",
         "V06_EVA_Diagram", "V07_Open_Space", "V08_Fire_Compartment", "V09_SC_Diagram", "V10_GFA_Diagram",
         "V11_UFA_Diagram", "V12_UFS_Diagram", "V13_Prescribed_Windows", "V14_SBD_Compliance"]
SCHEDS = ["S01_Drawing_List", "S02_Site_Area_Calc", "S03_Coordinates", "S04_Dev_Schedule", "S05_SC_PR_Summary",
          "S06_Open_Space_Calc", "S07_GFA_Concession_Req", "S08_GFA_Concession_List", "S09_Lift_Shaft",
          "S10_Exit_Doors_Routes", "S11_Discharge_Value", "S12_FRR_Compartment", "S13_Sanitary_Fitments",
          "S14_Window_Area_Calc", "S15_Refuse_RMRC", "S16_TBE_Room", "S17_Lift_Shaft_GFA",
          "S18_List_of_Modifications"]
ASSY = ["A01_Sheet_Assembly", "A02_Colour_Coding", "A03_Export", "A04_Submission_Validation"]
AUD = ([f"L2-Task-Logic/Views/AUD-{n}.md" for n in VIEWS] + [f"L2-Task-Logic/Schedules/AUD-{n}.md" for n in SCHEDS]
       + [f"L2-Task-Logic/Assembly/AUD-{n}.md" for n in ASSY])
FILES = {
    "top": ["README.md", "RUN.md"],
    "L1": [f"L1-Domain/{f}" for f in L1],
    "L2": ["L2-Task-Logic/AUD-000_Audit_Flow.md", "L2-Task-Logic/AUD-A1_Model_Health.md",
           "L2-Task-Logic/AUD-REG_Regression.md"] + AUD,
    "L3": ["L3-SOP/SOP-AUD-manual.md", "L3-SOP/SOP-AUD-mcp-revit-mcp.md"],
    "L4": ["L4-Capabilities/CAP-binding-revit-mcp.md", "L4-Capabilities/CAP-gaps.md"],
    "templates": ["templates/audit-results.schema.json", "templates/finding.schema.json",
                  "templates/na-table-template.md", "templates/report-template.html",
                  "templates/s14-analysis.schema.json", "templates/task-analysis.schema.json"],
    "report": ["report/render_report.py"],
    "tools": ["tools/common/xlsx_lite.py", "tools/common/geom.py", "tools/common/task_report.py",
              "tools/s14_lv/analyze.py", "tools/s14_lv/report.py", "tools/room_use/analyze.py",
              "tools/area_scheme/analyze.py", "tools/area_scheme/parse_areas.py", "tools/drawings/analyze.py",
              "tools/drawings/sample_colours.py", "tools/drawings/rvt_info.py", "tools/lists_health/analyze.py",
              "tools/common/build_results.py", "tools/common/readings.py", "tools/common/crop_readings.py", "tools/common/tasks.py", "tools/extract/g2_extract.py", "tools/extract/g1_extract.py", "tools/extract/mcp_formats.py", "tools/extract/g3_extract.py", "tools/extract/g5_extract.py", "tools/extract/g4_extract.py"],
    "groups": ["L2-Task-Logic/Groups/G2_Room_Use.md", "L2-Task-Logic/Groups/G3_Area_Scheme.md",
               "L2-Task-Logic/Groups/G4_Drawings.md", "L2-Task-Logic/Groups/G5_Lists_G6_Model_Health.md"],
    "skills": [f"skills/{n}/SKILL.md" for n in
               ["gbp-model-audit", "gbp-audit-g1-lighting-ventilation", "gbp-audit-g2-room-use",
                "gbp-audit-g3-area-scheme", "gbp-audit-g4-drawings", "gbp-audit-g5-lists-health"]],
}
TOOLS = """create_plan_views create_schedule create_section_view create_sheet delete_elements
export_gbxml export_ifc export_views get_active_context get_all_schedules
get_all_view_templates get_annotation_include_categories get_element_data
get_fill_and_line_patterns get_room_boundaries get_rooms get_running_revit_instances
get_schedulable_fields get_schedule_definition get_sheet_collections get_sheets
get_sheets_in_sheet_collection get_views get_views_on_sheets modify_element_parameters
modify_schedule_filters modify_schedule_grouping modify_schedule_sorting move_elements
open_view override_elements_graphics query_model rename_sheet review_changes
rotate_elements select_elements set_annotation_include_categories set_sheet_number
show_elements tag_elements""".split()
SECTIONS = ["## 1. 适用性", "## 2. 要取得的信息", "## 3. L1 检查项", "## 4. L2 计算与限值",
            "## 5. 常见坑", "## 6. 外部输入", "## 7. 依赖", "## 8. GAP"]
STATUSES = ["Pass", "Partial", "Fail", "Missing", "N/A（附条件）", "N/A 待声明", "Unclear"]
RESULTS = []


def report(name, ok, why=""):
    RESULTS.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {why}"))


def text(rel):
    p = PKG / rel
    return p.read_text(encoding="utf-8") if p.exists() else None


def md_files(*folders):
    for f in folders:
        d = PKG / f
        if d.exists():
            yield from sorted(d.rglob("*.md"))


def check_files(layer):
    missing = [f for f in FILES[layer] if not (PKG / f).exists()]
    report(f"files[{layer}] ({len(FILES[layer]) - len(missing)}/{len(FILES[layer])})", not missing,
           ", ".join(missing[:5]) + (" …" if len(missing) > 5 else ""))


def check_no_tool_names():
    hits = []
    for p in md_files("L1-Domain", "L2-Task-Logic"):
        t = p.read_text(encoding="utf-8")
        hits += [f"{p.name}:{tool}" for tool in TOOLS if re.search(rf"(?<![A-Za-z_]){tool}(?![A-Za-z_])", t)]
    report("no tool names in L1/L2", not hits, ", ".join(hits[:8]))


def check_no_harness_cmds():
    hits = [p.name for p in md_files(".") if re.search(r"\./a0\b|a0\.cmd|skills run", p.read_text(encoding="utf-8"))]
    report("no harness commands", not hits, ", ".join(hits))


def check_aud_sections():
    bad = []
    for rel in AUD:
        t = text(rel)
        if t is None:
            bad.append(f"{Path(rel).name}: missing")
            continue
        lines = t.splitlines()
        if not re.match(r"^# AUD-[VSA]\d{2} .+ · BIMGBPS §", lines[0]):
            bad.append(f"{Path(rel).name}: title")
        if len(lines) < 2 or not lines[1].startswith("关联："):
            bad.append(f"{Path(rel).name}: 关联 line")
        pos = [t.find(s) for s in SECTIONS]
        if -1 in pos or pos != sorted(pos):
            bad.append(f"{Path(rel).name}: sections")
            continue
        s1, s3 = t[pos[0]:pos[1]], t[pos[2]:pos[3]]
        if "不适用时" not in s1:
            bad.append(f"{Path(rel).name}: §1 不适用时")
        if "没有该图" not in s3 and "没有该表" not in s3:
            bad.append(f"{Path(rel).name}: §3 没有该图/表")
        if t.count("## 9. 可执行规格") != 1:
            bad.append(f"{Path(rel).name}: §9 可执行规格 ×{t.count('## 9. 可执行规格')}")
    stray = [p.name for p in (PKG / "L2-Task-Logic").rglob("*") if p.is_file() and not p.suffix]
    if stray:
        bad.append(f"{len(stray)} extensionless files ({', '.join(stray[:3])} …)")
    report(f"AUD sections ({len(AUD) - len(bad)}/{len(AUD)} clean)", not bad, "; ".join(bad[:6]))


def check_skills():
    bad = []
    for rel in FILES["skills"]:
        t = text(rel)
        if t is None:
            continue
        m = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", t, re.S)
        if not m:
            bad.append(f"{rel}: frontmatter")
            continue
        if m.group(1) != Path(rel).parent.name:
            bad.append(f"{rel}: name ≠ folder")
        if not m.group(2).startswith("Use when") or len(m.group(2)) > 1024:
            bad.append(f"{rel}: description")
        for ref in re.findall(r"`<PKG>/([^`\s]+)`", t):
            if not (PKG / ref).exists():
                bad.append(f"{rel}: <PKG>/{ref}")
        for ref in re.findall(r"`(gbp-[a-z0-9-]+)`", t):
            if f"skills/{ref}/SKILL.md" not in FILES["skills"]:
                bad.append(f"{rel}: skill {ref}")
    report(f"skills ({len(FILES['skills'])})", not bad, "; ".join(bad[:6]))


def check_limits_index():
    t = text("L1-Domain/DK-AUD-002_Limits_Index.md")
    if t is None:
        report("limits index", False, "missing")
        return
    rows = [l for l in t.splitlines() if l.startswith("| LIM-")]
    bad = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        # columns: ID | 限值 | 数值 | 条文 | 版本 | 原文摘句 | 用于 | 状态
        if len(cells) < 8 or not all(cells[3:5]) or cells[7] not in ("已对原文", "[GAP]"):
            bad.append(cells[0])
    report(f"limits index ({len(rows)} rows)", rows and not bad, "bad rows: " + ", ".join(bad[:8]) if rows else "no LIM rows")


def target_of(src, link):
    """Resolve a link as it will be after merging into hk-gbp-kb-text/Model Audit/, mapped to this workspace."""
    parts = ["Model Audit", *src.relative_to(PKG).parent.parts, *Path(link.split("#")[0]).parts]
    stack = []
    for part in parts:
        if part == "..":
            stack.pop() if stack else stack.append("..")
        elif part not in (".", ""):
            stack.append(part)
    if stack and stack[0] == "Model Audit":
        return PKG.joinpath(*stack[1:]), True
    if stack and stack[0] == "Legislation":
        return LEGIS.joinpath(*stack[1:]), False
    if stack[:2] == ["source", "PNAP"]:
        return PNAP_PDF.joinpath(*stack[2:]), False
    return REPO.joinpath(*stack), False


def check_links():
    bad = []
    for p in md_files("."):
        for link in re.findall(r"\]\(([^)\s]+)\)", p.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+://", link):
                continue
            link = link.replace("%20", " ")
            target, inside = target_of(p, link) if link.split("#")[0] else (p, True)
            if not target.exists():
                bad.append(f"{p.name} → {link}")
            elif "#" in link and inside and target.suffix == ".md":
                anchor = link.split("#", 1)[1]
                if f'id="{anchor}"' not in target.read_text(encoding="utf-8"):
                    bad.append(f"{p.name} → #{anchor}")
    report("links resolve", not bad, "; ".join(bad))

def check_schema():
    p = PKG / "templates" / "finding.schema.json"
    if not p.exists():
        report("finding schema", False, "missing")
        return
    try:
        s = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        report("finding schema", False, f"invalid JSON: {e}")
        return
    props, req = s.get("properties", {}), set(s.get("required", []))
    problems = []
    if props.get("severity", {}).get("enum") != ["Blocker", "Major", "Minor"]:
        problems.append("severity enum")
    if not set(STATUSES) <= set(props.get("status", {}).get("enum", [])):
        problems.append("status enum")
    need = {"id", "task", "status", "severity", "clause", "evidence", "label"}
    if not need <= req:
        problems.append("required: " + ", ".join(sorted(need - req)))
    report("finding schema", not problems, "; ".join(problems))


def validate_example(path):
    s = json.loads((PKG / "templates" / "finding.schema.json").read_text(encoding="utf-8-sig"))
    ex = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    problems = [f"missing {k}" for k in s["required"] if k not in ex]
    for k, spec in s["properties"].items():
        if k in ex and "enum" in spec and ex[k] not in spec["enum"]:
            problems.append(f"{k}={ex[k]!r} not in enum")
        if k in ex and "pattern" in spec and isinstance(ex[k], str) and not re.match(spec["pattern"], ex[k]):
            problems.append(f"{k} pattern")
    extra = set(ex) - set(s["properties"]) if s.get("additionalProperties") is False else set()
    problems += [f"unexpected {k}" for k in extra]
    report(f"example {Path(path).name} validates", not problems, "; ".join(problems))


def check_rules():
    want = {"RUN.md": ["没有对照表"],
            "L2-Task-Logic/AUD-000_Audit_Flow.md": ["项目输入清单", "两个口径", "../Legislation/", "无法执行代码"],
            "README.md": ["已知缺口", "前提"]}
    for rel, needles in want.items():
        t = text(rel)
        miss = needles if t is None else [n for n in needles if n not in t]
        report(f"rules[{Path(rel).name}]", not miss, ("file missing" if t is None else "missing: " + ", ".join(miss)))


def main(argv):
    layer = argv[argv.index("--layer") + 1] if "--layer" in argv else "all"
    if "--example" in argv:
        validate_example(argv[argv.index("--example") + 1])
    else:
        layers = list(FILES) if layer == "all" else [layer]
        for l in layers:
            check_files(l)
        if layer in ("L1", "L2", "all"):
            check_no_tool_names()
        if layer == "L2" or layer == "all":
            check_aud_sections()
        if layer in ("L1", "all"):
            check_limits_index()
        if layer in ("templates", "all"):
            check_schema()
        if layer in ("top", "all"):
            check_rules()
        if layer in ("skills", "all"):
            check_skills()
        if layer == "L2":
            check_rules()
        check_no_harness_cmds()
        check_links()
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
