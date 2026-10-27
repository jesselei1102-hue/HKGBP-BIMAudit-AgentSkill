# CAP-catalog · 审核用到的能力（功能 A）

Layer 4。本包审核需要 BIM MCP 和 agent 具备哪些**能力**。能力用稳定 ID 表达，不规定工具名：任何 MCP 的工具，只要能做到「要做到什么」并通过「判 Full 的要点」，就能绑定到该能力。

- 来源：知识库 HK GBP MCP Capability Catalog v3.0（§3 Host 能力、§4 Agent 能力）中功能 A 用到的部分；「本包要取到的数据」与「判 Full 的要点」按本包的提取文件补充。目录里写的数值限值不抄进来，判定一律以 L1 原文为准（[DK-AUD-005](../L1-Domain/DK-AUD-005_Errata.md)）。
- 某个 MCP 能做到哪些：见各 MCP 的 `CAP-binding-*`。接入新 MCP：[CAP-onboarding](CAP-onboarding.md)。提取文件的列与单位：[EXTRACT-FILES](../L3-SOP/EXTRACT-FILES.md)。
- 状态：**Full** 满足全部要点 / **Partial** 能取得一部分（写明缺什么，相关检查降级或 Unclear）/ **Missing** 做不到（相关检查 Unclear，引 [CAP-gaps](CAP-gaps.md)）。

## Host 能力（由 MCP 工具提供，只读）

| 能力 ID | 要做到什么 | 本包要取到的数据 | 判 Full 的要点 | 用于 |
| --- | --- | --- | --- | --- |
| `CAP-SESSION` | 找到运行中的 Revit 和当前模型，后续调用都作用于它 | 文档名、路径；需要时的实例 / 进程标识 | 没绑定时调用明确失败；多个文档不串 | 全部 |
| `CAP-PROJECT-CONTEXT` | 项目上下文：单位、标高、文件信息 | `levels.tsv`（标高名、高程 mm、是否楼层） | SFL / FFL 不合并；无街面标高时不编造 | MA-1、MA-2、V03、V04、S04 |
| `CAP-QUERY-ELEMENTS` | 按类别 / 视图 / 范围过滤构件，取回全部 id 与按类别计数 | `query_*.json`（证明一个不少）；`view_counts.json`（每个视图各类别数量） | 能取全部 id（无截断）；窗与幕墙嵌板可分开查；能按单个视图计数 | 多数提取；V02–V05 计数 |
| `CAP-EXTRACT-ROOMS` | 房间的名称、编号、标高、宿主算出的面积、位置 | `rooms.tsv`；`room_polygons.json` | 面积是 Revit 算的（不是包围盒）；未放置房间可识别；非矩形房间有边界轮廓 | MA-4.1、S10、S13、S14、V11、V13 |
| `CAP-EXTRACT-AREAS` | 按面积方案列出 Area：面积、分类参数、所属方案、位置 | `areas.tsv`、`area_schemes.tsv` | 不同方案不串；不拿 Room 冒充 GFA Area；项目参数可读 | MA-4、V09–V14、S02、S05–S08、S12 |
| `CAP-AREA-ENCLOSURE` | 判断 Area 边界是否闭合、有无缝隙 / 重叠 | `areas.tsv` 的面积（0 = 未闭合） | 能给出缝隙 / 重叠位置（只有面积为 0 可判 → Partial，GAP-02） | MA-4.3、V09–V12、A04 |
| `CAP-EXTRACT-OPENINGS` | 窗、幕墙、幕墙嵌板、门的面积、类型、位置 | `cw_part*.tsv`、`pn_part*.tsv`、`pn_bbox_sample.tsv`、`fs_windows.tsv`、`doors.tsv`、`doors_all.tsv` | 幕墙嵌板单独可取；门可读净宽参数；可开启面积无参数时留空，不默认 100 % | S14、V13、S10、MA-5.1 |
| `CAP-ASSOCIATE-OPENINGS` | 开口属于哪个房间 | （无专用工具时由 `AGENT-GEOMETRY` 用房间轮廓算） | MCP 直接给出开口—房间对并标出不确定的；用几何弱替代时最多 Partial | S14、V13 |
| `CAP-ASSOCIATE-FIXTURES-DOORS` | 洁具、门属于哪个房间（本包新增，目录未列） | `fixtures.tsv`、`doors_all.tsv` 的位置 + 房间轮廓 | 同上；弱替代最多 Partial | S13、S10、S14（reg 36 房间） |
| `CAP-EXTRACT-SITE` | 地界、地盘面积 | `points.tsv` 的地界行；`areas.tsv` 的地界面积 | 地界可读面积与位置；无街道资料时明确列为缺失 | MA-6、V01、S02–S06 |
| `CAP-EXTRACT-COORDINATES` | 测量点、项目基点的坐标与方位 | `points.tsv`（E/W、N/S、高程 mm、正北角） | HK1980 坐标可读；不是 HK1980 时不装作是 | MA-2.3、S03、V01 |
| `CAP-LIST-VIEWS-SHEETS` | 图纸、图上视图、视图属性、明细表清单 | `views_on_sheets.tsv`、`view_props.tsv`、`all_schedules.tsv`、`mcp/titleblocks.json` | 每张图纸上的视图（含图例、放在多张图上的）一个不漏；比例、样板、图上标题可读；视口在图纸上的位置可读 | S01、A01、A04、V 系列 |
| `CAP-MEASURE-PATH` | 沿走廊的行走距离 | — | 非直线距离；无网络时失败而非给假距离 | V02、S10 |
| `CAP-MEASURE-WIDTH` | 走廊、门、楼梯的净宽 | `doors_all.tsv` 的门净宽参数 | 声明饰面假设；只读门参数 → Partial | V02、S10 |
| `CAP-UI-SHOW` | 选中、缩放、打开视图给人复核 | — | 只改界面显示，不改模型 | 人工复核（可选） |
| `CAP-EXPORT-TABLE` | 明细表导出成 CSV | `_raw/` 下的明细表 CSV | 模型直接写文件；逗号或制表符分隔都可（脚本兼容） | GEN-06、S10、S11、S13、S14、停车 |
| `CAP-EXPORT-IMAGE` | 图纸 / 视图导出成 PNG | `sheets/*.png`（读图、取色、裁切图） | 指定视图导出；分辨率足够读字（约 1920 px 宽起） | GEN-03、GEN-05、V01、V08、V10、A02、读图 |
| `CAP-EXPORT-PDF` | 图纸导出成 PDF | — | 能指定图纸与纸张 | A03 |

审核**不用**的写入类能力（目录 §3.4、§3.5 的 CREATE-VIEW、CONFIGURE-VIEW、COLOUR-FILL、ANNOTATE、COMPOSE-SHEET、SET-PARAMETERS、AREA-BOUNDARIES、BIM-PACKAGE 等）属于功能 B，不在本表。

## Agent 侧能力（不需要 MCP 工具）

| 能力 ID | 要做到什么 | 需要 | 用于 |
| --- | --- | --- | --- |
| `AGENT-CLASSIFY` | 空间分类（GFA、采光通风的纳入 / 排除 / 待定），不只看房名 | L1 原文在场 | APL-01 至 APL-10、V10、S14 |
| `AGENT-EVALUATE-GFA` | GFA、地积比与豁免上限判定 | L1 原文 + 项目输入 | S05、S07、S08、V10 |
| `AGENT-EVALUATE-SC` | 上盖面积判定 | 同上 | S05、V09 |
| `AGENT-EVALUATE-LV` | 采光通风（Cap. 123F reg 30、31、36）判定 | 同上 | S14、V13 |
| `AGENT-EVALUATE-OTHER` | 其他法定判定（出口、洁具、垃圾房、电讯房、升降机、EVA、SBD 等） | 同上 | 各 AUD §4 |
| `AGENT-COMPLETENESS` | 交件完整性汇总；Missing 不等于 Present | 全部 AUD 结果 | A04 |
| `AGENT-GEOMETRY` | 点在多边形内、包围盒相交、法线侧探测、面积分摊 | 能执行 Python 3（标准库） | S14、V13、G2、G3 |
| `AGENT-FILE-INFO` | 从 .rvt 文件头读版本、协作状态 | 能读模型文件 | A03、MA-1.1 |
| `AGENT-REPORT-XLSX` | 写 Excel 报告 | 能执行 Python 3 | 各组报告 |
| `AGENT-IMAGE-SAMPLE` | 导出图按网格取色、统计灰阶、裁切放大 | 能执行代码读 PNG | GEN-03、GEN-05、V01、V08、V10、A02 |

`AGENT-*` 的判定都按 L2 规则：Unclear ≠ Pass，必须引原文条款。
