# CAP-binding-mcp-servers-for-revit · 能力对照（功能 A）

Layer 4。把 [CAP-catalog](CAP-catalog.md) 的能力 ID（摘自知识库 Capability Catalog v3.0） 对应到 mcp-servers-for-revit（开源 Revit MCP，约 40 个工具）的工具。只列功能 A（审核）用到的能力；写入类工具（`operate_element`、`delete_element`、`create_*`、`send_code_to_revit` 等）不属于审核，不用。

- 状态：**Full** 能完整取得 / **Partial** 能取得一部分 / **Missing** 没有工具。
- 标记：`实测`（日期，BD 样例模型）/ `待试`（工具存在，未在本项目实测）。
- 缺口详情见 [CAP-gaps](CAP-gaps.md)；调用细节见 [SOP-AUD-mcp-mcp-servers-for-revit](../L3-SOP/SOP-AUD-mcp-mcp-servers-for-revit.md)。
- 与 [CAP-binding-revit-mcp](CAP-binding-revit-mcp.md) 相同的能力 ID、相同的「用于」；差别在工具与状态。

## Host 能力

| 能力 ID | 用于 | mcp-servers-for-revit 工具 | 状态 | 标记 | 备注 |
| --- | --- | --- | --- | --- | --- |
| CAP-SESSION | 全部 | `get_running_revit_instances` | Full | 实测 2026-10-27 | 回传进程与当前文档 |
| CAP-PROJECT-CONTEXT | AUD-A1 MA-1、MA-2 | `query_model` + `get_element_data`（基点、Level） | Partial | 待试 | 不回传 Revit 版本（GAP-04，同 revit-mcp） |
| CAP-QUERY-ELEMENTS | 全部 | `query_model` | Full | 实测 2026-10-14、10-27 | `maxResults: 0` = 全部；`analysis.byCategory` 用显示名（Grids、Views…），`g4_extract.py` 换成 OST_ 名 |
| CAP-EXTRACT-ROOMS | MA-4.1、S10、S13、S14 | `query_model`（OST_Rooms）+ `get_element_data`（boundingBox、Name、Number、Area、Level） | Partial | 实测 2026-10-14 | 没有房间边界工具（GAP-08）：房间轮廓用包围盒，非矩形房间的归属可信度降低 |
| CAP-EXTRACT-AREAS | MA-4、V09–V14、S02–S08 | `query_model`（OST_Areas）+ `get_element_data` | Full | 实测 2026-10-14 至 15（Cursor 整套） | 方案要经视图区分 |
| CAP-AREA-ENCLOSURE | MA-4.3、A04 | 同上（面积 0 判未闭合） | Partial | 待试 | 读不到边界端点（GAP-02） |
| CAP-EXTRACT-OPENINGS | MA-5.1、S14、V13 | `query_model`（OST_Windows、OST_CurtainWallPanels）+ `get_element_data` | Partial | 实测 2026-10-14 至 15（Cursor 整套） | 一次可取整类；可开启只能从类型名判断 |
| CAP-ASSOCIATE-OPENINGS | S14、V13 | 无直接工具；包围盒交给 AGENT-GEOMETRY | Partial | 实测 2026-10-14 至 15 | 无房间边界，只能用房间包围盒关联（GAP-07、GAP-08） |
| CAP-ASSOCIATE-FIXTURES-DOORS | S13、S10；S14（reg 36 房间） | 无直接工具；`get_element_data`（boundingBox）交给 AGENT-GEOMETRY | Partial | 实测 2026-10-14 | 洁具 141、门 102 各一次取完；G2 结果与 revit-mcp 运行逐项相同 |
| CAP-EXTRACT-SITE | MA-6、V01、S02 | `query_model`（OST_SiteProperty）+ `get_element_data` | Partial | 待试 | 顶点坐标要由包围盒换算 |
| CAP-EXTRACT-COORDINATES | MA-2.3、S03 | `get_element_data`（基点） | Full | 待试 | — |
| CAP-LIST-VIEWS-SHEETS | 全部 | 无图纸 / 视图专用工具；`query_model`（OST_Sheets、OST_Views、OST_Viewports、OST_Schedules）+ `get_element_data`（Sheet Number、View Scale、View Template、Title on Sheet；视口的 View、View Name）+ 每张图纸一次 `query_model`（`searchScope: SpecificView`、`viewId` = 图纸） | Partial | 实测 2026-10-27 | A001–A006 的图上视图、顺序、属性与 revit-mcp 提取逐项相同；明细表清单 21 张（含图框修订表）。拿不到视口在图纸上的位置框（GAP-09）；图上的明细表实例未列 |
| CAP-MEASURE-PATH | V02、S10 | 无 | Missing | — | L2 本来就受 FS Code 缺失限制 |
| CAP-MEASURE-WIDTH | V02、S10 | 无（只能读门参数） | Partial | 待试 | — |
| CAP-UI-SHOW | 人工复核时 | `select_elements`、`zoom_to_elements`、`open_view` | Full | 待试 | 只改界面显示，不改模型 |
| CAP-EXPORT-TABLE | GEN-06 | `export_views`（CSV）；`get_schedule_data` | Partial | 实测 2026-10-14 | CSV 用制表符分隔（脚本已兼容） |
| CAP-EXPORT-IMAGE | GEN-03、GEN-05、报告截图 | `export_views`（PNG） | Full | 待试 | — |
| CAP-EXPORT-PDF | A03 | `export_views`（PDF） | Partial | 待试 | — |

## 各组需要的能力与本 MCP 的情况

| 组 | 主要能力 | 本 MCP |
| --- | --- | --- |
| G1（S14） | ROOMS、OPENINGS、ASSOCIATE-OPENINGS | 可用；房间用包围盒（GAP-08） |
| G2（S10、S11、S13、S15、S16） | ROOMS、ASSOCIATE-FIXTURES-DOORS、EXPORT-TABLE | 可用（2026-10-14 实测） |
| G3（面积组） | AREAS、AREA-ENCLOSURE | 可用 |
| G4（图纸） | LIST-VIEWS-SHEETS、QUERY-ELEMENTS（每视图计数）、EXPORT-IMAGE | 可用（2026-10-27 实测 V01–V03）；视口位置框缺（GAP-09，分析未用） |
| G5（清单与模型健康） | LIST-VIEWS-SHEETS（明细表清单）、PROJECT-CONTEXT、COORDINATES、SITE | 待试：明细表清单已查到（2026-10-27），整组未跑 |

## Agent 侧能力

与 [CAP-binding-revit-mcp](CAP-binding-revit-mcp.md) 的「Agent 侧能力」一节 相同（与 MCP 无关）。
