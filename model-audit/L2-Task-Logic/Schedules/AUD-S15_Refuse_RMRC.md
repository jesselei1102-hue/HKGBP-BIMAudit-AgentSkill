# AUD-S15 Refuse Storage & RMRC · BIMGBPS §5.3.15
关联：[TL-S15](../../../GBP%20Tasks/Schedules/TL-S15_Refuse_RMRC.md) · Roadmap 卡片 S15 · [LIM-19、LIM-20](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-03](../../L1-Domain/DK-AUD-003_Applicability.md)

同 [AUD-V12](../Views/AUD-V12_UFS_Diagram.md)（同一个适用性判定）。本文件只写差异。

## 1. 适用性

同 AUD-V12 §1（APL-03）。不适用时：**N/A（附条件）**，同一句 APL-03 理由句；图纸上没有 → N/A 待声明。

## 2. 要取得的信息

同 AUD-V12 §2；若适用，另取：垃圾房 / 回收房的实际面积；垃圾车出入路线（PNAP APP-35 第 3 段）。

## 3. L1 检查项

共用：GEN-01、GEN-06。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S15-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S15-L2 | APP-35 第 5 段三项：UFS、最小面积、实际面积 | 缺 → Partial |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S15-C1 | 门槛（同 V12-C1） | LIM-19 | — |
| S15-C2 | 最小面积 = UFS ÷ 除数；实际 ≥ 最小 | LIM-20 | UFS 未算 → Unclear |

## 5. 常见坑

同 AUD-V12。

## 6. 外部输入

INP-12。

## 7. 依赖

与 AUD-V12 同审。

## 8. GAP

同 AUD-V12。

## 9. 可执行规格

合并在 [G2 房间-用途组](../Groups/G2_Room_Use.md)：一次提取、一次分析、一份报告。本 Task 的规则见该文件 §3「S15」。

单独跑：`--tasks S15`，最少提取与依赖见 [G2「按 Task 单独跑」](../Groups/G2_Room_Use.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
