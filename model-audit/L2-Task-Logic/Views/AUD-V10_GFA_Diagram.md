# AUD-V10 GFA Diagram · BIMGBPS §5.2.10
关联：[TL-V10](../../../GBP%20Tasks/Views/TL-V10_GFA_Diagram.md) · Roadmap 卡片 V10 · MA-4.4 · [LIM-15、LIM-23](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [DK-AUD-004 §1](../../L1-Domain/DK-AUD-004_Colour_Standards.md)

与 [AUD-S08](../Schedules/AUD-S08_GFA_Concession_List.md)、[AUD-S07](../Schedules/AUD-S07_GFA_Concession_Req.md) 用同一组面积数据，一次读取、交叉校验（GEN-07）。

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 总 GFA 面积方案与扣减 / 豁免面积方案：逐层每个 Area 的面积、名称、编号、楼层、所在视图、有无标记、分类参数。
- 每个视图：轴网、尺寸、着色取样、半色调。
- 图例色块取样。
- 对应计算表的形式（GEN-01）。

## 3. L1 检查项

没有该图时：Missing（Blocker 级）。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V10-L1 | (a) 轴网 | 轴网数 | 有 → Pass |
| V10-L2 | (b) 布置尺寸 | 各豁免区尺寸 | 有 → Pass |
| V10-L3 | (c) Table 1 着色 | 逐色取样，对 DK-AUD-004 §1 | 完全相等 → Pass；不等 → Fail（写取样值） |
| V10-L4 | (d) 半色调底图 | GEN-03 | 无 → Fail |
| V10-L5 | (e) 分区标签可与表对照 | 编号、名称 | 名称为默认值 / 错字 → Minor |
| V10-L6 | (f) 对应表和计算 | GEN-01 | 图片 → Fail |
| V10-L7 | 分类完整 | 每个 Area 能映射到 Table 1 六类（含住用 / 非住用） | 不能 → Fail（Roadmap P4） |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V10-C1 | 申报 GFA = 总 GFA − 无封顶豁免 − 受 cap 豁免；与图上 / 表上数字比对 | LIM-15 | — |
| V10-C2 | 受 cap 豁免 ÷ 申报 GFA，住用与非住用分开 | ≤ 10 %（LIM-23） | 与 AUD-S08 一起判 |

各项能否豁免看 AUD-S07；本项只做算术。

## 5. 常见坑

- **同名、同面积的两套豁免区**：一套在别的标高、没有视图、没有标记，是残留。复算前先确认用哪套。
- 扣减 Area 本来就不在 accountable 合计里，不能再减一次（DK-AUD-005 §3.3）。
- 总 GFA 方案的视图可能只有线、没有填色。
- 上限是 10 %，不是 8 %（DK-AUD-005 §2）。

## 6. 外部输入

INP-07、INP-13。

## 7. 依赖

与 AUD-S07、AUD-S08、AUD-S05 同链；AUD-A02（颜色）。

## 8. GAP

- 面积边界的缝隙 / 重叠（GAP-02）：只能抓到面积为 0 的未闭合面积。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V10`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
