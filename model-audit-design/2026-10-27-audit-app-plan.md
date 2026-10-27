# Model Audit 对话窗口（MCP App）· 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal**：在交付包里加一个独立的 `gbp-audit` MCP server，在对话里弹出两个窗口：选检查；结果总览兼确认关口。

**Architecture**：

- 从 Ultraviolet MCP App 模板（`Design Theme/template/`）复制出 `work/model-audit/app/`（Node / TypeScript，stdio）。
- server 的纯逻辑分文件：路径守卫、任务清单、审核列表、总览读取、确认记录。每个文件先写 vitest 测试。
- 窗口是一个 `app.html`，按工具结果里的 `view` 显示「选检查」或「总览」。发给对话的指令由纯函数生成，可单测。
- Python 端只加两处：生成 `tasks.json` 的脚本；`build_results.py` / `render_report.py` 读确认记录并在报告里提醒。

**Tech Stack**：Node ≥ 20、TypeScript、`@modelcontextprotocol/sdk`、`@modelcontextprotocol/ext-apps`、zod、Vite（singlefile）、vitest；Python 3 标准库（unittest）。

**Spec**：[2026-10-27-audit-app-design.md](2026-10-27-audit-app-design.md)

## Global Constraints

- 整个 app 和窗口都用英文：界面文字、发给对话的指令、错误信息、工具描述。Sentence case，不用感叹号。
- Ultraviolet 规则（`ultraviolet-mcp-app` skill §3–§4）：颜色只用 `tokens.css` 变量；一个 `--accent`；数字和编号用 `var(--mono)`；主按钮在底部 `.dock`，每个视图一个 `.db.pri`；插入 HTML 的值都 `escapeHtml`；`ui://` 地址带内容哈希；`.app` 不用 `min-height: 100vh` / `overflow: hidden`；状态变化时 `context.schedule()`。
- server 不连 Revit、不上网；只读写审核根目录（`GBP_AUDIT_RUNS`，或启动参数 `--runs <dir>`，默认 `<package>/../model-audit-runs`）和交付包本身；拒绝越界路径。
- 「只给窗口」的工具：`_meta.ui.visibility: ["app"]`。
- Python：只用标准库；现有 155 个测试照常全过（`model-audit-design/_agent/test_*.py`）。
- 没有 `gate-confirmation.json` 时，`build_results.py` / `render_report.py` 的输出与现在逐字节相同。
- 提交信息结尾：`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。只在本地提交；推送 GitHub 先问操作者。

## Review Focus

1. 读数截图是另一台机器的绝对路径（例：Cursor 那份拷贝里的 `C:\Users\...\Desktop\...`）→ 该读数显示「No crop」，不报错（Task 5 测试 `crop outside the run is treated as missing`）。
2. 同一审核文件夹里同时有整组 JSON、`--tasks` 部分结果和 `.prev.json` → 整组 JSON 为准，不重复计数（Task 5 测试 `full group file wins over partial and prev`）。
3. 同一个读数 key 出现在两组（G3、G4 都有 `site_area` 之类）→ 标记按 `<group>:<key>` 区分（Task 6 测试 `marks are keyed by group and key`）。
4. agent 重跑分析后，窗口里的旧标记对不上新读数 → `save_gate` 以磁盘上当前的读数为准，`confirmed` 缺标记就拒绝（Task 6 测试 `confirmed is rejected when a current reading has no ok mark`）。
5. 宿主不支持窗口往对话发消息 → 显示指令和复制按钮（Task 9 模拟宿主场景 `no message capability`）。

---

## 文件结构

```
work/model-audit/
  tasks.json                          新：任务清单（Task 1 生成）
  tools/common/make_tasks_json.py     新：从 L2 卡片 + 各分析脚本 GROUP 生成 tasks.json
  tools/common/build_results.py       改：读 <run>/gate-confirmation.json → results["gate"]
  templates/audit-results.schema.json 改：可选的 gate
  report/render_report.py             改：Overview 里的读数核对提醒
  RUN.md                              改：§6d 窗口
  skills/gbp-model-audit/SKILL.md     改：有 gbp-audit 工具时用窗口
  README.md                           改：要求里加 Node.js（窗口可选）
  app/                                新：gbp-audit server（从模板复制）
    package.json  tsconfig.json  vite.config.ts  vitest.config.ts  README.md
    src/index.ts        stdio 入口；解析 --runs
    src/config.ts       包根目录、审核根目录
    src/paths.ts        路径守卫
    src/catalogue.ts    读 tasks.json
    src/runs.ts         列出审核文件夹
    src/overview.ts     读一次审核的结果（G1 归一化、G2–G5、读数、报告、已有确认记录）
    src/gate.ts         写 gate-confirmation.json
    src/app.ts          四个工具 + ui:// 资源
    app/app.html  app/main.ts  app/choose.ts  app/overview.ts
    app/logic/prompts.ts   发给对话的指令（纯函数）
    app/logic/selection.ts 勾选逻辑（跨组任务）
    app/theme/  app/ui/    模板原样
    test/*.test.ts  test/fixtures/
    dev/harness.html       模拟宿主（改成模拟本 app 的四个工具）
work/.gitignore                       改：忽略 app/node_modules/、app/build/
work/model-audit-design/_agent/test_app_catalogue.py   新
work/model-audit-design/_agent/test_gate.py            新
```

---

### Task 1: 任务清单 `tasks.json`

**Files:**
- Create: `work/model-audit/tools/common/make_tasks_json.py`、`work/model-audit/tasks.json`
- Test: `work/model-audit-design/_agent/test_app_catalogue.py`

**Interfaces:**
- Produces: `tasks.json` = `{"groups": [{"id": "G1", "name": "Lighting and ventilation"}, {"id": "G2", "name": "Room use"}, {"id": "G3", "name": "Area schemes"}, {"id": "G4", "name": "Drawings"}, {"id": "G5", "name": "Lists and model health"}], "tasks": [{"task": "AUD-S10", "tl": "TL-S10", "name": "Min Exit Doors & Routes", "summary": "BIMGBPS §5.3.10", "groups": ["G2"]}, ...]}`。`tasks` 按 G1→G5 首次出现的顺序；G1 = `["AUD-S14"]`；G2–G5 = 各 `analyze.py` 的 `GROUP`；`AUD-A1`：`tl` 为 `"MA-1–MA-7"`，名称和 `summary` 取 `L2-Task-Logic/AUD-A1_Model_Health.md` 标题行。
- `make_tasks_json.py [--check]`：无参数写 `tasks.json`；`--check` 只比较，不同就 exit 1 并打印差异。

- [ ] **Step 1: 写失败的测试** `test_app_catalogue.py`（unittest，风格同 `test_update.py`）：
  - `test_check_passes`：`make_tasks_json.py --check` exit 0。
  - `test_every_group_task_listed`：用 `ast` 读 4 个 `analyze.py` 的 `GROUP`，每个 task 都在 `tasks.json`，且 `groups` 含对应组。
  - `test_shared_tasks`：`AUD-V08`、`AUD-V10`、`AUD-V11` 的 `groups == ["G3", "G4"]`；`AUD-A1` 的 `groups == ["G2", "G5"]`；`AUD-S14` 的 `groups == ["G1"]`。
  - `test_names_from_cards`：`AUD-S10` 的 `name == "Min Exit Doors & Routes"`、`summary == "BIMGBPS §5.3.10"`。
  - `test_count`：37 项（36 个 Task + A1）。
- [ ] **Step 2: 运行**：`python -I test_app_catalogue.py` → FAIL（脚本不存在）。
- [ ] **Step 3: 写 `make_tasks_json.py`**：GROUP 用 `ast.literal_eval` 从源码取（不 import 分析脚本）；名称和条文用与 `build_results.card()` 相同的标题行正则。输出 `json.dumps(..., ensure_ascii=False, indent=1)` + 换行。运行一次生成 `tasks.json`。
- [ ] **Step 4: 运行**：`python -I test_app_catalogue.py` → 5 PASS。
- [ ] **Step 5: 提交** `feat: task catalogue for the audit window`。

### Task 2: 确认记录进报告（Python）

**Files:**
- Modify: `tools/common/build_results.py`（`main()` 写 results 之前）、`templates/audit-results.schema.json`、`report/render_report.py`（`s_overview`）
- Test: `work/model-audit-design/_agent/test_gate.py`

**Interfaces:**
- Consumes: `<run>/gate-confirmation.json`（Task 6 写出，格式见下）。
- Produces: `results["gate"] = {"mode": "confirmed"|"unreviewed", "saved": str, "checked": int, "unreviewed": [Reading], "disputed": [Reading]}`，`Reading = {"group", "key", "sheet", "item", "value", "note"}`。`<run>` = `--out` 所在文件夹。

确认记录格式（Task 6 用同一份）：

```json
{"mode": "confirmed", "saved": "2026-10-27T10:00:00Z",
 "readings": [{"id": "G3:height_c001", "group": "G3", "key": "height_c001", "sheet": "C001",
               "item": "Building height", "value": "12.15", "mark": "ok", "note": ""}]}
```

- [ ] **Step 1: 写失败的测试** `test_gate.py`：沿用 `test_update.py` 的 G2 fixture 跑出 `audit-results.json`。
  - `test_no_gate_file_no_gate_key`：没有确认记录 → results 里没有 `gate`。
  - `test_gate_copied`：记录 3 条（ok / none / wrong + note "value is 445"）、mode `unreviewed` → `gate.checked == 1`，`unreviewed` 1 条，`disputed` 1 条且 `note == "value is 445"`。
  - `test_schema_accepts_gate`：带 `gate` 的结果过 `render_report.py` 不出 INVALID（exit 0）。
  - `test_banner_lists_unreviewed`：BIM、AP 两版 HTML 都含 `1 sheet reading was not checked by a person` 和该读数的 key；含 `Marked wrong by the operator` 和 `value is 445`。
  - `test_all_checked_line`：mode `confirmed`、全部 ok → 含 `All 3 sheet readings were checked by the operator`，不含 `not checked`。
  - `test_bad_gate_file`：确认记录不是合法 JSON → `build_results.py` exit 2，输出含 `gate-confirmation.json`。
- [ ] **Step 2: 运行**：`python -I test_gate.py` → FAIL。
- [ ] **Step 3: 实现**：
  - `build_results.py`：`load_gate(run_dir) -> dict | None`；坏文件打印 `ERROR: <path>: <reason>` 并 `sys.exit(2)`。
  - schema：顶层 `properties` 加可选 `gate`（字段同上，`mode` 枚举两值）。
  - `render_report.py`：`s_overview` 末尾加 `gate_note(c)`；只有 `gate` 存在时才输出。用词同测试；单复数 `reading` / `readings`；各值 `html.escape`。
- [ ] **Step 4: 运行**：`python -I test_gate.py` → 6 PASS；再跑 `test_render.py`、`test_update.py` 全过。
- [ ] **Step 5: 提交** `feat: show the reading review state in the reports`。

### Task 3: server 骨架和路径守卫

**Files:**
- Create: `work/model-audit/app/`（复制模板，不含 `node_modules/`、`build/`）；删除 `src/data.ts`、`test/data.test.ts`、`app/ui/edits.ts`、`test/edits.test.ts`
- Create: `app/src/config.ts`、`app/src/paths.ts`、`app/test/paths.test.ts`
- Modify: `app/package.json`（`name: "gbp-audit"`、`bin`）、`app/src/app.ts`（`APP_NAME = "gbp-audit"`，先清空工具）、`app/src/index.ts`、`work/.gitignore`

**Interfaces:**
- Produces:
  - `config.ts`：`resolveConfig(argv: string[], env: NodeJS.ProcessEnv, here: string): { packageRoot: string; runsRoot: string }`。`packageRoot` = `app/` 的上一级；`runsRoot` 优先 `--runs`，再 `GBP_AUDIT_RUNS`，否则 `path.resolve(packageRoot, "..", "model-audit-runs")`。
  - `paths.ts`：`resolveInside(root: string, rel: string): string`，越界抛 `PathError`（`message: "Path is outside the allowed folder: <rel>"`）；`isInside(root: string, abs: string): boolean`。

- [ ] **Step 1: 复制模板、改名**；`npm install`；`npm test` 跑剩下的模板测试（css、glyphs、html、theme、uri、context）→ PASS。
- [ ] **Step 2: 写失败的测试** `paths.test.ts`：`resolveInside(root, "audit-1")` 返回 root 下路径；`".."`、`"../x"`、`"a/../../x"`、绝对路径 `C:\\Windows`、`"/etc"` 都抛 `PathError`；含空格和中文的文件夹名（`"audit 2026-10-27 测试"`）可以；`isInside` 对 root 本身返回 true。`config.test.ts`：三种来源的优先顺序。
- [ ] **Step 3: 运行** `npm test` → FAIL。
- [ ] **Step 4: 实现** `paths.ts`、`config.ts`（用 `path.resolve` + `path.relative`，判断 `..` 开头或绝对路径）。`index.ts` 用 `resolveConfig(process.argv.slice(2), process.env, ...)` 并传给 `registerApp(server, config)`。
- [ ] **Step 5: 运行** `npm test` → PASS；`npm run build` 成功。
- [ ] **Step 6: `.gitignore`** 加 `/model-audit/app/node_modules/`、`/model-audit/app/build/`；`git status` 不出现这两个目录。
- [ ] **Step 7: 提交** `feat: gbp-audit server skeleton`。

### Task 4: 任务清单和审核列表

**Files:**
- Create: `app/src/catalogue.ts`、`app/src/runs.ts`、`app/test/catalogue.test.ts`、`app/test/runs.test.ts`

**Interfaces:**
- Consumes: Task 1 的 `tasks.json`；Task 3 的 `resolveInside`。
- Produces:
  - `type Catalogue = { groups: { id: string; name: string }[]; tasks: { task: string; tl: string; name: string; summary: string; groups: string[] }[] }`
  - `loadCatalogue(packageRoot: string): Promise<Catalogue>`（文件缺失或坏 → 抛 `Error("tasks.json: <reason>")`）
  - `type RunInfo = { name: string; groups: string[]; partial: boolean; hasReports: boolean; modified: string }`
  - `listRuns(runsRoot: string): Promise<RunInfo[]>`：只列一层子文件夹；有分析 JSON（`C14_analysis_*.json`、`G[2-5]_*.json`，不含 `*.prev.json`）或 `audit-results.json` 才列；按修改时间倒序；`runsRoot` 不存在 → `[]`。
  - `newRunName(today: string, tasks: string[], all: boolean): string`：`audit-<today>-full` / `audit-<today>-<s10-s13>`（task 去掉 `AUD-`、小写、`-` 连接，最多 4 个，多于 4 个用 `-<n>tasks`）；重名时加 `-2`、`-3`（`existing: string[]` 第四个参数）。

- [ ] **Step 1: 写失败的测试**：
  - `catalogue`：读 Task 1 的真实 `tasks.json`（`../tasks.json`），37 项；坏 JSON 的临时文件 → 抛错含 `tasks.json`。
  - `runs`：在临时目录建 `a/`（`G3_analysis_x.json`）、`b/`（`G2_S10.json`）、`c/`（只有 `x.prev.json`）、`d/`（`audit-results.json` + `report-bim.html`）、文件 `e.txt` → 列出 a、b、d；`b.partial === true`；`d.hasReports === true`；`a.groups` 为 `["G3"]`；不存在的根目录 → `[]`。
  - `newRunName("2026-10-27", ["AUD-S10","AUD-S13"], false, [])` → `audit-2026-10-27-s10-s13`；全选 → `audit-2026-10-27-full`；6 个 → `audit-2026-10-27-6tasks`；已存在 → `-2`。
- [ ] **Step 2: 运行** → FAIL。**Step 3: 实现。** **Step 4: 运行** → PASS。
- [ ] **Step 5: 提交** `feat: catalogue and run listing`。

### Task 5: 总览读取

**Files:**
- Create: `app/src/overview.ts`、`app/test/overview.test.ts`、`app/test/fixtures/`
- Fixtures（由一个一次性脚本从 `work/model-audit-runs/` 复制并裁剪，脚本放 `model-audit-design/_agent/make_app_fixtures.py`）：
  - `run-full/`：`G3_analysis_s.json`（`audit-2026-10-13-g3` 原样）、`C14_analysis_s.json`（`audit-2026-10-13-s14` 裁成 rooms_included 2 条 PASS + 1 条 FAIL、rooms_pending 1 条）、`G2_analysis_s.json` + `G2_S10.json` + `G2_analysis_s.prev.json`（G2 原样复制三份，`G2_S10.json` 只留 S10 并把 1 条改成 FAIL 以便区分）、`_raw/crops/height_c001.png`（复制）；G3 里 `height_c001` 的 crop 改成 `_raw/crops/height_c001.png`（相对路径），另一条改成 `C:\\Other\\Machine\\crop.png`；`report-bim.html`、`report-ap.html`、`GBP_G3_x.html`（空文件即可）。
  - `run-bad/G4_analysis_bad.json`：内容 `{"checks": [`。
  - `run-empty/`：空文件夹。

**Interfaces:**
- Consumes: `Catalogue`（Task 4）、`resolveInside` / `isInside`（Task 3）。
- Produces:

```ts
type Status = "PASS" | "FAIL" | "UNCLEAR" | "N/A";
type Check = { id: string; task: string; group: string; item: string; object: string;
               expected: string; actual: string; status: Status; cite: string; fix: string };
type Reading = { id: string; group: string; key: string; sheet: string; item: string; value: string;
                 finding: string; confidence: string; note: string; crop: string | null };   // crop: run 内相对路径
type TaskRow = { task: string; tl: string; name: string; groups: string[];
                 counts: Record<Status, number> };
type Overview = { run: string; project: string; groups: string[]; partial: boolean;
                  tasks: TaskRow[]; checks: Check[]; readings: Reading[];
                  inputs: Check[]; warnings: string[];
                  reports: { bim: string | null; ap: string | null; groups: string[] };
                  gate: GateRecord | null;          // Task 6 的类型，已有记录时用来预填
                  counts: { checks: number; fail: number; unclear: number; readings: number } };
readOverview(runsRoot: string, run: string, catalogue: Catalogue): Promise<Overview>
class OverviewError extends Error { file: string }   // message: "<file>: <reason>"
```

  规则：
  - 文件：`C14_analysis_*.json` → G1；`G[2-5]_analysis_*.json` → 整组；`G[2-5]_<tasks>.json`（`tasks.ts` 的 `PARTIAL_NAME` 同款正则 `^([SVA]\d\d|A1)(-([SVA]\d\d|A1))*$`）→ 部分结果；跳过 `*.prev.json`。同组有整组文件就不读部分结果。
  - 状态：`APPLICABLE` → `UNCLEAR`（同 `build_results.STATUS`）；其他未知值 → `UNCLEAR`。
  - G1：`rooms_included` 每间一条，`id = "S14-R<id>"`，`item = "Lighting and ventilation"`，`object = "<name> <number> · <level>"`，`expected = "light ≥ <req_light_sqm> m², vent ≥ <req_vent_sqm> m²"`，`actual = "light <act_light_sqm> m², vent <act_vent_sqm> m²"`，`status` = 房间的 `status`，`cite` = `rule_cite`；`rooms_pending`、`rooms_no_area` 每间一条 UNCLEAR，`fix` = `classification_reason`（无则 `"Room has no area"`）。
  - `inputs` = `id` 以 `-INPUT` 结尾的检查（它们同时留在 `checks` 里）；`warnings` = 各组 `summary.data_quality_warnings`。
  - 读数 `id = "<group>:<key>"`；`crop`：相对路径按 run 解析，绝对路径在 run 内则转成相对；文件不存在或在 run 外 → `null`。
  - `tasks` 按 catalogue 顺序，只列有检查的任务；`counts` 四种状态都有键。
  - 报告：run 根下的 `report-bim.html`、`report-ap.html`；`GBP_*.html`（根下和 `assets/` 下）。
  - 已有 `gate-confirmation.json` 就读进 `gate`（坏文件 → `OverviewError`）。

- [ ] **Step 1: 写一次性脚本并生成 fixtures**；提交前人工看一眼 `run-full/` 大小（应小于 500 KB）。
- [ ] **Step 2: 写失败的测试** `overview.test.ts`：
  - `reads G1 and G3`：`groups` 含 G1、G2、G3；S14 有 3 条 PASS/FAIL + 1 条 UNCLEAR；G3 `AUD-S02` counts = `{PASS: 7, FAIL: 1, UNCLEAR: 1, "N/A": 0}`（同 `summary.per_task`）。
  - `full group file wins over partial and prev`：S10 的 counts 等于整组文件里的值，不受 `G2_S10.json` 改动影响；G2 检查数等于整组文件 `checks` 长度。
  - `partial only run`：只放 `G2_S10.json` 的临时 run → `partial === true`，只有 `AUD-S10`。
  - `crop outside the run is treated as missing`：`C:\Other\Machine\crop.png` 那条 `crop === null`；`height_c001` 的 `crop === "_raw/crops/height_c001.png"`。
  - `readings keyed by group`：所有 `id` 以 `G3:` 开头，且唯一。
  - `inputs and warnings`：`warnings` 含 G3 的两条；`inputs` 只含 `-INPUT` 检查。
  - `reports`：`bim`、`ap` 非 null，`groups` 含 `GBP_G3_x.html`。
  - `bad json names the file`：`run-bad` → `OverviewError`，`message` 含 `G4_analysis_bad.json`。
  - `empty run`：`run-empty` → `checks` 为空、`groups` 为空，不抛错。
  - `run outside root`：`readOverview(root, "../x", c)` → `PathError`。
- [ ] **Step 3: 运行** → FAIL。**Step 4: 实现。** **Step 5: 运行** → PASS。
- [ ] **Step 6: 提交** `feat: read one audit run for the overview`。

### Task 6: 写确认记录

**Files:**
- Create: `app/src/gate.ts`、`app/test/gate.test.ts`

**Interfaces:**
- Consumes: `readOverview`（Task 5）。
- Produces:

```ts
type Mark = "ok" | "wrong" | "none";
type GateMode = "confirmed" | "unreviewed";
type GateRecord = { mode: GateMode; saved: string;
                    readings: { id: string; group: string; key: string; sheet: string; item: string;
                                value: string; mark: Mark; note: string }[] };
saveGate(runsRoot: string, run: string, catalogue: Catalogue,
         marks: Record<string, { mark: Mark; note?: string }>, mode: GateMode,
         now?: () => Date): Promise<{ path: string; record: GateRecord }>
class GateError extends Error {}
```

  规则：读数列表取磁盘上当前的 `readOverview(...).readings`；`marks` 里没有的读数记 `none`；不认识的 `id` 忽略；`confirmed` 要求每条都是 `ok`，否则抛 `GateError("<n> readings are not marked ok: <ids>")`；`unreviewed` 不限；先写 `gate-confirmation.json.tmp` 再改名。

- [ ] **Step 1: 写失败的测试**（每个测试先把 `run-full` 复制到临时目录）：
  - `confirmed writes all ok`：全标 ok → 文件存在，`mode == "confirmed"`，条数 = 读数数，`saved` = 注入的时间。
  - `confirmed is rejected when a current reading has no ok mark`：少标一条 → `GateError`，文件不存在。
  - `unreviewed keeps none and wrong`：一条 wrong + note → 记录里该条 `mark == "wrong"`、`note` 保留，其余 `none`。
  - `marks are keyed by group and key`：给 `"G4:height_c001"`（不存在的组）→ 被忽略，`G3:height_c001` 仍是 `none`。
  - `overview reads the saved gate`：保存后 `readOverview(...).gate.mode == "unreviewed"`。
  - `no tmp file left`：保存后目录里没有 `.tmp`。
- [ ] **Step 2–4**：运行 FAIL → 实现 → PASS。
- [ ] **Step 5: 提交** `feat: save the gate confirmation`。

### Task 7: 四个工具

**Files:**
- Modify: `app/src/app.ts`
- Create: `app/test/tools.test.ts`

**Interfaces:**
- Consumes: Task 3–6 的全部函数。
- Produces（工具名、参数、`structuredContent`）：
  - `choose_checks()`，`_meta.ui.resourceUri`，描述 `"[MCP Apps] Opens the GBP Model Audit window to choose which checks to run."` → `{ view: "choose", catalogue, runs: RunInfo[], runsRoot, packageRoot, today: "YYYY-MM-DD", suggested: newRunName(today, [], true, existing) }`。
  - `show_overview({ run: string })`，`_meta.ui.resourceUri`，描述 `"[MCP Apps] Shows the results of one audit run for review before the reports are built, and the report links afterwards."` → `{ view: "overview", overview, runsRoot }`；`OverviewError` / `PathError` → `{ view: "overview", error: message }`，`isError: true`。
  - `get_crop({ run, file })`，`_meta.ui.visibility: ["app"]` → `{ mime: "image/png"|"image/jpeg", base64 }`；只允许 `.png` `.jpg` `.jpeg`、≤ 5 MB、在 run 内，否则 `isError` + 英文原因。
  - `save_gate({ run, marks, mode })`，`_meta.ui.visibility: ["app"]` → `{ path, record }`；`GateError` → `isError` + 原因。
- [ ] **Step 1: 写失败的测试**：用 SDK 的 `InMemoryTransport` 连 `Client` 和 server（`runsRoot` 指 fixtures）：
  - `lists four tools`；`choose_checks` 和 `show_overview` 带 `resourceUri`，`get_crop`、`save_gate` 带 `visibility: ["app"]`。
  - `show_overview returns the overview`（`run-full`）；`show_overview on a bad run returns isError with the file name`。
  - `get_crop returns base64 png`；`get_crop rejects a .json`；`get_crop rejects ../`。
  - `save_gate confirmed with missing marks is an error`。
  - `ui resource is served`：`resources/read` 能读到 `resourceUri`，mime 为 `RESOURCE_MIME_TYPE`。
- [ ] **Step 2–4**：FAIL → 实现 → PASS。
- [ ] **Step 5: 提交** `feat: gbp-audit tools`。

### Task 8: 发给对话的指令和勾选逻辑（纯函数）

**Files:**
- Create: `app/app/logic/prompts.ts`、`app/app/logic/selection.ts`、`app/test/prompts.test.ts`、`app/test/selection.test.ts`

**Interfaces:**
- Produces:
  - `selection.ts`：`toggleTask(sel: Set<string>, task: string): Set<string>`；`toggleGroup(sel, catalogue, group): Set<string>`（整组已全选则全取消，否则全选）；`groupsFor(sel, catalogue): string[]`（按 G1–G5 顺序）；`groupState(sel, catalogue, group): "all" | "some" | "none"`。
  - `prompts.ts`（全部英文，原文如下，`<…>` 为替换值）：
    - `runPrompt({ tasks, groups, runDir, mode: "new" | "merge", all })`：
      - new + all：`Run a full Model Audit on the open model. Follow model-audit/RUN.md §6b. Read-only. Run folder: <runDir>. Put every group's analysis JSON in that folder. After the analysis, call show_overview with run "<run name>" and wait for my confirmation before building the reports.`
      - new + 部分：`Run these Model Audit tasks on the open model: <S10, S13> (groups <G2>). Follow model-audit/RUN.md §6c: extract only what each group table lists, run each group's analyser with --tasks. Read-only. Run folder: <runDir>. After the analysis, call show_overview with run "<run name>" and wait for my confirmation before building the reports.`
      - merge：同部分，加一句 `Merge the results into the existing audit in that folder with build_results.py --update (RUN.md §6c step 4).`
    - `confirmPrompt(run)`：`Gate confirmed for run "<run>" (gate-confirmation.json saved). Build the reports per RUN.md §6b steps 3-4, then call show_overview with run "<run>" again.`
    - `rereadPrompt(run, wrong: { id, sheet, item, note }[])`：`These readings in run "<run>" were marked wrong:` + 每条一行 `- <id> (<sheet>, <item>): <note 或 "no note">` + `Re-read them from the sheets, re-run the analysis for the affected groups, then call show_overview with run "<run>" again.`
    - `unreviewedPrompt(run, unchecked: number)`：`Build the reports for run "<run>" without a full reading review (<n> readings not checked; recorded in gate-confirmation.json). Follow RUN.md §6b steps 3-4, then call show_overview with run "<run>" again.`
- [ ] **Step 1: 写失败的测试**：上面每个函数至少一例，断言完整文本；`groupsFor` 对 `AUD-V08` → `["G3","G4"]`；`toggleGroup` 两次回到空；`groupState` 三态；`rereadPrompt` 空 note 写 `no note`；run 名含引号时原样放进引号内（不转义，对话是纯文本）。
- [ ] **Step 2–4**：FAIL → 实现 → PASS。
- [ ] **Step 5: 提交** `feat: window prompts and selection logic`。

### Task 9: 窗口 ①「Choose checks」

**Files:**
- Modify: `app/app/app.html`、`app/app/main.ts`、`app/dev/harness.html`
- Create: `app/app/choose.ts`

**Interfaces:**
- Consumes: Task 7 的 `choose_checks` 结果；Task 8 的 `selection` / `prompts`。
- Produces: `main.ts` 的 `ontoolresult` 按 `structuredContent.view` 分派到 `renderChoose(data)` / `renderOverview(data)`（Task 10）；`sendToChat(text: string): Promise<void>`：`app.getHostCapabilities()?.message` 有则 `app.sendMessage({ role: "user", content: [{ type: "text", text }] })`，否则或失败时在 `.dock` 上方显示指令文本框 + `Copy` 按钮（`navigator.clipboard.writeText`，失败时选中文本）。

界面（英文原文）：
- 标题 `GBP Model Audit`，副标题 `Choose checks`；`.stats`：`37 tasks`、`<n> selected`、`<n> groups`。
- `.tabs`：`01 Lighting and ventilation` … `05 Lists and model health`（取 catalogue 组名）；每页表格列：勾选框、`TL`、`Task`、`Clause`；跨组任务行尾 `.chip`：`Also in G4`。每页表头 `Select group`。`.toolbar .search`：placeholder `Search by number or name`。
- 运行方式：单选 `New audit`（显示 `Folder: <suggested>`）/ `Add to an existing audit`（下拉 `runs`；没有时该项禁用，提示 `No earlier audits in <runsRoot>`）。
- `.dock`：`.db.pri` `Run <n> checks`（n = 0 时禁用）；次要 `Clear`。
- 点运行 → `sendToChat(runPrompt(...))`；成功后按钮变 `Sent` 并禁用，状态行 `Sent to the chat. The agent will open the overview when the analysis is done.`
- `createModelContext`：已选任务、运行方式、run 名。

- [ ] **Step 1: 改 `harness.html`**：模拟 `choose_checks`（返回 `../tasks.json` 的内容 + 两个假 run）、`show_overview`、`get_crop`、`save_gate`；`ui/message` 记入 `window.messages`；URL 参数 `?nomessage=1` 时 host capabilities 不含 `message`。
- [ ] **Step 2: 实现** `choose.ts`、`main.ts` 分派、`app.html` 结构。
- [ ] **Step 3: 验证**：`npm test`、`npm run build`、`ultraviolet-mcp-app` skill §5 的 UI typecheck 命令（对 `app/main.ts`）。
- [ ] **Step 4: 模拟宿主场景**（浅色、深色各一遍，每个场景一次 `javascript_exec`，每步后重新查询元素）：加载显示 37 项；搜索 `S10`；勾 `AUD-V08` 后 G3、G4 两页都勾上，`Also in G4` 可见；`Select group` 全选 / 全取消；`Run` 后 `window.messages[0]` 等于 `runPrompt` 的完整文本；`Add to an existing audit` 选一个 run 后文本含 `--update`；`?nomessage=1` 时出现 `Copy`；值里有 `<b>` 的任务名被转义；主题切换；`window.lastContext` 含已选任务。两种主题各截一张图。
- [ ] **Step 5: 提交** `feat: choose checks window`。

### Task 10: 窗口 ② / ③「Overview」

**Files:**
- Create: `app/app/overview.ts`
- Modify: `app/app/app.html`、`app/app/main.ts`、`app/dev/harness.html`（`show_overview` 返回 fixtures 里 `run-full` 的 `readOverview` 结果，用 `npm run fixture:overview` 生成的 JSON；在 `package.json` 加此脚本，调用 `build/` 里的 `readOverview`）

**Interfaces:**
- Consumes: `show_overview` 结果（Task 7）；`get_crop`、`save_gate`（`app.callServerTool`）；`prompts`（Task 8）；`sendToChat`（Task 9）。

界面（英文原文）：
- 副标题 `Review` （有报告时 `Reports ready`）；`.stats`：`<n> checks`、`<n> fail`、`<n> to check yourself`（= UNCLEAR 数）、`<n> readings to review`。
- `01 Tasks`：每行 TL、任务名、`PASS/FAIL/UNCLEAR/N/A` 计数（mono），点开列出检查：`Item`、`Object`、`Expected`、`Actual`、`Clause`、状态；UNCLEAR 行带 `.sig` 和 `Check this yourself: <fix>`（`fix` 空时 `Check this yourself.`）。默认只展开有 FAIL 或 UNCLEAR 的任务。
- `02 Readings`：每条一张卡：截图（进入该页时按需 `get_crop`，失败或 `crop === null` 显示 `No crop`）、`Value`、`Sheet`、`Finding`、`Confidence`、`Note`；两个切换按钮 `Correct` / `Wrong`；选 `Wrong` 出现输入框 placeholder `What is wrong (optional)`。已有 `gate` 时按其标记预填。没有读数时 `.empty`：`No sheet readings in this run.`
- `03 Data issues`：`inputs`（`<task>: <actual>` + `How to fix: <fix>`）和 `warnings`；都为空时 `.empty`：`No missing inputs or data warnings.`
- `04 Reports`（只有 `reports.bim` 或 `reports.ap` 存在时出现）：每个报告一行，路径（mono）、`Open`（`app.openLink({ url: file:///… })`，宿主无 `openLinks` 或失败时隐藏）、`Copy path`。
- `.dock`：
  - 全部 `Correct`：`.db.pri` `Confirm and build reports` → `save_gate(confirmed)` → `sendToChat(confirmPrompt)`。
  - 有 `Wrong`：`.db.pri` `Send back for re-reading` → `sendToChat(rereadPrompt)`（不写确认记录）。
  - 其余（有未标记）：`.db.pri` 禁用，文字 `Mark every reading to confirm (<n> left)`。
  - 次要按钮（总在）：`Build reports without full review` → `save_gate(unreviewed)` → `sendToChat(unreviewedPrompt)`；按钮旁说明 `The reports will list the readings nobody checked.`
  - 有报告时（窗口 ③）：dock 只留 `Copy report paths`。
- `save_gate` 失败：标记保留，状态行 `.sig.danger` 显示错误，按钮可再点。
- `error` 结果：整窗 `.empty`：`Could not read this run: <error>`。
- `createModelContext`：当前分页、各读数标记数、按下的按钮。

- [ ] **Step 1: 实现** `overview.ts`、`main.ts` 分派、harness 的 `show_overview` / `get_crop` / `save_gate`（`?gatefail=1` 时 `save_gate` 返回 `isError`）。
- [ ] **Step 2: 验证**：`npm test`、`npm run build`、UI typecheck。
- [ ] **Step 3: 模拟宿主场景**（两种主题）：统计数字等于 fixtures；`AUD-S02` 展开后 UNCLEAR 行显示 `Check this yourself:`；`02 Readings` 有截图的显示图片、外机路径那条显示 `No crop`；全部 `Correct` → 主按钮 `Confirm and build reports`，点后 `window.calls` 有 `save_gate` mode `confirmed`、`window.messages` 末条等于 `confirmPrompt`；一条 `Wrong` + 说明 → 主按钮变 `Send back for re-reading`，消息含说明；未标完 → 主按钮禁用并显示剩余数；`Build reports without full review` → `save_gate` mode `unreviewed`；`?gatefail=1` → 标记仍在、显示错误；`error` 结果 → 整窗错误；有报告时出现 `04 Reports`；读数值含 `<script>` 被转义；`window.lastContext`。各截一张图。
- [ ] **Step 4: 提交** `feat: overview window`。

### Task 11: 文档与接入

**Files:**
- Create: `app/README.md`
- Modify: `work/model-audit/RUN.md`（加 §6d）、`work/model-audit/skills/gbp-model-audit/SKILL.md`、`work/model-audit/README.md`、`work/README.md`（目录表一行）

内容（英文写 `app/README.md`；RUN.md / SKILL.md 随原文语言）：
- `app/README.md`：用途（一段）；`npm install`、`npm run build`；在 Claude Code（项目 `.mcp.json` 或 `~/.claude.json`）、Claude 桌面版、Cursor 的注册 JSON，`args` 为 `build/index.js` 的绝对路径和可选 `--runs <dir>`；改了 UI 要重连 server；隐私：不连 Revit、不上网。
- RUN.md §6d：有 `choose_checks` 工具时，操作者说「做 GBP 审核」→ 先调 `choose_checks`，按窗口发来的指令执行；分析完调 `show_overview(run)` 并停下等窗口的确认；收到确认后出报告，再调 `show_overview(run)`。所有组的分析 JSON 放在同一个审核文件夹。没有窗口时照 §6b / §6c / §7。
- SKILL.md：同上一句话版本，指向 RUN.md §6d。
- README：要求一节加「Node.js ≥ 20（仅对话窗口需要）」。

- [ ] **Step 1: 写文档。**
- [ ] **Step 2: 验证**：`python -I check_package.py` 全 PASS；`_agent` 下全部 `test_*.py` 通过（155 + Task 1、2 的 11 个）；`app/` 下 `npm test` 通过。
- [ ] **Step 3: 端到端（需操作者）**：在 Claude Code 注册 `gbp-audit`，重开会话；请操作者说「做 GBP 审核」，确认窗口弹出、选 1 个任务后指令进到对话；用现有 `audit-2026-10-13-g3` 调 `show_overview`，确认总览显示和 `Copy` / `sendMessage` 的实际表现。结果（含 §9 三个 GAP 的答案）记进 `model-audit-design/_agent/progress.md`。
- [ ] **Step 4: 提交** `docs: chat window for the Model Audit`。
