# AUD-V11 UFA Diagram · BIMGBPS §5.2.11
关联：[TL-V11](../../../GBP%20Tasks/Views/TL-V11_UFA_Diagram.md) · Roadmap 卡片 V11 · MA-4.5

## 1. 适用性

所有须计 UFA 的项目（S13 洁具、S10 人数要用 UFA）。不适用时：几乎不会出现；没有任何以 UFA 计算的要求时，才可 N/A，并写明理由。

## 2. 要取得的信息

- UFA 面积方案：已放置 Area 的数量、面积。
- 每个视图：轴网、填色、总 UFA 外框、房间标记。
- 房间 UFA 与 AUD-S10、AUD-S13 用的 UFA 是否同源。
- 对应计算表的形式（GEN-01）。

## 3. L1 检查项

没有该图时：Missing。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V11-L1 | (a) 轴网 | 轴网数 | 有 → Pass |
| V11-L2 | (b) 总 UFA 范围（色或注） | 填色 / 外框；方案内有无已放置面积 | 无填色无外框 → Fail |
| V11-L3 | (c) 对应表和计算 | GEN-01 | 图片 → Fail |

## 4. L2 计算与限值

条文无 UFA 限值，不判。只做 GEN-06：UFA 合计与 S13 每层 UFA 是否一致。

## 5. 常见坑

- 方案里的面积全部未放置；清理未放置面积之后方案变空，要重画。

## 6. 外部输入

无。

## 7. 依赖

后续：AUD-S10、AUD-S13、AUD-S04。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V11`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
