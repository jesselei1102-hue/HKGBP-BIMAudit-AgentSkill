# AUD-S07 GFA Concession Requirements · BIMGBPS §5.3.7
关联：[TL-S07](../../../GBP%20Tasks/Schedules/TL-S07_GFA_Concession_Req.md) · Roadmap 卡片 S07 · [LIM-23 至 LIM-25](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-06](../../L1-Domain/DK-AUD-003_Applicability.md)

## 1. 适用性

按 APL-06：申请了 APP-151 附录 A 的绿化 / 康乐设施或非必要机房豁免时适用。

不适用时：只申请必要设施（APP-151 第 5(a) 段）→ **N/A（附条件）**，用 APL-06 理由句。

## 2. 要取得的信息

- S08 清单里每个豁免项：类别（必要设施 / 受 cap 项）、面积。
- 图纸上有无前置条件表、SBD 合规声明、BEAM Plus 注册确认、目标评级声明。
- 递交日期（INP-09）。

## 3. L1 检查项

共用：GEN-01、GEN-02。没有该表时：适用 → Missing（内容）。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S07-L1 | 前置条件表存在 | 无 → Missing |
| S07-L2 | 表是模型生成（GEN-01） | 图片 → Fail |
| S07-L3 | ¶6 (d) 目标评级写在 GBP 上（模板：ADV-33 附录 A4 图 C042） | 无 → Missing |

## 4. L2 计算与限值

| ID | 前置条件（APP-151 ¶6） | 查什么 | 缺什么时 |
| --- | --- | --- | --- |
| S07-C1 | (a) 符合 APP-152（where applicable） | AUD-V14 结果 | — |
| S07-C2 | (b) 住用 / 综合用途符合 APP-156 | APL-01 | 非住用 → N/A |
| S07-C3 | (c) BEAM Plus NB 注册确认信 | INP-07 | 缺 → Missing |
| S07-C4 | (d) GBP 上的 BEAM Plus 目标评级 | 图纸 | 缺 → Missing |
| S07-C5 | (e) 后续阶段资料 | — | GBP 阶段 → N/A（本阶段） |
| S07-C6 | (f) 10 % 总上限 | LIM-23，与 AUD-S08 一起 | — |
| S07-C7 | (g) 个别项目的接受准则 | 各项 PNAP | 原文缺 → Unclear（DK-AUD-006 M-07） |

- 适用且 (a)(c)(d) 有任一缺 → **L2 Fail**：受 cap 面积不能批。
- 同时算敏感度：不批时申报 GFA、PR 变多少，AUD-S05 是否仍过。

## 5. 常见坑

- 递交日期决定适用哪一版 APP-151（LIM-25）。

## 6. 外部输入

INP-07、INP-09、INP-13。

## 7. 依赖

前置：AUD-S08、AUD-V14；联动：AUD-S18（例：入口 void 豁免同时触发修改申请）。

## 8. GAP

- APP-151 附录 A 各项接受准则（DK-AUD-006 M-07）；旧版 APP-151 附录 `[GAP]`。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S07`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
