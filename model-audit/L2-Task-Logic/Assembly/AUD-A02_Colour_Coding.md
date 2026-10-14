# AUD-A02 Colour Coding (GFA) · BIMGBPS §5.1.4、Table 1、§5.4
关联：[TL-A02](../../../GBP%20Tasks/Assembly/TL-A02_Colour_Coding.md) · Roadmap 卡片 A02 · [DK-AUD-004](../../L1-Domain/DK-AUD-004_Colour_Standards.md)

## 1. 适用性

每个项目都适用（GFA 图必有）。修订着色（§5.4）只适用于修订图。不适用时：首次提交 → 修订着色 N/A。

## 2. 要取得的信息

- GFA 图的逐色像素取样。
- 图例色块的逐色像素取样。
- 半色调（GEN-03）。
- 楼层平面用的着色体系（ADM-9），与 GFA 图分开。

## 3. L1 检查项

没有该图时：GFA 图不存在 → 见 AUD-V10（Missing）；本项记 Unclear。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| A02-L1 | Table 1（图） | GFA 图取样 = DK-AUD-004 §1 | 完全相等 → Pass |
| A02-L2 | Table 1（图例） | 图例取样 = DK-AUD-004 §1 | 完全相等 → Pass |
| A02-L3 | 两套体系分开 | GFA 图用 Table 1；楼层平面用 ADM-9；图案视图不判 | 混用 → Fail |
| A02-L4 | §4.2(d) 半色调 | GEN-03 | 无 → Fail（只缺此项 → 整体 Partial） |
| A02-L5 | §5.4 修订色 | 修订图才查 | 首次提交 → N/A |

## 4. L2 计算与限值

无 L2。

## 5. 常见坑

- GFA 图（Table 1）和楼层平面（ADM-9）是两套色，不要互相对照。
- harness 不能执行代码时，不能目测给 Pass（AUD-000 §7 规则 4）。

## 6. 外部输入

无。

## 7. 依赖

与 AUD-V10 同审。

## 8. GAP

- 修订着色规则未展开（DK-AUD-004 §5）。


## 9. 可执行规格

合并在 [G4 图面组](../Groups/G4_Drawings.md)。本 Task 的检查见该文件 §2。

单独跑：`--tasks A02`，最少提取与依赖见 [G4「按 Task 单独跑」](../Groups/G4_Drawings.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
