# G4 图面组 · 可执行规格（AUD-V01–V05、V13、A01–A03；V08 / V10 / V11 的图面项）

按 [AUD-000 §10](../AUD-000_Audit_Flow.md) 两段执行。工具：`tools/drawings/analyze.py`（分析）、`tools/drawings/sample_colours.py`（取色）、`tools/drawings/rvt_info.py`（读文件版本）、`tools/common/task_report.py`（报告）。提取配方：[SOP-AUD-mcp-revit-mcp §10 R-G4](../../L3-SOP/SOP-AUD-mcp-revit-mcp.md)。范例：`work/model-audit-runs/audit-2026-10-13-g4/`。

## 1. 数据范围

| 对象 | 能力 | 取什么 |
| --- | --- | --- |
| 图纸上的视图 | CAP-LIST-VIEWS-SHEETS | 每张图纸的视图：id、名称、类型、outline |
| 视图属性 | CAP-QUERY-ELEMENTS | 比例、视图样板、图上标题 |
| 每个视图的计数 | CAP-QUERY-ELEMENTS（视图范围） | 轴网、标高、尺寸、高程点、门 / 门标记、房间 / 房间标记、Area / Area 标记、文字、剖面 / 立面标记 |
| 图框与项目信息 | CAP-PROJECT-CONTEXT | 全部参数（原样保存） |
| 图像 | CAP-EXPORT-IMAGE + AGENT-IMAGE-SAMPLE | 导出图纸 PNG；按区域取 RGB（Table 1、粉红、灰阶占比） |
| 模型文件 | AGENT-FILE-INFO | .rvt 里的 BasicFileInfo：版本、build、协作；同目录其他 .rvt |
| 图面读取 | 读图 | 不能计数的内容（地段号、街道、坐标、标高标头文字）写 `readings.tsv`，带图纸与可信度 |

## 2. 规则

| Task | 检查 | 判 |
| --- | --- | --- |
| V01 | 比例 ≤ 1:500；坐标围成面积 = 地界；坐标表是不是图片；地盘粉红取样；地段号、出入口、北向；指明街道；高程点格式 | 粉红像素占区域 < 20 % → Fail |
| V02 | 每个平面：轴网、尺寸、剖立面标记 > 0；门标记 ÷ 门；房间标记 ÷ 房间；比例 ≤ 1:100；高程点格式（读不到 → UNCLEAR） | 局部平面无轴网 → Fail |
| V03 / V04 | 方向数；每个视图轴网、标高、尺寸；邻街标高（读图，只用于读过的图纸，没读的 → UNCLEAR）；标高标头 X.XXX mPD | 标头写「SFL … m」→ Fail（Major，GEN-04） |
| V05 | 1:50 详图是否在图上；标题有无 TYPICAL / NON-TYPICAL；索引 | 无标题 → Fail |
| V13 | 有无专门规定窗图；C1 / C2 取 S14 结果；C3（reg 31）→ UNCLEAR | — |
| V08 / V10 / V11 | 分区、GFA、UFA 图：尺寸、轴网；半色调（灰阶像素 > 5 %）；分区颜色 | 尺寸 0 → Fail；无半色调 → Fail |
| A01 | 图框数 = 图纸数；图号格式；占位值（XX-XX-2018、Author）；项目名与地址矛盾；BIM 编号版本段 = 文件版本 | Minor |
| A02 | GFA 填色与图例 = Table 1 RGB；平面与 GFA 图两套体系分开；修订色 | 完全相等才 Pass |
| A03 | .rvt；≤ 500 MB；版本 ≥ 2017（文件头）；无 Revit 链接；CAD 导入（GAP-03）；图片表汇总；同目录其他模型 | — |

## 3. 读图规则

同 G3 §3：先整张、再裁切；只对读过的图纸下结论；读不清记 low 并给出怎样补读。

- 判断类读数（街道是否标明指明街道、坐标格式、方位角与边长、修改清单、N/A 表）带 `finding`；没有 → UNCLEAR。Pass 要有裁切图，Fail 要写明看过的图纸；读数写「not read」或可信度 low 视为没读。
- 标高标头按读到的文字判：符合 `X.XXX mPD` → Pass，否则 Fail。
- 取色不给区域框时用整图统计：整张 A001 没有一个粉红像素 → Fail（有粉红 → 需区域框量占比）；C002 的填色与 Table 1 完全相等且没有更多的近似色 → Pass；半色调整图量不准（图片与文字也是灰），→ UNCLEAR，要区域框。
- 链接数来自 `model_counts.json`；没有 → UNCLEAR，不推定为 0。坐标围成面积对 G3 的地界面积（`--g3`）。

## 4. 与其他组的接口

- V13 C1 / C2 ← S14 分析 JSON。
- A03-L7 ← G3 的 Raster Images 清单。
- 标高基准（SFL 读数）→ INP-16、S05 高度口径。

## 5. 按 Task 单独跑

`--tasks`（[AUD-000 §10.4](../AUD-000_Audit_Flow.md)）。最少提取指 R-G4 的步：

| Task | 最少提取 | 依赖其他组 |
| --- | --- | --- |
| V01 | 1–3（只取 A001 的视图）；5–6 取色（可选）；8 读图、坐标（可选） | G3（可选：地界面积） |
| V02–V05 | 1–3（相关图纸）；8 读图（可选） | — |
| V08 / V10 / V11 图面 | 1–3（C005 / C002 / C004）；5–6 取色（可选） | — |
| V13 | 1–3（找规定窗图） | G1 S14（可选：玻璃 / 可开启两项） |
| A01 | 1–4（图框） | — |
| A02 | 1–3；5–6 取色（可选） | — |
| A03 | 7（rvt 文件头）；4 链接数（可选） | G3 rasters（可选） |
