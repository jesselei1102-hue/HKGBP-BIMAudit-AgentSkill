# SOP-AUD-mcp-mcp-servers-for-revit · 用 mcp-servers-for-revit 取得审核信息

Layer 3（MCP 专属）。MCP：开源 mcp-servers-for-revit（工具前缀因 harness 而异，例 `mcp-server-for-revit`）。能力对照见 L4 [CAP-binding-mcp-servers-for-revit](../L4-Capabilities/CAP-binding-mcp-servers-for-revit.md)。

本文件只写与 [SOP-AUD-mcp-revit-mcp](SOP-AUD-mcp-revit-mcp.md) 不同的地方；配方编号（R-S14、R-G2 … R-G5）、存档规则、转换脚本都相同。回传格式由 `tools/extract/` 按形状认出，不用说明是哪个 MCP。

**标记**：`实测`（日期，BD 样例模型）/ `待试`。

## 0. 通用规则

- 只用读取类工具和导出。写入工具与 `send_code_to_revit` **不属于审核**（RUN.md 安全规则）。
- 不需要进程 ID；`get_running_revit_instances` 标出当前连着的实例（`connected=true`）。`实测 2026-10-27`
- `query_model` 的 `maxResults: 0` = 全部 id（revit-mcp 设 0 一个都不回）。`实测`
- `get_element_data` 一次可取整类；`parametersOutputType: "SpecificParameters"` + `specificParameterNames` 只取所需参数。回传为 `{"elements": [{id, name, category, family, type, parameters{名: 显示值}}]}`。`实测`
- `query_model` 的 `analysis.byCategory` 用类别显示名（例 `Grids`、`Views`、`Elevations`）；`g4_extract.py` 按对照表换成 `OST_` 名，表外的名称列为警告。`实测 2026-10-27`
- 明细表 CSV 用制表符分隔；各脚本已兼容。`实测 2026-10-14`

## 1. 与 revit-mcp 配方不同的步骤

| 配方 | revit-mcp | 本 MCP（存成 `_raw/mcp/`） | 标记 |
| --- | --- | --- | --- |
| R-S14、R-G2 房间 | `get_rooms` + `get_room_boundaries` | `query_model`（OST_Rooms）→ `get_element_data`（boundingBox + Name、Number、Area、Level），存 `rooms*`；**不存** `room_boundaries`（没有该工具，房间轮廓用包围盒，GAP-08） | 实测 2026-10-14 |
| R-G4 第 1 步 图纸与图上视图 | `get_sheets` → `get_views_on_sheets` | ① `query_model`（OST_Sheets）→ `get_element_data`（Sheet Number），存 `sheets.json`；② 每张要审的图纸一次 `query_model`（`categories: ["OST_Viewports"]`、`searchScope: "SpecificView"`、`viewId` = 图纸 id、`maxResults: 0`），存 `sheet_viewports_<图纸 id>.json`；③ 这些视口 `get_element_data`（SpecificParameters：View、View Name），存 `viewports.json`。脚本按视图族、类型、名称把视口对到视图，图例放在几张图上就列几次 | 实测 2026-10-27 |
| R-G4 第 3 步 视图属性 | `get_element_data`（图上视图） | `query_model`（OST_Views）存 `query_view_props.json`；**全部**视图 `get_element_data`（SpecificParameters：Sheet Number、View Scale、View Template、Title on Sheet），存 `view_props.json`；脚本只留图上视图（图例、明细表除外） | 实测 2026-10-27 |
| R-G4 第 2 步 每视图计数 | 同左 | 同 revit-mcp：`query_model`（`searchScope: "SpecificView"`、`maxResults: 1`），存 `view_counts_<视图 id>.json` | 实测 2026-10-27 |
| R-G4 视口位置 | `get_views_on_sheets` 带 outline | 拿不到（GAP-09）；`views_on_sheets.tsv` 的 outline 两列留空，分析脚本未用 | 实测 2026-10-27 |
| R-G5 第 3 步 明细表清单 | `get_all_schedules` | `query_model`（OST_Schedules、`maxResults: 0`）→ `get_element_data`（basic），存 `schedules.json`；`g5_extract.py` 去掉图框修订表 | 查询实测 2026-10-27；整组待试 |
| 导出图纸 / 明细表 | `export_views` | `export_views`（PNG / CSV / PDF，`viewIds`） | CSV 实测 2026-10-14；PNG、PDF 待试 |

其余步骤（标高、基点、面积、门、洁具、窗、嵌板）都是 `query_model` + `get_element_data`，存法同 revit-mcp 配方。
