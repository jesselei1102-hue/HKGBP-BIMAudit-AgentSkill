---
name: gbp-audit-g1-lighting-ventilation
description: Use when checking natural lighting and ventilation of rooms in a Revit model for a Hong Kong GBP submission — BIMGBPS TL-S14 window area calculation or TL-V13 prescribed windows, Cap. 123F regs 30 and 36, glazing vs floor area, openable area. Read-only, two stages (analysis JSON, then Excel + HTML). 香港 GBP 采光通风 / 窗面积计算（S14、V13）审核。
---

# G1 · 采光与通风（S14，V13 共用）

包根 `<PKG>` = 同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹。未读过就先读 `<PKG>/RUN.md` §1–§5。

## 规格

`<PKG>/L2-Task-Logic/Schedules/AUD-S14_Window_Area_Calc.md` §9（可执行规格）。要点：

- 房间分为 included / excluded / pending / no_area；每类有理由。
- 开口按几何归到房间，每条记 match_method 与 confidence；归不进的不硬归，列出来。
- 限值（§9.4，按法例原文）：reg 30 采光玻璃 ≥ 1/10 地面面积、可开启 ≥ 1/16；厕所按 reg 36，玻璃 ≥ 1/10、可开启 ≥ 1/10，**不排除**。可开启只计顶高 ≥ 2 m 的开口。
- 两房之间的内部玻璃不算窗（reg 30(2)(b)）；百叶不计，另列；在地界外的玻璃单列。

## 第一段：提取 → 分析 → 停

1. 按 `<PKG>/L3-SOP/SOP-AUD-mcp-revit-mcp.md` §10「R-S14」提取，存进 `<run>/_raw/`。要用 `--fixtures`（推荐：含 WC 的房间按 reg 36 判，不靠房名）就先做 R-G2 第 2 步取洁具。MCP 回传原样存进 `_raw/mcp/`（文件名见 R-S14），再跑 `python "<PKG>/tools/extract/g1_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw`——它按族名判嵌板 H / L、核对数量；不要自己写转换脚本。
2. 跑：

   ```
   python "<PKG>/tools/s14_lv/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/C14_analysis_<名>.json \
     [--schedule <S14 明细表 CSV>] [--fixtures <G2 的 fixtures.tsv>] [--previous <上次 JSON>]
   ```

3. 把屏幕摘要给操作者看（房间分类数、通过 / 不通过、pending、数据质量警告）。**在这里停下**，等操作者确认或修正规则后再往下。

## 第二段：报告（只读分析 JSON）

```
python "<PKG>/tools/s14_lv/report.py" --analysis <run>/C14_analysis_<名>.json --outdir <run>
```

产出 Excel（§9.7 六张表，有 `--schedule` 时加 Schedule vs Model）和自包含 HTML。回复操作者：不通过的房间与修改方向、明细表与实测的差异、两个文件路径。

## 不可违反

只读；不编数值；UNCLEAR 不算 PASS；结论标 [FACT] / [INFERENCE] / [GAP]。任务页或旧 Prompt 写 1/8 的，以原文 1/10 为准，并在报告里指出。
