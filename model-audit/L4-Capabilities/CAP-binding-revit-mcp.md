# CAP-binding-revit-mcp · 能力对照（功能 A）

Layer 4。把 [Capability Catalog](../../HK%20GBP%20MCP%20Capability%20Catalog.md) 的能力 ID 对应到 Autodesk revit-mcp（Experimental Technical Preview）的工具。只列功能 A（审核）用到的能力；写入类能力不在本表。

- 状态：**Full** 能完整取得 / **Partial** 能取得一部分 / **Missing** 没有工具。
- 标记：`实测`（2026-10-12 至 13，BD 样例模型）/ `待试`。
- 缺口详情见 [CAP-gaps](CAP-gaps.md)；调用细节见 [SOP-AUD-mcp-revit-mcp](../L3-SOP/SOP-AUD-mcp-revit-mcp.md)。

换 MCP：新建 `CAP-binding-<名称>.md`，按同样的行填工具与状态。RUN.md 规定：当前 MCP 没有对照表时，先做对照表再审。

## Host 能力

| 能力 ID | 用于 | revit-mcp 工具 | 状态 | 标记 | 备注 |
| --- | --- | --- | --- | --- | --- |
| CAP-SESSION | 全部 | `get_running_revit_instances`、`get_active_context` | Full | 实测 | Revit 须在 Modify 状态 |
| CAP-PROJECT-CONTEXT | AUD-A1 MA-1、MA-2 | `query_model` + `get_element_data`（基点、Level） | Partial | 实测 | 不回传 Revit 版本（GAP-04） |
| CAP-QUERY-ELEMENTS | 全部 | `query_model` | Full | 实测 | 坐标、长度比较用英尺 |
| CAP-EXTRACT-ROOMS | MA-4.1、S10、S13、S14 | `get_rooms`、`get_room_boundaries` | Full | 实测 | 弧段拉成弦线 |
| CAP-EXTRACT-AREAS | MA-4、V09–V14、S02–S08 | `query_model`（OST_Areas）+ `get_element_data` | Full | 实测 | 方案要经视图区分 |
| CAP-AREA-ENCLOSURE | MA-4.3、A04 | 同上（面积 0 判未闭合） | Partial | 实测 | 读不到边界端点（GAP-02） |
| CAP-EXTRACT-OPENINGS | MA-5.1、S14、V13 | `query_model`（OST_Windows、OST_CurtainWallPanels）+ `get_element_data` | Partial | 实测 | 嵌板尺寸、面积可读；可开启只能从类型名判断 |
| CAP-ASSOCIATE-OPENINGS | S14、V13 | 无直接工具；由 `get_room_boundaries` + 包围盒交给 AGENT-GEOMETRY 计算 | Partial | 实测 | MCP 不回传开口所属房间；脚本按几何关联，带方法与可信度（GAP-07） |
| CAP-ASSOCIATE-FIXTURES-DOORS | S13、S10；S14（reg 36 房间） | 无直接工具；`get_element_data`（boundingBox）+ 房间轮廓，交给 AGENT-GEOMETRY | Partial | 实测 | 门无 From / To Room；洁具无所属房间；脚本按几何关联并标可信度 |
| CAP-EXTRACT-SITE | MA-6、V01、S02 | `query_model`（OST_SiteProperty）+ `get_element_data` | Partial | 实测 | 顶点坐标要由包围盒换算 |
| CAP-EXTRACT-COORDINATES | MA-2.3、S03 | `get_element_data`（基点） | Full | 实测 | — |
| CAP-LIST-VIEWS-SHEETS | 全部 | `get_sheets`、`get_views`、`get_views_on_sheets`、`get_all_schedules`、`get_schedule_definition`、`get_all_view_templates` | Full | 实测 | — |
| CAP-MEASURE-PATH | V02、S10 | 无 | Missing | 实测 | L2 本来就受 FS Code 缺失限制 |
| CAP-MEASURE-WIDTH | V02、S10 | 无（只能读门参数） | Partial | 待试 | — |
| CAP-UI-SHOW | 人工复核时 | `select_elements`、`show_elements`、`open_view` | Full | 待试 | 只改界面显示，不改模型 |
| CAP-EXPORT-TABLE | GEN-06 | `export_views`（CSV） | Partial | 实测 | 明细表不能导出图像（GAP-06） |
| CAP-EXPORT-IMAGE | GEN-03、GEN-05、报告截图 | `export_views`（PNG） | Full | 实测 | — |
| CAP-EXPORT-PDF | A03 | `export_views`（PDF） | Partial | 实测 | 固定 A3，只作检查用 |

## Agent 侧能力

不需要 MCP 工具，但需要 harness 具备相应能力。

| 能力 ID | 用于 | 需要 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| AGENT-CLASSIFY | APL-01 至 APL-10、V10 | Layer 1 原文在场 | Full | 原文缺 → Unclear |
| AGENT-EVALUATE-GFA / SC / LV / OTHER | 各 AUD §4 | Layer 1 原文 + 项目输入 | Partial | 受 DK-AUD-006 缺口限制 |
| AGENT-COMPLETENESS | AUD-A04 | 全部 AUD 结果 | Full | — |
| **AGENT-GEOMETRY**（建议加入 Catalog） | S14、V13；G2、G3 的面积与归属 | harness 能执行 Python 3（只用标准库） | Full（Claude Code 实测）| 定义：用提取文件做点在多边形内、包围盒相交、法线侧探测、面积分摊。脚本在 `tools/`。**无代码执行时**：按 AUD 卡 §9 的步骤人工逐房核对，或记 [GAP] |
| **AGENT-FILE-INFO**（建议加入 Catalog） | A03-L3、MA-1.1 | harness 能读模型文件 | Full（实测） | `tools/drawings/rvt_info.py` 读 .rvt 内 BasicFileInfo（Format 2027、build、协作）；可读时 GAP-04 关闭 |
| **AGENT-REPORT-XLSX** | 各组报告 | 同上 | Full（实测） | `tools/common/xlsx_lite.py` 写 Excel，不需 openpyxl |
| **AGENT-IMAGE-SAMPLE**（建议加入 Catalog） | GEN-03、GEN-05、V01、V08、V10、A02 | harness 能执行代码读 PNG 像素 | Full（Claude Code 实测）| 定义：对导出图像按网格取像素 RGB，统计颜色与灰阶占比；裁切放大。**无代码执行时**：改用 [SOP-AUD-manual 颜色一节](../L3-SOP/SOP-AUD-manual.md#man-colour)，或记 [GAP] |
