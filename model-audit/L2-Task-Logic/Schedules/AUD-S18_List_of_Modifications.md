# AUD-S18 List of Modifications · BIMGBPS §5.3.9
关联：[TL-S18](../../../GBP%20Tasks/Schedules/TL-S18_List_of_Modifications.md) · Roadmap 卡片 S18 · [APL-07](../../L1-Domain/DK-AUD-003_Applicability.md)

## 1. 适用性

按 APL-07：有任何须按 Form BA16 申请的修改或豁免时适用（例：非住用发展的入口 void 不计 GFA，属 reg 23(3)(a) 修改，见 ADM-2 附录 E）。

不适用时：**N/A（附条件）**，用 APL-07 理由句；只排查了豁免项时，理由句不能写「没有任何修改」。

## 2. 要取得的信息

- S08 清单里每个豁免项：属 reg 23(3)(b) 酌情，还是须修改。
- 其他可能须修改的设计：伸出街道、洗手间外窗、奖励地积比率等。
- 有无载入但未放上图纸的修改表（图片或明细表）。
- 表的形式与内容（ADV-33 附录 A3 表 1：描述、理由、位置）。

## 3. L1 检查项

共用：GEN-01。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S18-L1 | 清单存在、放在图纸上 | 无 → Missing |
| S18-L2 | 格式按 ADV-33 附录 A3 表 1 | 缺栏 → Partial |
| S18-L3 | 表是模型生成（GEN-01） | 图片 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S18-C1 | 每个须修改的项都在清单里 | APL-07 | APP-2 原文缺 → void 接受准则 Unclear |

有须修改项而无清单 → **L2 Fail**；撤回该豁免（INP-13）→ 可改 N/A（附条件）。

## 5. 常见坑

- 修改表图片已载入模型，但没有放在任何图纸上。
- 与 S07 联动：保留 void 豁免 → S07 前置条件和 S18 清单都要补。

## 6. 外部输入

INP-10、INP-13。

## 7. 依赖

前置：AUD-S08；联动：AUD-S07。

## 8. GAP

- APP-2 原文（DK-AUD-006 M-05）。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S18`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
