# Model Audit · 四层包

> 给 AP / 客户看的英文简明版：[README.simple.md](README.simple.md)

Roadmap **功能 A（Model Audit）** 按四层架构的实现：只读审核一个 Revit 模型能不能拿来做 GBP Stage I 提交。范围：

- A1 模型健康
- A2 数据就绪（36 个 Task 的 L1）
- A3 合规计算（L2）
- 回归

产出一份结构化结果 `audit-results.json` 和两份英文可视化报告：BIM 团队版、AP / 客户版。

本包可在任何能连 BIM MCP 的 harness 里运行（Cursor、Hermes、Claude Code 等），不依赖任何 harness 专有功能。

本文件和 [RUN.md](RUN.md) 命令里的 `Model Audit/` 指本包所在的文件夹（包根 = 同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹，例：本 repo 的 `model-audit/`），按实际位置替换。

## 四层

| 层 | 文件夹 | 内容 | 换什么时要改 |
| --- | --- | --- | --- |
| L1 行业知识 | [L1-Domain/](L1-Domain/) | 硬性要求、限值索引、适用性判定、颜色标准、勘误、缺少的原文 | 法例 / PNAP 更新 |
| L2 任务逻辑 | [L2-Task-Logic/](L2-Task-Logic/) | 总流程、模型健康、36 个 Task 的审核逻辑、回归；软件无关，不出现工具名 | 判定逻辑改变 |
| L3 SOP | [L3-SOP/](L3-SOP/) | 人工在 Revit 里怎么取；用某个 MCP 怎么取 | 换 Revit 版本、换 MCP |
| L4 能力 | [L4-Capabilities/](L4-Capabilities/) | 能力 ID → MCP 工具对照、能力缺口 | 换 MCP |
| 模板与报告 | [templates/](templates/)、[report/](report/) | 结果 schema、finding schema、N/A 表、HTML 模板、报告生成脚本 | 报告格式改变 |
| Skills | [skills/](skills/) | 6 个 `SKILL.md`：给支持 Skill 的 harness 自动触发；只指向本包，不含规则 | 加组、改命令 |
| 提取转换 | [tools/extract/](tools/extract/) | 把 MCP 原样回传转成提取文件（`g1_extract.py`、`g2_extract.py`、`g3_extract.py`、`g4_extract.py`、`g5_extract.py`，共用 `mcp_formats.py`；认 revit-mcp 与 mcp-servers-for-revit 两种格式） | 换 MCP 时加适配器 |
| 执行工具 | [tools/](tools/) | 每组的分析脚本（只读提取文件 → 分析 JSON + 屏幕摘要）、通用 Excel / HTML 报告、汇总成 audit-results.json；只用 Python 标准库（取色要 Pillow） | 规则或提取格式改变 |

### 合并同类项后的六组

| 组 | Task | 规格（L2） | 配方（L3） | 工具 |
| --- | --- | --- | --- | --- |
| G1 | S14（V13 共用） | [AUD-S14 §9](L2-Task-Logic/Schedules/AUD-S14_Window_Area_Calc.md) | R-S14 | `tools/s14_lv/` |
| G2 | S13、S10、S11、S15、S16 | [G2](L2-Task-Logic/Groups/G2_Room_Use.md) | R-G2 | `tools/room_use/` |
| G3 | S02、V09、S05、V10、S08、S07、V11、V12、V14、V06、V08、S12、V07、S06 | [G3](L2-Task-Logic/Groups/G3_Area_Scheme.md) | R-G3 | `tools/area_scheme/` |
| G4 | V01–V05、V13、A01–A03（及 V08 / V10 / V11 图面项） | [G4](L2-Task-Logic/Groups/G4_Drawings.md) | R-G4 | `tools/drawings/` |
| G5 / G6 | S01、S03、S04、S09、S17、S18、A04；A1 | [G5 / G6](L2-Task-Logic/Groups/G5_Lists_G6_Model_Health.md) | R-G5 | `tools/lists_health/` |

每组都是两段：先分析（提取文件 → 分析 JSON + 屏幕摘要，操作者确认），再出报告（Excel + HTML，只读分析 JSON）。规则见 [AUD-000 §10](L2-Task-Logic/AUD-000_Audit_Flow.md)。

## 读取顺序

1. 本文件 → [RUN.md](RUN.md)（运行规则与短 Prompt）。
2. [AUD-000](L2-Task-Logic/AUD-000_Audit_Flow.md)（总流程、状态词、项目输入清单、通用检查）。
3. 按 Task 读对应的 `AUD-*`；执行时查 L3（怎么取）和 L4（工具与缺口）。
4. 限值、适用性只信 L1；L1 只是索引，原文在 `../Legislation/`、`../source/`。

## 四种跑法

| 跑法 | 什么时候用 | 规则 |
| --- | --- | --- |
| 整套审核 | 第一次审一个模型：A1 + 36 个 Task，出两份总报告 | [RUN.md](RUN.md) §2–§6 |
| 逐组（两段式） | 平时的做法：G1 → G5 依次提取、分析、操作者确认、出组报告，最后汇总 | RUN.md §6b |
| 单个 Task | 只改了一处、只想复查一项（例：S10）；用 `--tasks` 只跑这一项，再用 `--update` 并回总结果，只有这一项会变 | RUN.md §6c、[AUD-000 §10.4](L2-Task-Logic/AUD-000_Audit_Flow.md) |
| 回归 | 模型修改后，与上一次的 `audit-results.json` 比 | [AUD-REG](L2-Task-Logic/AUD-REG_Regression.md) |

各跑法的短 Prompt 在 RUN.md §7。

## Skills（自动触发入口）

[skills/](skills/) 里有 6 个标准 `SKILL.md`（name + description 头），让 harness 在操作者只说「审 S14」「跑面积方案组」时自动找到本包。Skill 只写何时用、两段流程、命令和指向；规则只在 L1–L4，不复制。

| Skill | 用于 |
| --- | --- |
| `gbp-model-audit` | 总入口：整套审核、回归、选组 |
| `gbp-audit-g1-lighting-ventilation` | G1：S14、V13 |
| `gbp-audit-g2-room-use` | G2：S13、S10、S11、S15、S16 |
| `gbp-audit-g3-area-scheme` | G3：14 个面积方案 Task |
| `gbp-audit-g4-drawings` | G4：V01–V05、V13、A01–A03 |
| `gbp-audit-g5-lists-health` | G5 / G6：S01、S03、S04、S09、S17、S18、A04、A1 |

安装：把 `skills/` 下的 6 个文件夹整个复制（或链接）到该 harness 的 Skill 目录；包本身留在原处，Skill 运行时按「同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹」找包根。

**不用手动装**：运行审核的 Agent 按 [RUN.md](RUN.md) §1 第 0 步自己检查、安装和更新（只复制文件，不改内容；装完告诉操作者，新开对话后生效）。也可以直接对 Agent 说：「Install the Agent Skills from `Model Audit/skills/` as RUN.md §1 step 0 says.」

| Harness | Skill 目录（项目级 / 用户级） |
| --- | --- |
| Claude Code | `.claude/skills/` / `~/.claude/skills/` |
| Cursor | `.cursor/skills/` 或 `.agents/skills/` / `~/.cursor/skills/`（也读 `.claude/skills/`） |
| Hermes | `~/.hermes/skills/`（可放一个分类子文件夹，或把本包 `skills/` 加为外部 Skill 目录） |
| 其他 | 支持 `SKILL.md` 的按其文档；不支持的用下面的手动方式 |

## 各 harness 怎么用（手动）

- **Cursor**：在对话里 `@Model Audit/RUN.md`，再说「Run a full model audit」或用 RUN.md 里的短 Prompt。
- **Hermes**：把 `RUN.md` 作为任务说明载入，同时给它读 `Model Audit/` 文件夹的权限。
- **Claude Code**：在 `AGENTS.md` / `CLAUDE.md` 里加一行引用 `Model Audit/RUN.md`，或在对话里直接让它读 RUN.md。
- 其他 harness：同理。只要能读文件、调用 MCP，最好也能执行 Python。

## 前提

| 前提 | 没有时 |
| --- | --- |
| 已连接 BIM MCP，且 [L4-Capabilities](L4-Capabilities/) 里有它的对照表（现有：`CAP-binding-revit-mcp`） | 先按 Capability Catalog 为该 MCP 做一份对照表和 SOP，再审（RUN.md 规则） |
| G4、G5 的提取要 revit-mcp（mcp-servers-for-revit 没有房间边界、图纸、图纸上的视图、明细表清单这几类工具）；G1–G3 两个 MCP 都可以，`tools/extract/` 转出的提取文件相同 | 只连 mcp-servers-for-revit 时，G4、G5 缺的项记 Unclear |
| 法例原文在 `../Legislation/`（cap123、cap123f、cap123h、cap123i） | L2 一律 Unclear；限值索引不能代替原文 |
| BIMGBPS corpus、PNAP 在 `../source/` | 同上 |
| harness 能执行 Python 3 | 颜色取样改人工（L3 manual）；报告改用 HTML 模板手填，封面注明 |

## 报告

每次审核一个文件夹。整套审核（汇总后）：

```
audit-<date>/
  audit-results.json    审核结果（按 templates/audit-results.schema.json）
  decisions.json        AP 决定清单（可选；build_results.py --decisions）
  assets/               截图、裁切图、取色对比图、CSV
  report-bim.html       BIM 团队版
  report-ap.html        AP / 客户版
```

逐组或单个 Task 跑时，每组另有：

```
audit-<date>-<组>/
  _raw/                 MCP 原样回传（不手抄）和 tools/extract/ 转出的提取文件
  *_analysis_*.json     分析结果（G1 按 s14-analysis.schema.json，G2–G5 按 task-analysis.schema.json）
  analysis_console.txt  屏幕摘要，含「Readings to check」
  GBP_*.html / .xlsx    组报告（HTML 内嵌待核对的裁切图；Excel 有 Readings 表）
  assets/               有证据图时
```

样例模型的运行结果（2026-10-13 的整套审核和 G1–G5 各组）不随本 repo 发布。

生成（优先）：

```
python "Model Audit/report/render_report.py" --results audit-<date>/audit-results.json --audience bim --out audit-<date>/report-bim.html
python "Model Audit/report/render_report.py" --results audit-<date>/audit-results.json --audience ap  --out audit-<date>/report-ap.html
```

- 脚本只用标准库；先校验数据，不合格不生成（exit 2），缺截图不生成（exit 3）。
- AP 版自动去掉元素 ID、工具名、GAP 编号和标为 `bim` 的内容；把「Decisions required」放在总览之后。
- 不能执行 Python 时：按 [templates/report-template.html](templates/report-template.html) 的注释手填，`meta.filled_by = "template"`。

## 已知缺口

| 缺口 | 影响 | 详见 |
| --- | --- | --- |
| 尺寸覆盖值读不到 | §5.1.2 只能查图片表；手改尺寸要人工抽查 | [CAP-gaps](L4-Capabilities/CAP-gaps.md) GAP-01 |
| 面积边界端点读不到 | 小缝隙、重叠、隐藏边界查不出（退件高风险） | GAP-02 |
| CAD 导入查不到 | V05、自包含检查可能漏 | GAP-03 |
| Revit 版本、插件依赖读不到 | 版本：harness 能读模型文件时由 `tools/drawings/rvt_info.py` 补上，否则只能推断；插件依赖（MA-1.6）仍只能推断 | GAP-04 |
| 无 LOD 判据 | MA-3.3 只能人工抽查 | GAP-05 |
| 明细表不能导出图像 | 截图用整张图纸代替 | GAP-06 |
| MCP 不回传开口所属房间 | 已由 `tools/s14_lv/analyze.py` 按几何补上（每条带匹配方式与置信度）；仍缺 reg 31「面向室外」检查和百叶净通风面积，要人工核对 V13 图、向 AP 取百叶资料（INP-17） | GAP-07 |
| 图纸上的读数（表值、坐标、街道、附录等）靠读图 | 脚本判不了裁切图是否满足条文：组报告的「Readings to check」要操作者对着裁切图逐条核对；无裁切图的 PASS 一律改记 Unclear | RUN.md §6b |
| FS Code 2011 Part B / C / D | V02、V06、V08、S10–S12 的 L2 = Unclear | [DK-AUD-006](L1-Domain/DK-AUD-006_Missing_Sources.md) M-01 至 M-03 |
| Cap. 172、APP-2、APP-130、APP-151 附录 A 准则、APP-152 后退、ADM-9 色表 | S13、S18、V13、S07 (g)、V14、V02–V05 的部分判定 | DK-AUD-006 M-04 至 M-09 |
| BIMGBPS 新版 / ESH 介质；附表 1 电子版 | G9、A03、S05 | DK-AUD-006 M-10、M-11 |
| 仓库现有文件的错误（1/8、8 %、SC 简表、版本门槛、severity 分级） | 以原文为准 | [DK-AUD-005](L1-Domain/DK-AUD-005_Errata.md) |
| 粉红 RGB、半色调判据为本包约定 | V01、GEN-03 | [DK-AUD-004](L1-Domain/DK-AUD-004_Colour_Standards.md) |
| 未试的 MCP 做法（窗 / 嵌板、门净宽、明细表公式字段） | S14、V13、S10、GEN-02 | [SOP-AUD-mcp-revit-mcp](L3-SOP/SOP-AUD-mcp-revit-mcp.md)「待试」 |

## 验证依据

- 已在 BD 样例模型（`GBP_Revit_Templates_R27`，2026-10-12 至 13，第 1 轮功能 A 与功能 B 后回归准备）上验证：第 1 轮的每个发现都能对应到本包的检查项。
- 2026-10-14 至 15 在 Cursor 里用同一模型跑了整套（revit-mcp 和 mcp-servers-for-revit 两种 MCP）：找出的三个包内错误（制表符分隔的明细表 CSV、G5 车位计数、G4 未读读数被当作已读）已修；修后 G2 结果与原有运行逐项相同。
- 只在这一个模型上验证过，还没在其他项目上试。「常见坑」来自该样例。正常项目模型上，最常见的情况可能是图表根本不存在：按各 AUD 的「没有该图 / 表时」判。

## 维护

- 法例更新：改 L1（DK-AUD-002 的行与原文）。
- 换 MCP：加 `L3-SOP/SOP-AUD-mcp-<名称>.md` 和 `L4-Capabilities/CAP-binding-<名称>.md`。
- 发现新坑：加进对应 AUD 的「常见坑」。
- 报告格式：改 `templates/`（样式在 `report-template.html` 的 `report-css`）与 `report/render_report.py`，两者一起改。
- 改完跑测试和包检查（在 repo 的 `model-audit-design/_agent/`，只用标准库）：每个 `python -I test_*.py` 单独跑；`python -I check_package.py --layer all` 查文件、链接、Skill。
