# AUD-S01 List of Drawings · BIMGBPS §5.3.1
关联：[TL-S01](../../../GBP%20Tasks/Schedules/TL-S01_Drawing_List.md) · Roadmap 卡片 S01 · MA-7.1、MA-7.2

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 全部图纸：图号、图名、修订。
- 图纸目录在图上的形式：图纸目录明细表（Sheet List）还是图片。
- 目录内容。

## 3. L1 检查项

共用：GEN-01、GEN-06（[AUD-000 §8](../AUD-000_Audit_Flow.md)）。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S01-L1 | 目录是模型生成的图纸目录明细表（GEN-01） | 图片 → Fail |
| S01-L2 | 逐行与模型图纸比对：图号、图名、修订（GEN-06） | 有出入 → Fail，列出差异 |

## 4. L2 计算与限值

无 L2。

## 5. 常见坑

- 目录内容与图纸完全一致，但整张是图片：仍是 Fail。

## 6. 外部输入

无。

## 7. 依赖

后续：AUD-A01、AUD-A04。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G5 清单组与 G6 模型健康](../Groups/G5_Lists_G6_Model_Health.md)。本 Task 的检查见该文件 §1。

单独跑：`--tasks S01`，最少提取与依赖见 [G5「按 Task 单独跑」](../Groups/G5_Lists_G6_Model_Health.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
