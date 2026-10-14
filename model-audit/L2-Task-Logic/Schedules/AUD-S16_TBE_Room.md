# AUD-S16 TBE Room Floor Area · BIMGBPS §5.3.16
关联：[TL-S16](../../../GBP%20Tasks/Schedules/TL-S16_TBE_Room.md) · Roadmap 卡片 S16 · [LIM-18](../../L1-Domain/DK-AUD-002_Limits_Index.md) · [APL-04](../../L1-Domain/DK-AUD-003_Applicability.md)

## 1. 适用性

按 APL-04：商业、工业、住宅（独立屋除外）、旅馆建筑物适用（Cap. 123F reg 28A）；MAF 跟随 APP-84 注 2。

不适用时：**N/A（附条件）**，用 APL-04 理由句；图纸上没有 → N/A 待声明。

## 2. 要取得的信息

- 用途（APL-01）；AP 对「是否属 commercial building」的判断。
- 房间 / 面积名称有无 TBE；S08 清单 TBE 豁免项是否申请。
- 若适用：TBE 房面积、UFS（AUD-V12）。

## 3. L1 检查项

共用：GEN-01、GEN-06。没有该表时：适用 → Missing；不适用 → 查 N/A 声明。

| ID | 查什么 | 判 |
| --- | --- | --- |
| S16-L1 | 表是模型生成（GEN-01） | 图片 → Fail |
| S16-L2 | TBE 房面积与模型一致（GEN-06） | 不一致 → Fail |

## 4. L2 计算与限值

| ID | 计算 | 限值 | 缺什么时 |
| --- | --- | --- | --- |
| S16-C1 | 按 APP-84 附录 A 依 UFS 计最小面积；实际 ≥ 最小 | APP-84 附录 A | 附录 A 数值未入 DK-AUD-002 → `[GAP]` |

## 5. 常见坑

- Roadmap 互依 ①：S16 要单位数（S04），S04 要 GFA（S08），S08 要 S07，S07 又要 S16 的结论。审核时先用设计单位数判，S04 定稿后复核。

## 6. 外部输入

INP-12。

## 7. 依赖

与 AUD-S04、AUD-S07、AUD-S08、AUD-V12 互依。

## 8. GAP

- APP-84 附录 A 数值未录入 L1。

## 9. 可执行规格

合并在 [G2 房间-用途组](../Groups/G2_Room_Use.md)：一次提取、一次分析、一份报告。本 Task 的规则见该文件 §3「S16」。

单独跑：`--tasks S16`，最少提取与依赖见 [G2「按 Task 单独跑」](../Groups/G2_Room_Use.md)；并回总结果用 `build_results.py --update`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。
