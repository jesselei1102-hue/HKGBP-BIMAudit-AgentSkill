# AUD-S12 FRR / Compartment Schedule · BIMGBPS §5.3.12
关联：[TL-S12](../../../GBP%20Tasks/Schedules/TL-S12_FRR_Compartment.md) · Roadmap 卡片 S12 · MA-5.5 · [LIM-32](../../L1-Domain/DK-AUD-002_Limits_Index.md)

与 [AUD-V08](../Views/AUD-V08_Fire_Compartment.md) 一一对应。

## 1. 适用性

与 AUD-V08 相同。不适用时：几乎不会出现，不写 N/A。

## 2. 要取得的信息

- 分区面积（分区面积方案）、层高；体积 = 面积 × 层高。
- 墙、门的 FRR 参数。
- 表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S12-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S12-L2 | 分区面积、体积与模型一致；与 V08 图面一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S12-C1 | 分区面积 / 体积 / FRR vs 限值 | LIM-32（FS Code Part C） | 原文缺 → Unclear |

## 5. 常见坑

- 分区在面积方案里：做表需要面积明细表，不是房间明细表。

## 6. 外部输入

无。

## 7. 依赖

与 AUD-V08 同审。

## 8. GAP

- FS Code Part C 原文（DK-AUD-006 M-02）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S12`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
