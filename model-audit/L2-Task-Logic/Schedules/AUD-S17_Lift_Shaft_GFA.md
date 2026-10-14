# AUD-S17 Lift Shaft Schedule (GFA) · BIMGBPS §5.3.17
关联：[TL-S17](../../../GBP%20Tasks/Schedules/TL-S17_Lift_Shaft_GFA.md) · Roadmap 卡片 S17 · MA-5.4 · [LIM-27](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-05](../../L1-Domain/DK-AUD-003_Applicability.md)

同 [AUD-S09](AUD-S09_Lift_Shaft.md)（同一个适用性判定、同一张表）。本文件只写豁免计算的差异。

## 1. 适用性

同 AUD-S09 §1（APL-05）。不适用时：**N/A（附条件）**，同一句 APL-05 理由句。

## 2. 要取得的信息

同 AUD-S09 §2；另取：按 APP-89 计算的豁免面积、RLE / BSE 评估（INP-08）。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S17-L1 | 豁免面积计算在表内、为模型生成（GEN-01） | 图片 → Fail |
| S17-L2 | 豁免面积与 S08 清单对应项一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S17-C1 | APP-89 豁免面积 | APP-89（公式见 TL-S17） | — |
| S17-C2 | 评估文件 | APP-89 ¶8(c) | INP-08 缺 → Missing |
| S17-C3 | APP-151 前置条件 | APP-89 ¶9 → AUD-S07 | — |

## 5. 常见坑

同 AUD-S09。

## 6. 外部输入

INP-08、INP-13。

## 7. 依赖

与 AUD-S09、AUD-S08、AUD-S07 同链。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S17`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
