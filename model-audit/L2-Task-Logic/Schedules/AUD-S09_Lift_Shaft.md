# AUD-S09 Lift Shaft Schedule · BIMGBPS §5.3.17
关联：[TL-S09](../../../GBP%20Tasks/Schedules/TL-S09_Lift_Shaft.md) · Roadmap 卡片 S09 · MA-5.4 · [LIM-27](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-05](../../L1-Domain/DK-AUD-003_Applicability.md)

本文件也是 [AUD-S17](AUD-S17_Lift_Shaft_GFA.md) 的基础。两者对应 §5.3.17 同一张表：S09 管井道几何，S17 管豁免计算。

## 1. 适用性

按 APL-05：申请 PNAP APP-89 电梯井豁免、且建筑类别在 APP-89 第 5 段内时适用。

不适用时：**N/A（附条件）**，用 APL-05 理由句；图纸上没有 → N/A 待声明。

## 2. 要取得的信息

- S08 清单的「Larger lift shaft」、楼梯 / 电梯井水平面积两项是否申请。
- 用途（APL-01）。
- 若适用：井道开洞 / 电梯族、服务楼层、轿厢与井道内部面积。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S09-L1 | 表存在且为模型生成（GEN-01） | 图片 → Fail |
| S09-L2 | 每部电梯：井道尺寸、服务楼层 | 缺 → Partial |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S09-C1 | 轿厢 / 井道内部面积 vs 下限 | LIM-27（办公 2.1 / 4.4 m²） | — |

豁免面积的计算见 AUD-S17。

## 5. 常见坑

- 消防员升降机另有法定要求（APP-89 第 3 段），不要混入。
- 模型里没有井道对象时，表做不出来；先判适用性。

## 6. 外部输入

INP-08、INP-13。

## 7. 依赖

与 AUD-S17、AUD-S08 同链。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S09`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
