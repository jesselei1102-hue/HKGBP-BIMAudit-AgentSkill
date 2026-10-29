---
name: gbp-audit-g5-lists-health
description: Use when checking list-type schedules, model health or the final submission roll-up of a Revit model for a Hong Kong GBP submission — drawing list, site coordinates (HK1980), development schedule, lift shaft concessions, list of modifications, model health MA-1 to MA-7, and the TL-A04 "can it be submitted" roll-up (BIMGBPS TL-S01, S03, S04, S09, S17, S18, A04). Runs last; reads the other groups' analysis JSON. Read-only, two stages. 香港 GBP 清单组、模型健康与提交汇总审核。
---

# G5 / G6 · 清单组与模型健康（S01、S03、S04、S09、S17、S18、A04；A1）

包根 `<PKG>` = 同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹。未读过就先读 `<PKG>/RUN.md` §1–§5。

## 前提

G1–G4 已跑完，手上有四份分析 JSON 和 G3 / G4 的 `_raw/`。缺哪组就先跑那组（见 `gbp-model-audit`），不要跳过。

## 规格

`<PKG>/L2-Task-Logic/Groups/G5_Lists_G6_Model_Health.md` 与 `<PKG>/L2-Task-Logic/AUD-A1_Model_Health.md`。要点：

- 坐标：每点 = 地界角点按项目基点换算，到 0.001 m；E/W、N/S 显示值是毫米。
- 发展表逐栏对来源（G3、停车明细表）；高度不同口径时用楼层标高解释差额，标 [INFERENCE]。
- 标高名里的数字与实际标高差 > 0.5 mm → Fail。
- A04 只汇总其他检查，不另量。

**读图判断**：PASS 要有那一处的裁切图，FAIL 要在 `sheet` 写明看过的图纸，否则 UNCLEAR。报告把每条读数列在「To check by eye › Sheet readings」，标明未经人工核对，附裁切图；不等操作者确认，直接出报告。

**只跑某个 Task**：分析命令加 `--tasks <Task>`，只做规格「按 Task 单独跑」表列的提取；并回总结果用 `build_results.py --update`（`<PKG>/RUN.md` §6c）。

## 第一段：提取 → 分析 → 停

1. 按当前 MCP 的 L3 SOP（见 L4 对照表；基准 `<PKG>/L3-SOP/SOP-AUD-mcp-revit-mcp.md`，其他 MCP 的 SOP 只写不同的步骤）§10「R-G5」提取到 `<g5>/_raw/`：MCP 回传原样存进 `_raw/mcp/`，再跑 `python "<PKG>/tools/extract/g5_extract.py" --mcp <g5>/_raw/mcp --out <g5>/_raw`（不要自己写转换脚本）；图纸目录在 A001 上读。
2. 跑：

   ```
   python "<PKG>/tools/lists_health/analyze.py" --raw <g5>/_raw --project <名> --model <路径> --out <g5>/G5_analysis_<名>.json \
     --g2 <G2 JSON> --g3 <G3 JSON> --g4 <G4 JSON> --s14 <G1 JSON> --g3raw <g3>/_raw --g4raw <g4>/_raw --schedules <g5>/_raw/all_schedules.tsv
   ```

3. 给操作者看屏幕摘要。**在这里停下**，等确认。

## 第二段：报告

```
python "<PKG>/tools/common/task_report.py" --analysis <g5>/G5_analysis_<名>.json --outdir <g5> --name ListsHealth
```

之后要出总报告的，回到 `gbp-model-audit` §3 汇总。

## 不可违反

只读；不编数值；UNCLEAR 不算 PASS；结论标 [FACT] / [INFERENCE] / [GAP]。
