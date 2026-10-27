# 设计文档 · Model Audit 对话窗口 · 易用性改版

日期：2026-10-27  
读者：操作者（香港 BIM Manager）  
状态：待审。审过后再写实施计划，然后动手。  
前一版设计：[2026-10-27-audit-app-design.md](2026-10-27-audit-app-design.md)（功能、工具、数据不变；本文只改窗口怎么组织与引导）。

---

## 1. 要解决什么

操作者反映两个问题：

1. **信息太密**：一打开就是整张表（例：V02 一个任务 38 条检查），重点（不通过、要自己查的）埋在通过项里。
2. **不知道下一步做什么**：选完检查后不知道会发生什么；总览里不知道要做什么才能往下走。

外观（Ultraviolet 主题、颜色、字体）**不改**。窗口文字仍全部英文。

### 1.1 已定的选择（来自你的回答与浏览器选图）

| 问题 | 选择 |
| --- | --- |
| 先改哪个 | Audit app；Revit Schedule app 之后另议 |
| 总览第一眼 | 「你要做的事」清单 |
| 排法 | C：左边清单（带进度），右边显示选中那一项；窗口窄时改成上下排 |
| 什么时候能出报告 | 按类标「看过了」：不通过、需自行检查、缺输入各点一次；读数仍逐条核对。全部完成「Build reports」才亮；「Build without full review」一直可用 |
| 选检查窗口 | 同样左右结构；点 Run 后整个窗口变成「接下来会发生什么」 |

---

## 2. 两个窗口共用的骨架

```
┌ 进度条：1 Choose › 2 Analyse › 3 Review › 4 Reports（当前一步高亮，之前的标完成）
├ 左栏：分类清单（数量 / 进度 / 打勾）
├ 右栏：选中那一类的内容
└ 底部：进度文字 + 一个主按钮（必要时一个次要按钮）
```

- 进度条四步固定；选检查窗口在 1（点 Run 后到 2），总览在 3，报告出来后在 4。
- 窗口宽度不够两栏（< 560 px）时：左栏变成顶部一排可点的标签（`Failures 6`、`Check yourself 18`…），内容在下面。
- 底部仍是现有的 `.dock`，每个视图一个主按钮。

---

## 3. 选检查窗口

### 3.1 选之前

| 位置 | 内容 |
| --- | --- |
| 左栏 | 四个 BIMGBPS 章节：`Views`、`Schedules`、`Assembly & export`、`Model health`，每个显示「已选 / 总数」（例 `3/14`，有选时高亮）；下面两个快捷项 `Full audit (all 37)`、`Clear` |
| 右栏 | 章节名 + 一句说明（例 `BIMGBPS §5.2 · drawings on the sheets`）+ `Select all 14` / `Clear section`；任务列表每行：勾选框、**任务名（主）**、下面一行小字 `TL-V01 · §5.2.2`；搜索框保留在右栏顶部 |
| 右栏底部 | 保存位置一句话：`Results go to a new audit <名称> · Add to an earlier audit instead`；点后者展开现有的已有审核下拉 |
| 底部 | `3 checks selected · Views` + 主按钮 `Run 3 checks` |

### 3.2 点 Run 之后

整个窗口换成「接下来会发生什么」（进度条在 2）：

```
Sent to the agent
3 checks: Block / Key Plan, Floor Plans, Sections

[2 · The agent reads the model and runs the checks]   ← 当前
    Read-only, through the Revit MCP. Follow its progress in the chat.
    Keep Revit open and idle (no dialogs).
[3 · A review window opens in the chat]
    You look at the failures, the items to check yourself and the sheet readings, then confirm.
[4 · Reports]
    BIM team and AP / client editions, in the audit folder.

Instruction sent: "Run these Model Audit tasks …"  [Show]
底部：Waiting for the agent
```

宿主拒收消息时（复制框路径）：第 2 步改为 `Paste the instruction below into the chat to start.`，复制框照现在的做法显示在下面。

---

## 4. 总览窗口（核对）

### 4.1 左栏：待办清单

| 项 | 数量 | 何时打勾 |
| --- | --- | --- |
| `Failures` | 不通过的条数（红） | 右栏点 `I've seen these` |
| `Check yourself` | 待定的条数（不含 `-INPUT`）（紫） | 右栏点 `I've checked these` |
| `Missing inputs` | `-INPUT` 条数 + 数据警告数（灰） | 右栏点 `I've seen these` |
| `Sheet readings` | 还没标的读数 | 每条都标了 Correct / Wrong |
| `All checks (54)` | 全部检查 | 不算待办 |

某类数量为 0：直接打勾，显示 `None`。默认选中第一个还没打勾的项。

### 4.2 右栏：合并显示

- **合并规则**：同一任务（task）+ 同一检查项（item）合成一组。组标题：数量徽章 + `TL-V02` + 检查项名；下面一行列出对象（图纸 / 视图名与实际值的简写，例 `A002 G/F 11/30`；多于 4 个时显示前 4 个和 `+n more`，可展开）；再下一行 `Fix:`（不通过）或 `Look at:`（需自行检查），取该组检查的 `fix`；各条 fix 不同时列出不同的几条。
- 组内排序：按 BIMGBPS 章节与 TL 号；组展开后可看每条的预期、实际、条文（现在的明细行）。
- 每类顶部一句说明：
  - Failures：`Problems in the model. Nothing to do here except note them; fix in Revit later.`
  - Check yourself：`The tool could not decide. Each line says what to look at.`
  - Missing inputs：`Optional data not taken this run. Each line says how to add it.`
  - Sheet readings：`Values read off the sheets. Compare each with its crop.`
- **读数**：沿用现在的卡片（截图、值、Correct / Wrong、Wrong 时写原因）；已标的折叠成 `Show the 59 marked ▸`，只显示还没标的。
- **All checks**：现在的「按任务的表」（章节标题、计数、展开明细），原样保留。

### 4.3 底部与出报告

| 状态 | 底部文字 | 主按钮 | 次要按钮 |
| --- | --- | --- | --- |
| 还有类没打勾 | `2 of 4 reviewed` | `Build reports`（禁用） | `Build without full review` |
| 有读数标 Wrong | `1 reading marked wrong` | `Send back for re-reading` | `Build without full review` |
| 四类都打勾、读数全 Correct | `All reviewed` | `Build reports` | — |
| 报告已出（第 4 步） | `Reports ready` | `Copy report paths` | — |

- `Build reports` 存确认记录时 `mode: "confirmed"`；`Build without full review` 存 `mode: "unreviewed"`。
- **新增**：确认记录加一项 `reviewed: {"failures": true/false, "check_yourself": …, "inputs": …}`，报告在现有「Sheet readings」提醒旁加一句：哪几类在出报告前没有被看过（只有 `unreviewed` 时才可能出现）。
- 打勾状态只存在窗口里；窗口重开时，若已有确认记录就按记录恢复，否则从未勾开始。
- 报告页（第 4 步）：左栏多一项 `Reports`，默认选中；内容同现在（每份报告的路径、`Open`、`Copy path`）。

---

## 5. 改动范围

| 部分 | 改什么 |
| --- | --- |
| `app/app/choose.ts` | 左右结构、章节计数、快捷项、保存位置一句话、Run 后的「接下来」视图 |
| `app/app/overview.ts` | 待办清单、合并分组、按类打勾、底部状态、窄窗口标签 |
| `app/app/logic/`（新增纯函数） | `groupChecks(checks)` 合并分组；`reviewState(...)` 算各类是否完成与底部状态；`stepper(view, state)` 进度条状态 |
| `app/app/gbp.css` | 两栏、标签条、组卡片、进度条（只用主题变量） |
| `app/src/gate.ts`、`app.ts` | `save_gate` 接受并写入 `reviewed` |
| `tools/common/build_results.py`、`report/render_report.py`、schema | 带上 `gate.reviewed`，报告写出没看过的类 |
| 不改 | server 读取总览的逻辑、提取与分析脚本、提示词文字（RUN.md 不变） |

---

## 6. 测试

- vitest：`groupChecks`（同任务同项合并、对象多于 4 个、fix 不同、PASS 不进分组）；`reviewState`（四种底部状态、数量为 0 的类自动打勾、有 Wrong 时）；`stepper`。
- vitest：`save_gate` 写入 `reviewed`；旧记录没有 `reviewed` 时照读。
- Python：报告列出没看过的类；没有 `reviewed` 或全看过时不出现。
- 模拟宿主：浅色 / 深色；宽窗口两栏、窄窗口（< 560 px）标签条；选检查 → Run → 「接下来」视图；总览逐类打勾到 `Build reports` 亮；有 Wrong 时按钮变 `Send back for re-reading`；`Build without full review` 写入 `reviewed`；报告页。
- 现有 101 个窗口测试与全部 Python 测试照常通过。

---

## 7. 不做

- Revit Schedule app（另议）。
- 外观、颜色、字体。
- 进度条显示 agent 的实际进度（窗口拿不到 agent 的进度，只说明「看对话」）。
