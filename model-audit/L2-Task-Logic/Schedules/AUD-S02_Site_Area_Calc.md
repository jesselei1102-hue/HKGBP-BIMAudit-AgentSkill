# AUD-S02 Site Area Calculation · BIMGBPS §5.3.2
关联：[TL-S02](../../../GBP%20Tasks/Schedules/TL-S02_Site_Area_Calc.md) · Roadmap 卡片 S02 · MA-6.1、MA-6.2 · [LIM-02、LIM-14](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 地界（Property Line）面积。
- 各面积方案里的地盘 Area 面积。
- 表的形式、表值；地段划分。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S02-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S02-L2 | 地界面积 = 地盘 Area = 表值（GEN-06） | 不一致 → Fail |
| S02-L3 | 取整（LIM-02） | 不合 → Fail |
| S02-L4 | 多地段时按地段分列 | 只有一段 → 可接受，写明 |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S02-C1 | 模型地盘面积 vs Lease Plan / LSP | LIM-14（不计街道、后巷） | INP-01 缺 → Unclear |

## 5. 常见坑

- 同一地盘面积在几个方案里各有一个 Area，要逐个比对。

## 6. 外部输入

INP-01。

## 7. 依赖

后续：AUD-S05、AUD-V09、AUD-V07。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S02`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
