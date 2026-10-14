# AUD-000 · 审核总流程

Layer 2，与软件无关。所有 AUD 文件都以本文件为前提。执行时要「取得的信息」怎么拿，见 L3：人工用 [SOP-AUD-manual](../L3-SOP/SOP-AUD-manual.md)，MCP 用对应的 SOP-AUD-mcp-* 文件。

## 1. 三段

| 段 | 内容 | 文件 |
| --- | --- | --- |
| A1 模型健康 | 与具体 Task 无关的模型级检查（MA-1 至 MA-7） | [AUD-A1](AUD-A1_Model_Health.md) |
| A2 数据就绪 | 每个 Task 要用的图、表、数据是否齐、显示是否对 = 各 AUD 的 **L1** | Views / Schedules / Assembly 下 36 份 |
| A3 合规计算 | 有原文限值和项目资料时，按条文计算 = 各 AUD 的 **L2** | 同上 |

顺序：A1 → 36 个 Task 的 L1 → 能判的 L2 → [AUD-A04](Assembly/AUD-A04_Submission_Validation.md) 汇总。

## 2. 两层判定

- **L1（显示 / 形式）**：BIMGBPS 条文要求的内容在不在、是不是由模型生成、显示格式对不对。
- **L2（指标）**：数值按法例 / PNAP 是否合规。
- 两层分开写，不能互相抵消。例：表是图片（L1 Fail），即使数字算得对（L2 Pass），L1 仍是 Fail。

## 3. 状态词

| 状态 | 用于 |
| --- | --- |
| Pass | 条文各项都有，且对 |
| Partial | 部分项缺或不对 |
| Fail | 关键项不对（例：表是图片） |
| Missing | 适用、但图 / 表不存在 |
| N/A（附条件） | 已按 [DK-AUD-003](../L1-Domain/DK-AUD-003_Applicability.md) 判为不适用，理由句与条件已写出 |
| N/A 待声明 | 判为不适用，但图纸上还没有 N/A 声明 |
| Unclear | 缺原文、缺资料或工具读不到，判不了 |

规则：

- Unclear 不算 Pass；Missing 不算 Present（G11）。
- 「Missing」与「N/A 待声明」要分开：前者要补图表，后者只要补声明。

## 4. 证据格式

每条结论都写：

1. 元素 ID 或视图 / 图纸 ID，以及数值（带单位、三位小数）。
2. 条文（BIMGBPS 条款，加 `LIM-nn` / `APL-nn`）。
3. 标签：`[FACT]`（工具结果或原文）/ `[INFERENCE]`（推断）/ `[GAP]`（读不到或没有资料）。
4. 会推翻的情况：一句话，说什么事实出现会改变结论。

Findings 按 [finding.schema.json](../templates/finding.schema.json) 记录。

## 5. N/A 规则

- 只按 DK-AUD-003 的 APL 判定，理由句用其模板。
- 必带条件「AP 确认」。
- 全部 N/A 汇总到 TL-A04 的 N/A 表（[na-table-template](../templates/na-table-template.md)）。

## 6. 项目输入清单

模型里没有、要向人取得的资料。缺了的，相关 L2 记 Unclear，写「须 INP-nn」。

| ID | 资料 | 用于 | 来源 |
| --- | --- | --- | --- |
| INP-01 | Lease Plan / Land Survey Plan、Lot / IL 编号 | S02、S03、V01、S05 | 地契、测量师（ADM-21） |
| INP-02 | 指明街道（specified streets）与场地类别 | V01、S05、S06、V07 | AP 判定 + 街道资料 |
| INP-03 | 许可 PR / SC | S05、V09、GFA 链 | OZP、地契、Cap. 123F 附表 1 |
| INP-04 | 高度限制 mPD、mean street level | V03、V04 | OZP、地契、JPN 5 |
| INP-05 | 周边街道、开放空间（判窗的朝向） | V13、S14 | 场地模型、测量图 |
| INP-06 | 用途、occupancy factor、男女人数 | S10、S11、S13 | 设计说明、FS Code |
| INP-07 | APP-151 / APP-152 各豁免项的设计参数与证明（含 BEAM Plus 注册、目标评级） | S07、S08、V14 | 设计团队、顾问 |
| INP-08 | 升降机工程师评估（APP-89 ¶8(c)） | S17 | RLE / BSE |
| INP-09 | BD File Reference、Consent date、AP 资料、地址 | A01、S04 | 项目行政 |
| INP-10 | 修改 / 豁免申请清单（Form BA16） | S18 | AP |
| INP-11 | **AP 决定**：建筑高度口径 | V03、V04、S04、S05 | AP |
| INP-12 | **AP 决定**：用途分类（住用 / 非住用、洁具类别、是否商业建筑物） | V07、S06、S13、S15、V12、S16 | AP |
| INP-13 | **AP 决定**：各豁免项保留还是撤回 | S07、S08、S18、V10 | AP |
| INP-14 | **AP 决定**：各 N/A 的确认 | 全部 N/A 项、A04 | AP |
| INP-15 | **AP 决定**：提交哪个文件版本 | A1、A03 | AP |
| INP-16 | **AP 决定**：标高基准（项目基点还是测量点；HKPD 零点依据） | A1 MA-2.4、V01–V04、GEN-04 | AP + 测量资料 |
| INP-17 | **AP 决定**：其他计算口径（例：S14 表上的 notional area 依据） | 视情况 | AP |

每项记录：值、来源、日期、谁确认的。值变了，受影响的 AUD 要重判。

## 7. 判定规则（全部 AUD 适用）

1. **法例原文不在 `../Legislation/` 时**：L2 一律记 Unclear，写「须 Legislation/<文件>」。不凭记忆或转述文件引用数值。[DK-AUD-002](../L1-Domain/DK-AUD-002_Limits_Index.md) 只是索引，不能代替原文。
2. **AP 未决定的口径**（INP-11 至 INP-17）：两个口径都算，分别写出结论，交 AP，不替 AP 选。
3. **转述与原文冲突**：TL、Architecture、训练 Prompt 等与原文不符时，用原文，并在报告指出（[DK-AUD-005](../L1-Domain/DK-AUD-005_Errata.md)）。
4. **harness 无法执行代码时**：颜色、半色调、像素级检查（GEN-03、GEN-05）不能目测给 Pass。改用人工检查（SOP-AUD-manual 的颜色一节），或记 `[GAP]`。
5. **工具读不到的信息**：记 Unclear / `[GAP]`，指向 L4 的缺口编号（CAP-gaps 的 `GAP-nn`），不推断成 Pass。
6. **只读**：审核不修改模型。查到要修的，写成修复建议和修复方式（manual / function-b / AP）。

## 8. 通用检查（GEN）

各 AUD 第 3 节会引用这些编号，不重抄。

| ID | 检查 | 怎么判 |
| --- | --- | --- |
| GEN-01 | 图纸上的计算表、明细表是不是由模型生成 | 表是插入的图片（raster image） → L1 **Fail**，即使数字对（BIMGBPS §4.2(b)、§5.1.2）。同名的模型明细表存在且放在图上 → 再确认它**在图框范围内**（导出整张图纸看；放在图框外，打印时不会出现 → L1 Fail），然后按各 AUD 判 |
| GEN-02 | 表里的数值是不是手填 | 字段是软件量得的（面积、长度、数量）还是手填参数 / 文字。手填的即使数值对，也按 §5.1.2 指出（Minor，或在影响合规数字时为 Major） |
| GEN-03 | 面积图有没有半色调底图 | 按 DK-AUD-004 §4 的像素判据 |
| GEN-04 | 标高与高程点 | 格式 `X.XXX mPD`（LIM-03）；另查基准：各 Level 类型与高程点类型的标高基准设置、项目基点与测量点高程、标高名称里的数字与显示值是否同一口径。基准不一致记 Major，HKPD 零点无法确认记 Unclear |
| GEN-05 | 颜色 | 按 DK-AUD-004 取样判定。只能用导出图像的像素值，不用目测 |
| GEN-06 | 数字复核 | 能用模型元素重算的都重算（面积、地界、构件数量）。写「表值 / 模型值 / 一致否」。算术一致 ≠ 合规 |
| GEN-07 | 共用面积数据的交叉校验 | 同一组面积数据被多个 Task 用时（例：V10 ↔ S08 ↔ S05），一次读取、交叉校验 |

## 9. 每份 AUD 的结构

1. 适用性
2. 要取得的信息
3. L1 检查项
4. L2 计算与限值
5. 常见坑
6. 外部输入
7. 依赖
8. GAP
9. 可执行规格（已升级的 Task 才有；格式见本文件 §10）

「常见坑」来自 BD 样例模型（第 1 轮验证）。正常项目模型上，最常见的情况可能是图根本不存在：按「没有该图 / 表时」一行判 Missing 或 N/A。

## 10. 两段式执行标准（分析 → 报告）

每个 Task（或合并同类项后的一组 Task）按两段执行。第一段只分析，第二段只出报告。两段之间要停下给操作者确认。

### 10.1 第一段：分析（只读）

1. **提取**：按 L3 配方（[SOP-AUD-mcp-revit-mcp §10](../L3-SOP/SOP-AUD-mcp-revit-mcp.md)）调用 MCP，把原始值存成提取文件（`_raw/*.tsv` / `*.json`）。提取文件只放 MCP 回传的值，不放推算值。
2. **分析脚本**：`tools/<组>/analyze.py` 只读提取文件，写分析 JSON，打印屏幕摘要。脚本不调 MCP、不编数值；提取文件没有的值写进 `data_quality_warnings`，不补。
3. **分析 JSON** 的共同要求：
   - `project_info`：项目名、模型路径、分析时间、所用规则（含限值与法例出处）、勘误说明。
   - 每个被判定的对象（房间、开口、面积、图纸……）有 `id`（Revit ElementId）、名称、楼层、数值，以及：
     - 归类结果与理由（`classification`、`classification_reason`）；
     - 关联方法与可信度（`match_method`、`match_confidence`：high / medium / low），关联不上就放 `*_unassigned`，不强配；
     - 要求值、实际值、差额、Pass / Fail（三位小数）。
   - 被排除、待定、无数据的对象各有一节，每条写理由。
   - `summary`：计数、通过 / 不通过数、`data_quality_warnings`。
4. **屏幕摘要**：总数、各组计数、逐项要求 / 实际 / 结论表、待定清单、未关联清单、警告；有上一次结果时并列对比。
5. **确认关口**：把摘要给操作者看，确认后才进第二段。分类规则、限值有争议时，在这里改规则重跑，不改报告。

### 10.2 第二段：报告（只读分析 JSON）

1. 报告脚本 `tools/<组>/report.py` 只读分析 JSON，不再查模型。
2. **Excel**：每组至少有「逐项合规表」「明细表」「对象-证据拆分表」「类型汇总」「Summary」「排除 / 待定表」；首行冻结、可筛选；数值三位小数；Pass 绿、Fail 红、N/A 黄。用 `tools/common/xlsx_lite.py`（只用标准库），别的 harness 不必装 openpyxl。
3. **HTML**（单文件、自带 CSS / JS）：仪表板（计数卡、通过比例条）、「不通过项与修改方向」、可排序表格、可折叠明细、方法与限制、页脚声明「非屋宇署正式审批」。手机宽度不出现横向滚动。
4. 文件名：`GBP_<Task>_<主题>_<项目>_<yyyymmdd>.xlsx / .html`，放在本次审核文件夹。
5. 结果再汇总进 `audit-results.json`（每组一条或多条 finding，`evidence` 指向 Excel / HTML），由 `report/render_report.py` 出总报告。

### 10.3 合并同类项

| 组 | Task | 共用数据 | 工具 |
| --- | --- | --- | --- |
| G1 房间-开口 | S14、V13 | 房间、幕墙 / 嵌板、窗、门 | `tools/s14_lv/` |
| G2 房间-用途 | S13、S10 / S11、S15 / S16 | 房间、洁具、门、楼梯 | `tools/room_use/` |
| G3 面积方案 | V06–V12、V14、S02、S05–S08、S12 | Area、面积方案、地界 | `tools/area_scheme/` |
| G4 图面 | V01–V05、A01–A03 | 视图、图纸、导出图像 | `tools/drawings/` |
| G5 清单 | S01、S03、S04、S09 / S17、S18、A04 | 图纸、明细表、基点 | `tools/lists_health/` |
| G6 模型健康 | A1（MA-1 至 MA-7） | 全模型统计 | `tools/lists_health/`（与 G5 同一脚本） |

### 10.4 按 Task 单独跑

一组里的任一个或几个 Task 可以单独跑，结果与整组跑时该 Task 的结果逐条相同（测试保证）。

1. **只提取需要的**：各组规格的「按 Task 单独跑」表列出每个 Task 的最少提取（L3 配方第几步）和依赖的其他组。
2. **分析**：`analyze.py … --tasks S10`（可多个：`--tasks S10,S13`）。组内共用的计算照做，输出只留所选 Task；分析 JSON 记 `tasks`、`group_tasks`、`partial`。
3. **输入不齐时不猜**：
   - 缺必需输入 → 该 Task 不判，只出一条 `<Task>-INPUT`（UNCLEAR），写明缺什么、按哪一步取；不会拿空数据判成 0 或「没有」。
   - 缺可选输入 → 照判，另出一条 `<Task>-INPUT` 写明哪些检查因此没判。
4. **报告**：`task_report.py` 照常；文件名换成 Task 号（`GBP_G2_S10_<项目>_<日期>`）。
5. **并回总结果**：`build_results.py … --group <该组完整 JSON> <目录> --update <单独跑的 JSON>`：所选 Task 替换进该组 JSON（旧文件留作 `.prev.json`），重建该组报告，再汇总；其他 Task 的结果不变。然后照常出 bim / ap 两份总报告。
