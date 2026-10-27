# Model Audit 对话窗口 · 易用性改版 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal**：两个窗口改成「进度条 + 左栏清单 + 右栏内容」；总览变成按类核对的待办清单，选检查窗口点 Run 后说明接下来会发生什么。

**Architecture**：

- 判断逻辑写成纯函数（`app/app/logic/`）：合并分组、核对状态、进度条，各有 vitest。
- `choose.ts`、`overview.ts` 只负责拼 HTML、接事件，调用这些纯函数；用模拟宿主逐个场景验证。
- 确认记录多一项 `reviewed`，Python 端带进结果并写进报告。

**Tech Stack**：TypeScript（vitest、Vite singlefile）、Python 3 标准库（unittest）。

**Spec**：[2026-10-27-audit-app-ux-design.md](2026-10-27-audit-app-ux-design.md)

## Global Constraints

- 窗口文字全部英文；sentence case；不用感叹号。按钮、标签文字照 spec 原文。
- 外观不改：颜色只用 `tokens.css` 变量；每个视图一个 `.db.pri`；插入 HTML 的值都 `escapeHtml`。
- server 读取总览的逻辑、提取与分析脚本、RUN.md 不改。
- 现有 101 个窗口测试与全部 Python 测试照常通过；`check_package.py` 通过。
- 提交信息结尾：`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`；只在本地提交，推送先问操作者。

## Review Focus

1. 某一类数量为 0（例：没有读数、没有不通过）→ 该类自动打勾、显示 `None`，不挡出报告（Task 2 测试 `empty categories are done`）。
2. 同一组里各条的 `fix` 不同 → 全部不同的 fix 都列出，不只取第一条（Task 1 测试 `distinct fixes kept`）。
3. 旧的确认记录没有 `reviewed` → 照常读取，窗口从未勾开始，Python 不报错、报告不出现「没看过」一句（Task 3 测试 `old record without reviewed`）。
4. 窗口窄于 560 px → 左栏变成顶部标签条，内容不被挤成两窄列（Task 6 模拟宿主场景 `narrow`）。
5. 有读数标 Wrong 同时其他类未勾 → 主按钮是 `Send back for re-reading`（Wrong 优先），不是禁用的 `Build reports`（Task 2 测试 `wrong wins`）。

---

## 文件

```
app/app/logic/groups.ts     新：groupChecks
app/app/logic/review.ts     新：reviewState
app/app/ui/steps.ts         新：stepsHtml、navHtml（进度条、左栏 / 标签条）
app/app/choose.ts           改
app/app/overview.ts         改
app/app/gbp.css             改
app/src/types.ts、gate.ts、app.ts   改：reviewed
app/test/groups.test.ts、review.test.ts、steps.test.ts   新
app/test/gate.test.ts、tools.test.ts                     改
tools/common/build_results.py、report/render_report.py、templates/audit-results.schema.json   改
model-audit-design/_agent/test_gate.py                   改
```

---

### Task 1: 合并分组 `groupChecks`

**Files:** Create `app/app/logic/groups.ts`、`app/test/groups.test.ts`

**Interfaces:**
- Consumes: `Check`（`app/src/types.ts`）。
- Produces:

```ts
export type CheckGroup = {
  key: string;            // `${task}|${item}`
  task: string; item: string; status: Status;
  objects: { object: string; actual: string }[];   // 组内每条检查一项，按原顺序
  fixes: string[];        // 组内不同的非空 fix，按首次出现顺序
  checks: Check[];
};
export function groupChecks(checks: Check[], taskOrder: string[]): CheckGroup[];
```

  规则：只按 (task, item) 合并，status 取组内第一条（调用方先按类筛好）；组按 `taskOrder` 里的位置排，同任务内按 item 首次出现顺序。

- [ ] **Step 1: 写失败的测试** `groups.test.ts`：
  - `same task and item merge`：两条 `AUD-V02` / `Door marks on all doors` + 一条 `AUD-V02` / `No grid lines` → 2 组，第一组 `objects.length === 2`。
  - `distinct fixes kept`：组内 fix 为 `a`、`a`、`b`、`""` → `fixes` 为 `["a","b"]`。
  - `order follows the catalogue`：`taskOrder = ["AUD-V01","AUD-V02"]`，输入先 V02 后 V01 → 输出 V01 组在前。
  - `unknown task goes last`：不在 `taskOrder` 的任务排在最后。
- [ ] **Step 2: 运行** `npx vitest run test/groups.test.ts` → FAIL（模块不存在）。
- [ ] **Step 3: 实现** `groupChecks`。
- [ ] **Step 4: 运行** → PASS；全部 `npx vitest run` 通过。
- [ ] **Step 5: 提交** `feat: group checks by task and item for the review list`。

### Task 2: 核对状态 `reviewState`

**Files:** Create `app/app/logic/review.ts`、`app/test/review.test.ts`

**Interfaces:**
- Produces:

```ts
export type Seen = { failures: boolean; check_yourself: boolean; inputs: boolean };
export type ReviewInput = {
  failures: number; checkYourself: number; inputs: number;   // 各类条数（inputs = -INPUT 条数 + 警告数）
  readingsLeft: number; readingsWrong: number;               // 未标、标 Wrong 的读数
  seen: Seen; reportsReady: boolean;
};
export type ReviewState = {
  done: { failures: boolean; check_yourself: boolean; inputs: boolean; readings: boolean };
  doneCount: number;                                          // 0–4
  dock: "partial" | "wrong" | "ready" | "reports";
  label: string;                                              // 底部文字，原文见下
};
export function reviewState(i: ReviewInput): ReviewState;
```

  规则：某类条数为 0 → done；`readings` done ⇔ `readingsLeft === 0 && readingsWrong === 0`（有 Wrong 不算完成）。`dock`：`reportsReady` → `reports`；否则 `readingsWrong > 0` → `wrong`；否则 4 类都 done → `ready`；否则 `partial`。`label`：`partial` → `${doneCount} of 4 reviewed`；`wrong` → `1 reading marked wrong` / `${n} readings marked wrong`；`ready` → `All reviewed`；`reports` → `Reports ready`。

- [ ] **Step 1: 写失败的测试** `review.test.ts`：
  - `partial`：6 / 18 / 3、读数剩 2、seen 全 false → `dock "partial"`、`label "0 of 4 reviewed"`。
  - `ticks count`：seen.failures 与 seen.inputs 为 true、读数剩 0 → `doneCount 3`、`label "3 of 4 reviewed"`。
  - `empty categories are done`：failures 0、checkYourself 0、inputs 0、读数 0 → `dock "ready"`、`label "All reviewed"`。
  - `wrong wins`：readingsWrong 1、其他未勾 → `dock "wrong"`、`label "1 reading marked wrong"`；readingsWrong 2 → `"2 readings marked wrong"`。
  - `reports`：reportsReady → `dock "reports"`、`label "Reports ready"`。
- [ ] **Step 2: 运行** → FAIL。**Step 3: 实现。** **Step 4: 运行** → PASS。
- [ ] **Step 5: 提交** `feat: review state for the guided overview`。

### Task 3: 确认记录加 `reviewed`（server + Python）

**Files:** Modify `app/src/types.ts`、`app/src/gate.ts`、`app/src/app.ts`、`app/test/gate.test.ts`、`app/test/tools.test.ts`、`tools/common/build_results.py`、`report/render_report.py`、`templates/audit-results.schema.json`、`model-audit-design/_agent/test_gate.py`

**Interfaces:**
- Consumes: `Seen`（Task 2）。
- Produces:
  - `GateRecord` 加可选 `reviewed?: Seen`。
  - `saveGate(runsRoot, run, catalogue, marks, mode, now?, reviewed?: Seen)`：有 `reviewed` 就写入记录。
  - `save_gate` 工具参数加可选 `reviewed`（zod：三个 boolean）。
  - Python：`load_gate` 读 `reviewed`，结果 `gate.not_reviewed: list[str]`（值取 `failures`、`check_yourself`、`inputs` 中为 false 的；没有 `reviewed` 时为 `[]`）；schema 加 `not_reviewed`（字符串数组，枚举这三个值）；报告在「Sheet readings」那节加一句 `Not looked at before the reports: <列表>.`（`failures` → `failures`，`check_yourself` → `items to check yourself`，`inputs` → `missing inputs`），列表为空时不出现。

- [ ] **Step 1: 写失败的测试**：
  - `gate.test.ts`：`reviewed is saved`（传 `{failures:true, check_yourself:false, inputs:true}` → 记录里原样）；`old record without reviewed`（不传 → 记录没有 `reviewed`；`readOverview().gate.reviewed` 为 undefined）。
  - `tools.test.ts`：`save_gate accepts reviewed`。
  - `test_gate.py`：`test_not_reviewed_listed`（记录 `reviewed` 中 check_yourself 为 false → `gate.not_reviewed == ["check_yourself"]`，BIM 报告含 `Not looked at before the reports: items to check yourself.`）；`test_old_record_without_reviewed`（`not_reviewed == []`，报告无此句）。
- [ ] **Step 2: 运行** vitest 与 `python -I test_gate.py` → 新测试 FAIL。
- [ ] **Step 3: 实现**（TypeScript 与 Python 两边）。
- [ ] **Step 4: 运行** → 全部通过；`test_render.py`、`test_update.py` 通过。
- [ ] **Step 5: 提交** `feat: record which review lists were looked at`。

### Task 4: 进度条与左栏 `stepsHtml`、`navHtml`

**Files:** Create `app/app/ui/steps.ts`、`app/test/steps.test.ts`；Modify `app/app/gbp.css`

**Interfaces:**
- Produces:

```ts
export function stepsHtml(current: 1 | 2 | 3 | 4): string;
// 四个 <span>：1 Choose / 2 Analyse / 3 Review / 4 Reports；< current 加 class "done"，= current 加 "now"
export type NavItem = { id: string; label: string; count?: string; tone?: "fail" | "unclear" | "muted"; done?: boolean };
export function navHtml(items: NavItem[], selected: string): string;
// <nav class="side">：每项 <button data-nav=id>，含标签、count 徽章（tone 决定 class）、done 时 ✓；选中项 class "sel"
```

  CSS（只用主题变量）：`.steps`（进度条）、`.layout`（两栏 grid：左 34 %、右 1fr）、`.side`（左栏）、`.pane`（右栏）；`@media (max-width: 560px)`：`.layout` 单栏，`.side` 变成横向可换行的标签条。

- [ ] **Step 1: 写失败的测试** `steps.test.ts`：`stepsHtml(3)` 含 `class="done"` 两个、`class="now"` 一个且在 `3 Review` 上；`navHtml` 选中项含 `sel`、`done` 项含 `✓`、label 中的 `<b>` 被转义。
- [ ] **Step 2–4**：FAIL → 实现 → PASS。
- [ ] **Step 5: 提交** `feat: steps bar and side list for the windows`。

### Task 5: 选检查窗口

**Files:** Modify `app/app/choose.ts`、`app/dev/harness.html`（如需）

**Interfaces:** Consumes `stepsHtml(1|2)`、`navHtml`（Task 4）、现有 `selection.ts`、`prompts.ts`、`sendToChat`。

界面（英文原文，spec §3）：
- 左栏：四个章节，`count` = `已选/总数`（有选时 tone 正常、否则 muted）；下面 `Full audit (all 37)`、`Clear` 两个按钮（`data-quick="all"|"clear"`）。
- 右栏：章节名 + 说明（`BIMGBPS §5.2 · drawings on the sheets` 等，取 catalogue `sections[].clause` 加一句：views `drawings on the sheets`、schedules `tables on the sheets`、assembly `sheets, colours and export`、health `the model itself`）+ `Select all <n>` / `Clear section`；搜索框；任务行：勾选框、任务名、小字 `TL-V01 · §5.2.2`（`summary` 去掉 `BIMGBPS ` 前缀）。
- 右栏底部：`Results go to a new audit <name> · ` + 链接 `Add to an earlier audit instead`（点后展开现有下拉与 `Back to a new audit`）。
- 底部：`<n> checks selected · <章节名…>` + `Run <n> checks`。
- 点 Run 成功：窗口换成 spec §3.2 的「接下来」视图（`stepsHtml(2)`、三步卡片、`Instruction sent: "…" Show`、底部 `Waiting for the agent` + 禁用 `Sent`）；宿主拒收：第 2 步文字换成 `Paste the instruction below into the chat to start.`，下面是复制框。

- [ ] **Step 1: 实现**；`npm run build`；UI typecheck（`ultraviolet-mcp-app` skill §5 的命令）。
- [ ] **Step 2: 模拟宿主场景**（浅色、深色）：章节计数随勾选变化；`Full audit` 后底部 `37 checks selected`；`Clear`；跨组任务（V08）勾选后指令含 `G3, G4`；`Add to an earlier audit instead` → 指令含 `--update`；Run 后出现三步卡片和 `Waiting for the agent`；`?nomessage=1` 时出现复制框和 `Paste the instruction below…`；窄窗口（iframe 宽 400 px）标签条。各截一张图。
- [ ] **Step 3: 提交** `feat: guided choose checks window`。

### Task 6: 总览窗口

**Files:** Modify `app/app/overview.ts`、`app/dev/harness.html`（如需）

**Interfaces:** Consumes `groupChecks`（Task 1）、`reviewState`、`Seen`（Task 2）、`saveGate` 的 `reviewed` 参数经 `save_gate`（Task 3）、`stepsHtml`、`navHtml`（Task 4）。

界面（英文原文，spec §4）：
- 左栏项：`failures`、`check_yourself`、`inputs`、`readings`、`all`（`All checks (<n>)`），报告已出时最前面加 `reports` 并默认选中；否则默认选中第一个未完成的项；数量为 0 显示 `None` 且打勾。
- 右栏：每类标题 + 说明句（spec §4.2 原文）+ 右上按钮（failures / inputs：`I've seen these`；check_yourself：`I've checked these`；已勾时显示 `Seen ✓`，可再点取消）。
  - failures、check_yourself：`groupChecks` 的组卡片：徽章数量、`TL-xx`、item；对象行显示前 4 个 `object · actual`，多于 4 个加 `+<n> more`（点开显示全部）；`Fix: …`（failures）/ `Look at: …`（check_yourself，fix 为空时写 `Look at the drawings for this item.`）；点组卡片展开组内明细（预期、实际、条文）。
  - inputs：每条 `-INPUT` 一行（任务、缺什么、`How to fix: …`）+ 数据警告。
  - readings：现有读数卡片；已标的折叠成 `Show the <n> marked ▸`。
  - all：现有按章节的任务表，原样。
  - reports：现有报告列表。
- 底部：按 `reviewState` 的 `dock` 与 `label`（spec §4.3 表）；`Build reports` → `save_gate(confirmed, reviewed)`；`Build without full review` → `save_gate(unreviewed, reviewed)`；`Send back for re-reading` 照现在。
- 已有确认记录且含 `reviewed`：按记录恢复打勾。

- [ ] **Step 1: 实现**；`npm run build`；UI typecheck；`npm run fixture:overview`。
- [ ] **Step 2: 模拟宿主场景**（浅色、深色）：
  - 默认选中 `Failures`，V02 门标记合成一组且对象行显示 4 个；
  - 依次点 `I've seen these`、`I've checked these`、inputs 的按钮，左栏打勾、底部 `3 of 4 reviewed`；
  - 读数全标 Correct 后底部 `All reviewed`、`Build reports` 可点，点后 `window.calls` 里 `save_gate` 带 `reviewed` 三个 true，消息为 `confirmPrompt`；
  - 一条 Wrong → `Send back for re-reading`；
  - `Build without full review` → `mode unreviewed`、`reviewed` 反映实际打勾；
  - `?reports=…` 报告已出 → 左栏 `Reports` 默认选中；
  - `narrow`：iframe 宽 400 px → 标签条、单栏；
  - `?xss=1` 转义；`?error=1` 整窗错误。各截一张图。
- [ ] **Step 3: 提交** `feat: guided review window`。

### Task 7: 收尾

**Files:** Modify `app/README.md`（窗口说明一段）、`RUN.md` 不改

- [ ] **Step 1: 改 README 的窗口说明**（「Choose checks」「Overview」两段改写成新的流程：左栏清单、按类看过、出报告条件）。
- [ ] **Step 2: 全部验证**：`npx vitest run`（含新测试）、全部 `python -I test_*.py`、`python -I check_package.py`。
- [ ] **Step 3: 提交** `docs: describe the guided windows`。
