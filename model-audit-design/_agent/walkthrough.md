# Walkthrough · 只读包内文件，走 A1 与 AUD-S14

规则：不看本次对话、不看 `work/gbp-tasks/`，只用 `work/model-audit/`（并回后的 `Model Audit/`）及其链接到的仓库文件。

## A1（模型健康）

| 步骤 | 在包里哪里找到 | 结果 |
| --- | --- | --- |
| 从哪开始 | README「读取顺序」→ RUN §1 | 找到 |
| 确认 MCP 有对照表 | RUN §1.3 → L4 `CAP-binding-revit-mcp` | 找到 |
| 每个 MA 查什么 | AUD-A1 各表「要取得的信息」「判据」 | 找到 |
| 用 MCP 怎么取 | SOP-AUD-mcp-revit-mcp §1–§3、§4、§5 | MA-3.2、3.5、4.6、6.4、7.1、7.3、7.4 **原来没有** → 已补 §8b |
| 读不到的怎么记 | AUD-A1「盲点」栏 → CAP-gaps → SOP-AUD-manual 锚点 | 找到 |
| 面积明显不合理 | AUD-A1 MA-4「另查」 | **原来没有** → 已补 |
| 标高基准要 AP 决定 | AUD-000 INP 表 | **原来没有** → 已补 INP-16 |
| 记录与报告 | RUN §6 → audit-results.schema.json `a1[]` | 找到 |

## AUD-S14（窗面积）

| 步骤 | 在包里哪里找到 | 结果 |
| --- | --- | --- |
| 适用性 | AUD-S14 §1 → DK-AUD-003 APL-10 | 找到 |
| 限值 | AUD-S14 §4 → DK-AUD-002 LIM-06、07、10（原文摘句在内） | 找到 |
| TL-S14 写 1/8 怎么办 | AUD-S14 §5 → DK-AUD-005 §1 | 找到 |
| 表在哪 | SOP-AUD-mcp §5（图纸 → 视图 / 明细表）、§3（图片表） | 找到 |
| 房间与窗参数 | SOP-AUD-mcp §8（房间预设参数实测；窗 / 嵌板待试） | 找到（待试已标） |
| 证据截图 | RUN §4；SOP-AUD-mcp §6–§7；GAP-06（明细表用整张图纸） | 找到 |
| 结果写法 | RUN §6 → schema `tasks[]`（checks、calcs、evidence_ids、fix） | 找到 |
| 报告 | RUN §6 → render_report.py | 找到 |

## 结论

两条都能只靠包走完。缺的 3 处已补进包：SOP §8b、AUD-A1「面积明显不合理」、INP-16。
