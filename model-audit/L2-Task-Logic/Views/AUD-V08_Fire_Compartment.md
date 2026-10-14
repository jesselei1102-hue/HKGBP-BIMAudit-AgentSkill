# AUD-V08 Fire Compartment Diagram · BIMGBPS §5.2.8
关联：[TL-V08](../../../GBP%20Tasks/Views/TL-V08_Fire_Compartment.md) · Roadmap 卡片 V08 · MA-5.5 · [LIM-32](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

所有须划分防火分区的建筑物（FS Code Part C）。不适用时：几乎不会出现；如 AP 认为整栋为单一分区，仍须出图表明，不写 N/A。

## 2. 要取得的信息

- 分区面积方案（或 Room / 填充区域）：各分区面积、楼层、未放置面积。
- 每个视图的尺寸数、分区标签（分区号、FRR 分钟）。
- 分区着色取样；半色调底图（GEN-03）。
- 对应计算表的形式（GEN-01）。

## 3. L1 检查项

没有该图时：Missing。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V08-L1 | (a) 轴网 | 轴网数 | 有 → Pass |
| V08-L2 | (b) 分区界线尺寸与标签 | 尺寸数、标签 | 某层尺寸为 0 → Partial |
| V08-L3 | (c) 不同分区不同颜色 | 取样 | 相邻分区同色 → Fail |
| V08-L4 | (d) 半色调底图 | GEN-03 | 无 → Fail |
| V08-L5 | (e) 对应表和计算 | GEN-01；分区面积与 AUD-S12 表值一致（GEN-06） | 图片 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V08-C1 | 分区面积、体积 vs 限值 | LIM-32（FS Code Part C） | 原文缺 → Unclear |

## 5. 常见坑

- 分区方案里有未放置面积，令数字对不上。
- 个别楼层视图没有任何尺寸。

## 6. 外部输入

无。

## 7. 依赖

前置：AUD-V02（底图）；与 AUD-S12 一一对应。

## 8. GAP

- FS Code Part C 原文（DK-AUD-006 M-02）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V08`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
