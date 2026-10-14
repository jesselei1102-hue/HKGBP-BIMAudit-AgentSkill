# AUD-V01 Block / Key Plan · BIMGBPS §5.2.2
关联：[TL-V01](../../../GBP%20Tasks/Views/TL-V01_Block_Key_Plan.md) · Roadmap 卡片 V01 · MA-6.1、MA-2.3 · [LIM-02、LIM-03、LIM-11](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [DK-AUD-004 §2](../../L1-Domain/DK-AUD-004_Colour_Standards.md)

## 1. 适用性

每个项目都适用（§5.2.1(a)）。不适用时：不存在这种情况；没有该图按 Missing 记。

## 2. 要取得的信息

- Block plan、Location / Key plan 所在图纸、视图比例、视图样板。
- 地界（Property Line）：段数、方位、边长、面积；地盘 Area 的面积。
- 地盘填色的像素取样（导出图像）。
- 地段编号、街道名称与阔度、指明街道标示、车辆出入口、特别地区、北向符号与正北角。
- 坐标表：是模型数据还是图片；角点坐标值。

## 3. L1 检查项

没有该图时：Missing（Blocker 级缺项）。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V01-L1 | 比例 | Block plan 视图比例 | ≥ 1:500 → Pass |
| V01-L2 | (a) 地界 | 地界闭合；面积与地盘 Area 一致 | 一致 → Pass |
| V01-L3 | (b) 地盘着粉红 | 取样值（GEN-05、DK-AUD-004 §2） | 粉红 → Pass；非粉红色系 → Fail |
| V01-L4 | (c) 地段编号 | 图上有 Lot / IL 编号 | 有 → Pass |
| V01-L5 | (d) 指明街道 | 街道名、阔度，且标出哪几条是 specified streets | 只有街名阔度 → Partial |
| V01-L6 | (e) 界址坐标与尺寸 | 坐标是否模型生成（GEN-01）；数值与地界换算一致到 0.001 m；有无边长尺寸 | 坐标是图片或缺边长 → Fail |
| V01-L7 | (f) 车辆出入口 | 出入点、车道标示 | 有 → Pass |
| V01-L8 | (g) 特别地区 | 地盘内是否有 | 无 → N/A（写明） |
| V01-L9 | (h) 北向 | 北向符号；正北角与符号一致 | 有 → Pass |
| V01-L10 | 高程点格式 | 街道标高（GEN-04） | 非 `X.XXX mPD` → Fail（Minor） |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V01-C1 | 场地类别：街道阔度、临街比例 | LIM-11、LIM-12（与 AUD-S05 共用） | 指明街道资料（INP-02）缺 → Unclear |
| V01-C2 | 坐标是否等于 Lease Plan / LSP | ADM-21 | INP-01 缺 → Unclear |

## 5. 常见坑

- 地盘填色目测像粉红，取样却是薄荷绿（第 1 轮：230,250,240）。
- 坐标表是插入的 PNG，角点只是文字，没有边长尺寸。
- 街道高程点两位小数、无 mPD。

## 6. 外部输入

INP-01、INP-02（[AUD-000 §6](../AUD-000_Audit_Flow.md)）。

## 7. 依赖

后续：AUD-S02、AUD-S03（同一组地界数据）、AUD-S05（场地类别）、AUD-V09。

## 8. GAP

- 粉红的 RGB：BIMGBPS 原文没有指定数值（DK-AUD-004 §2）。


## 9. 可执行规格

合并在 [G4 图面组](../Groups/G4_Drawings.md)。本 Task 的检查见该文件 §2。

单独跑：`--tasks V01`，最少提取与依赖见 [G4「按 Task 单独跑」](../Groups/G4_Drawings.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
