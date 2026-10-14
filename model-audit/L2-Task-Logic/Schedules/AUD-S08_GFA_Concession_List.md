# AUD-S08 List of GFA Concessions · BIMGBPS §5.3.8
关联：[TL-S08](../../../GBP%20Tasks/Schedules/TL-S08_GFA_Concession_List.md) · Roadmap 卡片 S08 · MA-4.4 · [LIM-15、LIM-23](../../L1-Domain/DK-AUD-002_Limits_Index.md)

与 [AUD-V10](../Views/AUD-V10_GFA_Diagram.md) 一次读取、交叉校验（GEN-07）。

## 1. 适用性

有任何 GFA 豁免申请时适用。不适用时：没有任何豁免申请 → **N/A（附条件）**，理由句：「本项目没有申请任何 GFA 豁免。附条件：AP 确认。」

## 2. 要取得的信息

- 表 (a)：APP-151 附录 A 清单、ADM-2 附录 G / H 汇总，各有无。
- 表 (b)：无封顶 / 受 cap 分栏。
- 每项：数量、单个面积、小计。
- 扣减面积方案里对应 Area 的面积（与 V10 同一组）。

## 3. L1 检查项

共用：GEN-01、GEN-02、GEN-06。没有该表时：有豁免申请 → Missing。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S08-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S08-L2 | (a) 附录 A、G、H 齐 | 缺一 → Partial |
| S08-L3 | (b) 无封顶 / 受 cap 分栏 | 无 → Fail |
| S08-L4 | 逐项乘法：数量 × 单个面积 = 小计；小计与模型 Area 一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S08-C1 | 受 cap 合计 ÷ 申报 GFA，住用 / 非住用分开 | ≤ 10 %（LIM-23） | — → **Pass（只限算术）** |

各项可否豁免，看 AUD-S07 和各项 PNAP。

## 5. 常见坑

- 8 % 是旧文档的错值（DK-AUD-005 §2）。
- 重复的豁免区（AUD-V10 §5）。
- 不要把豁免再扣一次（DK-AUD-005 §3.3）。

## 6. 外部输入

INP-07、INP-13。

## 7. 依赖

与 AUD-V10、AUD-S07、AUD-S05 同链；后续 AUD-S04、AUD-S18。

## 8. GAP

无。


## 9. 可执行规格

合并在 [G3 面积方案组](../Groups/G3_Area_Scheme.md)：一次提取、一次分析、一份报告。本 Task 的检查见该文件 §2。

单独跑：`--tasks S08`，最少提取与依赖见 [G3「按 Task 单独跑」](../Groups/G3_Area_Scheme.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
