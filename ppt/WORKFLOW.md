---
name: code-walkthrough-ppt
displayName: 源码走读 PPT
slug: code-walkthrough-ppt
version: 1.0.0
author: 人月聊IT
category: 内容创作
platforms: WorkBuddy,Claude Code,Codex,Cursor,CodeBuddy
visibility: public
license: MIT
description: "把一套已有 IT 系统的源代码，做成一份能直接发给客户或同事看的项目介绍 PPT（1920×1080 单文件 HTML deck，纯白 Flat Design 咨询风格，不要求系统能运行）。内置 1920×1080 咨询版式硬骨架 + 三个模板库（结构图形 28 个、ECharts 数据图表 28 种、架构图 15 种）+ 四套浅色系统界面骨架 + 无头截图与坐标测量脚本。核心机制是读源码重绘而非真实截图——逐层读源码筛出核心功能（先给人确认）→ 按源码结构与字段重绘浅色界面 HTML → 无头浏览器截成 1600×900@DPR2 → 排成左右布局截图页（左栏 504px 讲功能、右栏 1316px 放截图占 70%，左右用 ①②③ 编号呼应）→ 十项质检。产出 6 章：项目整体介绍 / 端到端业务流程 / 整体功能架构 / 技术架构 / 核心功能点（8–15 页）/ 结语与能力边界，每个结论都带源码 文件:行 落点。触发词：把项目源码做成一份介绍 PPT、源码转 PPT、给这个系统做产品介绍演示文稿、基于代码出一份汇报 deck、技术方案汇报 PPT、系统功能介绍 PPT、源代码生成演示文稿、读源码做PPT、code walkthrough ppt、source to deck、project intro deck、code to slides。"
description_zh: "把一套已有 IT 系统的源代码做成 1920×1080 的项目介绍 HTML 幻灯片：内置咨询版式骨架与三个模板库，按源码重绘浅色界面并截图，核心功能页左栏讲功能、右栏放截图占 70%，每个结论都标注源码落点。不要求系统能运行。"
description_en: "Turn an existing codebase into a project-introduction HTML deck (1920x1080). Built-in consulting layout skeleton, three template libraries, four light UI shells, and headless screenshot tooling. Screens are redrawn from source instead of captured from a running system. Each feature page puts the write-up on the left and a screenshot at 70% width on the right, and every claim is traceable to a file:line in the source."
permissions:
  - file_read
  - file_write
  - shell_exec
permission_notes_zh: 只读取用户指定的源代码目录（不改动源码）。会在工作目录下创建重绘界面 HTML、images 截图与 deck 文件，并调用本机 Chrome 做无头渲染；不联网、不上传任何数据、不读取隐私数据。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
agent_created: true
---

# code-walkthrough-ppt —— 源码 → 项目介绍 deck

把一套已有 IT 系统的源码，变成一份**直接可以拿去汇报或发给客户的项目介绍 PPT**。

不要求系统能运行。界面靠"读源码 + 重绘浅色 HTML + 无头截图"还原；看不见的架构与流程靠内联 SVG 讲清楚。

> 本技能 = `code-walkthrough-video`（源码勘察 + 界面重绘截图流水线）+ `consulting-html-ppt`（1920×1080 硬骨架 + 三个模板库 + 质检）。
> 与视频技能的两处**根本差异**：① 界面重绘走**浅色**（与纯白 deck 融合），不是深色；② 产物是 deck，没有配音与时间轴。

**动手前必读：`references/01-code-discovery.md`（勘察方法）与 `references/04-layouts.md`（版式坐标）。**
架构图 / 流程图 / 图表的画法沿用咨询规范，见 `references/05-diagrams.md`，模板一律从 `assets/templates/` 取。

---

## ★ 开工前必须问用户的三件事

**不要猜、不要默认、不要自己拍板。逐条问，问完再动手。** 这三项直接决定成稿质量与返工量。

### 问一：源代码目录在哪

要问到**具体路径**，并确认：

- 是单仓库还是多仓库（前后端是否分开）
- 有没有要排除的目录（`node_modules`、`dist`、`build`、`.venv`、`vendor`、第三方 SDK 源码）
- 对应哪个**分支 / 版本**（deck 要对齐一个确定的版本）
- **本体模型 / 设计文档 / 需求文档在哪**（很多系统带 `models/`、`docs/`、`*.md` 规范文档，这是提炼业务名词的金矿）

拿到路径后先做规模探测（`references/01-code-discovery.md` 阶段 A），**把代码量与分层结构报给用户**再决定怎么读。

### 问二：讲哪些核心功能（本技能最容易被跳过、也最影响成稿的一问）

核心功能页是整份 deck 的主体（占 1/3 以上页数），选错了整份 deck 就废了。做法：

1. 扫一遍源码，按 `references/01-code-discovery.md` 的**三档判据**筛出候选
2. 列成清单（每项：功能名 + 一句话说明 + 建议页数），**给用户挑**
3. 数量区间 **8–15 页，硬上限 15**；超过要提醒用户"再讲下去 deck 会散"
4. 加一条硬约束：**每个核心功能都必须能落到一个看得见的界面**——挑到没有界面的功能（如纯后端的守卫、注册表），把它移到「技术架构」章节用图表讲，不占核心功能页

用户如果说"你看着办"，就挑**承担端到端主链路的业务动作 + 有业务规则或状态机的那些**，并把选择理由说出来让他确认。

### 问三：deck 页数档位与用途

PPT 没有时长上限，但**有注意力上限**。必须问到页数或场景：

| 场景 | 建议页数 | 核心功能页 |
|---|---|---|
| 短汇报（管理层 10 分钟过一遍） | 14–16 | 6 |
| **标准版（默认）** | **20–24** | **8–10** |
| 详细版（技术评审 / 交付文档） | 26–32 | 12–15 |
| 超过 32 页 | 拆成「概览版 + 详细版」两份 deck | — |

> 问完之后把答案复述一遍再动手：`源码目录 X ／ 核心功能 Y 个 ／ 目标 N 页`。

### 顺带要问的（不影响结构，影响素材）

- **品牌 / 产品名**：封面与页脚用（不给就用系统原名）
- **界面能不能给真实截图**：能的话优先用真实的（重绘永远比不上真图）；不能才走重绘
- **有没有不能出现的内容**：客户名、金额、内网地址、人名、**密钥**
- **deck 的读物语种**：默认中文

---

## 资源地图（本技能自带，图形一律从这里取素材，不许自创）

| 资源 | 路径 | 用途 |
|---|---|---|
| 源码勘察方法（**必读**） | `references/01-code-discovery.md` | 阶段 A/B/C 勘察流程、**核心功能三档判据**、链路候选挑选机制 |
| 浅色界面重绘（**必读**） | `references/02-ui-redraw-light.md` | 还原清单、字号规范、三套骨架用法、截图命令与坑 |
| deck 蓝图 | `references/03-deck-blueprint.md` | 六章 × 页数配比、章节顺序规则、反单调节奏 |
| 版式与坐标（**必读**） | `references/04-layouts.md` | 硬骨架、**五形态判定（含截图页）**、截图页精确坐标 |
| 图表取用 | `references/05-diagrams.md` | 六章内容 → 模板编号的映射表、内联 SVG / ECharts 取用口径 |
| 命令级流水线 | `references/06-pipeline.md` | 每步的确切命令、产物、验收点 |
| 已知坑清单 | `references/07-pitfalls.md` | 按「症状 → 根因 → 修法」组织，**动手前先扫一遍** |
| deck 工程骨架 | `assets/deck/deck-template.html` | 单文件多页 deck 骨架（居中缩放 + 键盘翻页 + 圆点 + 页码 + 备注） |
| **浅色界面骨架 ×4** | `assets/ui-shell/` | `shell-shell-light.html` 三栏工作台外壳 / `shell-list-light.html` 列表页 / `shell-form-light.html` 表单页 / `shell-detail-light.html` 详情页 |
| **模板库 A** | `assets/templates/图表模板库.html` | 示意 / 结构图形 01–22 + 文本分类版式 23–27（内联 SVG） |
| **模板库 B** | `assets/templates/echarts图表模板.html` | 数据 / 指标类真实图表 01–28（ECharts 5.5，`c01()…c28()`） |
| **模板库 C** | `assets/templates/架构图模板.html` | 软件 / IT 系统架构图 00–14（内联 SVG；00 为图元与连线规范） |
| 离线 ECharts | `assets/templates/echarts.min.js` | CDN 不通时替换 |
| 图标精灵 | `assets/templates/icons.svg` | 35 个单色线稿图标（`<symbol id="i-xxx">`） |
| 标注层规范 | `assets/annotation.md` | 截图标注圆标 / 引线 / 高亮框的画法与配色 |
| 可追溯表模板 | `assets/traceability.csv` | 页号↔功能↔源码↔重绘 HTML↔截图↔标注点 |

> 路径均相对 PPT 子工作流目录。使用合并技能时，`<skill>` 指向 `<合并技能根目录>/ppt`。

---

## 五步流程（按序执行，不许跳步）

### 第 1 步 · 勘察源码，产出大纲与核心功能清单

读 `references/01-code-discovery.md`。

产出三样东西：① 系统一句话定位（业务语言）② 一条端到端主链路（含触发点 → 校验 → 写表 → 事件 → 返回）③ **核心功能候选清单**（8–15 项，每项附源码落点）。

**给用户确认后再往下走。** 这一步错了，后面全白做。

### 第 2 步 · 重绘浅色界面并截图

读 `references/02-ui-redraw-light.md`。

```bash
# 每张截图 = 一个 html 文件，复制骨架后按"还原清单"改文案
cp "<skill>/assets/ui-shell/shell-list-light.html" "<工程>/ui/03-order-search.html"

python "<skill>/scripts/shoot_page.py" --in "<工程>/ui" --out "<工程>/images"
```

**三条铁律**：画布 1600×900、数据**全部仿真**、deck 里注明"界面为按源码结构重绘的示意页面"。

出图后**先看拼版** `contact_sheet.png`，一屏过完所有界面，比逐张点开快得多。

### 第 2.5 步 · 读元素坐标（写标注前必做，**不许目测**）

标注坐标靠目测估必然出错（误差 20–40px，圆标会正好压住卡片标题）。用无头浏览器读元素的真实 rect：

```bash
python "<skill>/scripts/rects.py" --in "<工程>/ui" > "<工程>/_build/rects.txt"
```

输出已经换算到 1316×740 截图坐标系，**框的四个数直接抄**；圆标按 `槽 x − 24, 槽 y + 26` 算。详见 `references/06-pipeline.md` 第 2.5 步。

### 第 3 步 · 定蓝图、排页面顺序

读 `references/03-deck-blueprint.md`。

产出 `blueprint.md`：每页写清 ① 页码 ② 章节 ③ **动作式结论标题**（不是图名）④ 形态（截图页/架构图页/图形页/数据页/文本分类页）⑤ 素材来源（哪个模板编号 / 哪张截图）。

**先过一遍"相邻两页骨架不同"再动手**——反单调是咨询风格最容易翻车的地方。

### 第 4 步 · 画图 + 标注 + 拼 deck

读 `references/04-layouts.md` 与 `references/05-diagrams.md`。

- 架构图 / 流程图 / 数据图：从 `assets/templates/` 的模板库**照抄**，只替换文字与数值
- 截图页：按 `references/04-layouts.md` 的**精确坐标**排（左 504 + 间距 60 + 右 1316），标注层用 deck 上的 SVG 覆盖层，不烙进截图
- deck 骨架：复制 `assets/deck/deck-template.html`，按 `blueprint.md` 逐页填

```bash
python "<skill>/scripts/build_deck.py" --parts "<工程>/pages" --out "<工程>/<系统名>-产品介绍.html" --images "<工程>/images"
```

### 第 5 步 · 质检与交付

```bash
python "<skill>/scripts/check_deck.py" "<工程>/<系统名>-产品介绍.html"
```

脚本按 `references/04-layouts.md` 的质检清单逐项扫（尺寸、溢出、红色唯一性、图片引用、编号呼应、可追溯表齐备），**不达标即返工**。

交付物：`<系统名>-产品介绍.html` + `images/` 目录 + `blueprint.md` + `traceability.csv`。
**打包分发时整个目录一起给**——deck 用相对路径引用 `images/`，单独发 html 会丢图。

---

## 硬骨架速查（不得违反 · 完整版见 `references/04-layouts.md`）

```text
画布：1920 × 1080        背景：#FFFFFF（纯白，不允许底色 / 渐变）
页面边距：四边各 20px     安全区：x 20–1900 / y 20–1060
标题区：y 20–170（高 150） 标题：48px / 700 / 左对齐 / 区域内垂直居中
                         → 动作式结论，不是图名
kicker（可选）：标题区右侧右对齐 x=1900，18px/600/#A3A3A3，letter-spacing 4px
分隔线：y=170，高 5px，纯黑 #000000，横向拉通 x 0–1920（左右顶到画布边缘）
内容区：y 175–1060（1880 × 885）
【截图页】左栏 504 + 间距 60 + 右栏 1316（截图 16:9 → 高 740，上下各留 72，垂直居中）
【分栏图】左栏 700 + 间距 60 + 右栏 1120×700（图形上下左右居中）
【通栏图】1880 × 700，左右拉满、垂直居中
页脚（可选）：y ≤ 1040
```

**居中缩放方案（多页 deck 必须照此实现）：**

```js
// stage 固定 1920×1080，transform-origin: top left
function fit(){
  const s = Math.min(innerWidth/1920, innerHeight/1080);
  const x = (innerWidth  - 1920*s)/2;
  const y = (innerHeight - 1080*s)/2;
  stage.style.transform = `translate(${x}px,${y}px) scale(${s})`;
}
addEventListener('resize', fit); fit();
```

> 不要用 `flex 居中 + transform: scale(center)`——1920px 元素在窄视口下会溢出导致左偏黑边。

---

## 五种形态判定（优先级：截图页 ＞ 数据页 ＞ 架构图页 ＞ 图形页 ＞ 文本分类页）

**每一页动手前，必须按以下顺序判断，不得跳步。**

| 页面类型 | 什么时候用 | 从哪儿取 | 容器尺寸 |
|---|---|---|---|
| **截图页** | 这一页要讲**一个具体功能的界面与机制**（核心功能章节几乎全是） | 重绘的浅色界面截图 + SVG 标注层 | 左 504 + 60 + 右 **1316** |
| **数据页**（真实图表） | 内容带**数值序列 / 对比基准 / 占比 / 归因 / 达成率 / 分布** | 模板库 B · 01–28 | 右 1120×700 或通栏 1880×700 |
| **架构图页**（软件 / IT 系统） | 内容讲系统的构成与运行：分层、应用、数据流、服务拆分、集成、安全、部署、演进或 UML 行为 / 关系 | 模板库 C · 00–14 | 分栏 1120×700 / 通栏 1880×700 |
| **图形页**（示意 / 结构） | 有**层级 / 流程 / 因果 / 对比 / 矩阵 / 时间 / 闭环 / 转化 / 角色×阶段**关系，**没有数值**，且**不属于软件 / IT 系统方案** | 模板库 A · 01–22 | 同上 |
| **文本分类页** | 既无结构关系、又无数值，只是「几个并列类目 + 各自说明」 | 模板库 A · 23–27 | 1200 宽绘制，通栏 1.567 投放 |

**五步判定铁律：**

- ① **这一页在讲某个功能的界面和机制吗？** 是 → 截图页。**有界面就必须用截图页**，不许用示意图替代真实界面还原。
- ② 有数字要对齐比较吗？有 → 数据页（B·01–28）。用一段文字说「营收同比增长 15%」是本页的失职。
- ③ 没有数字，讲的是软件 / IT 系统的构成、运行或演进吗？是 → 架构图页（C·01–14）。
- ④ 也不是，有可画的通用结构关系吗？有 → 图形页（A·01–22）。
- ⑤ 都不成立，只有并列类目 → 文本分类页（A·23–27），也必须由「**线 + 框**」构成骨架。

### 截图页版式（本技能新增的第五形态，坐标不得改）

```text
内容区 1880 = 左栏 504 + 间距 60 + 右栏 1316（右栏占 70%）

左栏（x 20–524，宽 504）：
  功能名（动作式）      28px/700/#333333
  ── 细分隔线 ──
  一句话价值            20px/400/#777777
  ①②③ 机制要点        每条 = 编号圆标 + 22px/700 标题 + 20px/400 说明（≤2 行）
  ── 撑到底部 ──
  ④ 边界与约束          20px/400/#A9720B（琥珀）

右栏（x 584–1900，宽 1316）：
  截图容器：1316 × 740，1px #CCCCCC 描边（禁用阴影），垂直居中（上下各留 72.5px）
  截图本体：1600×900 @DPR 2（3200×1800 PNG）等比缩至 1316 显示 → 等效 DPR 2.43
  标注层：SVG 覆盖在截图之上，圆标半径 17px，色 #CC0000

**不加顶部总结条**（用户明确要求）。代价是标题必须承担结论职责。
①②③ 编号必须与左栏要点一一对应 —— 这是把左右栏"绑"起来的关键。

**圆标放哪才不压字**（实测结论，务必照做）：

| 规则 | 值 |
|---|---|
| 圆标横向 `cx` | `框.x − 24`（骑左边线再左移半直径，落在卡片外的页面底色带上） |
| 圆标纵向 `cy` | `框.y + 26` |
| 框左端 | `≥ 44`（否则 `cx < 16` 越界） |

- 卡片的**间隙只有 8–10px**，塞不下直径 34px 的圆标 → **不要**把圆标骑在框的上下边线上。
- **不要**把圆标放框内左上角 —— 卡片标题文字通常就在那里。
- 坐标**不许目测**，用 `scripts/rects.py` 读真实 rect。
- 完整说明与边界约束见 `references/04-layouts.md`。
```

---

## 配色 & 字体速查

| 角色 | 色值 | 占比 | 用在哪 |
|---|---|---|---|
| 主色（红：结论 / 高亮 / **截图标注**） | `#CC0000` | 20% | deck 里的高亮与标注，**全页只有一处语义** |
| 深蓝（中层 / 机制） | `#006393` | 15% | 左栏图标、架构图中层 |
| 深青（文字主色） | `#333333` | 20% | 标题、正文 |
| 辅助灰（次要文字 / 轴 / 连线） | `#A3A3A3` | 45% | 说明、注释 |
| 浅灰背景 / 描边 / 主场填充 | `#F5F5F5` / `#CCCCCC` / `#FFF2F2` | — | — |
| 边界提示（琥珀） | `#A9720B` | — | 截图页左栏底部第 ④ 条 |

**禁止**：渐变、阴影、发光、3D、高饱和荧光色、彩色 emoji。

**界面重绘的配色**（与 deck 不同，见 `references/02-ui-redraw-light.md`）：跟原系统走，主色约束在 `#155EEF` 一带的浅色系统色；**界面的红留给状态语义**（如"未完成"标签），deck 的红留给标注——两者要能分清。

```css
/* 标题 */ font-size:48px; font-weight:700; color:#333333; line-height:1.2;
/* 小标题 */ 25–28px/700/#333（卡片内可 19–22px）
/* 正文 */ 20–22px/400; line-height:1.65   —— 下限 20px，禁止低于 20
/* 关键数字 */ 56–72px/700; color:#CC0000
/* kicker */ 18px/600/#A3A3A3; letter-spacing:4px; text-transform:uppercase
/* 页脚 / 注释 / 图内辅助 */ 13–16px/#A3A3A3   —— SVG 内文字 ≥13px
font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC","Noto Sans SC","Helvetica Neue",Arial,sans-serif;
```

---

## 九条铁律（牢记）

1. **截图先于示意**：有界面的功能必须用重绘截图讲，不许用图形页糊过去。
2. **骨架是硬约束**：20px 边距 / y=170 处 5px 黑线拉通 / 标题 48px / 内容区 175–1060 / 截图页 504+60+1316。
3. **取模板、不自创**：数据页取 B·01–28、架构图页取 C·01–14、图形页取 A·01–22、文本分类页取 A·23–27。
4. **技术结论必须有源码落点**：每个架构/机制结论都要能指到文件:行。**没找到证据的不许写进 deck**（宁可少一页，不许编一条）。
5. **数据全部仿真**：重绘界面里不得出现真实客户名、金额、账号、密钥、内网地址。源码里的密钥一律不得出现在 deck 任何位置（含页脚、注释、HTML 注释）。
6. **标注层是 deck 上的 SVG，不烙进截图**：底图干净可复用，标注可调、矢量不糊，同一张底图能在不同页讲不同标注。
7. **反单调**：相邻两页骨架不同；截图页连续不超过 **4** 页，第 5 页前必须插一页架构图/流程图/数据页调节节奏。
8. **①②③ 左右呼应**：截图页左栏要点编号与截图标注圆标一一对应，缺一不可。
9. **一页一结论**：每页标题写成动作式结论（「一次出库要过四道校验」），不写图名（「出库录入页」）。

---

## 已知坑（前 5 条，完整版见 `references/07-pitfalls.md`）

| # | 症状 | 根因 | 修法 |
|---|---|---|---|
| 1 | 截图尺寸不是 1600×900（出来 1080×617） | Windows 显示缩放（本机 150%） | 无头浏览器加 `--force-device-scale-factor=1` |
| 2 | 截图尺寸对，但**底部内容缺失** | `--window-size` 是窗口尺寸不是视口尺寸（标题栏吃掉约 16×95px） | 窗口开大一圈再裁：`--window-size=w+40,h+120`，截图后 `crop(0,0,w,h)` |
| 3 | 重绘改了 HTML，截图还是旧版 | Chrome 用户数据目录缓存 | 每页渲染前清 profile + `--incognito` |
| 4 | 截图里的红和 deck 的红打架 | 界面状态色（#C4320A）与 deck 标注色（#CC0000）都是红 | 界面状态标签改用低饱和；deck 红只给标注 |
| 5 | 编码写得很爽，deck 打不开图 | 只发了 html 没带 `images/` 目录 | 交付必须整目录；或改 base64 内联（>6 张截图不推荐） |

---

## 目录结构

```
<skill>/
├── SKILL.md                     本文件（决策骨架 · 五步流程 · 硬性规则）
├── README.md                    安装与使用
├── LICENSE                      本技能许可（MIT）
├── NOTICE                       第三方组件来源与许可声明
├── PUBLISH.md                   发行与发布指引
├── preview/                     技能市场列表配图
├── references/
│   ├── 01-code-discovery.md     ★ 源码勘察 + 核心功能三档判据
│   ├── 02-ui-redraw-light.md    ★ 浅色界面重绘 + 截图
│   ├── 03-deck-blueprint.md     deck 蓝图与页数配比
│   ├── 04-layouts.md            ★ 硬骨架 · 五形态 · 截图页坐标
│   ├── 05-diagrams.md           六章 → 模板编号映射
│   ├── 06-pipeline.md           命令级流水线
│   └── 07-pitfalls.md           ★ 已知坑清单
├── assets/
│   ├── deck/deck-template.html  单文件多页 deck 骨架
│   ├── ui-shell/                四套浅色界面骨架
│   ├── templates/               三个咨询模板库 + 图标 + 离线 ECharts（含 Apache-2.0 许可全文）
│   ├── annotation.md            标注层规范
│   └── traceability.csv         可追溯表模板
└── scripts/
    ├── shoot_page.py            HTML → 1600×900 @DPR2 截图 + 拼版
    ├── rects.py                 读界面元素真实 rect（标注对齐用，不许目测）
    ├── build_deck.py            页面片段 → 单文件 deck
    └── check_deck.py            质检（尺寸/溢出/红/图片/编号溯源）
```

## 工程目录（每份 deck 一个）

```
<工程>/
├── src/                       源码只读引用（可用软链或直接指原目录）
├── ui/*.html                  重绘的浅色界面（一张截图 = 一个文件）
├── images/*.png               截图产物 + contact_sheet.png
├── pages/*.html               deck 的页面片段（每页一个）
├── blueprint.md               页面蓝图（页码/章节/标题/形态/素材来源）
├── traceability.csv           可追溯表
└── <系统名>-产品介绍.html       ★ 交付物
```

所有脚本默认以 `--dir` 指定的目录为工程目录，也可用 `CW_PPT_DIR` 环境变量。

---

## 交付前检查清单

- [ ] 三个必问点都问过并且复述确认了
- [ ] 核心功能页数量在 8–15 之间，且每个都能落到一个界面
- [ ] 每个技术结论都有源码落点（可追溯表已填满）
- [ ] 全 deck 数据仿真、无真实客户/账号/密钥/内网地址（含 HTML 注释）
- [ ] 截图全部 1600×900；拼版逐张看过（无溢出、无裁切、字号在缩至 1316 宽后仍可读）
- [ ] 每页骨架合规：20px 边距、y=170 黑线拉通、截图页 504+60+1316
- [ ] ①②③ 左栏要点与截图标注一一对应
- [ ] 红色唯一性：全页红色只有一个语义落点
- [ ] 反单调：相邻页骨架不同；截图页连续不超过 4 页
- [ ] `check_deck.py` 全项通过
- [ ] 交付目录含 `images/`；收尾明确写出**能力边界**（哪些没做、哪些要人工介入、界面为示意重绘的声明）
