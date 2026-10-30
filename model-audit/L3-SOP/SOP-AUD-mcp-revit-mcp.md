# SOP-AUD-mcp-revit-mcp · 用 Autodesk revit-mcp 取得审核信息

Layer 3（MCP 专属）。MCP：Autodesk「Revit MCP Experimental Technical Preview」（工具前缀因 harness 而异，例 `revit-mcp`），40 个操作工具。能力对照见 L4 [CAP-binding-revit-mcp](../L4-Capabilities/CAP-binding-revit-mcp.md)。

换 MCP 时：新建一份 `SOP-AUD-mcp-<名称>.md`，保留同样的分类与 L2 编号。本文件不用改。

**标记**：

- `实测`：2026-10-12 至 13 在 BD 样例模型（Revit 2027 存档）上跑过。
- `待试`：工具存在，未在本项目实测。

## 0. 前提与通用规则

- Revit 必须处于选择状态（Modify），且没有打开的对话框，否则工具无响应。`实测`
- 每个调用都要带进程 ID：先 `get_running_revit_instances`。`实测`
- `query_model` 的包围盒坐标和长度类比较值用**英尺**；面积参数内部单位是 ft²。读 `get_element_data` 时，以 `displayValue`（项目单位）为准。`实测`
- `get_element_data` 每次只回传有限数量的元素：元素多时分批。`实测`
- 本 SOP 只用读取类工具和导出。删除、修改、建视图等写入工具**不属于审核**（RUN.md 安全规则）。

## 1. 会话与文件（AUD-A1 MA-1）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 打开的是哪个文件 | `get_running_revit_instances` → `get_active_context` | 记下路径、进程 ID、活动视图 | 实测 |
| 链接 | `query_model`，类别 `OST_RvtLinks`、`OST_PointClouds`、`OST_Coordination_Model` | 数量为 0 即无。**CAD 导入查不到**（GAP-03） | 实测 |
| 版本、插件依赖 | 无工具 | 文件名推断，记 `[INFERENCE]`（GAP-04） | 实测（确认读不到） |
| 文件大小 | 不经 MCP：读磁盘文件 | — | 实测 |

## 2. 单位、坐标、标高（MA-2、GEN-04）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 单位与精度 | `get_element_data` 读一个已知尺寸（Total Length）和一个 Area（Area） | 看 `displayValue` 的单位和小数位 | 实测 |
| 测量点、项目基点 | `query_model` 类别 `OST_SharedBasePoint`、`OST_ProjectBasePoint` → `get_element_data`（AllParameters） | E/W、N/S、Elev、Angle to True North；内部值是英尺 | 实测 |
| Level 类型的标高基准 | `query_model` 类别 `OST_Levels` → `get_element_data` 取类型 ID → 对类型读 `Elevation Base` | 逐个类型列出 Project Base Point / Survey Point | 实测 |
| 高程点类型 | `query_model` 类别 `OST_SpotElevations` → 类型 → `get_element_data` | 读 Elevation Base、前后缀；`Units Format` 读不出精度时，用导出图像看显示 | 实测 |

## 3. 数据性质（MA-3、GEN-01、GEN-02）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 图纸上的图片表 | `get_sheets` → 对每张图纸 `query_model`（SpecificView = 图纸 ID，类别 `OST_RasterImages`）→ `get_element_data`（尺寸、类型名） | 图片尺寸与类型名可推断内容（例：整张计算表） | 实测 |
| 未用图片类型 | 实例的类型 ID 与图片类型清单取差集 | 差集即未放置的类型 | 实测 |
| 尺寸覆盖值 | 无工具 | 只读到 Total Length，读不到覆盖值（GAP-01） | 实测（确认读不到） |
| 无关数据 | `query_model` 计数：`OST_LightingFixtures`、`OST_Ceilings`、`OST_DuctCurves`、`OST_PipeCurves`、`OST_ElectricalEquipment`、`OST_Sprinklers` 等 | 每类数量 | 实测 |

## 4. Room 与 Area（MA-4、AUD-V09–V14、S 系列）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| Room 清单 | `get_rooms` | 面积、楼层、位置；面积 0 = 未放置 / 未闭合 | 实测 |
| Room 边界 | `get_room_boundaries` | 弧段被拉成弦线 | 实测 |
| 某面积方案的 Area | 先 `get_views_on_sheets` 找到该方案的面积平面 → `query_model`（SpecificView，类别 `OST_Areas`）→ `get_element_data`（Area、Perimeter、Level、Name、Number、分类参数） | Area 与 Perimeter 都为 0 = 未放置；Level 为空 = 无楼层 | 实测 |
| 不在任何视图里的 Area | `query_model`（全模型，`OST_Areas`）与各视图结果取差集 | 用来找残留 / 重复的一套 | 实测 |
| 面积边界缝隙 | 无工具读边界线端点 | 只能抓面积 0（GAP-02） | 实测（确认读不到） |
| 地界 | `query_model` 类别 `OST_SiteProperty` → `get_element_data`（Area、包围盒） | 包围盒是英尺；顶点坐标由包围盒 + 项目基点换算 `[INFERENCE]` | 实测 |

## 5. 视图、图纸、计数（各 AUD §2）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 图纸清单 | `get_sheets` | 图号、图名 | 实测 |
| 图纸上的视图与明细表 | `get_views_on_sheets` | 返回视图 ID、类型、viewport / 明细表实例 ID | 实测 |
| 视图比例、样板 | `get_element_data`（视图 ID，`View Scale`、`View Template`） | 面积平面比例常为 Custom | 实测 |
| 视图内计数 | `query_model`（SpecificView），类别如 `OST_Grids`、`OST_Dimensions`、`OST_Doors`、`OST_DoorTags`、`OST_Rooms`、`OST_RoomTags`、`OST_SpotElevations`、`OST_TextNotes`、`OST_Areas`、`OST_AreaTags`、`OST_FilledRegion` | 结果按类别拆分 | 实测 |
| 门标记读哪个参数 | `get_element_data`（门标记族类型） | 看标签参数；读不到时导出图像看 | 实测 |
| 图例视图 | `get_views`（类型 Legend） | 用于颜色对照 | 实测 |

## 6. 明细表（GEN-01、GEN-02、GEN-06）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 有哪些明细表 | `get_all_schedules` | 只有名称与 ID | 实测 |
| 字段、筛选、排序 | `get_schedule_definition` | 计算栏是否显示为公式 `[GAP：待试]` | 实测（字段）/ 待试（公式） |
| 类别可用字段 | `get_schedulable_fields` | 找样板预设参数 | 实测 |
| 表值 | `export_views` 导出 CSV | **明细表只能导出 CSV，不能导出图像**（GAP-06）；看表在图上的样子要导出整张图纸 | 实测 |

## 7. 图像与颜色（GEN-03、GEN-05）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 视图 / 图纸图像 | `export_views`（PNG） | 每个视图一个文件；分辨率足够取色 | 实测 |
| PDF | `export_views`（PDF） | 页面固定 A3（1190.55 × 841.89 pt），只作检查用 | 实测 |
| 像素取色、灰阶占比 | 不经 MCP：`AGENT-IMAGE-SAMPLE`（harness 执行代码读 PNG 像素） | 每 3 px 取一点统计；裁切放大看文字。无代码执行 → [SOP-AUD-manual](SOP-AUD-manual.md#man-colour) | 实测 |

## 8. 构件（MA-5、AUD-S13、S14）

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| 洁具计数 | `query_model` 类别 `OST_PlumbingFixtures`，按楼层；结果按族 / 类型拆分 | 排除水箱、冲水阀、扶手；无楼层者用 `get_element_data` 读 Comments 与包围盒 | 实测 |
| 窗与幕墙嵌板 | `query_model` 类别 `OST_Windows`、`OST_CurtainWallPanels`（可加 `levelNameFilters`）→ `get_element_data`（Width、Height、Area、Mark） | 先看族名：Windows 类别可能只是消防设施符号；玻璃在幕墙嵌板，可开启扇看类型名（top hung / side hung）。嵌板面积可读，但**没有所属房间**，也常没有窗号（GAP-07） | 实测（2026-10-13，S14） |
| 明细表在不在图框内 | `get_views_on_sheets` 的 outline 与图框范围比；最终以导出整张图纸为准 | outline 为负坐标、远离图框 → 多半放在图框外 | 实测 |
| 房间上的预设参数 | `get_schedulable_fields`（Rooms）→ `get_element_data` | 例：系数、要求窗面积、DV | 实测 |
| 门净宽 | `query_model` 类别 `OST_Doors` → `get_element_data` | — | 待试 |

## 8b. 其他 MA 项

| L2 信息 | 调用 | 要点 | 标记 |
| --- | --- | --- | --- |
| MA-3.2 3D 视图与周边 | `get_views`（类型 ThreeD）；`query_model` 计数墙、楼梯、窗、幕墙、地形 / 周边体量 | 有 3D 视图且主要类别不为 0 | 待试 |
| MA-3.5 BD 模板一致性 | `query_model` 取族名 / 类型名，对照 BD 样板命名（前缀 `BD_`） | 只能看命名，判不了来源 → 结论标 `[INFERENCE]` | 待试 |
| MA-4.6 Level | `query_model` 类别 `OST_Levels` → `get_element_data`（名称、高程） | 与图纸楼层对照 | 实测 |
| MA-6.4 车辆出入口、特殊区域 | `export_views`（Block plan PNG）实看 | 图面判断 | 实测 |
| MA-7.1 / 7.3 图框与 BIM 编号 | `query_model` 类别 `OST_TitleBlocks`（全模型或每张图纸）→ `get_element_data`（AllParameters） | 图框数 = 图纸数；读图号、修订、日期、绘图人、BIM File Reference 字段 | 实测 |
| MA-7.4 图例 | `get_views`（类型 Legend）→ `get_views_on_sheets` | 图例在哪张图纸 | 实测 |

## 9. 已知的坑

- `query_model` 与 `get_element_data` 的长度、包围盒是英尺，换算 1 ft = 304.8 mm。
- 写入工具的面积参数按内部单位 ft² 解释（与审核无关，但读回时别误判）。
- `get_element_data` 的显示值已按项目单位四舍五入；复核三位小数时用显示值。
- 导出的文件名带时间戳；同一检查重跑时替换上次的结果。

## 10. 提取配方（两段式执行的第一步）

**取全部 id**：revit-mcp 的 `query_model` 设 `maxResults` 为大数（例 10000）——设 0 时**一个 id 都不回**；mcp-servers-for-revit 设 0 = 全部。存下的 `query_*` 被截断或没有 id，转换脚本会停下并说明。

本节是**基准配方**：其他 MCP 的 SOP 只写与它不同的步骤。每一步的「能力」栏是该步要的能力（[CAP-catalog](../L4-Capabilities/CAP-catalog.md)）：换 MCP 时，按它的对照表找到提供同一能力的工具代替本栏的调用。提取文件的列与单位见 [EXTRACT-FILES](EXTRACT-FILES.md)。

配方把 MCP 回传值存成提取文件，分析脚本只读这些文件（[AUD-000 §10](../L2-Task-Logic/AUD-000_Audit_Flow.md)）。长度、坐标一律英尺，面积用显示值（m²，三位小数）。文件用 UTF-8、Tab 分隔，首行是表头。一次回传太多时分几份（`cw_part1.tsv`、`cw_part2.tsv`……），脚本会合并。

<a id="r-s14"></a>
### R-S14 · 采光与通风（AUD-S14、AUD-V13）

每次调用的回传**原样**存进 `<run>/_raw/mcp/`（文件名决定用途，可分多份 `<种类>_<份>.json`），再用脚本转换；不手抄、不自己写转换脚本。

| 步 | 调用（只读） | 存成 `_raw/mcp/` | 能力 |
| --- | --- | --- | --- |
| 1 | 房间：同 R-G2 第 1 步（可直接复用 G2 存下的回传） | `query_rooms*`、`rooms*`、`room_boundaries*` | `CAP-EXTRACT-ROOMS` |
| 2 | `query_model` 类别 `OST_Walls`、名称含 glass / louvre（取全部 id，见下）→ `get_element_data`（basic + boundingBox + `Area`、`Mark`） | `query_cw*`、`cw*` | `CAP-EXTRACT-OPENINGS` |
| 3 | `query_model` 类别 `OST_CurtainWallPanels` → `get_element_data`（basic + boundingBox + `Area`）；全部嵌板都取，H / L 由脚本按族名与类型名判 | `query_pn*`、`pn*` | `CAP-EXTRACT-OPENINGS` |
| 4 | `query_model` 类别 `OST_Windows` → `get_element_data`（basic + boundingBox + `Area`、`Mark`） | `query_windows*`、`windows*` | `CAP-EXTRACT-OPENINGS` |
| 5 | `query_model` 类别 `OST_Doors` → `get_element_data`（basic + boundingBox + `Area`、`Mark`；与 R-G2 第 3 步合并成一次，再加 `width_MOE`、`Level`） | `query_doors*`、`doors*` | `CAP-EXTRACT-OPENINGS`、`CAP-MEASURE-WIDTH` |
| 6 | 模型里的 S14 明细表：`export_views`（CSV，`directoryPath` = `_raw`） | `_raw/` 下的 S14 CSV（给 `--schedule`） | `CAP-LIST-VIEWS-SHEETS`、`CAP-EXPORT-TABLE` |
| 7 | `python "Model Audit/tools/extract/g1_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw` | 写 `rooms.tsv`、`room_polygons.json`、`cw_part1.tsv`、`pn_part1.tsv`、`pn_bbox_sample.tsv`、`fs_windows.tsv`、`doors.tsv`、`doors_other.tsv` | 转换（不调 MCP） |

第 7 步的脚本：
- 嵌板：族名含 Louvre → L；类型名含 hung → H；其余是固定玻璃（玻璃已算在幕墙面积里），不收、列出数量。每块嵌板的包围盒都写进 `pn_bbox_sample.tsv`（开口顶高），不再抽样。
- 幕墙只收类型名含 glass / louvre 的；门按族名分成玻璃 / 入口门（`doors.tsv`）与其他（`doors_other.tsv`）。
- 规则都可改：`--wall-type-pattern`、`--louvre-family-pattern`、`--hung-type-pattern`、`--glass-door-pattern`；房间参数名同 R-G2。
- 核对与停止条件同 R-G2；输出夹里有不是这次写的 `cw_*` / `pn_*` 分片也会停（旧分片会被一起读入）。

然后：

```
python "Model Audit/tools/s14_lv/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/C14_analysis_<名>.json [--schedule <S14 明细表 CSV>] [--fixtures <G2 的 fixtures.tsv>] [--previous <旧 JSON>]
python "Model Audit/tools/s14_lv/report.py" --analysis <run>/C14_analysis_<名>.json --outdir <run>
```

要点（2026-10-13 实测）：
- 幕墙的 Area 是模型算出的面积；嵌板没有所属房间、没有窗号，所以房间关联由脚本按几何做（CAP-ASSOCIATE-OPENINGS）。
- 2026-10-14 用 g1_extract 重转 Cursor 2026-10-13 的 revit-mcp 回传：幕墙、嵌板、窗、门与我们的提取逐格一致，S14 32 间房结论相同；房间顶标高按模型修正后，2 个原来归到楼梯 S-1 的开口变为未关联（楼梯不在评估范围，结论不变）。
- 门不计入采光，但要看一遍：嵌在幕墙里的玻璃门面积已含在幕墙面积内，不要重复加。
- 本样例约 25 次 MCP 调用；房间轮廓只取 12 间（另 54 间是矩形，包围盒即轮廓）。

<a id="r-g2"></a>
### R-G2 · 房间-用途组（AUD-S13、S10、S11、S15、S16）

每次调用的回传**原样**存进 `<run>/_raw/mcp/`（文件名决定用途，可分多份），再用脚本转成提取文件；不手抄、不自己写转换脚本。

| 步 | 调用（只读） | 存成 `_raw/mcp/` | 能力 |
| --- | --- | --- | --- |
| 1 | `query_model` 类别 `OST_Rooms`（取全部 id，见下）→ `get_element_data`（basic + boundingBox + SpecificParameters `Name`、`Number`、`Area`、`Level`）；`get_room_boundaries`（MCP 有此工具时；至少非矩形房间和洗手间） | `query_rooms*.json`、`rooms*.json`、`room_boundaries*.json` | `CAP-EXTRACT-ROOMS` |
| 2 | `query_model` 类别 `OST_PlumbingFixtures` → `get_element_data`（basic + boundingBox） | `query_fixtures*.json`、`fixtures*.json` | `CAP-QUERY-ELEMENTS`（洁具位置，供 `CAP-ASSOCIATE-FIXTURES-DOORS`） |
| 3 | `query_model` 类别 `OST_Doors` → `get_element_data`（basic + boundingBox + SpecificParameters `width_MOE`、`Level`） | `query_doors*.json`、`doors*.json` | `CAP-EXTRACT-OPENINGS`、`CAP-MEASURE-WIDTH` |
| 4 | `get_all_schedules` → `export_views`（CSV，`directoryPath` = 本次 `_raw`） | `_raw/` 下的 GBP S10 / S11 / S13 CSV（模型直接写文件） | `CAP-LIST-VIEWS-SHEETS`、`CAP-EXPORT-TABLE` |
| 5 | `python "Model Audit/tools/extract/g2_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw` | 写 `rooms.tsv`、`fixtures.tsv`、`doors_all.tsv`、`room_polygons.json` | 转换（不调 MCP） |

第 5 步的脚本：
- 按回传的形状认格式（revit-mcp 与 mcp-servers-for-revit 都认得）；不认得就停，说明要加适配器。
- 核对：每个 `query_model` 的 id 都读到了、没有多读、没有重复、没有读取失败；`query_model` 结果被 `maxResults` 截断就停。
- 门宽参数名不同的项目用 `--width-param`；房间参数名不同用 `--name-param` / `--number-param` / `--area-param` / `--level-param`。面积不是 m²、门宽不是 mm 时按内部值换算。
- 屏幕上打印计数、各层洁具数、门族数、缺门宽的门；把这几行给操作者看。退出码 2 = 不写任何文件，按错误信息补取。

```
python "Model Audit/tools/room_use/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/G2_analysis_<名>.json [--use institutional] [--tasks S10]
python "Model Audit/tools/common/task_report.py" --analysis <run>/G2_analysis_<名>.json --outdir <run>
```

要点（2026-10-13 / 14 实测）：
- 门没有 From Room / To Room 参数可读，只能按几何关联；门的包围盒含开启弧线，所以用「网格 + 30 % 命中」去掉擦角的邻房。
- `width_MOE` 是门族里的逃生净宽（900 门 = 850，1700 双门 = 1650）；玻璃门族没有此参数 → UNCLEAR。
- revit-mcp 每次 `get_element_data` 只回有限个元素（全部参数约 20 个；只取所需参数时更多），所以分多份存；只取上表所列参数，回传量小得多。mcp-servers-for-revit 一次可取整类（2026-10-14：洁具 141 个、门 102 个各一次，约 0.04 秒）。两者转出的提取文件逐字节相同。

<a id="r-g3"></a>
### R-G3 · 面积方案组

每次调用的回传**原样**存进 `<run>/_raw/mcp/`（文件名决定用途），再用脚本转换；不手抄、不自己写转换脚本。

| 步 | 调用（只读） | 存成 `_raw/mcp/` | 能力 |
| --- | --- | --- | --- |
| 1 | `query_model` 类别 `OST_Areas`（取全部 id，见下） | `query_areas*` | `CAP-QUERY-ELEMENTS` |
| 2 | `get_element_data` 全部 Area：boundingBox + 下面的面积参数（SpecificParameters；revit-mcp 每次约 40 个，可分多份；同一 Area 分在几份里也可以，脚本按 id 合并） | `areas*` | `CAP-EXTRACT-AREAS` |
| 3 | `get_element_data` 全部面积方案（`OST_AreaSchemes`，basic）与地界（`OST_SiteProperty`，`Area`）——也可以和第 2 步放在同一批 | `area_schemes*`、`property_lines*`（或在 `areas*` 里） | `CAP-EXTRACT-AREAS`、`CAP-EXTRACT-SITE` |
| 4 | `query_model` 类别 `OST_RasterImages` → `get_element_data`（basic + `Width`、`Height`） | `query_rasters*`、`rasters*` | `CAP-QUERY-ELEMENTS`（光栅图，GEN-01） |
| 5 | `python "Model Audit/tools/extract/g3_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw` | 写 `areas.tsv`、`area_schemes.tsv`、`rasters.tsv` | 转换（不调 MCP） |
| 6 | `export_views`（PNG）C001–C008、A001 → 读图，必要时裁切放大 | `sheets/*.png`、`table_values.tsv`（见下面「读数规则」） | `CAP-EXPORT-IMAGE`；读图 |

面积参数（BD GBP 样板名）：Area Scheme Id、Area、Number、Name、Level、Common Area、GFA SUMMARY、GFA DEDUCT 2.2 / 2.3 / 21 / 25 / 27、SERVED FACADE、FRR minutes、FRC COMPARTMENT、FRC HEIGHT、Perimeter、Area Type。别的样板参数名不同：`--param-map map.json`。第 5 步核对 `query_model` 的 id 一个不少、每个 Area 的方案都读到；没放置的地界（无面积）不收并列出。2026-10-14 用它重转 2026-10-13 的回传，`areas.tsv`、`area_schemes.tsv` 与原提取逐字节相同。

```
python "Model Audit/tools/area_scheme/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/G3_analysis_<名>.json [--g2 <G2 JSON>]
python "Model Audit/tools/common/task_report.py" --analysis <run>/G3_analysis_<名>.json --outdir <run>
```

**读数规则（`table_values.tsv`，G4 / G5 的 `readings.tsv` 同理；`tools/common/readings.py` 强制执行）**

- 栏位：key、sheet、item、value、unit、confidence（high / medium）、note，可加 `box`（`x0,y0,x1,y1`，图纸 PNG 像素）、`crop`、`finding`。
- **只写在图上看到的数**。不能用模型值「补」表值，也不能「假设同上」；读不到就留空（→ UNCLEAR）。note 里出现 MODEL / FILLED / model extract / assume 的行会被拒用并在屏幕摘要列出。
- 和模型对不上的读数，要有格子的裁切图才判 FAIL：填 `box` 后跑 `python "Model Audit/tools/common/crop_readings.py" --raw <run>/_raw`，它写 `crops/<key>.png` 并填 `crop`；没有裁切图 → UNCLEAR。对得上的读数没有裁切图也可 PASS（medium）。
- 看图下的判断（例：附录 G 表有没有、BEAM Plus 目标评级有没有、地盘分类依据是否齐）写成一行，`finding` 填 PASS 或 FAIL；没有这一行 → UNCLEAR，不推定。
- **证据**：PASS 是说「图上有」——要有那一处的裁切图（`box` → `crop_readings.py`）；FAIL 是说「图上没有」——`sheet` 栏写明看过的图纸。缺证据 → UNCLEAR。
- **核对表**：每组的屏幕摘要列出全部读数（有没有裁切图），报告的「Sheet readings to check」把每条读数和它的裁切图并排。报告把它们列为未经人工核对；看报告的人逐条对一下：数对不对、判断是否真的满足规则（例：只有「CLASS OF SITE: C」不等于地盘分类依据齐全）。G3 用的 key：`appendices`、`beam_target_rating`、`site_class_info`。

**原样保存 MCP 回传（不手抄）**：回传过大时，Claude Code 会把结果原样存成文件并给出路径；把该文件复制到 `mcp/` 再用脚本解析。其他 harness 若直接显示结果，把 JSON 原文整段存成 `mcp/*.json`，不要逐值重打。AllParameters 每次最多 20 个元素。

<a id="r-g4"></a>
### R-G4 · 图面组

第 1–4 步的回传**原样**存进 `<run>/_raw/mcp/`，再用第 4b 步的脚本转换；不手抄、不自己写转换脚本。

| 步 | 调用（只读） | 存成 | 核对 | 能力 |
| --- | --- | --- | --- | --- |
| 1 | `get_sheets` → `get_views_on_sheets`（全部图纸） | `mcp/sheets*`、`mcp/views_on_sheets*` | — | `CAP-LIST-VIEWS-SHEETS` |
| 2 | 每个图上视图（图例、明细表除外）一次 `query_model`（`searchScope: SpecificView`、`maxResults: 1`） | `mcp/view_counts_<视图 id>.json`（回传不含视图 id，所以写进文件名） | 脚本列出没有计数的视图 | `CAP-QUERY-ELEMENTS`（按视图计数） |
| 3 | `get_element_data` 图上视图（basic + SpecificParameters：View Scale、View Template、Title on Sheet、Sheet Number） | `mcp/view_props*` | 脚本列出没有属性的视图 | `CAP-LIST-VIEWS-SHEETS` |
| 4 | `query_model` 类别 `OST_TitleBlocks`、`OST_ProjectInformation` → `get_element_data`（AllParameters）；`query_model` 类别 `OST_RvtLinks`（TypesAndInstances，`maxResults` 大数） | `mcp/titleblocks.json`（分析脚本直接读）、`mcp/query_rvtlinks*` | 图框数 = 图纸数 | `CAP-LIST-VIEWS-SHEETS`（图框）、`CAP-PROJECT-CONTEXT`、`CAP-QUERY-ELEMENTS`（链接数） |
| 4b | `python "Model Audit/tools/extract/g4_extract.py" --mcp <run>/_raw/mcp --out <run>/_raw` | 写 `views_on_sheets.tsv`、`view_props.tsv`、`view_counts.json`、`model_counts.json` | 图框里的修订明细表不列（`--keep-revision-schedules` 可保留）；类型名前的控制字符（系统剖面 / 立面类型）清掉并加视图类别，如 `Section (ARC_gbp)`；自定义比例记 `custom` | 转换（不调 MCP） |
| 5 | `export_views`（PNG）要取色或读字的图纸 | `sheets/*.png` | — | `CAP-EXPORT-IMAGE` |
| 6 | `python sample_colours.py --sheets sheets --out colour_samples.json [--regions regions.json]` | `colour_samples.json` | 不给区域框也行：每张图出一份整图统计，足以判粉红有无、Table 1 是否完全相等；半色调要区域框（`regions.json`），否则 UNCLEAR | `AGENT-IMAGE-SAMPLE` |
| 7 | `python rvt_info.py <模型.rvt> --out rvt_info.json`（只读模型文件） | `rvt_info.json` | 读不到文件 → GAP-04 照旧 | `AGENT-FILE-INFO` |
| 8 | 读图：地段号、街道、坐标表、标高标头、邻街标高；坐标格式、方位角与边长、修改清单、N/A 表 | `readings.tsv`、`coords.tsv` | 每行写图纸与可信度；判断类加 `finding`（PASS / FAIL）。key：`streets`、`level_heads`、`coords_table`、`coords_format`、`coords_bearings`、`modification_list`、`na_table` | 读图（人或 agent） |

```
python "Model Audit/tools/drawings/analyze.py" --raw <run>/_raw --project <名> --model <路径> --out <run>/G4_analysis_<名>.json [--s14 <S14 JSON>] [--g3 <G3 JSON>]
python "Model Audit/tools/common/task_report.py" --analysis <run>/G4_analysis_<名>.json --outdir <run>
```

2026-10-14 实测（只读）：用 g4_extract 转出的 `view_props.tsv` 与原提取逐字节相同；`views_on_sheets.tsv` 除 C007 的 4 张 GBP 明细表外逐行相同（今天的 `get_views_on_sheets` 已不在 C007 列出它们，2026-10-13 的提取里它们的图纸坐标为负值——模型变了还是旧提取有误，未核实）；5 个视图的计数与原提取逐项相同。

<a id="r-g5"></a>
### R-G5 · 清单组与模型健康

每次调用的回传**原样**存进 `<g5>/_raw/mcp/`，再用脚本转换。

| 步 | 调用（只读） | 存成 `_raw/mcp/` | 能力 |
| --- | --- | --- | --- |
| 1 | `query_model` 类别 `OST_Levels`（取全部 id）→ `get_element_data`（basic + `Elevation`、`Building Story`） | `query_levels*`、`levels*` | `CAP-PROJECT-CONTEXT` |
| 2 | `query_model` 类别 `OST_ProjectBasePoint`、`OST_SharedBasePoint`、`OST_SiteProperty` → `get_element_data`（basic + boundingBox + `E/W`、`N/S`、`Elev`、`Angle to True North`、`Area`） | `query_points*`、`points*` | `CAP-EXTRACT-COORDINATES`、`CAP-EXTRACT-SITE` |
| 3 | `get_all_schedules` | `schedules*` | `CAP-LIST-VIEWS-SHEETS`（明细表清单） |
| 4 | `python "Model Audit/tools/extract/g5_extract.py" --mcp <g5>/_raw/mcp --out <g5>/_raw` | 写 `levels.tsv`、`points.tsv`、`all_schedules.tsv`（图框里的修订明细表不列，`--keep-revision-schedules` 可保留） | 转换（不调 MCP） |
| 5 | 读 A001 图纸目录（图上读，不是提取） | `drawing_list.tsv` | 读图（人或 agent） |
| 6 | 已有：G2、G3、G4、S14 的分析 JSON；G3 `table_values.tsv`、`rasters.tsv`；G4 `coords.tsv`、`readings.tsv`、`rvt_info.json`；G2 停车明细表 CSV | — | 已有（其他组的结果） |

2026-10-14 实测（只读，约 5 次调用）：用 g5_extract 转出的 `levels.tsv`、`all_schedules.tsv` 与原提取逐字节相同，`points.tsv` 逐值相同，G5 分析 57 项结论相同。

```
python "Model Audit/tools/lists_health/analyze.py" --raw <g5>/_raw --project <名> --model <路径> --out <g5>/G5_analysis_<名>.json \
  --g2 <G2 JSON> --g3 <G3 JSON> --g4 <G4 JSON> --s14 <S14 JSON> --g3raw <g3>/_raw --g4raw <g4>/_raw --schedules <g5>/_raw/all_schedules.tsv
python "Model Audit/tools/common/task_report.py" --analysis <g5>/G5_analysis_<名>.json --outdir <g5> --name ListsHealth
```

要点：项目基点 E/W、N/S 的显示值是毫米（844820178 = 844,820.178 m）；地盘是矩形时，地界包围盒的四角就是界址点。
