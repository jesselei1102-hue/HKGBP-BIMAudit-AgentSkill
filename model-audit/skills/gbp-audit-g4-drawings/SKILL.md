---
name: gbp-audit-g4-drawings
description: Use when checking the drawings themselves in a Revit model for a Hong Kong GBP submission — block/key plan, floor plans, sections, elevations, details, prescribed-window diagram, colour coding against Table 1, title blocks and export (BIMGBPS TL-V01–V05, V13, A01–A03, and the drawing items of V08/V10/V11). Counts annotations per view, samples colours from sheet exports, reads the Revit version from the .rvt header. Read-only, two stages. 香港 GBP 图面组（平立剖、颜色、图框、导出）审核。
---

# G4 · 图面组（V01–V05、V13、A01–A03）

包根 `<PKG>` = 同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹。未读过就先读 `<PKG>/RUN.md` §1–§5。

## 规格

`<PKG>/L2-Task-Logic/Groups/G4_Drawings.md`。要点：

- 能计数的用计数（每个图上视图的轴网、尺寸、标记数）；不能计数的读图，写 `readings.tsv`，**只对读过的图纸下结论**，没读的 → UNCLEAR。
- 颜色只按像素取样判，不目测：Table 1 RGB 完全相等才 Pass；粉红占区域 < 20 % → Fail；灰阶 > 5 % 才算有半色调。
- V13 要专门的规定窗图；S14 明细表不算图。
- 不画区域框也能取色（整图统计判粉红有无、Table 1）；半色调要区域框。链接数写 `model_counts.json`，没有就 UNCLEAR。
- 判断类读数（`streets`、`coords_format`、`coords_bearings`、`modification_list`、`na_table`）填 `finding`。
- 文件版本读 .rvt 文件头（只读文件，不打开模型）。

**读图判断**：PASS 要有那一处的裁切图，FAIL 要在 `sheet` 写明看过的图纸，否则 UNCLEAR。确认关口请操作者对照报告「Sheet readings to check」的裁切图逐条核对。

**只跑某个 Task**：分析命令加 `--tasks <Task>`，只做规格「按 Task 单独跑」表列的提取；并回总结果用 `build_results.py --update`（`<PKG>/RUN.md` §6c）。

## 第一段：提取 → 分析 → 停

1. 按 `<PKG>/L3-SOP/SOP-AUD-mcp-revit-mcp.md` §10「R-G4」提取到 `<run>/_raw/`：MCP 回传原样存进 `_raw/mcp/`（每个视图的计数存成 `view_counts_<视图 id>.json`），再跑 `python "<PKG>/tools/extract/g4_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw`（不要自己写转换脚本）；其中：

   ```
   python "<PKG>/tools/drawings/sample_colours.py" --sheets <run>/_raw/sheets --out <run>/_raw/colour_samples.json [--regions <run>/_raw/regions.json]
   python "<PKG>/tools/drawings/rvt_info.py" <模型.rvt> --out <run>/_raw/rvt_info.json
   ```

   取色要 Pillow；没有时按 `L3-SOP/SOP-AUD-manual.md` 人工取色，并在报告注明。
2. 跑：

   ```
   python "<PKG>/tools/drawings/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/G4_analysis_<名>.json [--s14 <G1 JSON>] [--g3 <G3 JSON>]
   ```

3. 给操作者看屏幕摘要。**在这里停下**，等确认。

## 第二段：报告

```
python "<PKG>/tools/common/task_report.py" --analysis <run>/G4_analysis_<名>.json --outdir <run>
```

## 接口

- V13 C1 / C2 ← G1 JSON。
- 本组 JSON 与 `_raw/coords.tsv`、`readings.tsv`、`rvt_info.json` → G5。

## 不可违反

只读；不编数值；UNCLEAR 不算 PASS；结论标 [FACT] / [INFERENCE] / [GAP]。
