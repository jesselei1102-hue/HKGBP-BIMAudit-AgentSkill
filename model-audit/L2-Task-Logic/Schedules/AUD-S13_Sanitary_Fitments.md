# AUD-S13 Sanitary Fitment Provisions · BIMGBPS §5.3.13
关联：[TL-S13](../../../GBP%20Tasks/Schedules/TL-S13_Sanitary_Fitments.md) · Roadmap 卡片 S13 · MA-4.7 · [LIM-21、LIM-22](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-08](../../L1-Domain/DK-AUD-003_Applicability.md)

## 1. 适用性

每个项目都适用（APL-08）。要判的是「归入 Cap. 123I Part II 哪一类」。不适用时：不存在这种情况。

## 2. 要取得的信息

- 每层 UFA：逐房相加（与 AUD-V11 同源）。
- 实设洁具：按族 / 类型分层计数，排除水箱、冲水阀、扶手等配件；无障碍厕所另计。
- 男 / 女洗手间各自的洁具数。
- 没有楼层的洁具：备注与几何。
- 表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S13-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S13-L2 | 每层 UFA 与逐房合计一致（GEN-06） | 不一致 → Fail |
| S13-L3 | 实设数与模型计数一致 | 不一致 → Fail |
| S13-L4 | 没有楼层的洁具已归类 | 未处理 → Minor |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S13-C1 | 按表上采用的类别：人数 = UFA ÷ 系数（向上取整），按男女比分；查对应附表得要求数 | LIM-21（office）等 | — |
| S13-C2 | 敏感度：按另一合理类别再算一次 | LIM-22（公众娱乐场所）等 | Cap. 172 定义缺 → `[GAP]` |
| S13-C3 | 实设 ≥ 要求 | — | — |

两个类别结论相反 → **Pass（附条件：AP 确认类别）** 或 **Fail（附条件）**，交 AP（INP-12）。

## 5. 常见坑

- office 与公众娱乐场所两种口径，人数可差约 18 倍。
- 无楼层的「Plumbing Fixtures」可能是洗手台面，不是垃圾数据：先读备注与几何。

## 6. 外部输入

INP-06、INP-12。

## 7. 依赖

前置：AUD-V11。

## 8. GAP

- Cap. 172 定义（DK-AUD-006 M-04）。

## 9. 可执行规格

合并在 [G2 房间-用途组](../Groups/G2_Room_Use.md)：一次提取、一次分析、一份报告。本 Task 的规则见该文件 §3「S13」。

单独跑：`--tasks S13`，最少提取与依赖见 [G2「按 Task 单独跑」](../Groups/G2_Room_Use.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
