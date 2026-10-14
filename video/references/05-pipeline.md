# 05 · 五步流水线与工程目录

## 工程目录约定

每做一支视频，建一个独立工程目录（放在用户指定位置，或 `<当前项目>/video-<主题>/`）：

```
<工程目录>/
├── src/                       源码只读引用（源仓库路径即可，不必复制）
├── script/
│   ├── narration.json         分段解说稿（你写）
│   └── storyboard.json        分镜（你写）
├── ui/                        重绘的 HTML 界面（你写，一个页面一个文件）
├── shots_raw/                 无头浏览器截出来的原始 PNG
├── audio/                     逐段 mp3 + 词级时间戳（脚本产出，带缓存）
├── timing.json                全片绝对时间轴（脚本产出）
├── 解说稿.md / *.srt           脚本产出
├── contact_sheet.png          截图拼版（脚本产出，用来目视确认）
├── preview/probe/             探针抽帧（脚本产出，用来验收版式）
├── remotion/
│   ├── src/                   Remotion 组件（setup 时从技能模板复制）
│   ├── public/shots/          归一化后的截图
│   ├── public/audio/          配音 mp3
│   ├── props.json             正式分镜（make_props 产出）
│   ├── probe.json             探针分镜（probe_props 产出）
│   └── out/parts/part*.mp4    分块渲染产物
├── <标题>.mp4                 最终成片
├── <标题>.srt
└── <标题>_解说稿.md
```

**所有脚本默认以「当前工作目录」为工程目录**，也可以用 `--dir` / `CW_VIDEO_DIR` 指定。

```bash
cd "<工程目录>"          # 之后所有命令都在这里执行
```

---

## 第 0 步：环境准备（只做一次）

```bash
PY="<python>"            # 需要 edge-tts 与 pillow；用已装好的 venv
python "$PY" <skill>/scripts/check_env.py
```

`check_env.py` 会逐项报告，缺什么直接给修复命令。重点三项：`edge_tts`、无头浏览器、Remotion 依赖。

```bash
bash <skill>/scripts/setup_remotion.sh "<工程目录>"
```

优先复用本机已有 Remotion 依赖（秒级就绪）；没有才联网安装（走 npmmirror，约 1~2 分钟）。脚本也会把模板源码复制到 `<工程目录>/remotion/`。

---

## 第 1 步：勘察源码 → 大纲 → 确认讲解对象

读 `references/01-code-discovery.md`，产出候选清单，**让用户选定要讲哪个子系统/模块/功能**。

同时确认**目标时长**（≤ 10 分钟），据此定字数预算（`references/03-narrative.md`）。

---

## 第 2 步：重绘界面 → 截图 → 归一化

读 `references/02-ui-redraw.md`。

```bash
# 1) 把 assets/ui-shell/ 的骨架复制到 ui/ 改名，按源码里的还原清单改文案
#    一个页面一个 html

# 2) 截图（1600×900）
python <skill>/scripts/shoot_page.py --in ui --out shots_raw

# 3) 归一化 + 拼版，目视确认
python <skill>/scripts/prep_shots.py --raw shots_raw --out remotion/public/shots
```

**跑完第 3 步先看 `contact_sheet.png`**，确认没有溢出、没有白边、文案没问题，再往下走。

---

## 第 3 步：写解说稿 → 合成配音 → 拿时间轴

```bash
# 1) 写 script/narration.json（格式见 references/03-narrative.md）

# 2) 先估算时长，超了就删内容
python <skill>/scripts/build_audio.py --dir . --dry

# 3) 正式合成（会产出 timing.json / .srt / 解说稿.md，并自动同步 mp3 到 remotion/public/audio）
python <skill>/scripts/build_audio.py --dir .
```

这一步会：逐段调用云扬合成 → 抓词级时间戳 → 切字幕 → 拼全片绝对时间轴 → 打印每段时长与全片时长。

**跑完一定要看最后那行**：`全片时长 xx.xxs = x:xx（未超 10 分钟上限）`。超了回第 1 步删内容，然后**删掉 `audio/` 里对应的缓存重新合成**（缓存按「段名 + 语速」命名，改了文案不会自动失效——删掉该段 mp3 与 words.json 即可）。

---

## 第 4 步：写分镜 + 画图 → 探针验版式

```bash
# 1) 在 remotion/src/diagrams.tsx 里加自己的图，并注册进 DIAGRAMS
#    （复制 ARCH / FLOW 示例改文案最快；图元 API 见 references/04-diagrams.md）

# 2) 写 script/storyboard.json（格式见 references/04-diagrams.md）

# 3) 生成正式分镜
python <skill>/scripts/make_props.py --dir .

# 4) 探针：每个分镜压成 5 秒渲染一遍，逐张抽帧
bash <skill>/scripts/probe_render.sh
```

第 4 步会产出 `preview/probe/*.png`，**每个分镜两帧**，逐张看：

| 帧 | 取样点 | 看什么 |
|---|---|---|
| `NN_xxx_a.png` | 分镜内 0.5s | **画面边缘有没有被裁**（缓推镜头此刻幅度最大）、错峰动画第一批元素落位了没 |
| `NN_xxx_b.png` | 分镜内 3.5s | 文字有没有溢出、元素有没有被裁、高亮框有没有框住该框的东西 |

> 为什么要两帧：只取稳定态会漏掉"入场帧把品牌名切掉半个词"这类问题——镜头是缓缓推进的，**最长的那一刀在起始帧**（见 `references/06-pitfalls.md` B6）。

改图 / 改 `focus` → 重跑 `probe_render.sh`，直到全部通过。**这一步通常要来回 2~3 轮，是正常的。**
探针一次只要 1~2 分钟，正式渲染要十几分钟——所有版式问题都必须在这里解决。

---

## 第 5 步：正式渲染 → 拼接 → 验收交付

```bash
# 分块渲染（帧数自动从 props.json 读，目标每块约 2000 帧）
bash <skill>/scripts/render_chunks.sh

# 拼接 + 验收 + 产出交付物
bash <skill>/scripts/finalize.sh
```

`render_chunks.sh` 打印的帧数要与 `props.json` 的总帧数一致；`finalize.sh` 会把三个交付物复制到工程根目录：

- `<标题>.mp4`
- `<标题>.srt`
- `<标题>_解说稿.md`

### 交付前的人工验收（必做，两条）

```bash
# 1) 抽帧看字幕与画面的对位
FF="<ffmpeg 目录>"
for t in 5 30 75 150 240; do
  "$FF/ffmpeg.exe" -y -ss $t -i "<标题>.mp4" -vframes 1 -vsync 0 "preview/chk_$t.png" -loglevel error
done
```

逐张看：字幕内容与画面内容是否说的是同一件事。**声画错位是这类视频最刺眼的缺陷**，而且只在成片里才看得出来。

```bash
# 2) 时长与流信息
"$FF/ffprobe.exe" -v error -show_entries format=duration,size \
  -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of default=noprint_wrappers=1 "<标题>.mp4"
```

期望：`1920×1080`、`30/1`、`h264` + `aac`、时长与你设定的目标一致。

---

## 提速技巧

| 想省时间 | 做法 |
|---|---|
| 改文案不想重配全部 | `audio/` 里缓存按段命名，只删改动的那段 mp3 + words.json |
| 只改了一张截图 | 归一化后只需重渲受影响的分块（先把 `out/parts` 里对应块删掉，再改 `render_chunks.sh` 的块循环） |
| 只想看某几张图 | `probe_render.sh` 后只 Read 关心的那几张 PNG |
| 渲染卡住 | 见 `references/06-pitfalls.md` —— 多数是并发太高或 Chrome 路径不对 |
