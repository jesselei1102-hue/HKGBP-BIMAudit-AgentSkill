# G2 房间-用途组 · 可执行规格（AUD-S13、S10、S11、S15、S16）

按 [AUD-000 §10](../AUD-000_Audit_Flow.md) 两段执行。工具：`tools/room_use/analyze.py`（分析）、`tools/common/task_report.py`（报告）。提取配方：当前 MCP 的 L3 SOP 的 R-G2（基准：[SOP-AUD-mcp-revit-mcp §10 R-G2](../../L3-SOP/SOP-AUD-mcp-revit-mcp.md)；其他 MCP 的 SOP 只写不同的步骤，见 L4 对照表）。JSON：[task-analysis.schema.json](../../templates/task-analysis.schema.json)。范例：`work/model-audit-runs/audit-2026-10-13-g2/`。

五个 Task 共用同一组房间、洁具、门和三张模型明细表，所以合成一组：一次提取，一次分析，一份报告。

## 1. 数据范围

| 对象 | 能力 | 取什么 | 用于 |
| --- | --- | --- | --- |
| 房间 | CAP-EXTRACT-ROOMS | 名称、编号、楼层、面积、包围盒；洗手间等非矩形房间取边界轮廓 | 全部 |
| 洁具 | CAP-QUERY-ELEMENTS | 全部 Plumbing Fixtures：族、类型、楼层、包围盒中心 | S13；交给 S14 判 reg 36 房间 |
| 门 | CAP-QUERY-ELEMENTS | 全部门：族、类型、楼层、包围盒、`width_MOE`（逃生净宽） | S10；A1 模型健康 |
| 明细表 | CAP-EXPORT-TABLE | GBP S10、S11、S13 导出 CSV（模型直接写文件，不手抄） | 表值 vs 模型 |

## 2. 关联方法（AGENT-GEOMETRY）

- **洁具 → 房间**：包围盒中心点落在房间轮廓（或矩形房间包围盒）内，且在房间楼层高度内；重叠时取面积最小的房间。
- **洁具归类**：Toilet_Cubicle → WC；Accessible → 无障碍 WC（男女共用，不计入男 / 女数）；URN → 小便器；SNK → 洗手盆；Flush_Tank / Flush_Valve / Grab_Rail → 配件，不计；无楼层的 `BD_Plumbing Fixtures n` → 洗手台面，不计，记 S13-L4。
- **男 / 女**：按所在房间名（M LAV / F LAV）。
- **门 → 房间**：门包围盒四周各放大 0.5 ft，7×7 网格取点，落在同层哪个房间就算连到哪个房间；某房间命中数少于最多者的 30 % 视为擦角，去掉。不连任何房间的一侧是走廊 / 室外（无房间）。
- **游离门**：包围盒低于最低房间楼面 → A1 模型健康 Fail；在建筑外廓 30 ft 外 → 场地构件（例：入口闸），只作记录。

## 3. 规则与公式

### S13（Cap. 123I）
- **UFA**（reg 3）：房间面积合计，扣除楼梯、公共通道（入口大堂 `[INFERENCE]`）、电梯厅、电梯、洗手间（含无障碍厕所）、机电 / 水泵 / 水箱房、屋面「FR」；缩写不明的房间（ELR）先扣除并标出。
- **基准 A（office，reg 5）**：人数 = ⌈UFA ÷ 9⌉，男女 1:1；Table 5（男 WC、小便器）、Table 6（女 WC）、Table 7（洗手盆）；≤ 10 人时 reg 5(3) 至少 1 WC + 1 洗手盆。
- **基准 B（敏感度，reg 6）**：功能室、活动区按无座集会区 ⌈UFA ÷ 0.5⌉，男女 1:1.5，Table 8–10；其余房间按基准 A；两部分要求相加 `[INFERENCE]`。基准 B 不足记 **UNCLEAR**（AP 定类别，INP-12），不记 Fail。
- 每层分开算（各层有各自洗手间）。
- 表值：S13 明细表逐层、逐族计数 = 模型计数（S13-L3）；表上有没有 UFA、人数、要求数（S13-L2）。

### S10（FS Code 2011 Part B——原文缺，LIM-30）
逐房：表面积 = 房间面积（S10-L2）；人数 = ⌈面积 ÷ 系数⌉（S10-L3）；表上「提供出口数」≤ 房间边界上的门数（S10-D）；表上每门宽度 = 模型 `width_MOE`（S10-W）；模型净宽 ≥ 表上要求（S10-WR）；有可用楼面的房间都在表内（S10-L1）。系数、出口数、宽度限值本身 → UNCLEAR。房间边界上没有门（开敞出口）→ UNCLEAR，不判 Fail。

### S11（FS Code B12——原文缺）
每层每梯：表上楼层总人数 = S10 该层合计；楼梯数 = 模型 S-n 房间数；每梯人数 = ⌈总人数 ÷ 梯数⌉；每梯 DV = 各层每梯人数之和，与表上 permissible 比较 → UNCLEAR（限值未核）。

### S15（Cap. 123H）
非住用：UFS ≥ 3,960 m² 才要垃圾房。UFS 下限 = 房间面积扣除楼梯、电梯厅、洁具空间、机电；上限 = 各层房间外包矩形面积之和（屋面层只有楼梯 / 电梯 / 机房时不计）。上限 < 门槛 → N/A（附条件）；下限 ≥ 门槛 → 适用；其间 → UNCLEAR。

### S16（Cap. 123F reg 28A）
用途不是商业、工业、住宅、旅馆 → N/A（附条件：AP 确认不属「commercial building」）；同时列出名称含 TBE / telecom 的房间。

## 4. 分析 JSON

`checks`（每个对象每条规则一条：id、task、item、object、expected、actual、status、cite、method、confidence、evidence、fix）；`tables`：fixtures、ufa、s13、s10、s11、soil_rooms；`summary`（per_task 计数、警告）。

## 5. 屏幕摘要

提取计数（房间、洁具、门）；每个 Task 的 PASS / FAIL / UNCLEAR / N/A 计数；全部 FAIL、UNCLEAR、N/A 行（对象、期望、实际）；警告。

## 6. 报告

Excel：Task Summary、Checks（状态着色）、每张 table 一页、Summary。HTML：每个 Task 一张状态卡；「不通过 / 不能判定与修改方向」按 Task、按同一规则合并对象；全部检查可按 Task / 状态筛选、可排序；明细表可折叠；方法与限制；页脚声明。

## 7. 与其他组的接口

- `soil_rooms` 表 → S14 `--fixtures`：含 WC / 小便器的房间按 reg 36 判，不靠名称（本模型的「Room」= 无障碍厕所）。
- UFS 上 / 下限 → G3 面积方案复核。
- 游离门 → AUD-A1（MA-3）。

## 8. 按 Task 单独跑

`--tasks`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。最少提取指 R-G2 的步（第 5 步转换脚本每次都跑，没取的类别它会跳过并提示）：

| Task | 最少提取 | 必需 | 可选 |
| --- | --- | --- | --- |
| S13 | 1、2、4（S13 明细表） | 房间、洁具 | S13 明细表 CSV |
| S10 | 1、2、3、4（S10 明细表） | 房间、洁具（UFA 要排除有洁具的房间）、门 | S10 明细表 CSV |
| S11 | 1、2、3、4（S10、S11 明细表） | 房间、洁具、门、S10 与 S11 明细表 | — |
| S15 | 1、2 | 房间、洁具（UFS 下限要排除有洁具的房间） | — |
| S16 | 1 | 房间 | — |
| A1（游离门） | 1、3 | 房间、门 | — |
