# Model Audit 四层包 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal**：把 Roadmap 功能 A（A1 + A2 + A3，36 个 Task + 回归）写成按四层架构分层、可在任何 harness 运行的 Markdown / JSON 包。

**Architecture**：

- 按层分文件夹：L1 行业知识、L2 软件无关的审核逻辑、L3 人工与 MCP 的 SOP、L4 能力对照。
- 工具名只出现在 L3-MCP 和 L4。
- 一个只用标准库的检查脚本先写好、先失败；每完成一层，让它的那部分通过。

**Tech Stack**：Markdown、JSON Schema（draft 2020-12）、Python 3 标准库（只用于检查脚本，不属于包）。

**Spec**：`work/model-audit-design/2026-10-13-model-audit-design.md`（已获操作者同意，默认做法照用）。

## Global Constraints

- 包位置：`work/model-audit/`；并回仓库后是 `hk-gbp-kb-text/Model Audit/`。
- 共 56 个文件：README / RUN 2 + L1 6 + L2 39 + L3 2 + L4 2 + templates 4 + report 1（spec §4.8 修订）。
- 报告（spec §4.8）：英文；HTML + `assets/` 文件夹；两种读者 `bim` / `ap`；只用相对路径，不连网；脚本只用 Python 3 标准库。
- L1、L2 不出现 revit-mcp 的 40 个工具名中的任何一个。
- 包内不出现 `./a0`、`a0.cmd` 或任何 harness 专有命令。
- 包内链接用相对路径，以并回后的位置为准：
  - 仓库内文件：`../GBP Tasks/…`、`../source/…`
  - 法例：`../Legislation/cap123f/…`
- L1 每条限值都有：文件 + 条文 + 版本 + 状态（`已对原文` 或 `[GAP]`）。
- 状态词：Pass / Partial / Fail / Missing / N/A（附条件）/ N/A 待声明 / Unclear。Unclear 不算 Pass，Missing 不算 Present。
- finding schema：
  - `severity` ∈ {Blocker, Major, Minor}。
  - `status` 另设字段。
  - 旧 `shared-issue.schema.json` 不动；对应关系记入 DK-AUD-005：blocker = Blocker；warning = Major 或 Minor（人工判断）；info 不作为发现。
- 不写脚本进包；MCP 盲点只注明 `[GAP]`。
- 样例模型的结论不进包；只在 README 写「已在样例模型第 1 轮验证」。
- 语言：中文；条文原文摘句保留英文，每条 ≤ 1 句。
- 本工作区不是 git 仓库：每个任务的「提交」步骤改为运行检查脚本，并在 `_agent/progress.md` 记一行。

## Review Focus

1. **正常模型上图根本不存在**（不是样例那种「图在但有错」）：每份 AUD 要能判 Missing 或 N/A，不能默认「图存在」。由 Task 4–6 的检查断言覆盖：每份 AUD 第 1 节含「不适用时」，第 3 节含「没有该图 / 表时」。
2. **接的是另一个 MCP，没有对照表**：RUN.md 必须规定停下来说明，不能拿 revit-mcp 的工具名硬套。由 Task 10 断言覆盖：RUN.md 含「没有对照表」的停止规则。
3. **法例原文不在 `../Legislation/`**：L2 判定改 Unclear，不凭记忆引用数值。由 Task 3 断言覆盖：AUD-000 含此规则；Task 10 断言 README「前提」列出此项。
4. **harness 不能执行代码**：颜色、半色调检查改人工或 `[GAP]`，不目测给 Pass。由 Task 3 断言（AUD-000 通用检查）和 Task 8 断言（`AGENT-IMAGE-SAMPLE` 有「无代码执行时」）覆盖。
6. **AP 版带出内部细节**：元素 ID、工具名、GAP 编号、`audience = bim` 的内容出现在 `report-ap.html`。由 Task 9b 测试 `test_ap_has_no_internal_detail` 覆盖。
5. **AP 决定未出**（高度口径、用途分类、豁免取舍）：两个口径都算，不替 AP 选。由 Task 3 断言覆盖：AUD-000「项目输入清单」含 AP 决定栏，规则含「两个口径」。

---

## File Structure

```
work/model-audit/                       ← 包（交付物）
  README.md · RUN.md
  L1-Domain/DK-AUD-001…006
  L2-Task-Logic/AUD-000 · AUD-A1 · AUD-REG
  L2-Task-Logic/Views/AUD-V01…V14
  L2-Task-Logic/Schedules/AUD-S01…S18
  L2-Task-Logic/Assembly/AUD-A01…A04
  L3-SOP/SOP-AUD-manual.md · SOP-AUD-mcp-revit-mcp.md
  L4-Capabilities/CAP-binding-revit-mcp.md · CAP-gaps.md
  templates/audit-results.schema.json · finding.schema.json · na-table-template.md · report-template.html
  report/render_report.py
work/model-audit-design/_agent/         ← 检查用（不属于包）
  check_package.py · progress.md · round1-coverage.md · walkthrough.md
```

### 文件名（检查脚本按此清单核对）

L1：

- `DK-AUD-001_Hard_Requirements.md`
- `DK-AUD-002_Limits_Index.md`
- `DK-AUD-003_Applicability.md`
- `DK-AUD-004_Colour_Standards.md`
- `DK-AUD-005_Errata.md`
- `DK-AUD-006_Missing_Sources.md`

L2 共用：

- `AUD-000_Audit_Flow.md`
- `AUD-A1_Model_Health.md`
- `AUD-REG_Regression.md`

L2 Views（`Views/`）：

| 文件 | 文件 | 文件 |
| --- | --- | --- |
| `AUD-V01_Block_Key_Plan.md` | `AUD-V02_Floor_Plans.md` | `AUD-V03_Sections.md` |
| `AUD-V04_Elevations.md` | `AUD-V05_Details.md` | `AUD-V06_EVA_Diagram.md` |
| `AUD-V07_Open_Space.md` | `AUD-V08_Fire_Compartment.md` | `AUD-V09_SC_Diagram.md` |
| `AUD-V10_GFA_Diagram.md` | `AUD-V11_UFA_Diagram.md` | `AUD-V12_UFS_Diagram.md` |
| `AUD-V13_Prescribed_Windows.md` | `AUD-V14_SBD_Compliance.md` | |

L2 Schedules（`Schedules/`）：

| 文件 | 文件 | 文件 |
| --- | --- | --- |
| `AUD-S01_Drawing_List.md` | `AUD-S02_Site_Area_Calc.md` | `AUD-S03_Coordinates.md` |
| `AUD-S04_Dev_Schedule.md` | `AUD-S05_SC_PR_Summary.md` | `AUD-S06_Open_Space_Calc.md` |
| `AUD-S07_GFA_Concession_Req.md` | `AUD-S08_GFA_Concession_List.md` | `AUD-S09_Lift_Shaft.md` |
| `AUD-S10_Exit_Doors_Routes.md` | `AUD-S11_Discharge_Value.md` | `AUD-S12_FRR_Compartment.md` |
| `AUD-S13_Sanitary_Fitments.md` | `AUD-S14_Window_Area_Calc.md` | `AUD-S15_Refuse_RMRC.md` |
| `AUD-S16_TBE_Room.md` | `AUD-S17_Lift_Shaft_GFA.md` | `AUD-S18_List_of_Modifications.md` |

文件名与现有 TL 同名后缀，方便对照。

L2 Assembly（`Assembly/`）：

- `AUD-A01_Sheet_Assembly.md`
- `AUD-A02_Colour_Coding.md`
- `AUD-A03_Export.md`
- `AUD-A04_Submission_Validation.md`

### AUD 文件的固定小节标题（检查脚本按此匹配）

`## 1. 适用性`、`## 2. 要取得的信息`、`## 3. L1 检查项`、`## 4. L2 计算与限值`、`## 5. 常见坑`、`## 6. 外部输入`、`## 7. 依赖`、`## 8. GAP`

首行格式：`# AUD-XXX <名称> · BIMGBPS §x.x.x`  
第二行：`关联：` + TL 相对链接 + Roadmap 卡片 ID + MA 编号 + DK 条目。

---

### Task 1: 检查脚本（先失败）

**Files:**

- Create: `work/model-audit-design/_agent/check_package.py`
- Create: `work/model-audit-design/_agent/progress.md`

**Interfaces:**

- Produces: `python check_package.py [--layer L1|L2|L3|L4|templates|top|all]`。每项检查打印 `PASS <名称>` / `FAIL <名称>: <原因>`；有 FAIL 时 exit 1。
- 包根：`work/model-audit/`。链接解析的工作区映射：
  - `../GBP Tasks/`、`../source/`、`../HK GBP …md` → `knowledge/hk-gbp-submission/hk-gbp-kb-text/`
  - `../Legislation/cap123f/` → `knowledge/cap123f/`（123、123h、123i 同理）
  - PNAP 文字版另认 `knowledge/hk-gbp-pdf-extracts/PNAP/`

**检查项（函数名 → 断言）：**

| 函数 | 断言 |
| --- | --- |
| `check_files(layer)` | 上面「文件名」清单中该层的每个文件都存在 |
| `check_no_tool_names()` | L1-Domain、L2-Task-Logic 下所有 .md 不含 40 个工具名的任何一个（清单见下） |
| `check_no_harness_cmds()` | 全包不含 `./a0`、`a0.cmd`、`skills run` |
| `check_aud_sections()` | 每份 AUD-V/S/A 有 8 个固定小节标题、首行符合格式、第二行以 `关联：` 开头；第 1 节含「不适用时」；第 3 节含「没有该图」或「没有该表」 |
| `check_limits_index()` | DK-AUD-002 表格每行的「条文」「版本」「状态」三栏非空；状态 ∈ {已对原文, [GAP]} |
| `check_links()` | 所有相对链接能解析（包内直接解析；`../` 按工作区映射）；解析不了的打印 FAIL |
| `check_schema()` | `finding.schema.json` 能 `json.load`；`severity.enum == ["Blocker","Major","Minor"]`；`status.enum` 含上面 7 个状态词；`required` 含 `id, task, status, severity, clause, evidence, label` |
| `check_rules()` | RUN.md 含「没有对照表」；AUD-000 含「项目输入清单」「两个口径」「../Legislation/」「无法执行代码」；README 含「已知缺口」「前提」 |

40 个工具名（硬编码在脚本里）：

```
create_plan_views create_schedule create_section_view create_sheet delete_elements
export_gbxml export_ifc export_views get_active_context get_all_schedules
get_all_view_templates get_annotation_include_categories get_element_data
get_fill_and_line_patterns get_room_boundaries get_rooms get_running_revit_instances
get_schedulable_fields get_schedule_definition get_sheet_collections get_sheets
get_sheets_in_sheet_collection get_views get_views_on_sheets modify_element_parameters
modify_schedule_filters modify_schedule_grouping modify_schedule_sorting move_elements
open_view override_elements_graphics query_model rename_sheet review_changes
rotate_elements select_elements set_annotation_include_categories set_sheet_number
show_elements tag_elements
```

- [ ] **Step 1**：写 `check_package.py`，含上表 8 个函数和 `--layer` 参数。
- [ ] **Step 2**：运行 `python -I work/model-audit-design/_agent/check_package.py --layer all`。预期：FAIL（包还不存在），exit 1。
- [ ] **Step 3**：`progress.md` 记「Task 1 完成：检查脚本就绪，全部 FAIL（预期）」。

---

### Task 2: L1-Domain（6 份）

**Files:** Create `work/model-audit/L1-Domain/` 下 6 份（文件名见上）。

**Interfaces:**

- Produces：DK 条目编号，供 L2 引用。
- 格式：`DK-AUD-00x §n`；DK-AUD-002 每行编号 `LIM-nn`；DK-AUD-003 每个判定编号 `APL-nn`。

**内容来源**：

- `skills/gbp-audit-cards-*.md` 的「限值（已对原文）」
- `work/gbp-tasks/audit-report.md` 的第 2 层各节
- `work/gbp-architecture-review/architecture-review.md` 第 4 节（勘误）
- Roadmap §03（G1–G12）、Table 1

**必须有的条目**：

- DK-AUD-002 至少包含：
  - reg 30(2)(a)(i) 1/10、(ii) 1/16
  - reg 31 矩形水平面 21 m² / 2.3 m / 4.5 m
  - reg 36(2) 1/10 + 1/10
  - APP-151 ¶4 10 %
  - APP-151 ¶6 (a)–(g)
  - APP-136 ¶6 1/4
  - Cap 123H 附表四类门槛
  - Cap 123I reg 5(5) 9 m² / 人 1:1、reg 6 0.5 m² / 人 1:1.5
  - APP-152 ¶3 与 Table 2
  - Cap 123F reg 18A、20、21、23(1)(2)、25(1)(a)、28A
  - ADM-21 取整
  - BIMGBPS §5.1.1 三位小数
- DK-AUD-003 至少包含 APL：
  - 住用 / 非住用（Cap 123 s.2）
  - 休憩用地（reg 25）
  - 垃圾房（Cap 123H reg 3、3A）
  - TBE（reg 28A、APP-84 注 2）
  - 电梯井（§5.3.17、APP-89 ¶5）
  - 豁免前置条件（APP-151 ¶5(a)、¶6、¶10）
  - 修改清单（ADM-2 附录 E、reg 23(3)(b)）
  - 洁具类别（Cap 123I Part II，无兜底）
  - SBD 间距（APP-152 ¶3）
  - L&V 房间范围（reg 30、36）

  每条都附 N/A 理由句模板。
- DK-AUD-005 含：
  - 1/8 与 8 % 的全部出处（文件 + 行号，按 architecture-review §4 逐条照录）
  - SC 简表
  - 版本门槛
  - severity 对应关系（见 Global Constraints）

- [ ] **Step 1**：写 DK-AUD-001、004、006。
- [ ] **Step 2**：写 DK-AUD-002。每条「已对原文」的，在写入前用 Grep 在 `knowledge/` 找到原文摘句；找不到就标 `[GAP]`。
- [ ] **Step 3**：写 DK-AUD-003、005。
- [ ] **Step 4**：运行 `check_package.py --layer L1`。预期：`check_files(L1)`、`check_limits_index`、`check_no_tool_names` 中 L1 部分全部 PASS；链接 PASS。
- [ ] **Step 5**：`progress.md` 记一行。

---

### Task 3: L2 共用（AUD-000、AUD-A1、AUD-REG）

**Files:** Create `work/model-audit/L2-Task-Logic/AUD-000_Audit_Flow.md`、`AUD-A1_Model_Health.md`、`AUD-REG_Regression.md`。

**Interfaces:**

- Consumes：DK 条目（Task 2）。
- Produces：
  - AUD-000 的「项目输入清单」项目编号 `INP-nn`，供每份 AUD 第 6 节引用。
  - AUD-000 的通用检查编号 `GEN-nn`：图片表、手填参数、半色调、标高格式与基准。
  - AUD-A1 的 MA 编号沿用 Roadmap（MA-1.1 …）。

**AUD-000 必含**：

- A1 / A2 / A3 定义。
- 两层判定。
- 状态词。
- 证据格式（元素 ID、数值、条文、标签、会推翻的情况）。
- N/A 规则。
- `INP-nn` 表：Roadmap §04 全部 10 项 + AP 决定 5 项（高度口径、用途分类、豁免取舍、洁具类别、N/A 确认）。
- `GEN-nn`。
- 规则句：
  - 「法例原文不在 `../Legislation/` 时，L2 记 Unclear，不凭记忆引用数值」
  - 「harness 无法执行代码时，颜色与半色调检查改人工（L3 manual）或记 [GAP]」
  - 「AP 未决定的口径，两个口径都算」

**AUD-A1**：MA-1.1 至 MA-7.5 共 37 项。每项写：要取得的信息、判据、结果词、DK 条目、MCP 盲点标记（指向 L4 CAP-gaps）。

**AUD-REG**：来自 `skills/gbp-audit-regression.md`。去掉工具名，保留问题类表和关闭标准。

- [ ] **Step 1**：写三份。
- [ ] **Step 2**：运行 `check_package.py --layer L2`。预期：这三份的文件存在 PASS、无工具名 PASS；`check_rules` 中 AUD-000 部分 PASS（其余 FAIL 属预期）。
- [ ] **Step 3**：`progress.md` 记一行。

---

### Task 4: L2 Views（14 份）

**Files:** Create `work/model-audit/L2-Task-Logic/Views/` 下 14 份。

**Interfaces:**

- Consumes：DK（Task 2）、`INP-nn` / `GEN-nn`（Task 3）。
- Produces：每份第 3 节检查项编号 `V0x-Ln`、第 4 节 `V0x-Cn`。
  - 供 Task 11 的 round1 映射使用。
  - 也供 L3-MCP 引用（L3 按这些编号写「怎么取」）。

**内容来源**：`skills/gbp-audit-cards-views.md`。逐卡转写：

| 原卡字段 | 去向 |
| --- | --- |
| 「查」 | 拆成「2. 要取得的信息」（软件无关）和 L3-MCP 的条目（Task 7） |
| 「判」 | 3、4 节 |
| 「坑」 | 5 节 |
| 「外部输入」 | 6 节，改为 `INP-nn` |

另加 1、7、8 节。

共用卡：V04 写「同 AUD-V03」，只补差异（无立面视图时的判法）。

- [ ] **Step 1**：写 V01–V07。
- [ ] **Step 2**：写 V08–V14。
- [ ] **Step 3**：运行 `check_package.py --layer L2`。预期：Views 14 份的 `check_aud_sections` 全 PASS，无工具名 PASS，链接 PASS。
- [ ] **Step 4**：`progress.md` 记一行。

---

### Task 5: L2 Schedules（18 份）

**Files:** Create `work/model-audit/L2-Task-Logic/Schedules/` 下 18 份。

**Interfaces:** 同 Task 4。编号 `S0x-Ln` / `S0x-Cn`。

**内容来源**：`skills/gbp-audit-cards-schedules.md`，转写规则同 Task 4。「全部 Schedules 共用」的 5 条放进每份第 3 节的开头，写成引用 `GEN-nn`，不重抄。

共用卡（只写差异）：

- S06 同 V07
- S15 同 V12
- S17 同 S09

- [ ] **Step 1**：写 S01–S09。
- [ ] **Step 2**：写 S10–S18。
- [ ] **Step 3**：运行 `check_package.py --layer L2`。预期：Schedules 18 份全 PASS。
- [ ] **Step 4**：`progress.md` 记一行。

---

### Task 6: L2 Assembly（4 份）

**Files:** Create `work/model-audit/L2-Task-Logic/Assembly/` 下 4 份。

**内容来源**：`skills/gbp-audit-cards-assembly.md` 的 TL-A01–A04 部分。其 A1 表已在 Task 3 处理。

A04 第 3 节是汇总规则：硬性项表 + 引用各 AUD 结果，不另取信息。

- [ ] **Step 1**：写 4 份。
- [ ] **Step 2**：运行 `check_package.py --layer L2`。预期：L2 全部 39 份 PASS。
- [ ] **Step 3**：`progress.md` 记一行。

---

### Task 7: L3-SOP（2 份）

**Files:** Create `work/model-audit/L3-SOP/SOP-AUD-manual.md`、`SOP-AUD-mcp-revit-mcp.md`。

**Interfaces:**

- Consumes：L2 检查项编号（Tasks 3–6）。
- Produces：小节锚点，供 L4 CAP-gaps 指向：`#man-dim-override`、`#man-area-gaps`、`#man-cad-import`、`#man-version`、`#man-lod`、`#man-colour`。

**SOP-AUD-manual**：按「要取得的信息」分类组织（项目与单位、标高与坐标、Room / Area、视图与图纸、明细表、颜色）。

另设盲点抽查小节，每节写：在 Revit 哪里看、看什么、什么算有问题。小节就是上面 6 个锚点。

**SOP-AUD-mcp-revit-mcp**：

- 开头写 MCP 名称、版本标识（Experimental Technical Preview）、前提（Revit 处于 Modify 状态、无对话框）。
- 按同一分类，每条写：对应 L2 编号 → 工具调用顺序 → 关键参数 → 单位 → 坑 → `实测` / `待试`。
- 实测内容来源：
  - `skills/gbp-submission-prep-mcp-v2.md`
  - `work/gbp-tasks/tracker.md`「MCP 限制」
  - 三份审核卡的「查」
  - `skills/gbp-task-audit-v2.md` 七步

- [ ] **Step 1**：写两份。
- [ ] **Step 2**：运行 `check_package.py --layer L3`。预期：文件 PASS、链接 PASS、无 harness 命令 PASS。
- [ ] **Step 3**：`progress.md` 记一行。

---

### Task 8: L4-Capabilities（2 份）

**Files:** Create `work/model-audit/L4-Capabilities/CAP-binding-revit-mcp.md`、`CAP-gaps.md`。

**Interfaces:**

- Consumes：Catalog 的 CAP-* / AGENT-* ID（`../HK GBP MCP Capability Catalog.md`）、L3 锚点（Task 7）。
- Produces：`CAP-gaps` 的缺口编号 `GAP-nn`，供 README 汇总。

**CAP-binding** 表格栏：`能力 ID | 用于（AUD 编号） | revit-mcp 工具 | 状态 Full/Partial/Missing | 实测/待试 | 备注`。只列功能 A 用到的能力。

另加 `AGENT-IMAGE-SAMPLE`，内容含：

- 定义：导出图的像素取色、灰阶占比。
- 需要：harness 能执行代码。
- 无代码执行时：改 `SOP-AUD-manual#man-colour` 或记 [GAP]。
- 标「建议加入 Catalog」。

**CAP-gaps** 至少 6 条：

- GAP-01 尺寸覆盖值
- GAP-02 面积边界端点几何
- GAP-03 CAD 导入
- GAP-04 Revit 版本
- GAP-05 LOD
- GAP-06 明细表不能截图

每条写：影响的 AUD 检查编号、后果、人工补法链接。

- [ ] **Step 1**：写两份。
- [ ] **Step 2**：运行 `check_package.py --layer L4`。预期：PASS，含锚点链接。
- [ ] **Step 3**：`progress.md` 记一行。

---

### Task 9: templates（4 份）

**Files:** Create `work/model-audit/templates/`：`finding.schema.json`、`audit-results.schema.json`、`na-table-template.md`、`report-template.html`。

**Interfaces:**

- Produces：`finding.schema.json` 字段（RUN.md、报告引用）：
  - `id`（`^F[0-9]+$`）、`task`（`^(A1|AUD-[VSA][0-9]{2})$`）
  - `status`（7 词）、`severity`（Blocker / Major / Minor）
  - `clause`、`evidence`（数组，元素含 `element_id`、`value`、`note`）
  - `label`（FACT / INFERENCE / GAP）
  - `fix`、`fix_method`（manual / function-b / AP）、`overturn_if`
  - 必填：`id, task, status, severity, clause, evidence, label`
- Produces：`audit-results.schema.json`，顶层字段与子字段按 spec §4.8「数据」表。必填：`meta, verdict, a1, tasks, findings, decisions, inputs, unclear, evidence`；`regression` 可选。
  - `tasks[].l1_status` / `l2_status` 用 7 个状态词，另加 `Not judged`（L2 无限值时）。
  - `checks[].audience`、`fix[].audience`、`evidence[].audience` ∈ {bim, both}，缺省 both。
  - `evidence[].kind` ∈ {view, sheet, crop, swatch, csv}；`file` 是相对 `assets/` 的路径。
  - `findings` 的 items 直接 `$ref` 到 `finding.schema.json`。
- **na-table-template.md** 栏：`Task | Clause | Reason | Conditions | AP confirmed (date)`（英文，供报告用）。
- **report-template.html**（后备）：spec §4.8 的 11 节骨架，每节一个 `<!-- FILL: … -->` 注释，说明从 `audit-results.json` 哪个字段取值，以及 bim / ap 的过滤规则；内联 CSS；不含 JS 也能阅读。

- [ ] **Step 1**：写四份。
- [ ] **Step 2**：运行 `check_package.py --layer templates`。预期：`check_schema` PASS；`report-template.html` 存在。
- [ ] **Step 3**：手写一条样例 finding（第 1 轮 F1），用 `check_package.py --example <file>` 校验，预期 PASS。样例放 `_agent/`，不进包。
- [ ] **Step 4**：`progress.md` 记一行。

---

### Task 9b: 报告生成脚本 `report/render_report.py`

**Files:**

- Create: `work/model-audit/report/render_report.py`
- Test: `work/model-audit-design/_agent/test_render.py`，样本数据 `work/model-audit-design/_agent/sample-round1/`（`audit-results.json` + `assets/`）

**Interfaces:**

- Consumes：`audit-results.schema.json`（Task 9）。
- Produces：
  - CLI：`python render_report.py --results <audit-results.json> --audience bim|ap --out <file.html>`。
    - 成功：exit 0，打印写出的路径。
    - 校验失败：exit 2，逐条打印 `INVALID <path>: <reason>`，不写文件。
    - 缺 assets 文件：exit 3，打印 `MISSING ASSET <file>`，不写文件。
  - 函数：
    - `load_results(path) -> dict`
    - `validate(results, schema) -> list[str]`（只实现 schema 里用到的：type、required、enum、pattern、items、$ref）
    - `render(results, audience) -> str`

**测试（先写，先失败）**：

| 测试 | 断言 |
| --- | --- |
| `test_render_bim_has_all_sections` | bim 输出含 11 个节标题 id：`cover, overview, decisions*, model-health, tasks, findings, action-plan, na-table, not-determinable, regression*, appendix`（* 按数据有无） |
| `test_ap_has_no_internal_detail` | ap 输出不含：样本里的任何元素 ID、40 个工具名中的任何一个、`GAP-0`、`audience: bim` 项的文字、`[FACT]` / `[INFERENCE]` / `[GAP]` |
| `test_ap_decisions_first` | ap 输出里 `id="decisions"` 出现在 `id="overview"` 之后、`id="model-health"` 之前 |
| `test_labels_translated_for_ap` | ap 输出含 `Verified` / `Inferred` / `Not determinable`（样本里各有一例） |
| `test_every_fail_has_evidence` | 渲染前校验：status 为 Fail / Partial 的 task 都有 `evidence_ids`；样本里删去一个后 → `validate` 返回含该 task 的错误 |
| `test_invalid_results_rejected` | 缺 `verdict` → exit 2，且没有写出文件 |
| `test_missing_asset_rejected` | 引用不存在的 png → exit 3 |
| `test_offline` | 输出不含 `http://`、`https://`（`<a>` 内的条文外链除外：本包不用外链，故全部禁止） |
| `test_status_has_text` | 每个状态色块旁都有状态文字（正则：`class="st st-…">Pass<` 等） |

**实现要点**（测试未决定的部分）：

- 单文件 HTML，内联 CSS 与少量原生 JS（Task 卡筛选、表格排序、图片点开放大）；JS 关掉也能读。
- 状态色用 CSS 变量，深浅色两套（`prefers-color-scheme`）。
- 图片 `<img src="assets/…" loading="lazy">`；缩略图点开看原图。
- 文字一律 HTML 转义。

- [ ] **Step 1**：写 `test_render.py` 和最小样本数据（3 个 task：一个 Pass、一个 Fail（带证据）、一个 N/A；2 条 finding；1 个 decision；1 张 png、1 张 swatch png）。
- [ ] **Step 2**：运行 `python -I _agent/test_render.py`。预期：FAIL（脚本不存在）。
- [ ] **Step 3**：实现 `render_report.py`。
- [ ] **Step 4**：运行 `python -I _agent/test_render.py`。预期：9/9 PASS。
- [ ] **Step 5**：`check_package.py --layer all` 的 files 检查含 `report/render_report.py`；`progress.md` 记一行。

---

### Task 10: README.md、RUN.md

**Files:** Create `work/model-audit/README.md`、`RUN.md`。

**Interfaces:** Consumes 全部前面的编号与路径。

**README 小节**：

- 是什么
- 读取顺序
- 各 harness 用法：Cursor / Hermes / Claude Code 各 1–2 行
- 报告：产出文件夹结构、`render_report.py` 用法、脚本跑不了时用 `report-template.html`
- 前提：对照表、`../Legislation/`、代码执行
- 已知缺口：汇总 L1 `[GAP]`、DK-AUD-006、GAP-01…06，每条指回文件
- 验证依据
- 维护

**RUN.md 小节**（按 spec §4.2 的 7 项）：

1. 开始前，含规则「当前 MCP 没有对照表 → 停下来说明，先按 Catalog 做对照表」。
2. 顺序。
3. 判定规则。
4. 证据规则。
5. 安全（只读）。
6. 产出：先写 `audit-results.json`（按 schema）与 `assets/`，再生成 `report-bim.html`、`report-ap.html`；不能执行代码时按模板填，封面注明。
7. 三条短 Prompt。

- [ ] **Step 1**：写两份。
- [ ] **Step 2**：运行 `check_package.py --layer all`。预期：全部 PASS，exit 0。
- [ ] **Step 3**：`progress.md` 记一行。

---

### Task 11: 验证（第 1 轮对照 + 独立走查）

**Files:**

- Create: `work/model-audit-design/_agent/round1-coverage.md`、`walkthrough.md`
- 可能 Modify：包内文件（补漏）

**round1-coverage.md** 表：`第 1 轮发现 | 来源（audit-report 节）| 负责找出它的检查项编号 | 是否覆盖`。

- 行包括 F1–F12、H1、U1–U4，以及 36 项各自的 L1 / L2 结论（每项一行）。
- 「否」的行必须在本任务内补进对应 AUD，直到全部为「是」。

**walkthrough.md**：只读包内文件、不看本次对话，走 A1 与 AUD-S14 两条。记录：

- 每一步要用的信息在包里哪里找到。
- 找不到的列为缺陷，补进包里。

- [ ] **Step 1**：写 round1-coverage.md，补漏直到全「是」。
- [ ] **Step 2**：写 walkthrough.md，补漏。
- [ ] **Step 3**：用 Task 9b 的样本数据补全为第 1 轮的完整结果（36 项 + F1–F12，放 `_agent/sample-round1/`），两种读者各生成一次；在浏览器打开两份，截图看总览、一张 Fail 卡、AP 版的 Decisions 节。发现的问题补进脚本或模板。
- [ ] **Step 3b**：DK-AUD-002 每条「已对原文」再用 Grep 对一次原文摘句；不符的改正或改 `[GAP]`。
- [ ] **Step 4**：运行 `check_package.py --layer all`。预期：全部 PASS，exit 0。
- [ ] **Step 5**：`progress.md` 记最终一行；向操作者报告：文件数、检查结果、覆盖率、缺口清单，以及「审核卡 Skill 改为指向包」的提议（只提议，不执行）。
