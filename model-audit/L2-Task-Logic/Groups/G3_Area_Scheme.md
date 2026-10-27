# G3 面积方案组 · 可执行规格（AUD-S02、V09、S05、V10、S08、S07、V11、V12、V14、V06、V08、S12、V07、S06）

按 [AUD-000 §10](../AUD-000_Audit_Flow.md) 两段执行。工具：`tools/area_scheme/analyze.py`（分析）、`tools/common/task_report.py`（报告）。提取配方：当前 MCP 的 L3 SOP 的 R-G3（基准：[SOP-AUD-mcp-revit-mcp §10 R-G3](../../L3-SOP/SOP-AUD-mcp-revit-mcp.md)；其他 MCP 的 SOP 只写不同的步骤，见 L4 对照表）。JSON：[task-analysis.schema.json](../../templates/task-analysis.schema.json)。范例：`work/model-audit-runs/audit-2026-10-13-g3/`。

这 14 个 Task 都从同一组 Area（各面积方案）和地界算数，计算表都在 C001–C008 上，所以合成一组。

## 1. 数据范围

| 对象 | 能力 | 取什么 |
| --- | --- | --- |
| Area 与面积方案 | CAP-EXTRACT-AREAS | 每个 Area 的全部参数（方案、楼层、名称、面积、周长、Common Area 标签、GFA SUMMARY、GFA DEDUCT 2.2 / 2.3 / 21 / 25 / 27、SERVED FACADE、FRR minutes、FRC COMPARTMENT、FRC HEIGHT）与包围盒；方案名称 |
| 地界 | CAP-EXTRACT-SITE | Property Line 面积 |
| 计算表 | CAP-EXPORT-IMAGE | C001–C008、A001 导出 PNG；表是图片时逐值读取，写进 `table_values.tsv`（每值带图纸、可信度、备注） |
| 图片元素 | CAP-QUERY-ELEMENTS | Raster Images 名称（判 GEN-01） |
| 房间 UFA | G2 分析 JSON | 每层可用楼面面积（V11 对表） |

## 2. 规则与计算

| Task | 检查 | 方法 / 限值 |
| --- | --- | --- |
| 全部 | GEN-01 | 该表在模型里是 Raster Image → Fail |
| S02 | 地界 = 地盘面积方案 = Block / Location plan Area = 表值；取整 | ADM-21（≥ 2,000 m² 取至 1 m²，LIM-02）；与 Lease plan 对照要 INP-01 → UNCLEAR |
| V10 | 每层：总 GFA（ARC_gbp_gfa）− 打了 DEDUCT 标记的面积 = GFA SUMMARY 面积合计（两条独立算法）；与表上每层 GFA、扣减额、总数一致；无标签的可计 GFA 面积 → Minor；同一面积两个豁免项 → Fail | reg 23(3)(a)（LIM-15） |
| S08 | 每个 APP-151 项目（2.2、21 不受 cap；2.3、25 受 cap——由模型标记对 C003 栏位确认）合计、逐层值、不受 cap / 受 cap 总数、百分比 = 表值；受 cap ÷ GFA ≤ 10 %；附录 A、G、H 齐 | APP-151 ¶4（LIM-23） |
| S07 | ¶6(c) 注册信 → INP-07；¶6(d) 目标评级要写在图上（读 C001–C008、A001）；受 cap 面积不批时 PR | APP-151 ¶6（LIM-24） |
| V09 / S05 | 有盖面积 = SC 方案 Area = 表值；SC %、PR 与表一致；有盖面积不小于最大楼层外墙面积；两个建筑高度口径各查附表 1（非住用、丙类）；高度口径不一致 → Fail；场地分类资料只有「C」→ Partial | reg 20、21、附表 1（LIM-16，重建表要对电子版）；reg 23(1)（LIM-13） |
| V11 | UFA 方案有没有 Area；表上每层 UFA = 房间面积（G2） | GEN-06；表取整数 → 指出 |
| V12 | 沿用 G2 S15 的 UFS 上下限 | Cap. 123H（LIM-19） |
| V14 | 绿化面积、比率 = 表值；整体 ≥ 20 %；主要区没划分 → UNCLEAR；Lp 未写 → UNCLEAR | APP-152 Table 2（LIM-29）、¶3（LIM-28） |
| V06 | 每层 SERVED FACADE ÷ Perimeter ≥ 25 %；与表一致；服务立面是手填参数 → Minor；Part D → UNCLEAR | APP-136 ¶6（LIM-26） |
| V08 / S12 | 分区面积 = 表值；体积 = 面积 × 层高（由楼层标高算）= 表值；模型有而图上没有的分区 → Fail；分区未覆盖整层 → UNCLEAR；FRC HEIGHT 为 0 → Minor；限值 → UNCLEAR | FS Code Part C（LIM-32 缺） |
| V07 / S06 | 非住用 → N/A（附条件） | reg 25（LIM-17） |

## 3. 读图规则

- 先读整张图，再裁切放大要读的格子；每个值写进 `table_values.tsv`，注明图纸、可信度（high / medium）、备注。
- 读不清（例：250 / 255）时用表上自己的合计反推，并标 medium；绝不按模型值「补」表值，也不「假设同上」。
- 表值没读的检查记 UNCLEAR（不是 Fail）。
- **由代码强制**（`tools/common/readings.py`）：备注写明来自模型或假设的行一律拒用（UNCLEAR，并在屏幕摘要列出）；与模型不一致的读数要有该格的裁切图（`box` → `crop_readings.py` → `crop`）才判 Fail，否则 UNCLEAR；一致的读数无裁切图也可 Pass（medium）。
- 看图下的判断（附录 A / G / H 表、BEAM Plus 目标评级、地盘分类依据）各写一行带 `finding`（Pass / Fail）；没有这一行 → UNCLEAR，不推定。Pass 要有裁切图，Fail 要写明看过的图纸，否则 UNCLEAR。
- 全部读数连同裁切图列在屏幕摘要与报告「Sheet readings to check」，供操作者在确认关口逐条核对。

## 4. 分析 JSON 与报告

同 G2：`checks`（逐项）、`tables`（gfa、concessions、compartments、schemes、areas、readings）、`summary.gfa`。报告由 `task_report.py` 生成：每个 Task 一张卡、不通过与修改方向、全部检查可筛选、读图值一览。

## 5. 与其他组的接口

- A001 缩写表（ELR = Electric Room、FR = Flat）→ S14 房间归类。
- GFA 扣减方案把 ELR 列为必要机房（2.2）→ 同上。
- 总 GFA < 3,960 m² → 支持 G2 S15 / V12 的 N/A。

## 6. 按 Task 单独跑

`--tasks`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。每个 Task 都要 R-G3 第 1–4 步（Area 与面积方案）；第 5 步（Raster Images，判 GEN-01）和第 6 步（读图）只取该 Task 的图纸。缺第 5 步时 GEN-01 不判（不当作「没有图片表」）。

| Task | 读哪些图（第 6 步） | 依赖其他组 |
| --- | --- | --- |
| S02 | C001、C003 | — |
| V09 / S05 | C001、C003 | — |
| V10 | C002 | — |
| S08 | C003 | — |
| S07 | C001–C008、A001（目标评级）、C001 高度 | — |
| V11 | C004 | G2（可选：逐层 UFA 对表） |
| V12 | — | **G2（必需：S15 的 UFS 上下限）** |
| V14 | C008 | — |
| V06 | C006 | — |
| V08 / S12 | C005 | — |
| V07 / S06 | C001（用途） | — |
