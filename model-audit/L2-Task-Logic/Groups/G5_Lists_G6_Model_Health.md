# G5 清单组与 G6 模型健康 · 可执行规格（AUD-S01、S03、S04、S09、S17、S18、A04；AUD-A1）

按 [AUD-000 §10](../AUD-000_Audit_Flow.md) 两段执行。工具：`tools/lists_health/analyze.py`（分析，读其他组的分析 JSON）、`tools/common/task_report.py`（报告）。提取配方：[SOP-AUD-mcp-revit-mcp §10 R-G5](../../L3-SOP/SOP-AUD-mcp-revit-mcp.md)。范例：`work/model-audit-runs/audit-2026-10-13-g5/`。

G5 的表大多是「别处已算出的数」的汇总，G6 与 A04 是全部结果的汇总，所以放在最后跑，并直接读 G2、G3、G4、S14 的 JSON。

## 1. 规则

| Task | 检查 | 方法 |
| --- | --- | --- |
| S01 | 目录是 Sheet List 明细表（GEN-01）；逐行图号、图名、修订 = 模型图纸；模型有而目录没有的图纸 | 明细表清单；读 A001 目录；图框参数 |
| S03 | 坐标表是不是图片；HK1980 三位小数；有无方位角与边长；每点 = 地界角点按项目基点换算（到 0.001 m）；与测量图 → UNCLEAR | 项目基点 E / N / 角度 + 地界包围盒（矩形地盘） |
| S04 | 表是不是图片；GFA、SC、绿化、车位逐栏 = 来源（G3、停车明细表）；高度栏与 C001 计算同一口径 | 不同口径时用楼层标高解释差额，标 `[INFERENCE]` |
| S09 / S17 | APP-89 电梯井豁免有没有申请（C003 第 18、34 项） | 没申请 → N/A（附条件） |
| S18 | 须修改的项（例：第 25 项入口 void，ADM-2 附录 E）在不在修改清单 | 无清单 → Fail（Missing），或撤回该项（INP-13） |
| A1 | MA-1 版本、大小、链接；MA-2 共享坐标；MA-3 图片表；MA-4 标高名与标高值一致、房间面积合理；MA-5 游离门、无楼层构件；MA-6 地界；MA-7 图框数 | 标高名里的数字与 Elevation 差 > 0.5 mm → Fail |
| A04 | L1 容量格式；L2 图片表；L3 面积可复核（V11-L2、V10-L4、V08-L4、V10-L5）；L4 缺图（basis = Missing 的 V 项）；L5 缺表与图片表；L6 N/A 理由表 | 只汇总其他检查，不另量 |

规则共通：结论只来自数据。图上判断（坐标格式、方位角与边长、修改清单、N/A 表）读 G4 `readings.tsv` 的 `finding`，没有 → UNCLEAR；文件大小、版本、链接、地界面积、坐标面积、PR 等由数值比较得出，不写死。

## 2. 报告

同 G2：Task Summary、Checks、coords、levels、rollup（全部 Task 的 PASS / FAIL / UNCLEAR / N/A）、Summary。

## 3. 按 Task 单独跑

`--tasks`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。最少提取指 R-G5 的步；其他组的输入用 `--g2 / --g3 / --g4 / --s14 / --g3raw / --g4raw` 传入：

| Task | 本组提取 | 必需的其他组 | 可选 |
| --- | --- | --- | --- |
| S01 | 2（明细表清单）、3（图纸目录） | G4 分析 JSON（图框） | — |
| S03 | 1（基点、地界） | G4 `coords.tsv` | G4 `readings.tsv`（格式、方位角） |
| S04 | 1 | G3 分析 JSON、G3 `table_values.tsv` | 楼层标高、G3 rasters、G2 停车明细表 |
| S09 / S17 | — | — | G3 `table_values.tsv`（`lift_shaft_concession`） |
| S18 | 2 | G3 分析 JSON（豁免项） | G4 `readings.tsv`（修改清单） |
| A1 | 1 | G2、G3、G4、S14 分析 JSON；G3 rasters；G4 `rvt_info.json` | G4 `coords.tsv` |
| A04 | 全部 | 全部（A04 是全部 Task 的汇总；单独跑时本组其他 Task 照算，输出只留 A04） | — |
