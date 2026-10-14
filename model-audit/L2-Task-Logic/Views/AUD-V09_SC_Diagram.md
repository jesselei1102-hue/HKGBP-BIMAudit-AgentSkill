# AUD-V09 Site Area & SC Diagram · BIMGBPS §5.2.9
关联：[TL-V09](../../../GBP%20Tasks/Views/TL-V09_SC_Diagram.md) · Roadmap 卡片 V09 · MA-4.2、MA-4.3 · [LIM-02、LIM-16](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- SC 面积方案：有盖面积 Area（每栋分开）。
- 地盘图：地盘 Area、地界尺寸。
- 各栋标签与面积注记；着色取样；半色调（GEN-03）。
- 对应计算表的形式（GEN-01）。

## 3. L1 检查项

没有该图时：Missing。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V09-L1 | (a) 地界与尺寸 | 地界、尺寸（可能在同图另一视图） | 有 → Pass |
| V09-L2 | (b) 有盖范围（着色或标注 + 尺寸） | 有盖 Area、尺寸 | 有 → Pass |
| V09-L3 | (c) 各栋标签及上盖面积 | 标签、面积注记 | 只有标签无面积 → Partial |
| V09-L4 | (d) 对应表和计算 | GEN-01；SC = 有盖面积 ÷ 地盘面积（GEN-06） | 图片 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V09-C1 | SC 实际值 vs 准许值 | LIM-16（附表 1，按用途、场地类别、高度） | 与 AUD-S05 一起判；INP-02 / INP-11 缺 → 两个高度口径都查或 Unclear |

## 5. 常见坑

- 地界尺寸画在同一张图纸的地盘图视图上，不在 SC 视图里：不要误判缺失。
- 只有一栋时只标「1」、无面积，可接受程度由 AP 判。

## 6. 外部输入

INP-02、INP-03、INP-11。

## 7. 依赖

与 AUD-S05、AUD-S02 同链。

## 8. GAP

- 附表 1 数值核对（DK-AUD-006 M-11）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V09`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
