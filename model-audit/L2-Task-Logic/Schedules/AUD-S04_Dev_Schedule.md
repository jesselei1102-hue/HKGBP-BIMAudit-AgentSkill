# AUD-S04 Development Schedule · BIMGBPS §5.3.4
关联：[TL-S04](../../../GBP%20Tasks/Schedules/TL-S04_Dev_Schedule.md) · Roadmap 卡片 S04

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况；个别栏为「NIL」时，在栏内写 NIL，不写 N/A。

## 2. 要取得的信息

- Development Schedule 的形式与每一栏的值。
- 各栏的来源 Task 的结果：GFA（S08）、SC / PR（S05）、绿化（V14）、车位（停车构件数量）、高度（V03）、单位数、UFA（V11）。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S04-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S04-L2 | 逐栏对来源 Task（GEN-06） | 不一致 → 列出差异，标 Major |
| S04-L3 | 高度栏与 V03 / C 图同一口径 | 两处口径不同 → 两个都列（INP-11） |

## 4. L2 计算与限值

数字的合规判定在各来源 Task（S05、S08、V14…）。本表只判一致性，不另判 L2。地契条款（例：地契限高、车位要求）需 INP-01 → 否则 Unclear。

## 5. 常见坑

- Development Schedule 与计算表写的建筑高度可能不同口径。

## 6. 外部输入

INP-01、INP-09、INP-11。

## 7. 依赖

前置：AUD-S05、AUD-S08、AUD-V14、AUD-S16（单位数，互依关系见 Roadmap §06）。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S04`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
