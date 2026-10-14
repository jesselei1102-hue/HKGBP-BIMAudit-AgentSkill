# DK-AUD-004 · 颜色与图面标准

Layer 1。颜色类检查一律按导出图像的像素取样判定，不凭目测（判定方法见 [AUD-000](../L2-Task-Logic/AUD-000_Audit_Flow.md) `GEN-03`、`GEN-05`）。

## 1. BIMGBPS Table 1 · GFA Diagram 着色

出处：BIMGBPS §5.2.10(c)、Table 1「Colour Code System for GFA diagrams」（2019）。状态：已对原文。

| 类 | 含义 | RGB |
| --- | --- | --- |
| 1 | Accountable GFA · domestic | 255, 164, 25 |
| 2 | Accountable GFA · non-domestic | 227, 100, 102 |
| 3a | 不受 10 % cap · APP-151 所列豁免项（车位、上落货区除外）· PURPLE | 191, 0, 255 |
| 3b | 不受 10 % cap · 车位、上落货区及其他 · WOOD | 222, 184, 135 |
| 4a | 受 10 % cap · APP-151 所列项 | 30, 144, 255 |
| 4b | 受 10 % cap · 其他 | 144, 214, 236 |

**判定**：图上和图例上的取样值都要与表中数值**完全相等**。差一个数值也记 Fail，并写出取样值。

## 2. 地盘粉红（Block / Key Plan）

- 值：255, 218, 236。
- 出处：Roadmap §03 Table 1 旁注。
- 状态：BIMGBPS §5.2.2(b) 原文只写「pink」，不给 RGB → 取样明显不是粉红色系时记 Fail；颜色接近但不等于 255,218,236 时记 Partial，并写取样值 `[GAP：BD 是否指定 RGB]`。

## 3. PNAP ADM-9 · 平面材料与新旧工程着色

- 出处：BIMGBPS §5.1.4(a)；PNAP ADM-9。
- 状态：ADM-9 原文的颜色表未逐色核对 `[GAP]`。
- 判定办法：以模型自带的图例视图（如 A001「Colour Indication」）为准，逐色取样对照平面、剖面、立面上的填色。图例本身是否符合 ADM-9，记 `[GAP]`。

## 4. 半色调底图

- 出处：BIMGBPS §4.2(d)；§5.2.8(d)、§5.2.10(d) 等各面积图条文。状态：已对原文。
- 原文只要求「halftone under laying floor plans」，没有给数值判据。本包采用的判据 `[INFERENCE]`：
  - 导出面积图 PNG，统计纯黑（0,0,0）像素占比和 100–220 灰阶像素占比。
  - 墙线纯黑、灰阶占比 < 1 % → 判为**没有半色调底图**。
  - 墙线为灰、灰阶占比明显高于纯黑 → 有。
  - 介于两者之间 → Unclear，附截图交人工判断。

## 5. 修订着色

- 出处：BIMGBPS §5.4。首次提交（非修订图）→ N/A。修订图的颜色要求未在本包展开 `[GAP]`。
