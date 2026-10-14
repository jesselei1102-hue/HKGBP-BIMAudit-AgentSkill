# AUD-S10 Min Exit Doors & Routes · BIMGBPS §5.3.10
关联：[TL-S10](../../../GBP%20Tasks/Schedules/TL-S10_Exit_Doors_Routes.md) · Roadmap 卡片 S10 · MA-4.7、MA-5.3 · [LIM-30](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 每个房间：用途、面积（UFA 口径）、occupancy factor、人数、要求出口数 / 宽度、实设出口数 / 宽度。这些多为房间上的预设参数，先确认字段存在。
- 门的净宽。
- 表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S10-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S10-L2 | UFA = 房间面积（同一四舍五入口径）（GEN-06） | 不一致 → Fail |
| S10-L3 | 人数 = UFA ÷ 系数，向上取整 | 算错 → Fail |
| S10-L4 | 「要求」栏是公式还是手填（GEN-02） | 手填 → 指出 |
| S10-L5 | 有无未放置房间以空行出现 | 有 → Minor |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S10-C1 | 系数、出口数、出口宽度 | LIM-30（FS Code Part B） | 原文缺 → Unclear（DK-AUD-006 M-01） |

## 5. 常见坑

- 未放置房间会以空行出现在明细表里。

## 6. 外部输入

INP-06。

## 7. 依赖

前置：AUD-V11（UFA）；后续：AUD-S11（人数）。

## 8. GAP

- FS Code Part B 原文（DK-AUD-006 M-01）。

## 9. 可执行规格

合并在 [G2 房间-用途组](../Groups/G2_Room_Use.md)：一次提取、一次分析、一份报告。本 Task 的规则见该文件 §3「S10」。

单独跑：`--tasks S10`，最少提取与依赖见 [G2「按 Task 单独跑」](../Groups/G2_Room_Use.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
