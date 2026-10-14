# AUD-V07 Open Space Diagram · BIMGBPS §5.2.7
关联：[TL-V07](../../../GBP%20Tasks/Views/TL-V07_Open_Space.md) · Roadmap 卡片 V07 · [LIM-17](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-01、APL-02](../../L1-Domain/DK-AUD-003_Applicability.md)

本文件也是 [AUD-S06](../Schedules/AUD-S06_Open_Space_Calc.md) 的基础。

## 1. 适用性

按 APL-02：只适用于住用建筑物或综合用途建筑物的住用部分（Cap. 123F reg 25(1)(a)、附表 2）。

不适用时：**N/A（附条件）**，用 APL-02 的理由句；图纸上没有该句 → **N/A 待声明**。

## 2. 要取得的信息

- 用途（APL-01 的输入）：房间用途、Development Schedule 用途栏、有无居住单位 / 宿舍 / 管理员宿舍。
- 若适用：休憩用地面积方案或填充、视图、尺寸；场地类别（INP-02）；有盖面积。

## 3. L1 检查项

没有该图时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 条文 | 查什么 | 判 |
| --- | --- | --- | --- |
| V07-L1 | (a) 参照场地分类的位置与尺寸 | 视图、尺寸 | 有 → Pass |
| V07-L2 | (b) 对应计算表 | GEN-01 | 图片 → Fail |
| V07-L3 | N/A 声明 | 不适用时，图纸上有无理由句 | 无 → N/A 待声明 |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| V07-C1 | 休憩用地面积 vs 附表 2 要求（例：丙类 ≥ 有盖面积 1/4）；位置（后方 / 侧面） | LIM-17、附表 2 | 场地类别 INP-02 缺 → Unclear |

## 5. 常见坑

- 把「图不存在」直接记 Missing：要先判适用性。
- 管理员宿舍会使建筑物带有住用部分。

## 6. 外部输入

INP-02、INP-12（用途由 AP 确认）。

## 7. 依赖

前置：AUD-S02、AUD-S05；与 AUD-S06 同审。

## 8. GAP

无（Cap. 123 s.2 的定义已在 Knowledge）。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks V07`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
