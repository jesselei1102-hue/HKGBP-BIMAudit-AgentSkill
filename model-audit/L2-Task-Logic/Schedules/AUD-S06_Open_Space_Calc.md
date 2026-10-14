# AUD-S06 Open Space Calculation · BIMGBPS §5.3.6
关联：[TL-S06](../../../GBP%20Tasks/Schedules/TL-S06_Open_Space_Calc.md) · Roadmap 卡片 S06 · [LIM-17](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-02](../../L1-Domain/DK-AUD-003_Applicability.md)

同 [AUD-V07](../Views/AUD-V07_Open_Space.md)（同一个适用性判定、同一组数据）。本文件只写差异。

## 1. 适用性

同 AUD-V07 §1（APL-02）。不适用时：**N/A（附条件）**，用同一句 APL-02 理由句；图纸上没有 → N/A 待声明。

## 2. 要取得的信息

同 AUD-V07 §2；另取计算表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-06。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S06-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S06-L2 | 表值与 V07 图面面积一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

同 V07-C1。

## 5. 常见坑

同 AUD-V07。

## 6. 外部输入

INP-02、INP-12。

## 7. 依赖

与 AUD-V07 同审。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S06`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
