# AUD-S03 List of Coordinates · BIMGBPS §5.3.3
关联：[TL-S03](../../../GBP%20Tasks/Schedules/TL-S03_Coordinates.md) · Roadmap 卡片 S03 · MA-2.3 · [LIM-03](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 项目基点与测量点的 E / N、正北角。
- 地界各顶点坐标、各边长度与方位角（由地界几何换算）。
- 坐标表的形式与表值。

## 3. L1 检查项

共用：GEN-01、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S03-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S03-L2 | 坐标格式 HK1980、三位小数（LIM-03） | 不合 → Fail |
| S03-L3 | 有方位角与边长（条文「with bearings and distances」） | 缺 → Fail |
| S03-L4 | 表值 vs 地界换算值，逐点到 0.001 m（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S03-C1 | 坐标 vs 测量图 | ADM-21 | INP-01 缺 → Unclear |

## 5. 常见坑

- 坐标表是插入的 PNG。
- E/N 落在 8XX,XXX 只说明「像 HK1980」，要标 `[INFERENCE]`。

## 6. 外部输入

INP-01。

## 7. 依赖

与 AUD-V01 共用地界数据。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S03`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
