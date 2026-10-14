# AUD-S11 Discharge Value Schedule · BIMGBPS §5.3.11
关联：[TL-S11](../../../GBP%20Tasks/Schedules/TL-S11_Discharge_Value.md) · Roadmap 卡片 S11 · [LIM-30](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 每层：服务人数、逃生楼梯数、每梯分担人数、DV 总人数、允许 DV。
- 表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S11-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S11-L2 | 每层人数与 AUD-S10 合计一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S11-C1 | DV 总人数 ≤ 允许 DV | LIM-30（FS Code B12） | 原文缺 → Unclear |

## 5. 常见坑

- DV 数值存在每层**每个**房间上（重复）。读表时按层去重，不要把重复行当成多个楼梯。

## 6. 外部输入

INP-06。

## 7. 依赖

前置：AUD-S10。

## 8. GAP

- FS Code Part B 原文（DK-AUD-006 M-01）。

## 9. 可执行规格

合并在 [G2 房间-用途组](../Groups/G2_Room_Use.md)：一次提取、一次分析、一份报告。本 Task 的规则见该文件 §3「S11」。

单独跑：`--tasks S11`，最少提取与依赖见 [G2「按 Task 单独跑」](../Groups/G2_Room_Use.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
