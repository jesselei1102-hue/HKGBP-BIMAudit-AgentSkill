---
name: gbp-model-audit
description: Use when asked to audit a Revit model for a Hong Kong GBP (general building plans) Stage I submission — a full model audit, "can this model be submitted", a regression after fixes, or any BIMGBPS task TL-S01–S18, TL-V01–V14, TL-A01–A04 or model health MA-1–MA-7 when you are not sure which group skill applies. Read-only. 香港 GBP 入则模型审核总入口：整套审核、回归、或不确定该用哪一组时用。
---

# GBP Model Audit · 总入口

## 0. 找到包

本 Skill 属于 Model Audit 包。包根是同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹（常见：`Model Audit/`、`work/model-audit/`）。下文记为 `<PKG>`，路径都相对它。找不到就问操作者，不要猜。

## 1. 每次开始

1. 读 `<PKG>/RUN.md` §1–§5：确认打开的是副本、只读、当前 MCP 有 `L4-Capabilities/CAP-binding-*` 对照表、法例原文在不在。
2. 读 `<PKG>/L2-Task-Logic/AUD-000_Audit_Flow.md`：状态词、项目输入清单（INP-01–17）、§10 两段式规则。
3. 向操作者确认已有的项目输入。

## 1b. 有对话窗口时

当前会话有 `choose_checks` 工具（对话窗口 server，见 `<PKG>/app/README.md`）：先调它，让操作者在窗口里选检查，照窗口发来的指令执行；分析完调 `show_overview(run)` 等确认。完整步骤见 `<PKG>/RUN.md` §6d。没有这个工具就照下文。

## 2. 选组

| 操作者要的 | 用哪个 Skill |
| --- | --- |
| S14、V13（采光通风、规定窗） | `gbp-audit-g1-lighting-ventilation` |
| S13、S10、S11、S15、S16（洁具、出口门、排放值、垃圾房、电讯房） | `gbp-audit-g2-room-use` |
| S02、S05–S08、S12、V06–V12、V14（地盘面积、GFA、豁免、上盖、UFA、防火分区面积图） | `gbp-audit-g3-area-scheme` |
| V01–V05、V13 图面、A01–A03（平立剖、颜色、图框、导出） | `gbp-audit-g4-drawings` |
| S01、S03、S04、S09、S17、S18、A04、模型健康 MA-1–7 | `gbp-audit-g5-lists-health` |

## 2b. 只跑一个（或几个）Task

1. 用上表找到组，调用那组的 Skill，加 `--tasks <Task>`（例：`--tasks S10`）。
2. 只做该组规格「按 Task 单独跑」表列的提取步；缺的输入脚本会出 `<Task>-INPUT`（UNCLEAR）并写明怎么补，不会拿空数据判。
3. 已有整次审核：汇总时加 `--update <单独跑的 JSON>`（`--group` 里放该组完整 JSON），只替换这个 Task，其他不变；再出两份总报告。见 `<PKG>/RUN.md` §6c。

## 3. 整套审核

1. 依次跑 G1 → G2 → G3 → G4 → G5；后组要读前组的分析 JSON。每组都按该组 Skill 的两段式：先分析、给操作者看屏幕摘要、确认后再出报告。
2. 汇总（`<run>` 为本次审核文件夹）：

   ```
   python "<PKG>/tools/common/build_results.py" --out <run>/audit-results.json --project <名> --model <路径> --date <YYYY-MM-DD> \
     --s14 <G1 运行文件夹>/audit-results.json [--decisions <AP 决定事项 JSON>] --group <G2 JSON> <G2 目录> --group <G3 JSON> <G3 目录> --group <G4 JSON> <G4 目录> --group <G5 JSON> <G5 目录>
   python "<PKG>/report/render_report.py" --results <run>/audit-results.json --audience bim --out <run>/report-bim.html
   python "<PKG>/report/render_report.py" --results <run>/audit-results.json --audience ap  --out <run>/report-ap.html
   ```

   exit 2 = JSON 不合格，按 `INVALID` 行改；exit 3 = 缺截图。
3. 回复操作者：能否原样提交、Blocker 清单、要 AP 决定的事、要提供的资料、两份报告路径。

## 4. 回归

按 `<PKG>/L2-Task-Logic/AUD-REG_Regression.md`，对照上次的 `audit-results.json`，每条标 closed / partly closed / open / new。

## 5. 不可违反

- 只读：不删、不改、不建模型元素或视图。
- 不编数值、不编出处；读不到就是 UNCLEAR，引 `L4-Capabilities/CAP-gaps.md` 的 GAP 编号。
- 限值只引 `L1-Domain/DK-AUD-002_Limits_Index.md`，以法例原文为准；转述与原文冲突时用原文（`DK-AUD-005_Errata.md`）。
- AP 未决定的口径两个都算，并列写，不替 AP 选。
- 结论标 [FACT] / [INFERENCE] / [GAP]。

范例：`work/model-audit-runs/audit-2026-10-13-full/`（36 个 Task + A1）。
