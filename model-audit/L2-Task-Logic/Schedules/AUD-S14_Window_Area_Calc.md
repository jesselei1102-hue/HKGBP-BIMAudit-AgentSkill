# AUD-S14 Window Area Calculation · BIMGBPS §5.3.14
关联：[TL-S14](../../../GBP%20Tasks/Schedules/TL-S14_Window_Area_Calc.md) · Roadmap 卡片 S14 · MA-5.1、MA-5.2 · [LIM-06、LIM-07、LIM-10](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-10](../../L1-Domain/DK-AUD-003_Applicability.md)

与 [AUD-V13](../Views/AUD-V13_Prescribed_Windows.md) 同审。

## 1. 适用性

有 reg 30 或 reg 36 范围的房间时适用（APL-10）。不适用时：只有完全没有这几类房间才可能，理由句须列出房间用途。

## 2. 要取得的信息

- 适用房间清单（APL-10）：用途、楼面面积、UFA。
- 每个房间对应的窗 / 幕墙嵌板：窗号、玻璃面积、可开启面积。
- 「实设面积」是由窗族 / 嵌板几何量得，还是手填文字。
- 个别房间按其他面积（例：notional area）计算时，口径来源。
- 表的形式与表值；哪些楼层有值。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：适用 → Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S14-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S14-L2 | §5.3.14 (c) 栏位：use、UFA、required / provided openable、required / provided window | 缺栏 → Partial |
| S14-L3 | 适用房间都在表内；只列首层、其余层「同上」时，其余层是否真有值 | 缺 → Partial |
| S14-L4 | 实设面积是手打算式（GEN-02） | 手打 → 指出 |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S14-C1 | 要求窗面积 = 楼面面积 × 1/10；实设 ≥ 要求 | LIM-06 | — |
| S14-C2 | 要求可开启 = 楼面面积 × 1/16（便溺房间 1/10）；实设 ≥ 要求 | LIM-07、LIM-10 | 可开启参数缺 → 写假设，不默认 100 % |

## 5. 常见坑

- **TL-S14 与训练 Prompt 写 1/8，原文是 1/10**（DK-AUD-005 §1）。按 1/8 算出的旧结论要重算。
- 个别房间按 notional area 计：先查口径来源，不要直接判错。
- 只查 Windows 会漏幕墙嵌板。BD 样板里 Windows 类别可能只有消防设施符号，真正的玻璃是幕墙嵌板：固定玻璃为系统嵌板，可开启扇为「top hung / side hung」类型的嵌板。
- 「要求」栏是手填值，常被向下取整，结果比原文要求小（例：129.340 m² 写成 12.900，原文是 12.934）。
- 明细表放上图纸后，要确认它在图框内（GEN-01）。

## 6. 外部输入

INP-05、INP-12、INP-17。

## 7. 依赖

与 AUD-V13 同审；UFA 对照 AUD-V11。

## 8. GAP

- APP-130 性能化（DK-AUD-006 M-06）。
- 外伸开口是否「直接面向室外」的 reg 31 检查（街道 ≥ 4.5 m 或 21 m² 矩形水平面）：要地界与邻近建筑几何，未计算。

## 9. 可执行规格

按 [AUD-000 §10](../AUD-000_Audit_Flow.md) 两段执行。工具：`tools/s14_lv/analyze.py`（分析）、`tools/s14_lv/report.py`（报告）。提取配方：当前 MCP 的 L3 SOP 的 R-S14（基准：[SOP-AUD-mcp-revit-mcp §10 R-S14](../../L3-SOP/SOP-AUD-mcp-revit-mcp.md)；其他 MCP 的 SOP 只写不同的步骤，见 L4 对照表）。JSON 结构：[s14-analysis.schema.json](../../templates/s14-analysis.schema.json)。范例：`work/model-audit-runs/audit-2026-10-13-s14/`。

### 9.1 数据范围

| 对象 | 来源 | 用途 |
| --- | --- | --- |
| 房间 | CAP-EXTRACT-ROOMS：名称、面积、楼层、包围盒；非矩形且临开口的房间另取边界轮廓 | 用途、面积、楼层、平面范围 |
| 幕墙 | CAP-QUERY-ELEMENTS：幕墙类型（类型名含 glass / louvre）的 Area、Mark、Level、包围盒 | 玻璃面积 |
| 幕墙嵌板 | CAP-EXTRACT-OPENINGS：Glazed_Panel（类型名含 hung）与 Louvre_Panel 的 Area、中心点；每组（类型 + 中心高度）取一个包围盒 | 可开启面积、开口顶高 |
| 窗 | CAP-EXTRACT-OPENINGS：全部窗的族名、Mark、Area、包围盒 | 消防设施窗另列，不计 |
| 门 | CAP-QUERY-ELEMENTS：全部门的族名；玻璃门取包围盒 | 确认没有漏计、也不重复计 |

### 9.2 房间归类（按用途语义，首个匹配生效；规则在 `DEFAULT_RULES.room_rules`，可用 `--rules` 覆盖）

| 组 | 规则 | 依据 |
| --- | --- | --- |
| reg 36 | 名称含 LAV / TOILET / WC / BATH / SHOWER | 含便溺设备：玻璃 ≥ 1/10、可开启 ≥ 1/10（reg 36(2)） |
| reg 30 | OFFICE、CONFERENCE、RECEPTION；FUNCTION ROOM、FRn、ACTIVITY AREA | 办公室直接适用；有人使用的房间按操作者规则适用，标「AP 确认用途」 |
| excluded | 机电 / 消防房、STORE、ENT HALL、FLL、ELV、S-n | 不是居住、办公室或厨房 |
| pending | 「Room」、未定义缩写（ELR）、GUARD ROOM、屋面「FR」 | 用途不明，不硬判 |
| no_area | 面积 = 0 | 未放置 / 未闭合 |

### 9.3 开口归类与关联

1. 幕墙按类型：玻璃幕墙 → 采光；外百叶幕墙 → 「louvre，待审」；Windows 类别里族名含 Fire_Service → 消防设施窗另列。
2. 嵌板 → 宿主幕墙：嵌板中心落在幕墙包围盒内（容差 0.2 ft）。hung 嵌板 = 可开启；Louvre_Panel 不算玻璃（从宿主面积扣除），也不算可开启窗，另列。
3. 幕墙 → 房间（side probe）：
   - 墙的法线方向取包围盒中等于类型厚度（众数，3.28 ft）的那一边。
   - 在墙两侧、墙面外 1 ft 处各取 9 个点，测点是否在房间内（有轮廓用轮廓，否则用包围盒），并要求与房间竖向重叠 ≥ 1 ft。
   - 一侧有房间、另一侧在建筑外廓外 → `external`，归该房间（多个房间按命中比例分摊）；可信度：轮廓或矩形房间 high，非矩形包围盒 medium。
   - 两侧都有房间 → `internal`：不是面向室外的订明窗（reg 30(2)(b)），不计。
   - 一侧有房间、另一侧是外廓内无房间 → `unroomed`：low，不计，待 AP 确认。
   - 两侧都没有房间 → 未关联；再向外 2–15 ft 找最近房间，只作「修改方向」提示，不计。
4. 开口顶高：嵌板顶 − (房间 SFL + 0.05 m) ≥ 2 m 才计可开启（reg 30(2)(a)(ii)、reg 36(3)）。

### 9.4 公式

- reg 30：要求采光 = A × 1/10；要求通风 = A × 1/16。
- reg 36：要求采光 = A × 1/10；要求通风 = A × 1/10。
- 实际采光 = Σ（幕墙 Area − 其中百叶嵌板面积）× 分摊比例，只计 `external`。
- 实际通风 = Σ hung 嵌板面积 × 分摊比例，只计 `external` 且顶高 ≥ 2 m。
- 另列：百叶面积（不计），`vent_pass_if_louvre_counted`；若只差百叶 → 状态 `FAIL*`。
- 全部三位小数；Pass 判定不容许向下取整。

### 9.5 分析 JSON 各节

`project_info`、`level_correspondence`、`rooms_included`（含 `matched_openings`、`glazing_beyond_boundary`）、`rooms_excluded`、`rooms_pending`（含 `openings_found`）、`rooms_no_area`、`openings_all`（含 `panels`）、`openings_unassigned`、`openings_fire_service`、`doors_reviewed`、`summary`。

### 9.6 屏幕摘要

房间分组计数；开口、嵌板、消防窗、门计数；通过 / 不通过；逐房表（面积、规则、要求 / 实际采光、要求 / 实际通风、结论）；待定房间；未关联开口及其 facing；警告；按 1/8 的对照数（只作与旧结果对账）；与上次结果的逐项对比。

### 9.7 报告

Excel 六张表：Room L&V Compliance、Opening Detail、Room Opening Breakdown、Opening Type Summary、Summary、Excluded Rooms。HTML：仪表板、不通过项与修改方向、四张可排序表、可折叠的开口明细与排除房间、方法与限制、页脚声明。

### 9.8 结果写回 audit-results.json

- 每个不通过房间合并成一条 finding（Major；`fix.method` = AP 或 manual），`evidence` 指向 Excel / HTML。
- 表值与模型值不一致的（例：要求值被向下取整）另成 finding。
- 待定房间合成一条 `Unclear` + `INP-17`。

单独跑：S14 本身就是一组（G1），按 R-S14 提取、跑 `tools/s14_lv/`；并回总结果时把新的 audit-results.json 给 `build_results.py --s14`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
