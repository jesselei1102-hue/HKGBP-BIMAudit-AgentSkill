# CAP-gaps · 能力缺口（功能 A，revit-mcp）

Layer 4。每个缺口写：影响哪些检查、后果、人工补法。按规则，工具读不到的信息记 Unclear / `[GAP]`，不推断成 Pass（[AUD-000](../L2-Task-Logic/AUD-000_Audit_Flow.md) §7 规则 5）。

| ID | 缺口 | 影响的检查 | 后果 | 人工补法 |
| --- | --- | --- | --- | --- |
| GAP-01 | 读不到尺寸的覆盖值（Replace With Text） | MA-3.1、GEN-02、A04-L2；所有含尺寸的 V 系列 | §5.1.2「禁止手打尺寸」只能查到图片表，查不到改过的尺寸；A04 只能写「未发现」 | [手改尺寸抽查](../L3-SOP/SOP-AUD-manual.md#man-dim-override) |
| GAP-02 | 读不到面积边界线的端点几何 | MA-4.3、V09–V12、V10-L7、A04-L3 | 只能抓面积为 0 的未闭合面积；小缝隙、重叠、隐藏边界查不出。这类问题会被直接退件 | [边界缝隙检查](../L3-SOP/SOP-AUD-manual.md#man-area-gaps)；或 BD BIM Area Tool |
| GAP-03 | 查不到 CAD 导入 / 链接（ImportInstance） | MA-1.5、MA-3.4、V05、A03-L4 | CAD 详图、外部依赖可能漏看；V05 不能直接判 Missing | [CAD 导入检查](../L3-SOP/SOP-AUD-manual.md#man-cad-import) |
| GAP-04 | 不回传 Revit 版本；无法判插件依赖（版本部分：harness 能读模型文件时由 AGENT-FILE-INFO 补上，2026-10-13 实测 Format 2027） | MA-1.1、MA-1.6、A03-L3、A03-L6 | 只能从文件名推断，记 `[INFERENCE]` | [版本检查](../L3-SOP/SOP-AUD-manual.md#man-version) |
| GAP-05 | 没有 LOD 判据 | MA-3.3 | 只能不判，或人工抽查后记结论 | [LOD 抽查](../L3-SOP/SOP-AUD-manual.md#man-lod) |
| GAP-07 | MCP 不回传开口（窗、幕墙嵌板）所属房间 | S14-C、V13-C1、V13-C2 | 已由 AGENT-GEOMETRY 补上（`tools/s14_lv/analyze.py`，每条带 match_method / match_confidence）。仍缺：① reg 31「面向室外」的街道 / 矩形水平面检查（要地界、邻楼几何）；② 百叶净通风面积；③ 嵌板顶高按每组一个样本 | ① 人工按 V13 图核对；② 向 AP 取百叶资料（INP-17）；③ 有疑问的组补取包围盒 |
| GAP-06 | 明细表不能导出图像，只能 CSV | GEN-01、GEN-06、报告截图 | 「表在图上的样子」要导出整张图纸看；报告里的表截图用图纸截图代替 | 导出整张图纸 PNG（[SOP-AUD-mcp-revit-mcp §6](../L3-SOP/SOP-AUD-mcp-revit-mcp.md)） |

## 不算缺口、但会限制 L2 的

- 法例 / PNAP 原文缺失：见 [DK-AUD-006](../L1-Domain/DK-AUD-006_Missing_Sources.md)。
- 项目资料与 AP 决定缺失：见 AUD-000 §6 的 `INP-nn`。

这两类与 MCP 无关，换 MCP 也解决不了。
