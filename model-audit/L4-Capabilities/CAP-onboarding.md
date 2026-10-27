# CAP-onboarding · 接入一个新的 MCP

Layer 4。当前连着的 BIM MCP 在本文件夹还没有 `CAP-binding-<名称>.md` 时，按本步骤做出对照表与 SOP，再审（RUN.md 规则）。依据知识库 Capability Catalog v3.0 §2（接到 MCP 后怎么判定 Task），按本包的提取文件具体化。全程只读：写入类工具一律不调用。

## 1. 列出工具

读 MCP 暴露的全部工具：名称、说明、参数。只看名称不够，按说明与参数判断它能做什么。

- 某些宿主只在连接时读一次工具清单：若工具数明显偏少（例如只有一个「列出实例」），先重连或重启会话再列。

## 2. 逐项对照能力

对 [CAP-catalog](CAP-catalog.md) 的每个 Host 能力，找出能做到它的工具（一个工具可对应多个能力，一个能力也可能要几个工具组合）。常见对应：

| 工具看起来能… | 候选能力 |
| --- | --- |
| 列出运行中的实例 / 打开的文档 | `CAP-SESSION` |
| 按类别、标高、视图过滤构件；返回 id 与计数 | `CAP-QUERY-ELEMENTS` |
| 读构件参数与包围盒 | 配合上一项，得到 `CAP-EXTRACT-ROOMS`、`CAP-EXTRACT-AREAS`、`CAP-EXTRACT-OPENINGS`、`CAP-EXTRACT-SITE`、`CAP-EXTRACT-COORDINATES`、`CAP-PROJECT-CONTEXT` |
| 房间 / 面积边界 | `CAP-EXTRACT-ROOMS` 的轮廓部分；`CAP-AREA-ENCLOSURE` |
| 图纸、视图、视口、明细表清单 | `CAP-LIST-VIEWS-SHEETS`（没有专用工具时，可由按类别查询 + 读参数组合，见 mcp-servers-for-revit 的做法） |
| 导出 CSV / PNG / PDF | `CAP-EXPORT-TABLE`、`CAP-EXPORT-IMAGE`、`CAP-EXPORT-PDF` |
| 选中、缩放、打开视图 | `CAP-UI-SHOW` |

找不到工具的能力先记 Missing；没有专用工具、由 agent 几何计算代替的（开口 / 洁具 / 门归属房间），最多记 Partial。

## 3. 实测

用当前模型（最好是 BD 样例模型，便于与已有运行比对），按 [基准配方](../L3-SOP/SOP-AUD-mcp-revit-mcp.md#r-s14) 每一步的「能力」栏，逐项用找到的工具做一次最小调用：

- 回传要能满足 [CAP-catalog](CAP-catalog.md) 的「判 Full 的要点」才记 Full；缺了哪一点就记 Partial 并写明。
- 每项记 `实测 <日期>`；没试的记 `待试`，不要推测成 Full。
- 回传原样存进一个试验运行文件夹的 `_raw/mcp/`，跑对应的 `tools/extract/g*_extract.py`：
  - 脚本认得格式并写出提取文件 → 与 [EXTRACT-FILES](../L3-SOP/EXTRACT-FILES.md) 的列和单位核对；有已有运行时，逐行比对。
  - 脚本停下并说「unknown … format – add an adapter」→ 在 `tools/extract/mcp_formats.py`（或该组脚本）加适配器，先在 `model-audit-design/_agent/test_extract_g*.py` 写会失败的测试，再实现。不要手抄值、不要每次另写转换脚本。

## 4. 写对照表与 SOP

- `L4-Capabilities/CAP-binding-<名称>.md`：照 [CAP-binding-revit-mcp](CAP-binding-revit-mcp.md) 的列（能力 ID、用于、工具、状态、标记、备注），加一张「各组需要的能力与本 MCP 的情况」表（照 [CAP-binding-mcp-servers-for-revit](CAP-binding-mcp-servers-for-revit.md)）。
- `L3-SOP/SOP-AUD-mcp-<名称>.md`：只写与基准配方不同的步骤（调用、要存的文件名、限制），照 [SOP-AUD-mcp-mcp-servers-for-revit](../L3-SOP/SOP-AUD-mcp-mcp-servers-for-revit.md)。
- 新出现的缺口加进 [CAP-gaps](CAP-gaps.md)（写明只在哪个 MCP）。
- `model-audit-design/_agent/check_package.py` 的文件清单与能力检查加上这两个新文件。

## 5. 判定各组能不能跑

每组主要能力见各 `CAP-binding-*` 的组表：

- **能跑**：该组要的能力都是 Full。
- **降级跑**：有 Partial：照跑，受影响的检查按 L2 规则记 Unclear 并引 GAP。
- **不能跑**：有 Missing 的必需能力：该组相关任务记 Unclear（`<Task>-INPUT` 写明缺什么），不拿空数据判。

把判定写给操作者，再按 RUN.md 开始审核。
