# AUD-V05 Typical Details · BIMGBPS §5.2.5
关联：[TL-V05](../../../GBP%20Tasks/Views/TL-V05_Details.md) · Roadmap 卡片 V05 · MA-1.5 · [LIM-03](../../L1-Domain/DK-AUD-002_Limits_Index.md)

## 1. 适用性

适用范围取决于项目有哪些须出详图的部位（PNAP 列举的冷气机平台、无障碍设施、护栏、幕墙等），由 AP 确定（INP-14）。不适用时：在 TL-A04 N/A 表逐个部位写理由。

## 2. 要取得的信息

- 详图视图（drafting / detail / 大比例剖面）：清单、比例、样板、详图编号、所在图纸。
- 平面上的详图索引标记，与详图编号、图纸是否对应。
- 视图名与图上标题（有无 TYPICAL / NON-TYPICAL）。
- 模型里存在、但没有详图的部位清单。
- CAD 详图（导入或链接）。

## 3. L1 检查项

没有该图时：模型里完全没有详图 → Missing（若 AP 确认有须出详图的部位）。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V05-L1 | (a) 能定位 | 索引标记 ↔ 详图编号 ↔ 图纸 | 对得上 → Pass |
| V05-L2 | (b) 能分典型 / 非典型 | 标题 | 无 → Fail |
| V05-L3 | (c) 关键尺寸、标高、构造 | 每张详图的尺寸、标高、构造说明 | 逐张判 |
| V05-L4 | 覆盖面 | 须出详图的部位 vs 已有详图 | 缺 → Partial，列出部位交 AP |

## 4. L2 计算与限值

本条文不给数值。栏杆高度、挡烟垂壁深度等按 B(C)R / FS Code `[GAP]` → 不判，写「须 <规例>」。

## 5. 常见坑

- 详图视图名就是「SECTION」，没有标题，分不出典型 / 非典型。
- CAD 详图可能存在，但工具看不到（GAP-03）：不能直接记 Missing，要先人工确认。

## 6. 外部输入

INP-14（适用部位由 AP 确认）。

## 7. 依赖

前置：AUD-V02、AUD-V03；后续：AUD-S07（豁免项的详图）。

## 8. GAP

- CAD 导入不可见（GAP-03）。
- B(C)R、FS Code 原文（DK-AUD-006 M-01 至 M-03）。


## 9. 可执行规格

合并在 [G4 图面组](../Groups/G4_Drawings.md)。本 Task 的检查见该文件 §2。

单独跑：`--tasks V05`，最少提取与依赖见 [G4「按 Task 单独跑」](../Groups/G4_Drawings.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
