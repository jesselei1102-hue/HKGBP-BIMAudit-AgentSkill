# 设计文档 · Model Audit 四层包

日期：2026-10-13  
读者：操作者（香港 BIM Manager，四层架构的作者）  
状态：待审。审过后再写实施计划，然后动手。

---

## 1. 要做什么

把 Roadmap **功能 A（Model Audit）** 整理成一套按你的四层架构分层的文件。覆盖：

- A1 模型健康（MA-1 至 MA-7）
- A2 数据就绪
- A3 合规计算

按 36 个 Task 展开，另加回归。

### 1.1 已定的选择（来自你的回答）

| 问题 | 选择 |
| --- | --- |
| 范围 | 整个功能 A：A1 + A2 + A3，36 个 Task |
| 和现有 TL 的关系 | 独立的 Audit 包；链接现有 TL，不重复「交什么」，不改现有文件 |
| MCP 盲点 | 只注明 GAP，不写脚本 |
| 运行环境 | 要能在其他 harness 运行（Cursor、Hermes 等），不依赖 AgentZero |
| 组织方式 | 方案 A：按层分文件夹 |

### 1.2 成功标准

1. **能独立使用**：一个没有看过本工作区对话的 Agent，在任一 harness 里只读 `README.md` → `RUN.md`，就能对一个 Revit 模型跑完功能 A，并产出符合模板的 Audit Report。
2. **层次干净**：
   - L1、L2 不出现任何 MCP 工具名。
   - 工具名只出现在 L3-MCP 和 L4 对照表里。
   - 换 MCP 时，只需新增一份 L3-MCP 和一份 L4 对照表。
3. **限值有出处**：
   - L1 每一条限值都写明文件、条文、版本，以及「已对原文」或 `[GAP]`。
   - 已对原文的，都是在本工作区 Knowledge 原文里核过的。
4. **缺口看得见**：每个缺口在所在层标 `[GAP]`，并汇总到 README「已知缺口」。
5. **和第 1 轮一致**：样例模型第 1 轮的每一个发现（F1–F12、H1、各 Task 结论），按这套包重跑都应该能找出来。拿第 1 轮做对照，作为验收。

### 1.3 不做的

- 功能 B（准备 / 写入）。
- 补 MCP 盲点的脚本（含 pyRevit / Dynamo）。唯一的例外是 §4.8 的报告生成脚本。
- 修改你仓库里的现有文件，包括勘误：只列出，由你在仓库里改。
- 样例模型的结论（留在 `work/gbp-tasks/`）。
- 各 harness 的专用配置文件（`.cursor/rules`、Hermes skill 格式等）。只在 README 写调用方法。

---

## 2. 放在哪里、怎么并回仓库

- 本工作区：`work/model-audit/`。
- 并回仓库：整个文件夹放到 `hk-gbp-kb-text/Model Audit/`，与 `GBP Tasks/`、`source/` 同级。

**路径约定**：包内链接一律用相对路径，以并回后的位置为准。

| 指向 | 写法 |
| --- | --- |
| 现有 TL | `../GBP Tasks/Schedules/TL-S14_Window_Area_Calc.md` |
| BIMGBPS corpus | `../source/HK GBP/corpus/…` |
| PNAP | `../source/PNAP/…`（PDF）。本工作区另有文字摘录 `hk-gbp-pdf-extracts` |
| Capability Catalog、Roadmap | `../HK GBP MCP Capability Catalog.md` 等 |

**法例原文不在你的仓库里** `[FACT]`。Cap. 123、123F、123H、123I 的逐字版只在本工作区 `knowledge/cap123*/`。

- 包内引用法例时，以「文件 + 条文 + 版本」为准。路径写成约定的 `../Legislation/cap123f/…`。
- **建议**你把四份法例文件夹一起放进仓库的 `Legislation/`。没放的话，这些链接会断，引用照样成立，但 Agent 读不到原文，L2 判定要记 Unclear。README 会写明这一点。

---

## 3. 结构

```
Model Audit/
  README.md
  RUN.md
  L1-Domain/
    DK-AUD-001_Hard_Requirements.md
    DK-AUD-002_Limits_Index.md
    DK-AUD-003_Applicability.md
    DK-AUD-004_Colour_Standards.md
    DK-AUD-005_Errata.md
    DK-AUD-006_Missing_Sources.md
  L2-Task-Logic/
    AUD-000_Audit_Flow.md
    AUD-A1_Model_Health.md
    Views/AUD-V01 … AUD-V14
    Schedules/AUD-S01 … AUD-S18
    Assembly/AUD-A01 … AUD-A04
    AUD-REG_Regression.md
  L3-SOP/
    SOP-AUD-manual.md
    SOP-AUD-mcp-revit-mcp.md
  L4-Capabilities/
    CAP-binding-revit-mcp.md
    CAP-gaps.md
  templates/
    audit-results.schema.json
    finding.schema.json
    na-table-template.md
    report-template.html
  report/
    render_report.py
```

共 56 个文件：README / RUN 2 + L1 6 + L2 39 + L3 2 + L4 2 + templates 4 + report 1。（2026-10-13 修订：加入可视化报告，见 §4.8；原 udit-report-template.md 由 eport-template.html 取代。）

---

## 4. 各部分规格

### 4.1 README.md

- 一段话：这是什么、对应架构哪一部分（功能 A 的四层实现）。
- 读取顺序：README → RUN → AUD-000 → 按 Task 读 AUD-*，执行时查 L3、L4。
- 各 harness 的用法（每种一两行）：
  - Cursor：在对话里 `@Model Audit/RUN.md`。
  - Hermes：把 `RUN.md` 作为任务说明载入。
  - Claude Code：同上，或写进 `AGENTS.md` 的引用。
- 前提：
  - 已连接的 BIM MCP，查 L4 对照表；没有对照表的 MCP，先按 Catalog 做一份。
  - 法例原文已在 `../Legislation/`。
  - harness 能执行代码（像素取色用，没有则改人工）。
- 已知缺口汇总表：从各层的 `[GAP]` 收集，每条指回所在文件。
- 验证依据：样例模型第 1 轮（2026-10-12 至 13）。只写「已验证」，不写样例的结论。
- 版本与维护：法例更新改 L1；换 MCP 加 L3-MCP + L4；新坑加进对应 AUD 文件。

### 4.2 RUN.md（编排协议，任何 harness 通用）

内容就是给 Agent 的运行规则，分为：

1. **开始前**：
   - 确认打开的文件和路径。
   - 确认是只读审核。
   - 选用 L4 对照表；如果当前 MCP 没有对照表，停下来说明。
2. **顺序**：A1 → 36 个 Task 的 L1（A2）→ 有原文与资料的 L2（A3）→ A04 汇总。
3. **判定规则**：
   - 状态词：Pass / Partial / Fail / Missing / N/A（附条件）/ N/A 待声明 / Unclear。
   - Unclear 不算 Pass，Missing 不算 Present（G11）。
   - 需要 AP 定的口径，两个都算，不替 AP 选。
4. **证据规则**：
   - 每条结论附元素 ID、数值、条文。
   - 标 `[FACT]` / `[INFERENCE]` / `[GAP]`。
   - 写「会推翻的情况」。
5. **安全**：
   - 只读。
   - 任何写入（包括「顺手修」）都不属于本包。
   - 查到要修的，记成修复建议。
6. **产出**：按 `templates/` 写 Audit Report；截图、CSV 放报告旁的 `_evidence/`。
7. **短 Prompt 模板**，三条：
   - 整套审核
   - 单个 Task
   - 回归

不出现任何 harness 专有命令。

### 4.3 L1-Domain（审核用的行业知识）

**共同格式**：每条带「出处」：文件、条文、版本，加上状态。状态只有两种：

- `已对原文`：本工作区 Knowledge 原文里核过。
- `[GAP]`：原文不在手。

| 文件 | 内容 |
| --- | --- |
| DK-AUD-001 硬性要求 | G1–G12 逐条：要求、出处（BIMGBPS §4.2–§4.4、§5.1）、对应 MA 编号 |
| DK-AUD-002 限值索引 | 表格：限值、数值、条文、原文摘句（≤ 1 句）、用于哪些 AUD、状态。例：reg 30(2)(a)(i) 1/10；APP-151 ¶4 10 %；APP-136 ¶6 1/4；Cap 123H 附表 3,960 m²；Cap 123I reg 5(5) 9 m² / 人；APP-152 Table 2 |
| DK-AUD-003 适用性 | 每个「if applicable」的判定树：输入（用途、面积、申请项）→ 适用 / 不适用 → 条文 → N/A 理由句模板 |
| DK-AUD-004 颜色 | Table 1 六色 RGB、ADM-9 材料色（只列已在图例中核过的）、地盘粉红、半色调判据（灰阶占比） |
| DK-AUD-005 勘误 | 1/8 与 8 % 的每一处（文件 + 行号）、SC 简表、Revit 版本门槛；每条写正确值和出处 |
| DK-AUD-006 缺的资料 | FS Code 2011 Part B / C / D、Cap. 172、APP-2、APP-130、APP-151 附录 A 各项接受准则；每条写影响哪些 AUD |

外部项目资料（地契、OZP、指明街道、测量图）**不放 L1**。它们由 AUD-000 的「项目输入清单」处理。

### 4.4 L2-Task-Logic（软件无关）

**AUD-000 审核总流程**：

- 三段 A1 / A2 / A3 的定义。
- 两层判定（L1 显示 / 形式，L2 指标）。
- 状态词、证据格式。
- N/A 规则。
- **项目输入清单**：Roadmap §04 的外部资料 + AP 决定。每项写：值、来源、日期、影响哪些 AUD；缺了就是 Unclear。
- 通用检查：
  - 表是不是模型生成的（图片表 → F1 类）。
  - 手填参数。
  - 半色调。
  - 标高格式与基准。

**AUD-A1 模型健康**：

- MA-1 至 MA-7 逐项：检查什么、判据、结果词、对应 DK-AUD-001。
- 不写工具名，只写要取得的信息，例如「各 Level 类型的标高基准设置」。

**AUD-V / S / A 每份的固定小节**：

```
# AUD-XXX <名称> · BIMGBPS §x.x.x
关联：TL 文件 · Roadmap 卡片 · MA 编号 · DK 条目
1. 适用性        → DK-AUD-003 的哪个判定；不适用时的 N/A 理由句
2. 要取得的信息  → 软件无关的数据项清单（例：每个面积方案中各 Area 的面积、名称、楼层、所在视图）
3. L1 检查项     → 按条文 (a)(b)(c) 逐项：查什么、怎么判
4. L2 计算与限值 → 公式 + DK-AUD-002 条目；缺原文 / 资料则写成 Unclear 条件
5. 常见坑        → 第 1 轮发现、换模型也可能出现的
6. 外部输入      → 指向 AUD-000 项目输入清单
7. 依赖          → 前后 Task、交叉校验（例：V10 ↔ S08）
8. GAP           → 本项特有的缺口
```

内容来源：现有 `gbp-audit-cards-*` 三份审核卡（已确认）。把其中的工具名、MCP 做法移到 L3-MCP，其余重组到上面的小节。

共用卡的项各自建文件，但写「同 AUD-xxx」并只补差异：

- S06 ↔ V07
- S15 ↔ V12
- S09 ↔ S17
- V03 ↔ V04

**AUD-REG 回归**：来自已确认的 `gbp-audit-regression`。基线、问题类表、关闭标准、副作用检查，去掉工具名。

### 4.5 L3-SOP

**SOP-AUD-manual**：人在 Revit 里怎么查，按 L2 的「要取得的信息」组织。重点是 MCP 盲点的人工抽查：

- 尺寸 Value Override：怎么找。
- 面积边界的缝隙、重叠、隐藏边界：怎么看。
- CAD 导入：Manage → Links / Imports。
- Revit 版本：About。
- 每项写「查到什么算有问题」。

**SOP-AUD-mcp-revit-mcp**：用 Autodesk revit-mcp（Experimental Technical Preview）执行 L2 的每一类信息获取。

- 写调用顺序、关键参数、单位（长度英尺、面积内部单位 ft²）、已知的坑。坑包括：
  - `HasValue` 报错
  - 明细表只能导出 CSV
  - 导出 PDF 固定 A3
  - 面积 0 = 未放置
- 每条注明「实测」或「待试」。
- 第 1 轮的做法都来自实测；新加的写「待试」。

### 4.6 L4-Capabilities

**CAP-binding-revit-mcp**：

- 表格：CAP-* / AGENT-* → revit-mcp 工具名 → 状态（Full / Partial / Missing）→ 实测 / 待试 → 备注。
- 只列功能 A 用到的能力。
- 新增 Agent 侧能力 `AGENT-IMAGE-SAMPLE`（导出图的像素取色），标为「建议加入 Catalog」。

**CAP-gaps**：每个 Missing / Partial，写：

- 影响哪些 AUD 检查
- 后果（只能 Unclear / 只能抽查）
- 人工补法（指向 SOP-AUD-manual 的哪一节）

已知 6 项：

| 缺口 | 影响 |
| --- | --- |
| 尺寸覆盖值 | §5.1.2 |
| 面积边界端点几何 | 缝隙 / 重叠 |
| CAD 导入 | — |
| Revit 版本 | — |
| LOD | — |
| 明细表截图 | 只能 CSV + 整张图纸导出 |

### 4.7 templates

- **audit-report-template.md**：Roadmap §05 格式，分 Header、Summary、Findings、Calculations、N/A 表、声明（readiness audit，非 BD / BA 批核）。
- **finding.schema.json**：在 `shared-issue.schema.json` 上扩展。新增字段：
  - `id`（F 编号）、`task`
  - `status`（状态词）
  - `clause`、`evidence`（元素 ID、数值）、`label`（FACT / INFERENCE / GAP）
  - `fix`、`fix_method`（manual / function-b / AP）
  - `overturn_if`

  `severity` 改用 Roadmap 的 Blocker / Major / Minor / Unclear。原 schema 是 blocker / warning / info，**两者不一致**，见第 6 节。
- **na-table-template.md**：Task、条文、理由句、条件、AP 确认（日期）。

### 4.8 可视化报告（2026-10-13 加入）

**已定**（操作者）：报告用英文；格式为 HTML + 截图文件夹；优先由脚本生成，脚本跑不了时由 Agent 按 HTML 模板填写；同一份结果数据生成两份报告：内部版和 AP / 客户版。

**产出**（每次审核一个文件夹，例：`audit-<日期>/`）：

```
audit-<date>/
  audit-results.json     审核结果（唯一的数据来源）
  report-bim.html        内部版
  report-ap.html         AP / 客户版
  assets/                截图、裁切图、取色对比图、CSV
```

两份 HTML 都只引用 `assets/` 里的相对路径；不连网，不用外部 CSS / JS / 字体。整个文件夹打包就能转发。

**数据**：`templates/audit-results.schema.json`。

| 顶层字段 | 内容 |
| --- | --- |
| `meta` | 项目、模型路径与版本、MCP、harness、日期、轮次（`round`）、包版本 |
| `verdict` | 能否原样提交（`submittable`: true / false）+ 前 3 个原因（引 F 编号） |
| `a1[]` | MA 编号、结果、证据、条文、`gap` |
| `tasks[]` | 每个 Task：`id`、名称、条款、适用性（含 N/A 理由句与条件）、`l1_status`、`l2_status`、检查项 `checks[]`（ID、结果、证据、`audience`）、计算 `calcs[]`（公式、数值、限值、条文、结果、口径）、`evidence_ids[]`、`finding_ids[]`、修改方向 `fix[]`（内容、方式 manual / function-b / AP、`audience`）、会推翻的情况 |
| `findings[]` | 按 `finding.schema.json` |
| `decisions[]` | 要 AP 决定的事：INP 编号、问题、选项、影响的 Task |
| `inputs[]` | 要外部提供的资料：INP 编号、资料、影响的 Task |
| `unclear[]` | 判不了的项：Task、原因类别（原文 / 资料 / 工具）、要提供什么 |
| `regression` | 可选：每个 F 的上一轮状态与本轮状态 |
| `evidence[]` | `id`、`file`（相对 `assets/`）、`kind`（view / sheet / crop / swatch / csv）、`caption`、`task`、`audience`（bim / both） |

**两种读者的过滤规则**（脚本按 `--audience` 执行）：

| 内容 | bim | ap |
| --- | --- | --- |
| 元素 ID、参数名、视图 ID | 显示 | 不显示（证据只写说明文字） |
| 工具名、GAP 编号、L1–L4 文件引用 | 显示 | 不显示 |
| `audience = bim` 的检查项、修改方向、证据 | 显示 | 不显示 |
| 标签 FACT / INFERENCE / GAP | 原样 | 改为 Verified / Inferred / Not determinable |
| 要 AP 决定的事（`decisions[]`） | 第 6 节「修改计划」内 | **放在总览之后的第一节** |
| 外部资料（`inputs[]`） | 列在 Unclear 一节 | 单独一节「Information required」 |
| 声明 | readiness audit，非 BD 批核 | 同左，并加「不代替 AP 的专业判断」 |

**报告各节**（outline 已与操作者确认）：

| # | 节 | bim | ap |
| --- | --- | --- | --- |
| 1 | Cover | ✓ | ✓ |
| 2 | Overview：结论 + 前 3 原因、L1 / L2 状态计数卡、Blocker / Major / Minor 计数、36 项状态格（点击跳转）、Blocker 清单 | ✓ | ✓ |
| 3 | Decisions required | （并入 6） | ✓ |
| 4 | Model health（A1） | ✓ | 只列 Fail / Unclear |
| 5 | Task breakdown：36 张卡，可按状态 / 类别 / 严重度筛选；卡内含适用性、L1 检查项、L2 计算、截图（缩略图点开看大图；取色对比色块）、F 编号、修改方向、会推翻的情况 | ✓ | ✓（按过滤规则） |
| 6 | Findings 总表（可排序） | ✓ | ✓（不含元素 ID） |
| 7 | Action plan：按人工 Revit / 功能 B / AP / 外部资料分组，组内按严重度和依赖排序 | ✓ | 只列 AP 与外部资料两组，其余合并为「Model corrections by the BIM team」 |
| 8 | N/A table（TL-A04） | ✓ | ✓ |
| 9 | Not determinable：Unclear 与 GAP | ✓ | ✓（GAP 改说明文字） |
| 10 | Regression comparison（有 `regression` 时） | ✓ | ✓ |
| 11 | Appendix：证据索引、包版本、对照表、条文出处 | ✓ | 只列条文出处 |

**状态颜色**：每个状态固定一种颜色，并同时显示文字（不只靠颜色区分）；浅色、深色主题都可读。

**生成方式**：

1. **脚本（优先）**：`report/render_report.py`，只用 Python 3 标准库。
   - 用法：`python render_report.py --results audit-results.json --audience bim|ap --out report-<audience>.html`
   - 先按 schema 的必填项和枚举值校验 `audit-results.json`，不合格就停，并列出哪一项。
   - 引用的 `assets/` 文件不存在时，列出来，不生成坏链接。
   - 不连网，不改输入。
2. **模板（后备）**：harness 不能执行代码时，Agent 按 `templates/report-template.html` 填写。模板内有每一节的占位和过滤规则说明。模板生成的报告要在封面注明「hand-filled from template」。

**截图规则**：

- 每个 Fail / Partial 的检查项，至少一张证据：视图或图纸导出、裁切放大，或取色对比。
- 明细表不能导出图像（GAP-06）：用整张图纸的导出代替。
- 取色对比图：取样色块与标准色块并排，注 RGB 值。由 `AGENT-IMAGE-SAMPLE` 产生；做不到时这一项写「not sampled」。
- 文件名：`<task>-<序号>-<kind>.png`。
---

## 5. 怎么验证

1. **结构自查**：
   - 54 个文件都在。
   - 每份 AUD 都有 8 个小节。
   - 每份 DK 条目都有出处和状态。
2. **层次自查**：在 L1、L2 里检索 revit-mcp 的 40 个工具名，结果必须为 0。
3. **限值核对**：DK-AUD-002 每条「已对原文」的，逐条回到 Knowledge 原文再核一次。
4. **对照第 1 轮**：
   - 把 audit-report 的 F1–F12、H1 和 36 项结论，逐条映射到负责找出它的 AUD 检查项。
   - 映射不到的，说明包有漏，要补。
   - 映射表放 `work/model-audit-design/_agent/round1-coverage.md`。
5. **报告**：用第 1 轮样例的数据写一份样本 udit-results.json（放 _agent/，不进包），两种读者各生成一次。检查：两份都能离线打开；AP 版不含元素 ID、工具名、GAP 编号；每个 Fail / Partial 都有证据；坏数据会被脚本拒绝。在浏览器里看一遍。
6. **独立可用性**：
   - 用「只有这个包」的视角，把一个 Task（S14）和 A1 走一遍，看有没有要靠本次对话才知道的东西。
   - 有的话，补进包里。
   - 你若同意，也可以另开一个干净的 Agent 来做这一步。不同意就由我自查。

---

## 6. 风险与待你决定的点

| # | 事项 | 我的默认做法 |
| --- | --- | --- |
| 1 | 法例原文不在仓库 | 引用写「文件 + 条文 + 版本」，路径用 `../Legislation/`；建议你把四份法例放进仓库 |
| 2 | `shared-issue.schema.json` 的 severity（blocker / warning / info）与 Roadmap（Blocker / Major / Minor）不一致 | 新 schema 用 Roadmap 的；旧 schema 不动，在 DK-AUD-005 记一笔 |
| 3 | `AGENT-IMAGE-SAMPLE` 不在 Catalog | 在 L4 里定义，标「建议加入 Catalog」 |
| 4 | 审核卡 Skill 与 L2 内容重复 | 包做完后再提议改成「指向包」，现在不动 |
| 5 | 第 1 轮只有一个模型（BD 样例），而且样例里所有图都已存在 | 「常见坑」注明来自样例；正常模型上「图不存在」的情况，在 AUD 里按 Missing / N/A 写清楚 |
| 7 | 报告脚本要 harness 能执行代码 | 不能执行时退回 HTML 模板，封面注明 |
| 8 | 截图多时文件夹大 | 截图压缩为 PNG、宽度上限 1600 px；原图不放进 assets |
| 6 | 文件数多（56） | L2 每份控制在一页左右；共用卡只写差异 |

---

## 7. 之后的步骤

1. 你审这份设计文档。
2. 我写实施计划，按层分批：L1 → L2（AUD-000、A1、Views、Schedules、Assembly、REG）→ L3 → L4 → templates → README / RUN → 验证。
3. 按计划执行，每批做完告诉你进度。
