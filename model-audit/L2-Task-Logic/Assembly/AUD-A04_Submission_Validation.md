# AUD-A04 Submission Validation · BIMGBPS §4.2、§5.2.1、§5.3、§5.5
关联：[TL-A04](../../../GBP%20Tasks/Assembly/TL-A04_Submission_Validation.md) · Roadmap 卡片 A04 · [DK-AUD-001](../../L1-Domain/DK-AUD-001_Hard_Requirements.md) · [DK-AUD-003](../../L1-Domain/DK-AUD-003_Applicability.md)

本项不另取模型信息，只汇总 AUD-A1 与 36 个 AUD 的结果，判「能不能原样提交」。

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- AUD-A1 的结果（MA-1 至 MA-7）。
- 每个 AUD-V / S / A 的 L1、L2 状态与 Findings。
- 每个 N/A 的理由句、条件、AP 确认情况。

## 3. L1 检查项

没有该表时：N/A + 理由表不存在 → Missing。

| ID | 硬性项 | 来源 | 判 |
| --- | --- | --- | --- |
| A04-L1 | 容量、格式 | AUD-A1 MA-1、AUD-A03 | 任一 Fail → Fail |
| A04-L2 | 尺寸 / 面积不是手打（§5.1.2） | 全部 GEN-01、GEN-02 结果；尺寸覆盖值（GAP-01） | 有图片表 → Fail；覆盖值未查 → Unclear |
| A04-L3 | 面积可复核（§4.2(e)(f)） | 未放置 Room / Area、重复面积、半色调、边界缝隙（GAP-02） | 任一 → Fail |
| A04-L4 | 适用的视图都在（§5.2.1） | Views 14 份：Missing 与 N/A 分开数 | 有 Missing → Fail |
| A04-L5 | 适用的表都在（§5.3） | Schedules 18 份：图片 / Missing / N/A 分开数 | 有 Missing → Fail |
| A04-L6 | N/A + 理由表 | 每个 N/A（附条件）都有理由句，且出现在图纸上 | 无表 → Missing；有「N/A 待声明」→ Partial |

## 4. L2 计算与限值

无新计算。列出所有 L2 状态为 Unclear 的项及原因（缺原文 / 缺资料 / 工具读不到），按 G11 不算 Pass。

## 5. 常见坑

- 「N/A 待声明」不算通过：理由要出现在图纸上。
- Unclear 不算 Pass（G11）。

## 6. 外部输入

INP-14（各 N/A 的 AP 确认）。

## 7. 依赖

前置：全部。

## 8. GAP

- 汇总时，凡依赖 GAP-01、GAP-02 的项，结论只能是「未发现」，不是「没有」。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks A04`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
