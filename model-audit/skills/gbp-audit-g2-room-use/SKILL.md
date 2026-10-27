---
name: gbp-audit-g2-room-use
description: Use when checking room-use schedules in a Revit model for a Hong Kong GBP submission — BIMGBPS TL-S13 sanitary fitments (Cap. 123I), TL-S10 exit doors and routes, TL-S11 discharge value, TL-S15 refuse storage (Cap. 123H), TL-S16 telecom room (reg 28A). Matches fixtures and doors to rooms by geometry. Read-only, two stages. 香港 GBP 洁具、出口门、排放值、垃圾房、电讯房（S13、S10、S11、S15、S16）审核。
---

# G2 · 房间-用途组（S13、S10、S11、S15、S16）

包根 `<PKG>` = 同时含 `RUN.md` 和 `L2-Task-Logic/` 的文件夹。未读过就先读 `<PKG>/RUN.md` §1–§5。

## 规格

`<PKG>/L2-Task-Logic/Groups/G2_Room_Use.md`。要点：

- 洁具按中心点归房间；门按「放大 0.5 ft + 7×7 网格 + 30 % 命中」归房间（§2）。
- S13 两个口径并列：基准 A（office，reg 5）不足 → FAIL；基准 B（reg 6 娱乐场所，敏感度）不足 → UNCLEAR，由 AP 定类别（INP-12）。
- S10 / S11 限值来自 FS Code（原文缺）→ 限值本身 UNCLEAR；但表值与模型不一致（面积、人数、门数、`width_MOE` 净宽）照判。
- S15 用 UFS 上 / 下限判 N/A / 适用 / UNCLEAR；S16 按用途判 N/A（附条件）。

**只跑某个 Task**：分析命令加 `--tasks <Task>`，只做规格「按 Task 单独跑」表列的提取；并回总结果用 `build_results.py --update`（`<PKG>/RUN.md` §6c）。

## 第一段：提取 → 分析 → 停

1. 按当前 MCP 的 L3 SOP（见 L4 对照表；基准 `<PKG>/L3-SOP/SOP-AUD-mcp-revit-mcp.md`，其他 MCP 的 SOP 只写不同的步骤）§10「R-G2」提取到 `<run>/_raw/`（房间可复用 G1 的 `rooms.tsv`、`room_polygons.json`）。MCP 回传原样存进 `_raw/mcp/`（文件名见 R-G2），再跑 `python "<PKG>/tools/extract/g2_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw` 转成提取文件——不要自己写转换脚本；它会核对 `query_model` 的 id 一个不少。明细表用 `export_views` 让模型直接写 CSV。
2. 跑：

   ```
   python "<PKG>/tools/room_use/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/G2_analysis_<名>.json [--use <用途>]
   ```

3. 给操作者看屏幕摘要（§5）。**在这里停下**，等确认。

## 第二段：报告

```
python "<PKG>/tools/common/task_report.py" --analysis <run>/G2_analysis_<名>.json --outdir <run>
```

回复：每个 Task 的状态、要 AP 决定的口径、文件路径。

## 接口

- `_raw/fixtures.tsv` → G1 `--fixtures`：含 WC / 小便器的房间按 reg 36 判。
- 本组 JSON → G3 `--g2`、G5 `--g2`。

## 不可违反

只读；不编数值；UNCLEAR 不算 PASS；两个口径都算，不替 AP 选；结论标 [FACT] / [INFERENCE] / [GAP]。
