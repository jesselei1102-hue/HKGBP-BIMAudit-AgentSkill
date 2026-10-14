# AUD-V13 Prescribed Windows · BIMGBPS §5.2.13
关联：[TL-V13](../../../GBP%20Tasks/Views/TL-V13_Prescribed_Windows.md) · Roadmap 卡片 V13 · MA-5.1、MA-5.2、MA-6.3 · [LIM-06 至 LIM-10](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-10](../../L1-Domain/DK-AUD-003_Applicability.md)

与 [AUD-S14](../Schedules/AUD-S14_Window_Area_Calc.md) 同审：S14 算面积，V13 证明朝向与布置。

## 1. 适用性

有居住、办公、厨房房间（reg 30），或有便溺污水设备的房间（reg 36）时适用（APL-10）。不适用时：只有项目完全没有这几类房间才可能，理由句须列出房间用途。

## 2. 要取得的信息

- 适用房间清单（APL-10）：每个房间的用途、楼面面积。
- 每个房间的开口：窗与幕墙嵌板；玻璃面积、可开启面积、开口顶部高度。
- 开口朝向：面对的街道（阔度）或矩形水平面（面积、底边、深度）；周边遮挡。
- 有无专门的规定窗 diagram；平面、立面上的窗标记与尺寸。

## 3. L1 检查项

没有该图时：适用而无专门 diagram → Missing（只在平立面零散出现，按下表逐项判 Partial）。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V13-L1 | (a) 规定窗面积 | diagram 上的面积标示 | 无 → Missing |
| V13-L2 | (b) 关键位置矩形水平面 | 矩形水平面图示与尺寸 | 无 → Missing |
| V13-L3 | (c) 可开启窗（平面或立面） | 标记、尺寸 | 零散 → Partial |
| V13-L4 | (d) 居室 / 厨房 / 办公的窗 | 适用房间都有对应窗 | 部分 → Partial |
| V13-L5 | (e) 窗的布置 | 能否从图上看出布置 | 只能拼凑 → Partial |
| V13-L6 | (f) 性能化（APP-130） | 是否采用 | 未采用 → N/A |
| V13-L7 | (g) 对应表和计算 | GEN-01（与 S14 同一张表） | 图片 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V13-C1 | 每个适用房间：玻璃面积 ≥ 楼面面积 1/10 | LIM-06 | — |
| V13-C2 | 可开启 ≥ 1/16，开口顶部 ≥ 2 m（便溺房间 ≥ 1/10） | LIM-07、LIM-10 | 可开启参数缺 → 写假设，不默认 100 % |
| V13-C3 | 朝向：面对 ≥ 4.5 m 街道，或矩形水平面达标且无遮挡 | LIM-08、LIM-09 | 周边资料 INP-05 缺 → Unclear |

## 5. 常见坑

- **TL-S14、训练 Prompt、Architecture 写采光 1/8；原文是 1/10**（DK-AUD-005 §1）。按 1/8 算出的旧结论都要重算。
- 只查 Windows 会漏幕墙嵌板。
- 房间名（Function Room、Activity Area）不等于用途：按 APL-10 交 AP。

## 6. 外部输入

INP-05、INP-12。

## 7. 依赖

与 AUD-S14 同审；前置 AUD-V02、AUD-V04。

## 8. GAP

- APP-130 原文（DK-AUD-006 M-06）。
- 遮挡斜面检查需要周边几何，模型多半没有。


## 9. 可执行规格

合并在 [G4 图面组](../Groups/G4_Drawings.md)。本 Task 的检查见该文件 §2。

单独跑：`--tasks V13`，最少提取与依赖见 [G4「按 Task 单独跑」](../Groups/G4_Drawings.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
