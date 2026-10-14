---
name: code-walkthrough-video
display_name: "源码讲解视频"
display_name_en: "Code Walkthrough Video"
description: 把一套已有 IT 系统的源代码做成中文知识讲解视频（1920×1080、微软云扬配音、硬字幕、≤10 分钟）。做法是从源码勘察出业务大纲，把前端界面按源码结构重绘成 HTML 再截图，配上自绘的分层/流程/状态图，最后用 Remotion 渲染成片。当用户提到「给这个系统源码做一个讲解视频」「代码走读视频」「系统介绍视频」「把我们的项目做成演示视频」「源码转视频」「code walkthrough video」时使用。适用于 Spring Boot / Vue / React / 小程序 / Electron / 传统 Java Web 等任意技术栈，**不要求系统能跑起来**。
agent_created: true
---

# 源码 → 知识讲解视频

把一套已有 IT 系统的源码，变成一支**能直接发给客户或同事看的讲解视频**。

不要求系统能运行。界面靠"读源码 + 重绘 HTML + 无头截图"还原，看不见的架构靠自绘图表讲清楚。

---

## ★ 开工前必须问用户的三件事

**不要猜、不要默认、不要自己拍板。逐条问，问完再动手。** 这三项直接决定成本与内容，猜错的返工代价是小时级的。

### 问一：源代码目录在哪

要问到**具体路径**，并确认：

- 是单仓库还是多仓库（前后端是否分开）
- 有没有需要排除的目录（`node_modules`、`dist`、`vendor`、第三方 SDK 源码）
- 能读到的分支/版本（讲解要对应某个确定的版本）

拿到路径后先做一次规模探测（`references/01-code-discovery.md` 阶段 A），**把代码量报给用户**：
小系统可以逐模块读；十万行以上必须让用户先把范围收窄，否则会淹在里面。

### 问二：讲哪个子系统 / 模块 / 功能

这是最容易被跳过、也最影响成片质量的一问。做法：

1. 扫一遍源码，列出 3~8 个候选（按业务动作命名，不按技术分层）
2. 每个候选给出一句话说明 + 建议时长
3. **让用户选**，允许他说"全系统的整体架构"或"我全都要"（后者要提醒时长上限）

候选清单格式与提取方法见 `references/01-code-discovery.md` 阶段 B4。

用户如果说"你看着办"，那就挑**最靠近主业务的端到端链路**（一次请求从进到出），并且**把选择理由说出来让他确认**。

### 问三：时长要求

**硬上限 10 分钟。** 必须问到具体数字，因为它直接换成字数预算：

| 目标时长 | 可讲字数 | 建议章节数 |
|---|---|---|
| 2 分钟 | 约 570 | 3 |
| 3 分钟 | 约 890 | 4 |
| 4 分钟 | 约 1210 | 5 |
| 5 分钟 | 约 1530 | 6 |
| 6 分钟 | 约 1850 | 6~7 |
| 8 分钟 | 约 2480 | 7~8 |
| 10 分钟 | 约 3120 | 9~10 |

随时可查：`python <skill>/scripts/build_audio.py --budget <秒数>`

用户说不清时长就**按内容量反推**：给他几个档位（"这条链路讲透大约需要 5 分钟，要更短我就砍掉××部分"），让他选。

> 问完之后把答案复述一遍再动手：`源码目录 X ／ 讲 Y ／ 目标 N 分钟`。

### 顺带要问的（不影响结构，影响素材）

- **品牌/产品名**：顶部水印与落版用（不给就不显示水印）
- **界面能不能给真实截图**：能的话优先用真实的；不能才走重绘
- **有没有不能出现的内容**：客户名、金额、内网地址、人名

---

## 一次性准备

```bash
# 自检（缺什么会直接给修复命令）
python "<skill>/scripts/check_env.py"

# 装配 Remotion 依赖（优先复用本机已有的，秒级就绪；没有才联网装）
bash "<skill>/scripts/setup_remotion.sh" "<工程目录>"
```

环境硬依赖：`edge-tts` + `pillow` 的 Python、Chrome 或 Edge、ffmpeg、node、Remotion 4.x。

---

## 五步流程

### 第 1 步 · 勘察源码，出大纲并确认讲解对象

读 `references/01-code-discovery.md`。

产出：候选清单 → **用户选定** → 一份 3~7 章的讲解大纲，每章能回答"做什么 / 为什么这么设计 / 边界在哪"。

### 第 2 步 · 重绘界面并截图

读 `references/02-ui-redraw.md`。

```bash
cp "<skill>/assets/ui-shell/shell-desktop-dark.html" "<工程>/ui/<页面名>.html"
# 按源码里的路由/表头/枚举/主题变量改文案（一个页面一个文件）

python "<skill>/scripts/shoot_page.py"   --in ui --out shots_raw
python "<skill>/scripts/prep_shots.py"   --raw shots_raw --out remotion/public/shots
```

第 3 条命令会产出 `contact_sheet.png` 拼版，**先看拼版再往下走**。

> 三条铁律：画布 1600×900、数据全部仿真、不在解说里声称"这是系统实际截图"。

### 第 3 步 · 写解说稿，合成配音

读 `references/03-narrative.md`。

```bash
# 先估算，超了先删内容（不调 TTS，秒出）
python "<skill>/scripts/build_audio.py" --dir . --dry

# 确认后正式合成
python "<skill>/scripts/build_audio.py" --dir .
```

产出 `timing.json` / `<srtName>` / `解说稿.md`，并把 mp3 同步到 `remotion/public/audio/`。

**最后一行会打印全片时长与是否超 10 分钟**——超了就回第 1 步删内容。

> 合成前把解说稿给用户过一遍。配音生成后再改文案要重新合成 + 重新分镜 + 重新渲染。

### 第 4 步 · 画图 + 写分镜 + 探针验版式

读 `references/04-diagrams.md`。

```bash
# 在 remotion/src/diagrams.tsx 里加图并注册进 DIAGRAMS（复制 ARCH / FLOW 改最快）
# 写 script/storyboard.json

python "<skill>/scripts/make_props.py" --dir .
bash   "<skill>/scripts/probe_render.sh"
```

探针把每个分镜压成 5 秒渲染一遍，**每个分镜抽两帧**到 `preview/probe/`：

- `_a`（0.5s，入场态）——看**画面边缘有没有被裁**（缓推镜头在此刻幅度最大）、错峰动画第一批元素有没有落位
- `_b`（3.5s，稳定态）——看文字溢出、元素被裁、高亮框是否框准

**逐张看**，改到全过为止，通常要 2~3 轮。

### 第 5 步 · 正式渲染、拼接、验收交付

```bash
bash "<skill>/scripts/render_chunks.sh"    # 自动分块，每块约 2000 帧
bash "<skill>/scripts/finalize.sh"          # 拼接 + 帧数核对 + 产出交付物
```

交付物三件：`<标题>.mp4`、`<标题>.srt`、`<标题>_解说稿.md`。

**验收两条**（见 `references/05-pipeline.md` 第 5 步）：

1. **抽 5~6 帧看字幕与画面对位**——声画错位是这类视频最刺眼的缺陷，只在成片里看得出来
2. `ffprobe` 核对 `1920×1080 / 30fps / h264+aac` 与总时长

---

## 不可违反的硬性规则

| # | 规则 | 原因 |
|---|---|---|
| 1 | 配音固定用 **`zh-CN-YunyangNeural`（云扬）**，`rate=+6%` | 一套产品视频的音色必须一致；换音色观众立刻听出来 |
| 2 | 调用 `edge_tts` 前**必须** `import edge_tts_patch` | 微软已废弃旧端点，不补丁一律 403（见 `references/06-pitfalls.md` A1） |
| 3 | 时长 **≤ 10 分钟** | 用户要求；超了先删内容，不要靠拉快语速硬压 |
| 4 | 截图统一 **1600×900** | 比例不一致会让 `objectFit:cover` 裁切，高亮框必然错位 |
| 5 | 界面数据**全部仿真**；解说中注明"界面为按源码结构重绘的示意页面" | 合规 |
| 6 | 分镜时间**按段内比例**（`f0`/`f1`），不写绝对秒数 | 配音重合成后自动跟随，不用改分镜 |
| 7 | **正式渲染前必须跑探针** | 探针 1~2 分钟，正式渲染十几分钟 |
| 8 | 长片**必须分块渲染**再无损拼接 | 一次渲染必卡死 |
| 9 | 交付前**必须抽帧看声画对位** | 唯一的兜底验收 |

---

## 目录结构

```
<skill>/
├── SKILL.md
├── scripts/
│   ├── check_env.py         环境自检
│   ├── setup_remotion.sh    装配/复用 Remotion 依赖
│   ├── edge_tts_patch.py    ★ 云扬端点补丁（必须 import）
│   ├── build_audio.py       配音 + 字幕 + 时间轴 + 解说稿
│   ├── shoot_page.py        HTML → 1600×900 截图
│   ├── prep_shots.py        截图归一化 + contact sheet
│   ├── make_props.py        storyboard.json → props.json（含自检）
│   ├── probe_props.py       生成探针分镜
│   ├── probe_render.sh      探针渲染 + 每分镜抽 2 帧（入场态 / 稳定态）
│   ├── render_chunks.sh     分块渲染
│   ├── finalize.sh          拼接 + 验收 + 交付
│   └── _env.sh              共用环境探测
├── project/                 Remotion 模板（不含 node_modules，569MB 不进包）
│   ├── src/diagrams.tsx     ★ 图表工具箱 + 2 个示例图
│   ├── src/scenes.tsx       片头 / 截图（含 focus 高亮）/ 图表 / 落版
│   ├── src/overlays.tsx     硬字幕 / 章节角标 / 进度条
│   └── src/theme.ts         深色主题，全套配色从这里取
├── references/
│   ├── 01-code-discovery.md 源码勘察与大纲
│   ├── 02-ui-redraw.md      界面重绘规范
│   ├── 03-narrative.md      解说稿与时长预算
│   ├── 04-diagrams.md       图表与分镜
│   ├── 05-pipeline.md       命令级流水线
│   └── 06-pitfalls.md       ★ 已知坑清单（动手前先扫一遍）
└── assets/ui-shell/         三套 1600×900 界面骨架
```

## 工程目录（每支视频一个）

```
<工程>/
├── src/                      源码只读引用
├── script/narration.json     分段解说稿
├── script/storyboard.json    分镜
├── ui/*.html                 重绘的界面
├── shots_raw/  audio/  timing.json  中间产物
├── preview/probe/            探针抽帧（验收用）
├── remotion/                 Remotion 工程 + props.json + out/parts/
└── <标题>.mp4 / .srt / _解说稿.md      交付物
```

所有脚本默认以当前工作目录为工程目录，也可用 `--dir` 或 `CW_VIDEO_DIR` 指定。

---

## 交付前检查清单

- [ ] 三个必问点都问过并且复述确认了
- [ ] 全片 ≤ 10 分钟（`build_audio.py` 最后一行确认）
- [ ] 解说稿用户过过一遍
- [ ] 界面数据的仿真性、合规性检查（无真实客户/账号/密钥/内网地址）
- [ ] 探针帧逐张看过（入场帧 `_a` + 稳定帧 `_b`）：无文字溢出、无元素被裁、画面边缘没切掉文字、高亮框精准
- [ ] `finalize.sh` 的期望帧数 == 实际帧数
- [ ] 抽 5~6 帧确认字幕与画面对位
- [ ] ffprobe 确认 1920×1080 / 30fps / h264+aac
- [ ] 交付物三件齐（mp4 / srt / 解说稿）
- [ ] 收尾明确写出**能力边界**（哪些没做、哪些要人工介入）
