# SOP-AUD-manual · 人在 Revit 里怎么取得审核信息

Layer 3（Revit 专属，与 MCP 无关）。按 L2 各 AUD 第 2 节「要取得的信息」分类。两种情况用本文件：

1. 没有接 MCP，人工审核。
2. 接了 MCP，但该信息属 MCP 盲点（L4 [CAP-gaps](../L4-Capabilities/CAP-gaps.md) 的 `GAP-nn`）。

菜单路径以 Revit 2023–2027 为准，版本间可能略有不同 `[INFERENCE]`。

## 1. 项目、单位、文件

| 信息 | 怎么取 | 用于 |
| --- | --- | --- |
| 长度 / 面积单位与精度 | Manage → Project Units：Length、Area、Volume 的单位与 Rounding | MA-2.1、MA-2.2 |
| 文件大小 | 资源管理器看 .rvt 大小；提交前先 File → Purge Unused 再看 | MA-1.3 |
| 中心文件 | Collaborate 选项卡是否显示工作集；File → Save As 时有无 Detach 选项 | MA-1.4 |
| 链接 | Manage → Manage Links：Revit、CAD Formats、Point Clouds 等各页 | MA-1.5 |
| 无关数据 | Visibility / Graphics 里勾选照明、天花、机电类别，看视图里有无元素；或建一张多类别明细表计数 | MA-3.4 |
| 未用类型 | Manage → Purge Unused 的清单（只看、不点 OK） | MA-3.4 |

## 2. 标高与坐标

| 信息 | 怎么取 | 用于 |
| --- | --- | --- |
| 测量点、项目基点 | 平面视图打开 Site 类别，选中两点，看 Properties 的 N/S、E/W、Elev、Angle to True North | MA-2.3、AUD-S03 |
| 标高基准 | 选 Level → Edit Type → Elevation Base；选高程点 → Edit Type → Elevation Origin / 基准设置、Units Format | MA-2.4、GEN-04 |
| MSL | 剖面 / 立面上找 MSL 标注；无则问 AP（INP-04） | MA-2.5、AUD-V03 |

## 3. Room 与 Area

| 信息 | 怎么取 | 用于 |
| --- | --- | --- |
| 未放置 / 未闭合 Room | 房间明细表（含 Area、Level），找面积为 0 或「Not Placed」「Not Enclosed」 | MA-4.1 |
| Area 面积、方案 | 每个面积方案建 Area 明细表（Area Scheme 在新建时选） | MA-4.2、AUD-V09–V14 |
| 重复 Area | 同一明细表按 Level、Name 排序，找同名同面积 | MA-4 另查、AUD-V10 |

## 4. 视图与图纸

| 信息 | 怎么取 | 用于 |
| --- | --- | --- |
| 视图比例、样板 | 视图 Properties：View Scale、View Template | 各 AUD §2 |
| 图纸上的图片表 | 打开图纸，选中表格，看是 Raster Image 还是 Schedule Graphics；或 Manage → Manage Images | GEN-01 |
| 视图内计数 | 视图内右键某类元素 → Select All Instances → Visible in View，看状态栏的数量 | AUD-V02 等 |

## 5. 明细表

| 信息 | 怎么取 | 用于 |
| --- | --- | --- |
| 字段是否为计算值 | 打开明细表 → Properties → Fields：计算栏标有 fx；其余看是内置参数还是共享参数 | GEN-02 |
| 表值 | 明细表 → Export → Reports → Schedule（.txt / .csv） | GEN-06 |

<a id="man-colour"></a>
## 6. 颜色与半色调

harness 不能执行代码、或要人工复核时用。

1. 把图纸或视图导出为 PNG（File → Export → Images and Animations → Image），分辨率 ≥ 150 dpi。
2. 用任一取色工具（例：Windows「画图」的取色器、Photoshop）读填色区域中心的 RGB，每种颜色至少取 3 点。
3. 对照 [DK-AUD-004](../L1-Domain/DK-AUD-004_Colour_Standards.md)：Table 1 要完全相等。
4. 半色调：在墙线上取色。纯黑（0,0,0）→ 没有半色调；灰色 → 有。这是简化判法，记 `[INFERENCE]`。

## 7. MCP 盲点的人工抽查

<a id="man-dim-override"></a>
### 7.1 尺寸是否手改（GAP-01）

- 在 GBP 平面、剖面、立面上，逐个双击关键尺寸（总尺寸、轴距、走廊净宽、建筑高度）的数字，打开 Dimension Text 对话框。
- 「Use Actual Value」以外的选项（例：Replace With Text）= 手改。
- 抽查不少于每张图 5 个尺寸，含所有与合规判定有关的尺寸。
- **有问题**：任何一个合规相关尺寸被替换文字 → Blocker（G3）。
- 对话框名称与选项名随版本可能不同 `[INFERENCE]`。

<a id="man-area-gaps"></a>
### 7.2 面积边界缝隙、重叠、隐藏边界（GAP-02）

- 打开每个面积平面：Visibility / Graphics 打开 Area Boundary 子类别，放大检查转角、墙与边界相接处。
- Manage → Review Warnings：找「Area is not in a properly enclosed region」「Area Boundary lines overlap」一类警告。
- 检查有无线型为 Invisible 的边界线。
- 有 BD BIM Area Tool 时，再用它跑一次检查，作为对照。
- **有问题**：任何缝隙、重叠或隐藏边界 → Blocker（BIMGBPS / LandsD 零容忍）。

<a id="man-cad-import"></a>
### 7.3 CAD 导入（GAP-03）

- Manage → Manage Links → CAD Formats 页：列出链接与导入。
- Visibility / Graphics → Imported Categories 页：列出视图里的导入。
- **有问题**：提交文件里有外部 CAD 链接（非自包含）；CAD 详图有内容而未被审核 → 补审。

<a id="man-version"></a>
### 7.4 Revit 版本（GAP-04）

- 正在运行的版本：Help → About。
- 文件保存版本：用较新 Revit 打开时若提示升级，说明保存版本较旧。确切版本可从文件的 BasicFileInfo 读，但要脚本 `[INFERENCE]`。
- **有问题**：保存版本低于 2017（LIM-05）。

<a id="man-lod"></a>
### 7.5 LOD（GAP-05）

- 抽查主要构件（墙、楼板、楼梯、窗、幕墙）的 3D 与剖面表达，对照 LOD 300 的一般描述（BIMGBPS §4.4 引 BIMForum）。
- 只能记结论 + 截图，不给数值判据。
- **有问题**：主要构件只有体块、没有构造层或开口。
