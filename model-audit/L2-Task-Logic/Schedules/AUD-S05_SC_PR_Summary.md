# AUD-S05 Site Classification + SC / PR Summary · BIMGBPS §5.3.5
关联：[TL-S05](../../../GBP%20Tasks/Schedules/TL-S05_SC_PR_Summary.md) · Roadmap 卡片 S05 · [LIM-11 至 LIM-16](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-01](../../L1-Domain/DK-AUD-003_Applicability.md)

## 1. 适用性

每个项目都适用。不适用时：不存在这种情况。

## 2. 要取得的信息

- 街道阔度（标注）；地界各边长度。
- 有盖面积（SC 方案）；申报 GFA（S08 / V10）；地盘面积（S02）。
- 用途（APL-01）；mean street level 与屋顶标高（V03）。
- 表的形式；表上「支持场地分类的资料」写了什么。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S05-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S05-L2 | §5.3.5(a)：支持场地分类的资料（哪几条街、临街比例、指明街道依据） | 只写「CLASS OF SITE: C」 → Partial |
| S05-L3 | SC、PR 算术（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

逐步写成表：

| ID | 步骤 | 限值 / 条文 | 缺什么时 |
| --- | --- | --- | --- |
| S05-C1 | 用途：住用 / 非住用 / 综合 | APL-01 | INP-12 未定 → 各算一次 |
| S05-C2 | 街道阔度 | LIM-11（≥ 4.5 m） | — |
| S05-C3 | 临街比例 | LIM-12 | — |
| S05-C4 | 指明街道 | reg 18A(3) | INP-02 缺 → `[GAP]`，结论附条件 |
| S05-C5 | 地盘面积 | LIM-14 | — |
| S05-C6 | 建筑高度 | LIM-13 | 两个口径都算（INP-11） |
| S05-C7 | 准许 SC | LIM-16（附表 1 对应栏） | — |
| S05-C8 | 准许 PR | LIM-16 | — |
| S05-C9 | 稳健性：甲 / 乙 / 丙类数值是否相同；全部豁免不获批时 PR 是否仍过 | — | — |

结论写法：两个高度口径都过、且稳健性成立 → **Pass（附条件：指明街道成立、用途确认）**。

## 5. 常见坑

- 不用 Architecture 的 SC 简表（DK-AUD-005 §3.1）。
- 附表 1 在 Knowledge 里是重建表，引用具体数值前对电子版（DK-AUD-006 M-11）。

## 6. 外部输入

INP-01、INP-02、INP-03、INP-11、INP-12。

## 7. 依赖

前置：AUD-S02、AUD-S08、AUD-V03；与 AUD-V09 同链。

## 8. GAP

- 指明街道的法律地位，只能从地契 / 路政资料确认。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S05`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
