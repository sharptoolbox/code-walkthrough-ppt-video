# 06 · 命令级流水线

本文件给出每一步的**确切命令、产物、验收点**。所有脚本默认以 `--dir` 或环境变量 `CW_PPT_DIR` 指定工程目录。

> 路径占位符：`<skill>` = 合并技能中的 `ppt` 子目录，`<工程>` = 本次 deck 的输出目录。

---

## 第 0 步 · 环境自检

```bash
python "<skill>/scripts/shoot_page.py" --check
```

检查：Chrome/Edge 可执行文件、Python PIL 是否可用、输出目录可写。

**硬依赖**：Chrome 或 Edge（无头截图用）、Python 3 + Pillow（拼版与裁剪用）。**不需要 node、不需要 ffmpeg、不需要 TTS**（与视频技能的关键区别）。

---

## 第 1 步 · 勘察源码

```bash
# 建工程目录
mkdir -p "<工程>"/{ui,images,pages}

# 规模探测（手工执行，见 references/01-code-discovery.md 阶段 A1）
cd "<源码目录>"
ls -la
find . -maxdepth 2 -type d -not -path "*/node_modules/*" -not -path "*/.git/*" \
     -not -path "*/.venv/*" -not -path "*/dist/*" | sort
```

**产物**：`<工程>/blueprint.md` 的前两节（系统定位 + 核心功能候选清单）

**验收点**：
- 代码量与分层结构已报给用户
- 核心功能候选 8–15 项，每项都指到了一个界面
- 每个技术架构结论都有 `文件:行` 落点
- 已单独记下「源码里没有的东西」清单

---

## 第 2 步 · 重绘浅色界面

```bash
# 复制骨架（按页面类型选）
cp "<skill>/assets/ui-shell/shell-shell-light.html"   "<工程>/ui/【整体界面页】.html"
cp "<skill>/assets/ui-shell/shell-list-light.html"    "<工程>/ui/【列表功能页】.html"
cp "<skill>/assets/ui-shell/shell-form-light.html"    "<工程>/ui/【录入功能页】.html"
cp "<skill>/assets/ui-shell/shell-detail-light.html"  "<工程>/ui/【详情功能页】.html"
# ... 一个页面一个文件，文件名 = 截图名
```

改完文案后：

```bash
python "<skill>/scripts/shoot_page.py" --in "<工程>/ui" --out "<工程>/images"
```

**产物**：`<工程>/images/*.png`（1600×900 @DPR2，实际 3200×1800）+ `<工程>/images/contact_sheet.png`

**验收点**（**必须逐张看拼版，不许跳过**）：
- 每张都是 1600×900（不是 3200×1800 之外的其他尺寸）
- 无滚动条、无内容溢出、无右侧大片空白
- 表头/按钮/状态标签缩到 1316 宽后仍可读（≥18px 源字号）
- 状态标签颜色语义正确（成功绿 / 警告橙 / 危险红 / 中性灰）
- 界面里的红是低饱和系统状态色

---

## 第 2.5 步 · 读元素坐标（写标注前必做）

标注坐标**不许目测**。把界面 HTML 灌进无头浏览器，直接读每个元素的真实 rect：

```bash
# 脚本会给界面注入一段探测 JS，--dump-dom 把结果吐回来
python "<skill>/scripts/rects.py" --in "<工程>/ui" > "<工程>/_build/rects.txt"
```

输出每行形如：

```
panel  主信息：选择主记录后自动带出  x=248 y=372 w=1334 h=434 | 槽 x=204 y=306 w=1097 h=357
```

`槽 x/y/w/h` 已经换算到 1316×740 的截图本地坐标系，**直接抄进标注定义**即可。

**怎么用**：
1. 按语义在输出里找对应的区块容器（`panel` / `bar` / `thead` / `tbody` / `pg` / `chips` …）
2. 框 = 该区块的 `槽 x/y/w/h`
3. 圆标 = `(槽 x − 24, 槽 y + 26)`，见 `references/04-layouts.md` 的圆标定位表
4. 若框落在贴着左边界（`x < 44`）或右端越界，先按 04 的规则收窄框，再算圆标

> 这一步只要几分钟，但能把「圆标压标题」「框落错区块」这两类返工全部省掉。

---

## 第 3 步 · 定蓝图

手工写 `<工程>/blueprint.md`，格式见 `references/03-deck-blueprint.md` 第四节。

**产物**：`<工程>/blueprint.md`

**验收点**：每页都有 7 个字段（页码 / 章节 / 动作式标题 / 形态 / 素材来源 / 源码落点 / 演讲备注）；反单调规则通过；截图页连续 ≤4 页。

---

## 第 4 步 · 画图 + 拼 deck

```bash
# 页面片段放在 <工程>/pages/ 下，每页一个 html（只写 <section class="page">…</section>）
ls "<工程>/pages"

# 组装：把片段按文件名顺序拼进 deck 骨架，并重写 images 引用
python "<skill>/scripts/build_deck.py" \
  --parts  "<工程>/pages" \
  --out    "<工程>/<系统名>-产品介绍.html" \
  --images "<工程>/images"
```

**产物**：`<工程>/<系统名>-产品介绍.html`（单文件多页 deck，图片用**相对路径** `images/xxx.png` 引用）

**验收点**：
- 浏览器打开能放映；`←/→` 翻页、圆点跳转、页码正常
- 加 `?all` 参数能用一屏渲染全部页面（供打印 / PDF / 无头截图）
- 按 `N` 键能看演讲备注
- 图片全部加载成功（无裂图）

---

## 第 5 步 · 质检

```bash
python "<skill>/scripts/check_deck.py" "<工程>/<系统名>-产品介绍.html"
```

脚本检查项：

| # | 检查项 | 判定 |
|---|---|---|
| 1 | 页面数量与 `blueprint.md` 一致 | 数量不等 → 报错 |
| 2 | 每页有 `.ptitle` / `.hr` | 缺 → 报错 |
| 3 | 截图页三数之和 = 1880（504+60+1316） | 不等 → 报错 |
| 4 | 截图的 `images/` 引用文件都存在 | 缺文件 → 报错 |
| 5 | 标注坐标不越界（`x+w≤1316`、`y+h≤740`） | 越界 → 报错 |
| 6 | 红色唯一性：统计 `#CC0000` 出现的语义组数 | > 1 组 → 警告 |
| 7 | 截图页连续页数 ≤ 4 | 超过 → 警告 |
| 8 | 每个截图页的标注数与左栏要点数一致 | 不等 → 警告 |
| 9 | `traceability.csv` 行数 == 核心功能页数 | 不等 → 警告 |
| 10 | 无明显敏感串（`api_key`、`secret`、`password=`、内网 IP 段） | 命中 → 报错 |

**产物**：控制台报告

**验收点**：错误（error）项必须清零；警告（warn）项要逐条判断是否为真问题。

---

## 第 6 步 · 交付

```bash
# 打包（整目录，含 images）
cd "<工程>" && tar -czf "<系统名>-产品介绍.tar.gz" "<系统名>-产品介绍.html" images blueprint.md traceability.csv
```

**交付物四件**：

| 文件 | 说明 |
|---|---|
| `<系统名>-产品介绍.html` | ★ 主交付物，浏览器直接打开放映 |
| `images/` | 截图目录，**必须一起给** |
| `blueprint.md` | 页面蓝图（含源码落点，可追溯） |
| `traceability.csv` | 可追溯表（页号↔功能↔源码↔HTML↔截图↔标注） |

**验收两条**：

1. **换一台机器打开**：把整个目录拷到另一个路径，确认图片仍然显示（验证相对路径真生效）
2. **打印成 PDF 走一遍**：`?all` 模式下打印，确认无空白页、ECharts 有渲染、截图不跨页

---

## 常见中断与恢复

| 中断在 | 恢复方式 |
|---|---|
| 截图脚本报"找不到浏览器" | 手工指定 `--chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"` |
| 某张截图底部内容缺失 | 见 `07-pitfalls.md` #2（视口尺寸问题），**不要改 CSS** |
| deck 里图片裂了 | 确认 html 与 `images/` 的相对位置没变；不要单独移动 html |
| ECharts 在打印 PDF 里空白 | 用 `?all` 模式打开再打印；或把 `assets/templates/echarts.min.js` 拷到 deck 同级 |
| 模板 SVG 复制后整体偏上 | 删掉模板自带的「图底说明」行并把 viewBox 收至内容下沿 |
