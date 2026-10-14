# DK-AUD-005 · 勘误（仓库现有文件中的错误或不一致）

Layer 1。下列文件是本包的上游或参考。审核时**以原文为准**：凡与本表冲突的，以本表右栏为准，并在报告里指出。

行号按 2026-10-13 的仓库副本。改动请在仓库里做，本包不改它们。

## 1. 采光比率写成 1/8

**正确值**：

- Cap. 123F reg 30(2)(a)(i)：窗玻璃 ≥ 楼面面积 **1/10**；(ii) 可开启 ≥ 1/16（LIM-06、LIM-07）。
- reg 36(2)：便溺房间玻璃与可开启都 ≥ 1/10（LIM-10）。

| 文件 | 行 |
| --- | --- |
| [TL-S14_Window_Area_Calc.md](../../GBP%20Tasks/Schedules/TL-S14_Window_Area_Calc.md) | 13、57 |
| [TL-S14-LV-Compliance-Prompt.md](../../training/TL-S14-LV-Compliance-Prompt.md) | 26、59 |
| [HK GBP Four-Layer Architecture.md](../../HK%20GBP%20Four-Layer%20Architecture.md) | 54（DK-REG-004）、195 |
| [Domain Knowledge - BD BIM GBP Specification.md](../../Domain%20Knowledge%20-%20BD%20BIM%20GBP%20Specification.md) | 278 |
| [HK GBP MCP Skills Research.md](../../HK%20GBP%20MCP%20Skills%20Research.md) | 132、355 |
| [HK GBP MCP Capability Catalog.md](../../HK%20GBP%20MCP%20Capability%20Catalog.md) | 53、288、396 |
| [GBP Tasks × Capabilities Matrix.md](../../GBP%20Tasks%20×%20Capabilities%20Matrix.md) | 7 |
| HK GBP Submission Roadmap（HTML，S14 卡片「审核 A」） | 655 |

**影响**：按 1/8 算出的 L&V 结论都偏严，要按 1/10 重算。

## 2. GFA 豁免上限写成 8 %

**正确值**：PNAP APP-151 第 4 段，受 cap 豁免 ≤ 发展项目总 GFA 的 **10 %**，住用与非住用分开计（LIM-23）。BIMGBPS Table 1 也写 10 %。

| 文件 | 行 |
| --- | --- |
| [HK GBP Four-Layer Architecture.md](../../HK%20GBP%20Four-Layer%20Architecture.md) | 62、135、141（及 DK-REG-003 示例） |
| [Domain Knowledge - BD BIM GBP Specification.md](../../Domain%20Knowledge%20-%20BD%20BIM%20GBP%20Specification.md) | 246 |
| [HK GBP MCP Skills Research.md](../../HK%20GBP%20MCP%20Skills%20Research.md) | 127 |
| [MVP_v0.1_GFA_Workflow.md](../../Revit%20SOP/MVP_v0.1_GFA_Workflow.md) | 405、474 |
| [MVP_v0.1_GFA_Tools.md](../../MCP%20Tools/MVP_v0.1_GFA_Tools.md) | 573、574 |
| `mvp_gfa/calculator.py` | Roadmap P1 所指（不在本工作区副本内） |

## 3. 其他

| # | 问题 | 正确做法 | 出处 |
| --- | --- | --- | --- |
| 3.1 | Architecture DK-STD-002、Research §1.6 的 SC 简表按区域给单值（Urban B 66.6 % 等） | 准许 SC / PR 取决于用途、场地类别和建筑高度，只查 Cap. 123F 附表 1（LIM-16） | Roadmap P6 |
| 3.2 | Architecture、Research 写 Revit ≥ 2023 | BIMGBPS §4.3(c) 写 2017 或以上（LIM-05）；BD 现行要求待确认 `[GAP]` | Roadmap P3 |
| 3.3 | `net_gfa = raw − mandatory − concession + bonus`，raw 只累加 accountable 面积 | 同一 Area Scheme 里豁免区不在 accountable 合计内，不能再减一次 | Roadmap P2 `[INFERENCE]` |
| 3.4 | MVP 的 `GFA_Category` 不分住用 / 非住用、不分 3a / 3b / 4a / 4b | 对应不到 Table 1 六色，也算不了分开的 10 % 上限（DK-AUD-004 §1） | Roadmap P4 |
| 3.5 | Architecture 开头写「正式架构（Active）· 8 Skills / 18 Tools / 2 MCP Servers」 | Catalog §9 已声明此为历史对照；以 Capability Catalog（CAP-*）为准 | Roadmap P7 |

## 4. 严重度分级不一致

[shared-issue.schema.json](../../MCP%20Tools/schemas/shared-issue.schema.json) 的 `severity` 是 `blocker / warning / info`。Roadmap §05 与本包 [finding.schema.json](../templates/finding.schema.json) 用 `Blocker / Major / Minor`，并把「判不了」放在 `status = Unclear`，不作为严重度。

本包不改旧 schema（它属于 MVP GFA 工具）。两者对应：

| shared-issue | 本包 |
| --- | --- |
| blocker | Blocker |
| warning | Major 或 Minor，按影响人工判断：影响提交可否 → Major，只影响图面整洁 → Minor |
| info | 不作为发现 |
