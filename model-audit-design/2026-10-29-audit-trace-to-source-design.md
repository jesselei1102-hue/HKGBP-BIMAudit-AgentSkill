# 审核结果回查源头：设计规格

日期：2026-10-29
范围：`model-audit/`（分析后处理、对话窗口 `app/`、L4 能力、RUN.md）与 `model-audit-design/_agent/`（条文索引生成脚本）
上一版窗口设计：`2026-10-27-audit-app-ux-design.md`

## 1. 目标与约束

操作者的话：「我看到检查结果之后，无法快速回查源头是怎么样的」。选定的两种回查：

1. **在 Revit 里定位**：从一条结果一步打开对应的图纸 / 视图，或选中并缩放到对应的构件。
2. **依据的条文原文**：点条文号直接看条文内容。

操作者的决定：

- 结果的对象是模型里的东西时都要有 Revit ID（「补齐 ID」），不只用分析脚本已有的 ID。
- 条文原文打包进交付包（`model-audit/clauses.json`），离线可用；随包推到 GitHub。政府文件原文公开转载由操作者判断并已决定打包；README 写明每份来源与版本。

约束：

- `gbp-audit` 服务器保持独立，不连 Revit；定位经由 agent，用当前接上的 Revit MCP 工具完成。
- 审核只读：定位只打开视图、选中、缩放，不改模型。
- 界面文字全英文。
- 交付包要能在别的 harness 运行：包里只放生成好的 `clauses.json`，生成脚本留在本工作区（只有这里有 Knowledge）。
- 已发布文件里不出现本机用户路径。

成功标准：在核对窗口里，有 ID 的结果一点 `Show in Revit` 就把消息发到对话、agent 在 Revit 里打开或选中它；任一条文号一点就在该行下面展开原文和出处；不在索引里的条文明确说「不在包里」。

## 2. 补齐 Revit ID

### 2.1 一个解析步骤

新增 `model-audit/tools/common/resolve_ids.py <run>`，在各组分析之后、`build_results.py` 之前运行（RUN.md §6b 第 4 步前、§6c 合并前各加一步）。

- 读该次审核 `<run>/_raw/` 里已有的提取表，建立名称 → ID 的对照：

| 对象写法 | 查哪里 | `object_kind` |
| --- | --- | --- |
| 开头是图纸号（`^[A-Z]\d{3}\b`，如 `C003 site area calculation`） | 图纸导出文件名里的 ID（`<名>_<id> - Sheet - <号> - …`）、`views_on_sheets.tsv` | `sheet` |
| 视图名（与 `view_props.tsv` 的名称完全相同） | `view_props.tsv` | `view` |
| 楼层名完全相同（`G/F`、`SFL 0.25_G/F`） | `levels.tsv` | `level` |
| 面积方案名完全相同（`ARC_gbp_ufa`） | `area_schemes.tsv` | `scheme` |
| 房间号或房间名完全相同（`S-1`） | `rooms.tsv`（G1 / G2 提取） | `room` |
| 图片名包含在对象文字里 | `rasters.tsv` | `element` |
| 明细表名完全相同 | `all_schedules.tsv` | `schedule` |

- 只填 `object_id` 为空的检查；分析脚本自己写的 ID 永远优先（其 `object_kind` 按原样，无则不写）。
- 填入的同时写 `object_kind` 和 `id_from: "lookup"`，以便追溯。
- 一条对象对上多个 ID、或一个都对不上：不填，不猜。
- 不是模型里的东西（`model folder`、`site area`、`all rows`）照旧为空。
- 原地改各组分析 JSON（`G*_analysis*.json` 及按 Task 的 `G*_<task>.json`）；重复运行结果相同。
- 打印一行统计：填了多少、仍为空多少。

### 2.2 数据流向窗口

- `src/types.ts` 的 `Check` 增加 `object_id: number | null`、`object_kind?: string`；`src/overview.ts` 读入时带上（原文件没有这两项时为 `null` / 缺省）。
- 报告：`build_results.py` 已把 `object_id` 写进 `element_ids` / `element_id`，解析后的 ID 自动进报告，不用改。

## 3. Show in Revit

### 3.1 窗口

- 核对窗口每张卡片展开后的明细表、以及 All checks 的明细行：有 `object_id` 的行在对象一栏后加文字按钮 `Show in Revit`。
- 卡片只含一个对象时，卡片头部也有这一按钮。
- 点击发一条消息到对话（新函数 `locatePrompt` 放在 `app/logic/prompts.ts`）：

  > Show "<object>" in Revit (<kind>, ID <id>): open it if it is a sheet or view, otherwise select it and zoom to it. Read-only — do not change the model. Then come back to the review window.

  没有 `object_kind` 时 `(<kind>, ` 一段写成 `(ID <id>`。
- 消息被宿主拒绝时，照现有做法显示可复制的文字框。
- 窗口状态（model context）在点击后加一行 `Last action: show in Revit <id>`。

### 3.2 交付包

- `L4-Capabilities/CAP-catalog.md` 增加 `CAP-SHOW-IN-REVIT`：在 Revit 里打开图纸 / 视图或选中并缩放构件；只改界面，不改模型。
- 各 binding：
  - `CAP-binding-mcp-servers-for-revit.md`：`open_view`（图纸、视图）、`select_elements` + `zoom_to_elements`（其他）。
  - `CAP-binding-revit-mcp.md`：按该服务器现有工具填写；没有时写 Gap，并在 `CAP-gaps.md` 记一条。
- RUN.md §6d 增加一条：收到「Show … in Revit」时按 binding 执行，只读，完成后一句话报告。

## 4. 条文原文

### 4.1 条文索引 `model-audit/clauses.json`

- 由 `model-audit-design/_agent/build_clauses.py` 生成（不进交付包），读本工作区 Knowledge。
- 只收包里实际引用到的条文：扫 `tasks.json`、`L2-Task-Logic/**/*.md`、分析脚本里的 `cite` 字符串与测试样例的分析 JSON，抽出条文引用。
- 每条：

```json
{ "key": "BIMGBPS 5.2.3", "title": "Floor Plan", "text": "<verbatim>", "source": "BIMGBPS (2019) p.15" }
```

- 按来源：

| 引用写法 | key | 取文 | source |
| --- | --- | --- | --- |
| `BIMGBPS §5.2.3`、`§4.2(b)` | `BIMGBPS 5.2.3`、`BIMGBPS 4.2` | `hk-gbp-pdf-extracts/BIMGBPS_e.md` 按节标题切分（目录页除外） | `BIMGBPS (2019) p.<页>` |
| `Cap. 123F reg 23(2)` | `Cap. 123F reg 23` | `knowledge/cap123f/` 按条 | `Cap. 123F · e-Legislation <版本日期>` |
| `Cap. 123 s 16`、`Cap. 123H reg 3`、`Cap. 123I reg 5` | 同上格式 | `knowledge/cap123`、`cap123h`、`cap123i` | 同上 |
| `PNAP APP-151 ¶6(d)` | `PNAP APP-151 ¶6` | `hk-gbp-pdf-extracts/PNAP/` 按编号段落；找不到段落就不收 | `PNAP APP-151` |
| `GEN-01`、`LIM-14` | 原样 | 包内 `L2-Task-Logic/AUD-000_Audit_Flow.md`（GEN）、`L1-Domain/DK-AUD-002_Limits_Index.md`（LIM）的对应行 | `Model Audit <文件名>` |

- 分项（`(b)`、`(2)`、`(d)`）不再细切：显示整节 / 整条 / 整段，在标题里注明分项。
- 原文逐字保留，不改写、不翻译。
- 生成时写覆盖清单 `model-audit-design/_agent/clauses-coverage.md`：每个引用 → 找到 / 没找到（原因）。FS Code 2011 不在 Knowledge，列为没找到。
- 交付包 README 加一段：`clauses.json` 的来源与各自版本，原文逐字摘录。

### 4.2 窗口

- 新函数 `clauseRefs(cite: string): { label: string; key: string | null }[]`（`app/logic/clauses.ts`）：按 `;` 与 `,` 拆分；同一文件名延续到后面的引用（`BIMGBPS §4.2(b), §5.1.2` → `BIMGBPS 4.2`、`BIMGBPS 5.1.2`）；括号里的 `GEN-nn`、`LIM-nn` 单独成项；认不出的保留 label、key 为 `null`。
- 明细表的条文一栏改为一串链接（label 原样显示）。点一个，在该行下面展开：标题（含分项）、原文、小字出处；再点收起。同一时间每行只展开一条。
- 不在索引里：`Clause text not in the package`；FS Code 引用：`FS Code 2011 is not in the package sources`。
- `show_overview` 回传 `clauses`：只含本次结果引用到的条目（服务器读 `clauses.json` 按 key 挑出）；`clauses.json` 缺失时回传空，窗口一律显示「不在包里」。

## 5. 测试

- Python：`test_resolve_ids.py`（各对照规则、分析脚本自带 ID 优先、多重匹配不填、重复运行不变、非模型对象为空）；`test_build_clauses.py`（BIMGBPS 切节、条例按条、分项归到整节、GEN / LIM、FS Code 列为没找到）。
- TypeScript：`clauses.test.ts`（`clauseRefs` 的拆分与延续）、`prompts.test.ts`（`locatePrompt` 两种写法）、`overview.test.ts`（`object_id` / `object_kind` 读入，旧文件缺省为 null；`clauses` 只含引用到的条目）。
- 模拟宿主场景：有 ID 的行显示 `Show in Revit` 并发出消息；`nomessage=1` 时出可复制框；点条文展开 / 收起；不在包里的提示；窄窗口 400 px。
- 真实模型：对一次 V01–V03 审核跑 `resolve_ids.py`，统计 ID 覆盖；在对话里点一次 `Show in Revit`，agent 在 Revit 打开该视图（只读）。

## 6. 改动范围

- 新增：`tools/common/resolve_ids.py`、`model-audit/clauses.json`、`app/app/logic/clauses.ts`、`model-audit-design/_agent/build_clauses.py` 与测试。
- 修改：`app/src/types.ts`、`app/src/overview.ts`、`app/src/app.ts`（`show_overview` 带 `clauses`）、`app/app/overview.ts`、`app/app/logic/prompts.ts`、`RUN.md`、L4 的 catalog / binding / gaps、交付包 README、`app/README.md`。
- 不改：各组分析脚本（ID 由解析步骤补）、报告模板、Revit MCP 服务器。
