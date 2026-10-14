# AUD-V14 SBD Compliance Diagrams · BIMGBPS §5.2.14
关联：[TL-V14](../../../GBP%20Tasks/Views/TL-V14_SBD_Compliance.md) · Roadmap 卡片 V14 · [LIM-28、LIM-29](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-09](../../L1-Domain/DK-AUD-003_Applicability.md)

与 [AUD-S07](../Schedules/AUD-S07_GFA_Concession_Req.md) 前置条件 (a) 相关：申请受 cap 豁免时，SBD 合规是前提。

## 1. 适用性

按 APL-09：楼宇间距看 APP-152 第 3 段门槛；绿化看 Table 2（地盘 ≥ 1,000 m²）；后退的门槛 `[GAP]`。

不适用时：逐项写 N/A（附条件），理由句用 APL-09。

## 2. 要取得的信息

- 地盘面积；连续投影立面长度 Lp；街道阔度。
- 绿化面积方案：各块面积、编号、楼层；主要区 / 非主要区划分。
- SBD 面积方案（间距、后退）：有无面积、有无视图使用。
- 对应计算表的形式（GEN-01）。

## 3. L1 检查项

没有该图时：适用项无图 → Missing。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V14-L1 | (a) 楼宇间距、后退、绿化覆盖 | 三项各有无图 | 只有绿化 → Partial（其余看适用性） |
| V14-L2 | (b) 能分无盖绿化、水景、主要 / 非主要区 | 区划 | 无主要区划分 → Partial |
| V14-L3 | 对应表和计算 | GEN-01；绿化合计 ÷ 地盘面积（GEN-06） | 图片 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V14-C1 | 整体绿化覆盖率 | LIM-29（例：1,000–20,000 m² 地盘 ≥ 20 %） | — |
| V14-C2 | 主要区绿化覆盖率 | LIM-29（≥ 10 %） | 主要区未划分 → Unclear |
| V14-C3 | 楼宇间距是否适用 | LIM-28 | Lp 资料缺 → Unclear |

## 5. 常见坑

- 方案里有面积但没有任何视图使用。
- 只有整体绿化、没有主要区面积 → 主要区 10 % 判不了。

## 6. 外部输入

INP-07。

## 7. 依赖

后续：AUD-S07 (a)、AUD-S04（绿化百分比）。

## 8. GAP

- APP-152 后退门槛（DK-AUD-006 M-08）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V14`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
