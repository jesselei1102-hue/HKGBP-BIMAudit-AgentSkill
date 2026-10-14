# DK-AUD-002 · 限值索引

Layer 1。L2 第二层判定用到的每一个数值限值。每行都写：条文、版本、原文摘句（≤ 1 句），以及状态。

- **已对原文**：已在法例 / PNAP / BIMGBPS 原文里核过摘句。
- **[GAP]**：原文不在手，数值只能当线索，L2 判定须记 Unclear。

法例原文的约定位置是 `../../Legislation/`（[cap123](../../Legislation/cap123/README.md) · [cap123f](../../Legislation/cap123f/README.md) · [cap123h](../../Legislation/cap123h/README.md) · [cap123i](../../Legislation/cap123i/README.md)）。不在时，见 [AUD-000](../L2-Task-Logic/AUD-000_Audit_Flow.md)「法例原文不在时」。

| ID | 限值 | 数值 | 条文 | 版本 | 原文摘句 | 用于 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIM-01 | 面积、体积精度 | 三位小数 | BIMGBPS §5.1.1 | 2019 | "…cubic metres (m3) respectively and rounded off to three decimal places." | 全部面积类 | 已对原文 |
| LIM-02 | 地盘面积取整 | < 2,000 m² → 0.1 m²；≥ 2,000 m² → 1 m² | PNAP ADM-21；BIMGBPS §5.1.1 | Knowledge 摘录版 | "…rounded off (5 up 4 down) to the nearest 0.1m2 for area under 2000m2 and to the nearest 1m2 for area of 2000m2 and above." | S02、V09 | 已对原文 |
| LIM-03 | 坐标与标高格式 | 8XX,XXX.XXX mN / mE；X.XXX mPD | BIMGBPS §5.1.3 | 2019 | "The HK 1980 Grid and HKPD should be presented in metres corrected to three decimal places…" | V01–V04、S03 | 已对原文 |
| LIM-04 | 单个 BIM 文件大小 | ≤ 500 MB | BIMGBPS §4.3(b) | 2019 | "Each BIM file should be limited to the size of 500MB." | A1、A03 | 已对原文 |
| LIM-05 | Revit 版本 | 2017 或以上 | BIMGBPS §4.3(c) | 2019 | "BA currently accepts BIM native files created by (i) Revit version 2017 or later…" | A1、A03 | 已对原文 |
| LIM-06 | 采光：窗玻璃面积 | ≥ 房间楼面面积 1/10 | Cap. 123F reg 30(2)(a)(i) | 17.9.2026 | "the aggregate superficial area of glass in the window or windows is not less than one-tenth of the area of the floor of the room" | S14、V13 | 已对原文 |
| LIM-07 | 通风：可开启面积 | ≥ 楼面面积 1/16；开口顶部离地 ≥ 2 m（独立 / 半独立屋 1.9 m） | Cap. 123F reg 30(2)(a)(ii) | 17.9.2026 | "…to an extent at least equal in the aggregate to one-sixteenth of the area of the floor of the room, be opened…" | S14、V13 | 已对原文 |
| LIM-08 | 订明的窗朝向：矩形水平面 | ≥ 21 m²；底边 ≥ 2.3 m；深 ≥ 4.5 m（临地界 ≥ 2.3 m）；或面对 ≥ 4.5 m 街道 | Cap. 123F reg 31(1)(a)、31(2) | 17.9.2026 | "it has an area of not less than 21 m2" | V13、S14 | 已对原文 |
| LIM-09 | 订明的窗：遮挡斜面 | 居住 71½°；办公 / 厨房 76°；临地界 80½° / 83°；窗台按楼面上 1 m 计 | Cap. 123F reg 31(1)(c)(d)、31(3)(b) | 17.9.2026 | "…inclined… at an angle of 71 1/2° from the horizontal where the window is in a room used for habitation or 76°…" | V13 | 已对原文 |
| LIM-10 | 便溺房间窗 | 玻璃 ≥ 1/10；可开启 ≥ 1/10；开启部分顶部 ≥ 2 m | Cap. 123F reg 36(2)(3) | 17.9.2026 | "a part thereof, not less in area than the equivalent of one-tenth of the area of the floor of the room, can be opened directly into the open air" | S14、V13 | 已对原文 |
| LIM-11 | 场地类别：街道阔度 | 指明街道 ≥ 4.5 m | Cap. 123F reg 18A(1) | 17.9.2026 | "class A site… abuts on one specified street not less than 4.5 m wide or on more than one such street" | S05、V01、V09 | 已对原文 |
| LIM-12 | 场地类别：临街比例 | 乙类 ≥ 40 % 地界临 2 街；丙类 ≥ 60 % 临 3 街 | Cap. 123F reg 18A(2) | 17.9.2026 | "a corner site shall not be regarded as abutting on 3 specified streets unless at least 60 per cent of the boundary of the site abuts on the streets" | S05 | 已对原文 |
| LIM-13 | 建筑物高度量法 | 由指明街道（≥ 4.5 m）平均水平量起 | Cap. 123F reg 23(1) | 17.9.2026 | "…the height of a building shall be measured from the mean level of the street or streets on which it fronts or abuts…" | S05、V03、V04、S04 | 已对原文 |
| LIM-14 | 地盘面积口径 | 不计街道及后巷；计入献作公众通道的面积 | Cap. 123F reg 23(2) | 17.9.2026 | "no account shall be taken of any part of any street or service lane" | S02、S05 | 已对原文 |
| LIM-15 | GFA 定义 | 外墙以内、逐层量度（含地面以下楼层）+ 露台 | Cap. 123F reg 23(3)(a) | 17.9.2026 | "…the gross floor area of a building shall be the area contained within the external walls of the building measured at each floor level…" | V10、S08、S05、S15 | 已对原文 |
| LIM-16 | 准许上盖面积、地积比率 | 按用途、场地类别、建筑高度查附表 1 各栏 | Cap. 123F reg 20(2)(3)、21(1)(3)、附表 1 | 17.9.2026 | "the site coverage for a non-domestic building… on a class A site shall not exceed that percentage of the area of the site specified in the eighth column of the First Schedule" | S05、V09 | 已对原文 |
| LIM-17 | 休憩用地适用范围 | 只适用于住用建筑物；数值见附表 2 | Cap. 123F reg 25(1)(a)、附表 2 | 17.9.2026 | "Every domestic building on a class A or B site or on a class C site shall have within the site an open space…" | V07、S06 | 已对原文 |
| LIM-18 | 电讯及广播设施适用范围 | 商业、工业、住宅（独立屋除外）、旅馆建筑物 | Cap. 123F reg 28A | 17.9.2026 | "Every commercial building, industrial building, residential building (other than a building for the residence of a single family) and hotel building shall be provided with access facilities…" | S16 | 已对原文 |
| LIM-19 | 垃圾房门槛 | 住用 UFS ≥ 1,320 m²；非住用（非工业）≥ 3,960 m²；工业 ≥ 3,960 m²（物料回收室）；综合用途合计 ≥ 1,320 m² | Cap. 123H reg 3、附表 | 9.2.2012 | "(a) Usable floor space 3 960 m2 or more but less than 39 600 m2"（附表「Non- domestic Building (except Industrial Building)」一行） | S15、V12 | 已对原文 |
| LIM-20 | 垃圾房面积 | 住用 UFS ÷ 347；非住用 UFS ÷ 925；工业 UFS ÷ 2,320（≥ 2.25 m²） | Cap. 123H 附表 | 9.2.2012 | "Total usable floor space in m2 divided by 925" | S15 | 已对原文 |
| LIM-21 | 洁具：office 人数与男女比 | 每 9 m² UFA 1 人；男女 1:1 | Cap. 123I reg 5(5)(a)(i)、5(5)(c)(ii)（office 属「any other workplace」，男女 1:1） | 23.4.2020 | "for an office—at the rate of 1 person for every 9 m2 of the usable floor area of the office" | S13 | 已对原文 |
| LIM-22 | 洁具：公众娱乐场所无座集会区 | 每 0.5 m² 1 人；男女 1:1.5 | Cap. 123I reg 6 | 23.4.2020 | "the proportion of male persons to female persons in a place of public entertainment is deemed to be 1:1.5" | S13 | 已对原文 |
| LIM-23 | GFA 豁免上限 | 受 cap 豁免 ≤ 发展项目总 GFA 的 10 %；住用 / 非住用分开计 | PNAP APP-151 ¶4 | Knowledge 摘录版 | "This cap is set at 10% of the total GFA of the development." | S08、V10、S07 | 已对原文 |
| LIM-24 | 豁免前置条件 | ¶6 (a)–(g)：APP-152 合规、APP-156（住用）、BEAM Plus 注册、目标评级写在 GBP 上 … | PNAP APP-151 ¶6 | Knowledge 摘录版 | "…compliance with the following requirements will be pre-requisites for the granting of GFA concessions…" | S07 | 已对原文 |
| LIM-25 | 前置条件生效日期 | 2024-06-30 或之后递交的新 GBP | PNAP APP-151 ¶10 | Knowledge 摘录版 | "…development proposals submitted to the BA for approval on or after 30 June 2024…" | S07 | 已对原文 |
| LIM-26 | EVA 主要立面 | ≥ 建筑周界墙总长 1/4 | PNAP APP-136 ¶6 | 2006-07 | "In the measurement of one-fourth of the length of the perimeter wall as the major façade…" | V06 | 已对原文 |
| LIM-27 | 电梯井豁免：轿厢 / 井道下限 | 办公：轿厢内部 ≥ 2.1 m²、井道 ≥ 4.4 m²；须 RLE / BSE 评估 | PNAP APP-89 ¶8 | 2025-06 | "…accommodation is not less than 2.1m2 and 4.4 m2 respectively" | S09、S17 | 已对原文 |
| LIM-28 | 楼宇间距适用门槛 | 地盘 ≥ 20,000 m²，或连续投影立面 Lp ≥ 60 m | PNAP APP-152 ¶3 | Knowledge 摘录版 | "sites that are less than 20,000m2 and proposed with building or group of buildings having a continuous projected façade length (Lp) of 60m or above" | V14、S07 | 已对原文 |
| LIM-29 | 绿化覆盖率 | 地盘 1,000–20,000 m²：主要区 10 %、整体 20 %；≥ 20,000 m²：15 % / 30 % | PNAP APP-152 Table 2 | Knowledge 摘录版 | "Minimum Site Coverage of Greenery… 1,000 m2 – 20,000 m2 10% 20%" | V14、S04 | 已对原文 |
| LIM-30 | 出口人数系数、出口数、宽度、DV | — | FS Code 2011 Part B（B8.1、B12 等） | — | — | S10、S11、V02 | [GAP] |
| LIM-31 | EVA 阔度、净高、承重、坡度、距立面距离 | — | FS Code 2011 Part D | — | — | V06 | [GAP] |
| LIM-32 | 防火分区面积 / 体积、FRR | — | FS Code 2011 Part C | — | — | V08、S12 | [GAP] |

## 注

- LIM-16：附表 1 在 Knowledge 中为整理者重建的表，引用具体数值前须对电子版法例（DK-AUD-006 M-11）。
- LIM-19、LIM-20：附表经 RTF 抽取后表格被压平，数值已核，版式须对原件。
- LIM-26：只覆盖「主要立面 1/4」主测试；FS Code Part D 的阔度、净高、承重、距离见 LIM-31。

## 用法

- L2 写 L2 判定时引 `LIM-nn`，不要直接抄数值，以免两处不一致。
- 状态为 `[GAP]` 的：L2 判定写「Unclear：须 <资料>」，并在 [DK-AUD-006](DK-AUD-006_Missing_Sources.md) 记录。
- 法例或 PNAP 更新时，只改本表和原文，L2 不必改，除非判定逻辑本身变了。
