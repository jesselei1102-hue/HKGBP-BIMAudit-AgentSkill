# AUD-V12 UFS Diagram · BIMGBPS §5.2.12
关联：[TL-V12](../../../GBP%20Tasks/Views/TL-V12_UFS_Diagram.md) · Roadmap 卡片 V12 · [LIM-19](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-03](../../L1-Domain/DK-AUD-003_Applicability.md)

本文件也是 [AUD-S15](../Schedules/AUD-S15_Refuse_RMRC.md) 的基础。UFS 图的用途是 §5.3.15 的「Total UFS」。

## 1. 适用性

跟随 S15，按 APL-03：建筑物属 Cap. 123H 附表所列（按用途与 UFS 门槛）时适用。

不适用时：**N/A（附条件）**，理由句引 APL-03（总楼面面积已低于门槛即可，不必另算 UFS）；图纸上没有该句 → **N/A 待声明**。

## 2. 要取得的信息

- 用途（APL-01）。
- 外墙以内总楼面面积（总 GFA 方案合计）。
- 若适用：UFS 面积方案、视图、填色。

## 3. L1 检查项

没有该图时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V12-L1 | (a)(b) UFS 范围与计算 | 视图、填色、计算表（GEN-01） | 有 → Pass |
| V12-L2 | N/A 声明 | 理由句 | 无 → N/A 待声明 |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V12-C1 | 总楼面面积（UFS 的上限）vs 门槛 | LIM-19 | 用途 INP-12 未定 → 两种用途门槛都写 |

## 5. 常见坑

- 门槛余量看起来很小（第 1 轮：差 15.880 m²）：写明为什么仍稳健——UFS 还要扣楼梯、洗手间、机房等。

## 6. 外部输入

INP-12。

## 7. 依赖

与 AUD-S15 同审；AUD-S16（TBE 按 UFS 计面积时需要本图）。

## 8. GAP

- Cap. 123H 附表经抽取压平，版式须对原件（LIM-19 注）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V12`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
