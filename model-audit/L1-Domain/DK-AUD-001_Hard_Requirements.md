# DK-AUD-001 · 提交硬性要求（G1–G12）

Layer 1。每个 Task 都适用的硬性规则，与软件无关。审核时由 [AUD-A1](../L2-Task-Logic/AUD-A1_Model_Health.md) 和各 AUD 的通用检查（[AUD-000](../L2-Task-Logic/AUD-000_Audit_Flow.md) `GEN-nn`）引用。

出处路径以并回仓库后的位置为准。BIMGBPS 原文在 [corpus](../../source/HK%20GBP/corpus/)。

| # | 要求 | 出处 | 状态 | 对应 MA |
| --- | --- | --- | --- | --- |
| G1 | 绘图单位 mm；面积 m²、体积 m³ 取三位小数 | BIMGBPS §5.1.1（2019）：「rounded off to three decimal places」 | 已对原文 | MA-2.1、MA-2.2 |
| G2 | 地盘面积：< 2,000 m² 取到 0.1 m²；≥ 2,000 m² 取到 1 m²（四舍五入） | BIMGBPS §5.1.1；PNAP ADM-21 | 已对原文 | MA-6.2 |
| G3 | 尺寸、面积由软件自动生成，禁止手动输入 | BIMGBPS §5.1.2 | 已对原文 | MA-3.1 |
| G4 | 坐标 HK1980 Grid、标高 HKPD，米三位小数；负值写 `– X.XXX mPD` | BIMGBPS §5.1.3：「(8XX,XXX.XXX mN, 8XX,XXX.XXX mE) and (X.XXX mPD)」 | 已对原文 | MA-2.3、MA-2.4 |
| G5 | 着色：平面材料、新旧工程按 PNAP ADM-9；GFA 图按 BIMGBPS Table 1 | BIMGBPS §5.1.4、§5.2.10、Table 1 | 已对原文 | — |
| G6 | 面积图须叠对应的半色调底层平面 | BIMGBPS §4.2(d)：「Area diagrams should be shown with the corresponding halftone under laying floor plans」 | 已对原文 | — |
| G7 | 面积可在软件中点选预设 zone 复核，也可指定点量测复核 | BIMGBPS §4.2(e)(f) | 已对原文 | MA-4.3 |
| G8 | 删除与法定提交无关的数据（照明、天花、机电等） | BIMGBPS §4.2(g) | 已对原文 | MA-3.4 |
| G9 | 单个 BIM 文件 ≤ 500 MB；`.rvt`；Revit 2017 或以上；自包含，不依赖插件 | BIMGBPS §4.3(b)(c)(e)(g)：「Revit version 2017 or later」 | 已对原文 | MA-1.1 至 MA-1.6 |
| G10 | 一般采用 LOD 300 | BIMGBPS §4.4 | 已对原文 | MA-3.3 |
| G11 | Agent 判定：Unclear 不算 Pass，Missing 不算 Present；每条结论引条文；声明非 BA 批核 | Capability Catalog §4、§6；Roadmap §03 | 已对原文（仓库文件） | 全部 |
| G12 | 写入前先说明要改什么；不覆盖中心文件 | Four-Layer Architecture「Execution Safety」；Roadmap §03 | 已对原文（仓库文件） | 全部（审核只读，本包不写入） |

## 说明

- G9 的版本门槛：Architecture 与 Research 写「≥ 2023」，与 BIMGBPS 原文不符，见 [DK-AUD-005](DK-AUD-005_Errata.md) §3。BD 现行要求是否已更新 `[GAP]`，见 [DK-AUD-006](DK-AUD-006_Missing_Sources.md)。
- BIMGBPS 为 2019 版。是否有新版、ESH 是否改变提交介质（§4.3(a) DVD-ROM） `[GAP]`。
- G11、G12 不是法规，是审核方法规则；放在这里，是因为每个 Task 都适用。
