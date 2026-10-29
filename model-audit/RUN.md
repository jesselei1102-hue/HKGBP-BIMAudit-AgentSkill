# RUN · Model Audit 运行规则

给运行审核的 Agent 读。任何 harness 通用。先读 [README](README.md) 的「前提」。

## 1. 开始前

0. **Skills（每次开始时检查一次）**：当前 harness 支持 `SKILL.md`（Claude Code、Cursor、Codex、Hermes 等）时，看它的项目级 Skill 目录（README「Skills」一节的表；Cursor 用项目根的 `.cursor/skills/`）里有没有本包 `skills/` 下的 6 个文件夹。
   - 没有，或文件与本包的不一致：把这 6 个文件夹原样复制过去（覆盖同名文件夹，不改内容，不动目录里的其他 Skill）。
   - 复制后列出目录确认 6 个 `SKILL.md` 都在，并告诉操作者：装了 / 更新了哪些；要新开对话才生效；本次对话照常按 RUN.md 执行。
   - harness 不支持 Skill，或操作者说不装：跳过，不影响审核。
   - 这一步只写项目里的 Skill 目录，不碰模型。
1. 确认打开的模型：文件名、路径；记下会话标识（如进程 ID）。确认是**副本或可只读的文件**，不是要交付的中心文件。
2. 确认这是**只读审核**。本包对模型不包含任何写入步骤（第 0 步装 Skill 只写项目文件夹）。
3. 选对照表：在 [L4-Capabilities/](L4-Capabilities/) 找当前 MCP 的 `CAP-binding-*`。
   - **当前 MCP 没有对照表**：停下来，告诉操作者。先按 [CAP-onboarding](L4-Capabilities/CAP-onboarding.md) 为它做对照表和 `L3-SOP/SOP-AUD-mcp-*`，再开始。不要拿别的 MCP 的工具名硬套。
4. 检查前提：法例原文（`../Legislation/`）、代码执行能力。缺哪项，按 README 的「没有时」处理，并写进报告的 Not determinable。
5. 读 [AUD-000](L2-Task-Logic/AUD-000_Audit_Flow.md)，向操作者收集或确认「项目输入清单」（INP-01 至 INP-17）里已有的项。

## 2. 顺序

1. A1：[AUD-A1](L2-Task-Logic/AUD-A1_Model_Health.md)（MA-1 至 MA-7）。
2. 36 个 Task 的 L1：Views → Schedules → Assembly（A04 最后）。
3. 能判的 L2：有原文限值、有项目资料的。
4. [AUD-A04](L2-Task-Logic/Assembly/AUD-A04_Submission_Validation.md) 汇总。
5. 写结果、生成报告（第 6 节）。

共用同一组数据的 Task（例：V10 / S08 / S05 / S07；V07 / S06；V12 / S15；S09 / S17；V03 / V04；V13 / S14）一次读取、交叉校验。

## 3. 判定规则

- 状态词只用：Pass / Partial / Fail / Missing / N/A（附条件）/ N/A 待声明 / Unclear（L2 没有限值时用 Not judged）。
- Unclear 不算 Pass；Missing 不算 Present。
- L1、L2 分开判，不互相抵消。
- 适用性只按 [DK-AUD-003](L1-Domain/DK-AUD-003_Applicability.md)；N/A 用其理由句，并带「AP 确认」条件。
- AP 未决定的口径：两个都算，并列写出，不替 AP 选。
- 限值只引 [DK-AUD-002](L1-Domain/DK-AUD-002_Limits_Index.md) 的 `LIM-nn`，并以原文为准；转述文件与原文冲突时，用原文并指出（[DK-AUD-005](L1-Domain/DK-AUD-005_Errata.md)）。
- 工具读不到的，记 Unclear，引 [CAP-gaps](L4-Capabilities/CAP-gaps.md) 的 `GAP-nn`，并按其人工补法建议操作者抽查。

## 4. 证据规则

- 每条结论：元素 / 视图 / 图纸 ID、数值（单位，面积三位小数）、条文、标签（FACT / INFERENCE / GAP）、会推翻的情况。
- 每个 Fail / Partial 的检查项至少一张证据（视图或图纸导出、裁切放大、取色对比）。明细表不能导出图像时，用整张图纸导出。
- 颜色只按像素取样判，不目测。
- 文字字段（evidence、caption、note）**不要写元素 ID**，ID 放进 `element_ids` / `element_id` 字段。AP 版会去掉这些字段，并兜底遮掉文字里的 ID。
- 只给内部看的检查项、修改方向、截图，标 `"audience": "bim"`。

## 5. 安全

- 只读。不删除、不修改、不新建任何模型元素或视图，也不「顺手修」。
- 查到要修的，写成 `fix`，并标修改方式：manual / function-b / AP / external。
- 不确定的就写不确定，不编数值、不编出处。

## 6. 产出

在审核文件夹（例：`audit-<date>/`）里：

1. `assets/`：截图等证据。文件名 `<task>-<序号>-<kind>.png`；宽度不超过 1600 px。
2. `audit-results.json`：按 [audit-results.schema.json](templates/audit-results.schema.json)；findings 按 [finding.schema.json](templates/finding.schema.json)。
3. 两份报告：

   ```
   python "Model Audit/report/render_report.py" --results audit-<date>/audit-results.json --audience bim --out audit-<date>/report-bim.html
   python "Model Audit/report/render_report.py" --results audit-<date>/audit-results.json --audience ap  --out audit-<date>/report-ap.html
   ```

   - exit 2：数据不合格，按 `INVALID` 行改 JSON 再生成。
   - exit 3：缺截图，补上或删去该证据。
   - 不能执行 Python：按 [report-template.html](templates/report-template.html) 手填两份，`meta.filled_by = "template"`。
4. Excel 问题清单（一行一个对象：Revit ID、所在图纸 / 视图、修改方向、给 agent 的一句话）：

   ```
   python "Model Audit/report/issue_list.py" --results audit-<date>/audit-results.json --out audit-<date>/issues.xlsx
   ```

5. 只出操作者选的输出（窗口指令里写明；没说就三份都出）。
6. 回复操作者：结论（能否原样提交）、Blocker 清单、要 AP 决定的事、要提供的资料、各份输出的路径。

## 6b. 逐组执行（两段式）

1. 按 L3 配方 R-S14、R-G2、R-G3、R-G4、R-G5 提取，存进各组 `_raw/`；MCP 回传太大时原样存档再解析，不手抄。
2. 依次跑 G1 → G2 → G3 → G4 → G5（后组读前组的 JSON），每组看屏幕摘要；规则有疑问就在这里停下问操作者。摘要末尾的「Readings to check」不用停下核对：报告把每条读数列为未经人工核对（not checked by a person），附裁切图（读图判断是全流程最弱的一环，所以一定要列）。
3. 每组出报告：`tools/s14_lv/report.py`（G1）或 `tools/common/task_report.py`（G2–G5）。
4. 汇总：`python tools/common/build_results.py --out <run>/audit-results.json … --s14 … --group <JSON> <目录> …`。它按各组 `_raw/` 的提取表补上每个对象的 Revit ID（`tools/common/resolve_ids.py`），写出问题清单（`issues`，每个对象一行）与图纸读数（`readings`）。再按 §6 出所选输出：`report/render_report.py` 的 bim / ap 两份报告、`report/issue_list.py` 的 Excel 问题清单；总报告的证据链接各组 Excel / HTML。
5. 范例：`work/model-audit-runs/audit-2026-10-13-full/`（36 个 Task + A1）。

## 6c. 按 Task 单独跑

规则见 [AUD-000 §10.4](L2-Task-Logic/AUD-000_Audit_Flow.md)。步骤（以 S10 为例）：

1. 查 S10 属哪组、最少提取哪几步：任务卡 §9 末行 → G2「按 Task 单独跑」表。只做那几步提取。
2. 分析：`python "Model Audit/tools/room_use/analyze.py" --raw <run>/_raw … --out <run>/G2_S10.json --tasks S10`。看屏幕摘要；有 `S10-INPUT` 就照它补提取，或告诉操作者哪项没判，然后接着做。
3. 报告：`python "Model Audit/tools/common/task_report.py" --analysis <run>/G2_S10.json --outdir <run>`（文件名 `GBP_G2_S10_…`）。
4. 已有整次审核时并回去：`build_results.py` 用上次的全部参数，再加 `--update <run>/G2_S10.json`（`--group` 里要有 G2 的完整 JSON）；然后重出所选输出（§6）。只有 S10 的结果会变。
5. S14 本身就是一组（G1），单独跑即 R-S14 + `tools/s14_lv/`，并回时给 `--s14` 新的 audit-results.json。

## 6d. 用对话窗口（有 `gbp-audit` 工具时）

`app/` 是一个可选的 MCP server（见 [app/README.md](app/README.md)），在对话里弹出一个窗口，只用来选：检查哪些 Task、要哪些输出、结果放哪个审核文件夹。有 `choose_checks` 工具时：

1. 操作者要做 GBP 审核 → 先调 `choose_checks`，等窗口发来的指令，照指令执行（§6b 整套 / §6c 部分 Task；并入已有审核时用 `build_results.py --update`）。
2. 所有组的分析 JSON 放在指令写的审核文件夹。分析完直接汇总、出指令里列的输出（§6 第 3–5 步），不再回窗口确认：没有确认关口，读数在报告里列为未经人工核对。
3. 回复操作者结论和各份输出的路径。操作者要打开报告时由 agent 打开（Windows：`start "" "<路径>"`；macOS：`open "<路径>"`），只开审核文件夹里的文件。
4. 没有窗口时照 §6b / §6c / §7，输出默认三份都出。

## 7. 短 Prompt

- **整套审核**：「Run a full Model Audit on the open model. Follow `Model Audit/RUN.md`. Read-only. Produce `audit-<date>/` with audit-results.json, assets and both reports.」
- **一组**：「Run group G3 (area schemes) on the open model. Follow `Model Audit/RUN.md` §6b and `L2-Task-Logic/Groups/G3_Area_Scheme.md`. Read-only. Show me the on-screen summary before the report.」
- **单个 Task**：「Audit AUD-S10 only on the open model. Follow `Model Audit/RUN.md` §6c: extract only what the G2 table lists for S10, run the G2 analyser with `--tasks S10`, show me the summary, then merge it into the current audit-results.json with `--update` and re-render both reports. Read-only.」
- **回归**：「Run a regression against `audit-<previous date>/audit-results.json`. Follow `Model Audit/RUN.md` and `L2-Task-Logic/AUD-REG_Regression.md`. Read-only. Fill the regression block and render both reports.」
