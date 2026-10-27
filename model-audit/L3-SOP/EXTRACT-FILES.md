# EXTRACT-FILES · 提取文件（L3 与分析脚本之间的约定）

分析脚本（`tools/*/analyze.py`）只读本页列出的文件，不读 MCP 回传、不连模型。不管用哪个 MCP，只要写出同样的文件，分析、报告、对话窗口都不用改。接入新 MCP 时，转换脚本（`tools/extract/g*_extract.py`）的输出要与本页一致（[CAP-onboarding](../L4-Capabilities/CAP-onboarding.md) 第 3 步）。

## 通用约定

- 位置：每次审核的 `<run>/_raw/`；MCP 原样回传在 `<run>/_raw/mcp/`。
- `.tsv`：UTF-8、制表符分隔、首行表头；空值留空。一次回传太多时可分片（`cw_part1.tsv`、`cw_part2.tsv`…），脚本合并。
- 单位：坐标、包围盒、长度用 **英尺**（Revit 内部单位，模型坐标）；面积用显示值 **m²、三位小数**（`*_m2`）；标高、宽度、坐标偏移带单位后缀（`*_mm`、`*_m`、`*_ft`）。
- `id` 是 Revit 元素 id（整数）。
- 只放 MCP 回传的值或从图上读到的值，不放推算值（[AUD-000 §10](../L2-Task-Logic/AUD-000_Audit_Flow.md)）。

## 由转换脚本写出（来自 MCP）

| 文件 | 列 | 写出者 | 读的人 | 能力 |
| --- | --- | --- | --- | --- |
| `rooms.tsv` | id, name, number, level, area_m2, minx, miny, minz, maxx, maxy, maxz | g1 / g2_extract | S14、G2 | `CAP-EXTRACT-ROOMS` |
| `room_polygons.json` | `{房间 id: [环, …]}`；每环为 `[x, y]` 点列（英尺），第一环外轮廓，其余为洞；只有取到边界的房间才有，其余按包围盒 | g1 / g2_extract | S14、G2 | `CAP-EXTRACT-ROOMS` |
| `fixtures.tsv` | id, family, type, level, cx, cy, z | g2_extract | G2（S13） | `CAP-QUERY-ELEMENTS` |
| `doors_all.tsv` | id, family, type, level, width_moe_mm, minx, miny, minz, maxx, maxy, maxz | g2_extract | G2（S10） | `CAP-EXTRACT-OPENINGS`、`CAP-MEASURE-WIDTH` |
| `cw_part*.tsv` | id, type, level, area_m2, mark, minx … maxz | g1_extract | S14 | `CAP-EXTRACT-OPENINGS` |
| `pn_part*.tsv` | id, kind（H 可开启 / L 百叶）, type, area_m2, cx, cy, cz | g1_extract | S14 | `CAP-EXTRACT-OPENINGS` |
| `pn_bbox_sample.tsv` | id, minz, maxz | g1_extract | S14（开口顶高） | `CAP-EXTRACT-OPENINGS` |
| `fs_windows.tsv`、`doors.tsv` | id, family, type, level, mark, area_m2, minx … maxz | g1_extract | S14 | `CAP-EXTRACT-OPENINGS` |
| `doors_other.tsv` | family, count, note | g1_extract | S14（列出未计入的门族） | `CAP-EXTRACT-OPENINGS` |
| `areas.tsv` | id, scheme, level, name, area_m2, number, common_area, gfa_summary, d22, d23, d21, d25, d27, served_facade_mm, frr, compartment, frc_height, perimeter_mm, area_type, minx, miny, maxx, maxy | g3_extract | G3、G5 | `CAP-EXTRACT-AREAS`、`CAP-EXTRACT-SITE` |
| `area_schemes.tsv` | id, name, areas（该方案的 Area 数） | g3_extract | G3 | `CAP-EXTRACT-AREAS` |
| `rasters.tsv` | id, name, width_mm, height_mm | g3_extract | G3、G4、G5（GEN-01 图片表） | `CAP-QUERY-ELEMENTS` |
| `views_on_sheets.tsv` | sheet_id, sheet, view_id, view_name, view_type（FloorPlan、AreaPlan、Section、Elevation、Legend、Schedule…）, outline_miny, outline_maxy（图纸英尺；MCP 不给时留空） | g4_extract | G4、G5 | `CAP-LIST-VIEWS-SHEETS` |
| `view_props.tsv` | view_id, name, view_type_name, sheet, scale（1:n 写 n；自定义写 custom）, template, title_on_sheet | g4_extract | G4 | `CAP-LIST-VIEWS-SHEETS` |
| `view_counts.json` | `{视图 id: {OST_类别: 数量}}`；`_` 开头的键是说明 | g4_extract | G4 | `CAP-QUERY-ELEMENTS` |
| `model_counts.json` | `{"OST_RvtLinks": n}` | g4_extract | G4、G5（MA-1.5、A03） | `CAP-QUERY-ELEMENTS` |
| `mcp/titleblocks.json` | 图框与项目信息的 `get_element_data` 原样回传（两种 MCP 格式都读） | （不转换） | G4（A01；G5 的 S01 读 G4 JSON 里的图框表） | `CAP-LIST-VIEWS-SHEETS` |
| `levels.tsv` | id, name, type, elevation_mm, building_story（1 / 0） | g5_extract | G5 | `CAP-PROJECT-CONTEXT` |
| `points.tsv` | id, kind（Survey Point、Project Base Point、Property Line bbox min / max）, x_ft, y_ft, z_ft, ew_mm, ns_mm, elev_mm, angle_true_north（度） | g5_extract | G5 | `CAP-EXTRACT-COORDINATES`、`CAP-EXTRACT-SITE` |
| `all_schedules.tsv` | id, name（图框修订表不列） | g5_extract | G5（S01） | `CAP-LIST-VIEWS-SHEETS` |
| 明细表 CSV | 模型导出的原文件（逗号或制表符分隔） | MCP 导出 | S14、G2、G5（停车） | `CAP-EXPORT-TABLE` |

## 由其他工具写出

| 文件 | 内容 | 写出者 | 能力 |
| --- | --- | --- | --- |
| `sheets/*.png` | 图纸导出图（约 1920 px 宽起） | MCP 导出 | `CAP-EXPORT-IMAGE` |
| `colour_samples.json` | 每张图的颜色统计；有 `regions.json` 时按区域统计 | `tools/drawings/sample_colours.py` | `AGENT-IMAGE-SAMPLE` |
| `regions.json` | 取色区域框（图纸 PNG 像素） | 人或 agent | — |
| `rvt_info.json` | 文件名、大小、格式（Revit 版本）、build、协作状态 | `tools/drawings/rvt_info.py`（读 .rvt 文件头） | `AGENT-FILE-INFO` |
| `crops/<key>.png` | 读数格子的裁切图 | `tools/common/crop_readings.py` | `AGENT-IMAGE-SAMPLE` |

## 读图写出（人或 agent 看图）

规则见 [SOP-AUD-mcp-revit-mcp §10 读数规则](SOP-AUD-mcp-revit-mcp.md#r-g3)：只写图上看到的值，不拿模型值补；判断类加 `finding`；PASS 要裁切图，FAIL 要写看过的图纸。

| 文件 | 列 | 读的人 |
| --- | --- | --- |
| `table_values.tsv` | key, sheet, item, value, unit, confidence（high / medium）, note, finding, box（x0,y0,x1,y1 像素）, crop | G3、G5 |
| `readings.tsv` | key, sheet, item, value, confidence, note, finding, box, crop | G4、G5 |
| `coords.tsv` | point, E_m, N_m, source | G4（V01）、G5（S03） |
| `drawing_list.tsv` | number, rev, title（A001 图纸目录） | G5（S01） |
