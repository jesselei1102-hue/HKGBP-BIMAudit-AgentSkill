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
| L3 SOP | [L3-SOP/](L3-SOP/) | 人工在 Revit 里怎么取；用某个 MCP 怎么取（基准配方每步标能力）；提取文件的约定 [EXTRACT-FILES](L3-SOP/EXTRACT-FILES.md) | 换 Revit 版本、换 MCP |
| L4 能力 | [L4-Capabilities/](L4-Capabilities/) | 能力清单 [CAP-catalog](L4-Capabilities/CAP-catalog.md)、接入新 MCP 的步骤 [CAP-onboarding](L4-Capabilities/CAP-onboarding.md)、各 MCP 的能力对照、能力缺口 | 换 MCP |
| 模板与报告 | [templates/](templates/)、[report/](report/) | 结果 schema、finding schema、N/A 表、HTML 模板、报告生成脚本 | 报告格式改变 |
| Skills | [skills/](skills/) | 6 个 `SKILL.md`：给支持 Skill 的 harness 自动触发；只指向本包，不含规则 | 加组、改命令 |
| 提取转换 | [tools/extract/](tools/extract/) | 把 MCP 原样回传转成提取文件（`g1_extract.py`、`g2_extract.py`、`g3_extract.py`、`g4_extract.py`、`g5_extract.py`，共用 `mcp_formats.py`；认 revit-mcp 与 mcp-servers-for-revit 两种格式） | 换 MCP 时加适配器 |
| 对话窗口（可选） | [app/](app/) | `gbp-audit` MCP server：在对话里弹出「选检查」和「总览 / 确认关口」两个窗口；要 Node.js ≥ 20。见 [app/README.md](app/README.md)、RUN.md §6d | 改窗口或任务清单 |
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

## 36 个 Task 与法例对照

每个 Task 查什么、对应 BIMGBPS 哪一节、第二层（L2 合规计算）引哪条法例或 PNAP。本表只是索引：数值与原文摘句只在 [DK-AUD-002 限值索引](L1-Domain/DK-AUD-002_Limits_Index.md)（`LIM-nn`），适用性与 N/A 理由句只在 [DK-AUD-003 适用性](L1-Domain/DK-AUD-003_Applicability.md)（`APL-nn`），以那两份和法例原文为准。

- 法例简称：**Cap. 123** = Buildings Ordinance；**B(P)R** = Cap. 123F Building (Planning) Regulations；**Cap. 123H** = Building (Refuse Storage and Material Recovery Chambers and Refuse Chutes) Regulations；**Cap. 123I** = Building (Standards of Sanitary Fitments, Plumbing, Drainage Works and Latrines) Regulations。
- **FS Code** = Code of Practice for Fire Safety in Buildings 2011，原文不在本包，标 `[GAP]` 的 L2 一律记 Unclear（[DK-AUD-006](L1-Domain/DK-AUD-006_Missing_Sources.md)）。
- 「只查 BIMGBPS」= 只有图面 / 格式要求（L1），没有法例限值。

### 计算表（Schedules）

| Task | 是什么 | BIMGBPS | 法例 / PNAP 条文 | 引用 |
| --- | --- | --- | --- | --- |
| [S01](L2-Task-Logic/Schedules/AUD-S01_Drawing_List.md) | 图纸目录：是不是 Sheet List 明细表，与模型图纸逐张对上 | §5.3.1 | 只查 BIMGBPS | — |
| [S02](L2-Task-Logic/Schedules/AUD-S02_Site_Area_Calc.md) | 地盘面积计算 | §5.3.2 | B(P)R reg 23(2)（不计街道、后巷）；PNAP ADM-21（取整） | LIM-02、LIM-14 |
| [S03](L2-Task-Logic/Schedules/AUD-S03_Coordinates.md) | 地界坐标表：HK1980 坐标、方位角、边长 | §5.3.3 | 只查 BIMGBPS（§5.1.3 坐标格式） | LIM-03 |
| [S04](L2-Task-Logic/Schedules/AUD-S04_Dev_Schedule.md) | 发展摘要表：GFA、SC / PR、绿化、车位、高度、单位数、UFA，逐栏对来源 Task | §5.3.4 | 不另引条文；各栏跟随来源 Task（高度 B(P)R reg 23(1)，绿化 APP-152 Table 2） | LIM-13、LIM-29 |
| [S05](L2-Task-Logic/Schedules/AUD-S05_SC_PR_Summary.md) | 场地类别 + 上盖面积 / 地积比率汇总 | §5.3.5 | B(P)R reg 18A（场地类别）、reg 20、21 与附表 1（准许 SC / PR）、reg 23(1)–(3)(a)；Cap. 123 s.2（用途） | LIM-11 至 LIM-16、APL-01 |
| [S06](L2-Task-Logic/Schedules/AUD-S06_Open_Space_Calc.md) | 休憩用地计算（只适用于住用） | §5.3.6 | B(P)R reg 25(1)(a) 与附表 2 | LIM-17、APL-02 |
| [S07](L2-Task-Logic/Schedules/AUD-S07_GFA_Concession_Req.md) | GFA 豁免前置条件（BEAM Plus、APP-152 等） | §5.3.7 | PNAP APP-151 ¶4（10 % 上限）、¶5(a)（必要设施）、¶6（前置条件）、¶10（生效日期） | LIM-23 至 LIM-25、APL-06 |
| [S08](L2-Task-Logic/Schedules/AUD-S08_GFA_Concession_List.md) | GFA 豁免清单，与 V10 交叉校验 | §5.3.8 | B(P)R reg 23(3)(a)（GFA 定义）；PNAP APP-151 ¶4 | LIM-15、LIM-23 |
| [S09](L2-Task-Logic/Schedules/AUD-S09_Lift_Shaft.md) | 电梯井表：井道几何 | §5.3.17 | PNAP APP-89 ¶5（适用建筑类别）、¶8（轿厢 / 井道下限） | LIM-27、APL-05 |
| [S10](L2-Task-Logic/Schedules/AUD-S10_Exit_Doors_Routes.md) | 最少出口门数与走火通道：人数、要求与实设出口数 / 宽度 | §5.3.10 | FS Code Part B `[GAP]` | LIM-30 |
| [S11](L2-Task-Logic/Schedules/AUD-S11_Discharge_Value.md) | 逃生楼梯排放值（DV）：每层人数、每梯分担人数 | §5.3.11 | FS Code Part B `[GAP]` | LIM-30 |
| [S12](L2-Task-Logic/Schedules/AUD-S12_FRR_Compartment.md) | 耐火时效 / 防火分区表：分区面积、体积，与 V08 一一对应 | §5.3.12 | FS Code Part C `[GAP]` | LIM-32 |
| [S13](L2-Task-Logic/Schedules/AUD-S13_Sanitary_Fitments.md) | 洁具数量：按 UFA 算人数，比实设洁具 | §5.3.13 | Cap. 123I Part II 类别；reg 5(5)（office 每 9 m² 1 人）、reg 6（公众娱乐场所）；Cap. 172 定义 `[GAP]` | LIM-21、LIM-22、APL-08 |
| [S14](L2-Task-Logic/Schedules/AUD-S14_Window_Area_Calc.md) | 窗面积计算：采光（玻璃 ≥ 1/10）、通风（可开启 ≥ 1/16），与 V13 同审 | §5.3.14 | B(P)R reg 30(2)(a)(i)(ii)、reg 36(2)(3)（便溺房间） | LIM-06、LIM-07、LIM-10、APL-10 |
| [S15](L2-Task-Logic/Schedules/AUD-S15_Refuse_RMRC.md) | 垃圾房及物料回收房：UFS 门槛、最小面积 | §5.3.15 | Cap. 123H reg 3、3A 与附表；PNAP APP-35 ¶5 | LIM-19、LIM-20、APL-03 |
| [S16](L2-Task-Logic/Schedules/AUD-S16_TBE_Room.md) | 电讯及广播设备（TBE）房面积 | §5.3.16 | B(P)R reg 28A；PNAP APP-84 注 2（MAF） | LIM-18、APL-04 |
| [S17](L2-Task-Logic/Schedules/AUD-S17_Lift_Shaft_GFA.md) | 电梯井表：GFA 豁免计算（与 S09 同一张表） | §5.3.17 | PNAP APP-89 ¶5、¶8 | LIM-27、APL-05 |
| [S18](L2-Task-Logic/Schedules/AUD-S18_List_of_Modifications.md) | 修改清单：须按 Form BA16 申请的修改 / 豁免 | §5.3.9 | Form BA16；B(P)R reg 23(3)(a) 与 23(3)(b) 的区分；PNAP ADM-2 附录 E、ADV-33 附录 A3 | APL-07 |

### 图（Views）

| Task | 是什么 | BIMGBPS | 法例 / PNAP 条文 | 引用 |
| --- | --- | --- | --- | --- |
| [V01](L2-Task-Logic/Views/AUD-V01_Block_Key_Plan.md) | 位置图 / 索引图：地界、街道阔度、坐标 | §5.2.2 | B(P)R reg 18A(1)（指明街道 ≥ 4.5 m）；ADM-21（地盘面积取整） | LIM-02、LIM-03、LIM-11 |
| [V02](L2-Task-Logic/Views/AUD-V02_Floor_Plans.md) | 各层平面图 | §5.2.3 | FS Code Part B `[GAP]`（出口） | LIM-03、LIM-30 |
| [V03](L2-Task-Logic/Views/AUD-V03_Sections.md) | 剖面图：标高、建筑物高度 | §5.2.4 | B(P)R reg 23(1)（高度由街道平均水平量起） | LIM-03、LIM-13 |
| [V04](L2-Task-Logic/Views/AUD-V04_Elevations.md) | 立面图：标高、建筑物高度 | §5.2.4 | B(P)R reg 23(1) | LIM-03、LIM-13 |
| [V05](L2-Task-Logic/Views/AUD-V05_Details.md) | 典型详图 | §5.2.5 | 只查 BIMGBPS | LIM-03 |
| [V06](L2-Task-Logic/Views/AUD-V06_EVA_Diagram.md) | 紧急车辆通道（EVA）图 | §5.2.6 | PNAP APP-136 ¶6（主要立面 ≥ 周界 1/4）；FS Code Part D `[GAP]` | LIM-26、LIM-31 |
| [V07](L2-Task-Logic/Views/AUD-V07_Open_Space.md) | 休憩用地图（只适用于住用） | §5.2.7 | B(P)R reg 25(1)(a) 与附表 2；Cap. 123 s.2（用途） | LIM-17、APL-01、APL-02 |
| [V08](L2-Task-Logic/Views/AUD-V08_Fire_Compartment.md) | 防火分区图 | §5.2.8 | FS Code Part C `[GAP]` | LIM-32 |
| [V09](L2-Task-Logic/Views/AUD-V09_SC_Diagram.md) | 地盘面积及上盖面积图 | §5.2.9 | B(P)R reg 20、21 与附表 1；ADM-21 | LIM-02、LIM-16 |
| [V10](L2-Task-Logic/Views/AUD-V10_GFA_Diagram.md) | GFA 图：逐层面积与豁免着色，与 S08 交叉校验 | §5.2.10 | B(P)R reg 23(3)(a)；PNAP APP-151 ¶4 | LIM-15、LIM-23 |
| [V11](L2-Task-Logic/Views/AUD-V11_UFA_Diagram.md) | 实用楼面面积（UFA）图；数值供 S13、S04 用 | §5.2.11 | 只查 BIMGBPS | — |
| [V12](L2-Task-Logic/Views/AUD-V12_UFS_Diagram.md) | 实用楼面空间（UFS）图，跟随 S15 | §5.2.12 | Cap. 123H reg 3 与附表 | LIM-19、APL-03 |
| [V13](L2-Task-Logic/Views/AUD-V13_Prescribed_Windows.md) | 订明的窗图：窗面向的矩形水平面、遮挡斜面，与 S14 同审 | §5.2.13 | B(P)R reg 30、31(1)–(3)、36 | LIM-06 至 LIM-10、APL-10 |
| [V14](L2-Task-Logic/Views/AUD-V14_SBD_Compliance.md) | 可持续建筑设计图：楼宇间距、后退、绿化 | §5.2.14 | PNAP APP-152 ¶3（间距门槛）、Table 2（绿化）；后退门槛 `[GAP]` | LIM-28、LIM-29、APL-09 |

### 整套与提交（Assembly）

| Task | 是什么 | BIMGBPS | 法例 / PNAP 条文 | 引用 |
| --- | --- | --- | --- | --- |
| [A01](L2-Task-Logic/Assembly/AUD-A01_Sheet_Assembly.md) | 图纸组装：图框参数、项目信息、图号 | §4.3(f)、§5.5.1–5.5.2、§6.3–6.4 | 只查 BIMGBPS | DK-AUD-001 G9 |
| [A02](L2-Task-Logic/Assembly/AUD-A02_Colour_Coding.md) | GFA 着色与修订着色：逐色取样比图例 | §5.1.4、Table 1、§5.4 | 只查 BIMGBPS（GFA 图用 Table 1；楼层平面另用 PNAP ADM-9 色系，逐色 RGB 原文 `[GAP]`） | DK-AUD-004 |
| [A03](L2-Task-Logic/Assembly/AUD-A03_Export.md) | 导出：文件格式、≤ 500 MB、Revit ≥ 2017、链接、PDF 尺寸 | §4、§6 | 只查 BIMGBPS（§4.3(b)(c)） | LIM-04、LIM-05 |
| [A04](L2-Task-Logic/Assembly/AUD-A04_Submission_Validation.md) | 提交前总核：汇总 A1 与其余各 Task，判能不能原样提交；含 N/A 汇总表 | §4.2、§5.2.1、§5.3、§5.5 | 不另引条文；汇总上面各项 | DK-AUD-001、DK-AUD-003 |

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
| 已连接 BIM MCP，且 [L4-Capabilities](L4-Capabilities/) 里有它的能力对照表（现有：`CAP-binding-revit-mcp`、`CAP-binding-mcp-servers-for-revit`） | 先按 Capability Catalog 为该 MCP 做一份对照表和 SOP，再审（RUN.md 规则） |
| 各组要用的能力在对照表里是 Full 或 Partial；agent 按当前 MCP 暴露的工具对照，不按 MCP 名称选 | 对照表里 Missing 或 Partial 缺的部分，相关检查记 Unclear，并引 [CAP-gaps](L4-Capabilities/CAP-gaps.md) 的 GAP 编号 |
| 法例原文在 `../Legislation/`（cap123、cap123f、cap123h、cap123i） | L2 一律 Unclear；限值索引不能代替原文 |
| BIMGBPS corpus、PNAP 在 `../source/` | 同上 |
| 想用对话窗口：Node.js ≥ 20，并注册 `app/` 的 server | 用 RUN.md §7 的文字指令，流程相同 |
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
- 换 MCP：按 [CAP-onboarding](L4-Capabilities/CAP-onboarding.md) 加 `L3-SOP/SOP-AUD-mcp-<名称>.md` 和 `L4-Capabilities/CAP-binding-<名称>.md`（例：mcp-servers-for-revit 的两份）；回传格式不认得时在 `tools/extract/` 加适配器，输出对齐 [EXTRACT-FILES](L3-SOP/EXTRACT-FILES.md)。
- 发现新坑：加进对应 AUD 的「常见坑」。
- 报告格式：改 `templates/`（样式在 `report-template.html` 的 `report-css`）与 `report/render_report.py`，两者一起改。
- 改完跑测试和包检查（`model-audit-design/_agent/`，只用标准库；只在维护者本地，不随 repo 发布）：每个 `python -I test_*.py` 单独跑；`python -I check_package.py --layer all` 查文件、链接、Skill。
