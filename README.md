

https://github.com/user-attachments/assets/44fe4baa-0d27-4de4-acd0-5a41e4b6e952

# GBP Model Audit

A read-only audit package for Revit models prepared for a Hong Kong GBP (general building plans) Stage I submission.
It checks the 36 BIMGBPS tasks (TL-S01–S18, TL-V01–V14, TL-A01–A04) and model health (MA-1 to MA-7) through a Revit MCP
server, and writes an English report in two editions (BIM team, AP / client).

香港 GBP 入则 Revit 模型只读审核包：按 BIMGBPS 36 个 Task 与模型健康 MA-1 至 MA-7，通过 Revit MCP 取数，出 BIM 团队版与 AP / 客户版英文报告。

<video src="https://github.com/user-attachments/assets/44fe4baa-0d27-4de4-acd0-5a41e4b6e952" controls width="800"></video>
## Contents

| Folder | What |
| --- | --- |
| [model-audit/](model-audit/) | The package: four layers (L1 domain, L2 task logic, L3 Revit SOP, L4 MCP capabilities), executable tools, report templates and Agent Skills. Start with [model-audit/README.md](model-audit/README.md) and [model-audit/RUN.md](model-audit/RUN.md). |
| [model-audit-design/](model-audit-design/) | Design and plan documents; `_agent/` holds the tests, validation scripts, real-response fixtures and the progress ledger. |

## Requirements

- A Revit model opened in Revit with a Revit MCP server connected to your agent (revit-mcp; mcp-servers-for-revit for element data).
- Python 3 (standard library; Pillow for colour sampling).
- The legislation and BIMGBPS source texts are **not** included; the package expects them next to it (`../Legislation/`, `../source/`) and reports UNCLEAR without them.

## Tests

```
cd model-audit-design/_agent
python -I test_s14.py
```

Each `test_*.py` runs on its own (standard library `unittest`). Tests that compare with the original sample audit runs are
skipped when those runs are not present.

## Status

Validated on one sample model (the BD GBP Revit template). Not yet tried on other projects. Results are an aid to the
BIM / AP review, not a Buildings Department approval.
