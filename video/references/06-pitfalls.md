# 06 · 已知坑清单

按「症状 → 根因 → 修法」组织。**动手前先扫一遍**，能省掉大部分返工。

---

## A. 配音（最容易整个卡住的一环）

### A1 合成全部 403 `WSServerHandshakeError`

**症状**：`edge_tts` 抛 403，换网络/换 IP/换请求头都没用。HTTPS 的 `voices/list` 却是 200。

**根因**：微软已废弃旧端点 `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1`（2026-10 起先在多数国家、10-12 起美国也一律 403）。这与出口 IP、系统时钟、库版本、请求头**全都无关**——不要在这上面浪费时间。Edge 155 已改用 `api.msedgeservices.com`，token 改放在 `Ocp-Apim-Subscription-Key` 查询参数里。

**修法**：调用 `edge_tts` 前先 `import edge_tts_patch`（技能自带 `scripts/edge_tts_patch.py`）。音色、语速、词级时间戳全都不变。

排查顺序（若打了补丁仍失败）：
1. 确认补丁真的 import 成功（`print(edge_tts.communicate.WSS_URL)` 应含 `msedgeservices`）
2. 用 HTTPS `voices/list` 探活：200 说明网络没问题，问题在 WSS 端点
3. 检查有没有代理劫持 WSS（`env | grep -i proxy`）

### A2 `drm.py` 在中文 Windows 上报日期解析错误

**症状**：走到 DRM 校验时抛异常，或 `Sec-MS-GEC` 生成失败。

**根因**：`drm.py` 用 `strptime(..., "%a, %d %b %Y ...")` 解析服务端返回的英文日期，中文 locale 下 `%a`/`%b` 认不出 `Mon`/`Oct`。

**修法**：`edge_tts_patch.py` 已把 `DRM.parse_rfc2616_date` 换成 `email.utils.parsedate_to_datetime`。

### A3 音频变了但时长没变（改了文案没生效）

**症状**：改了 `narration.json`，`timing.json` 里该段时长还是旧的。

**根因**：`audio/` 有缓存，按「段 id + 语速」命名，改文案不会自动失效。

**修法**：删掉改动那段的 `<id><rate>.mp3` 和 `<id><rate>.words.json`，再跑 `build_audio.py`。

### A4 全片超时长

**症状**：合成完发现超出目标时长。

**修法**：不要靠调 `rate` 硬压。顺序是 **① 删内容 → ② 提高 rate（最多 `+12%`）**。而且改稿阶段就该用 `build_audio.py --dry` 估时长，别等合成完才发现。

---

## B. 截图

### B1 截图尺寸不对（1600×900 变成 1080×617 之类）

**症状**：`--window-size=1600,900` 但输出尺寸小一圈。

**根因**：Windows 显示缩放（本机 150%）会等比缩小视口。

**修法**：无头浏览器必须加 **`--force-device-scale-factor=1`**。`shoot_page.py` 里已有，不要删。

### B2 高亮框对不准

**症状**：`focus` 框偏上/偏左/整体错位。

**根因**：截图比例不是 16:9，`objectFit:cover` 把图裁了，而 focus 是按整图比例算的。

**修法**：所有截图先过 `prep_shots.py` 归一化到 1600×900。**不要直接把不同比例的图丢进 `remotion/public/shots/`。**

### B3 说明条折出孤字

**症状**：左下角说明条把「场景 → 概念 → 实体」折成「……实 / 体」。

**根因**：说明条宽 212px，中文断行会把最后一个字甩到下一行。

**修法**：`scenes.tsx` 里已给 callout/note 加了 `textWrap: 'balance'`。新增文字容器时记得也加。

### B4 截图正好 1600×900，但**底部内容被切掉**（页脚/分页器消失）

**症状**：图片尺寸完全正确，可是页面最底下那条（分页器、底部按钮）不见了，或者下方多出一条空白带。

**根因**：`--window-size` 设的是**窗口尺寸，不是视口尺寸**。窗口标题栏 + 边框会吃掉约 **16×95px**，真实视口只有 1584×805。页面按 900px 高布局，最后 95px 就永远拍不到。

排查手法（值得记住）：在页面里塞一段诊断脚本，无头跑 `--dump-dom` 打印 `window.innerWidth / innerHeight`，就能看到 `iw:1584, ih:805`。

```bash
# 关键：先确认视口，不要靠猜
chrome --headless=new --window-size=1600,900 --dump-dom <带诊断脚本的页面>
```

**修法**：`shoot_page.py` 已处理——**窗口开大一圈再裁**：

```python
"--window-size=%d,%d" % (w + 40, h + 120),   # 开大，保证视口 ≥ 目标
# 截图后
im = Image.open(png)
if im.size != (w, h) and im.width >= w and im.height >= h:
    im.crop((0, 0, w, h)).save(png, "PNG", optimize=True)
```

自己写截图命令时，若发现"尺寸对但内容缺"，先怀疑这条，**不要先去改 CSS 布局**（会白改）。

### B5 截图内容不变（像是拿到了旧缓存）

**症状**：改了 HTML，重新截图，出来的还是上一版。

**根因**：Chrome 的用户数据目录留了缓存。

**修法**：`shoot_page.py` 已加两条——渲染每页前 `shutil.rmtree(tmpdir, ignore_errors=True)` 清 profile，启动参数带 `--incognito`。**不要图省事复用同一个 profile 连续拍多页。**

### B6 ★ 探针帧里页面左侧被切掉半个词（品牌名变成「理平台」）

**症状**：截图本身完整，但视频分镜里画面左边少了一块，能把一个词切成两半。

**根因**：截图分镜带缓推镜头（Ken Burns），`scale(1.055)` + `-8px` 平移意味着**左右各裁掉约 54px**（图像空间）。骨架侧边导航的左边距只有 12~24px，自然被切。

注意它**不是**截图或 CSS 的问题——去查截图和布局会白费功夫。判断方法：探针帧上被切的量 ≈ 全宽（1600）的 3% 左右，且**右侧对称也少了一点**，就是裁剪而非布局溢出。

**修法**（技能已修）：
1. `scenes.tsx` 把幅度收小到 `scale 1.02 → 1.004`、平移 `±5px / ±4px`，最大裁边约 20px；
2. 骨架左侧导航内边距 12px → 22px、顶栏 24px → 30px，给镜头留出安全边距。

换算公式（调参用）：`卡片像素 × 1.143 = 图像像素`，`裁边量 ≈ (1400 × 幅度 / 2 + 平移) × 1.143`。
详见 `references/02-ui-redraw.md` 的「缓推镜头会裁边」。

---

## C. Remotion 渲染

### C1 打包阶段报错，提示无法删除 `node_modules/.cache/webpack/...`

**根因**：受限环境下所有删除操作走回收站并 fail-closed，Remotion 清理缓存失败直接中断渲染。

**修法**：`remotion.config.ts` 里 `Config.overrideWebpackConfig((c) => ({ ...c, cache: false }))`——关掉持久化缓存，该目录永不生成，Remotion 判定为不存在从而跳过清理。代价是每次重新打包（几十秒）。

### C2 渲染报浏览器启动失败 / `spawn EFTYPE`

**根因**：Remotion 自带的 Chrome Headless Shell 在部分机器上不可用。

**修法**：用系统 Chrome：

```bash
--chrome-mode=chrome-for-testing \
--browser-executable="C:/Users/<用户>/AppData/Local/Google/Chrome/Application/chrome.exe"
```

新版 Chrome 没有旧版 headless，`--chrome-mode=chrome-for-testing` 不能省。

### C3 长片渲染卡死

**症状**：跑几分钟没输出，或者跑到某个时间点不动了。

**根因**：一次渲染几千帧内存吃满。

**修法**：分块。`render_chunks.sh` 已按每块约 2000 帧自动切，`--concurrency=4`，失败自动降 2 重试一次，最后 ffmpeg `-c copy` 无损拼接。

### C4 用 `remotion still` 验证画面，长时间无响应

**根因**：本机 `still` 命令不稳定（常 7 分钟以上无响应）。

**修法**：**不要用 `remotion still` 验画面**。用 `probe_render.sh` 渲染一小段再抽帧，稳定且 1 分钟内出结果。

### C5 渲染进度看起来卡死

**根因**：把输出管到 `| tail`，进度被缓冲。

**修法**：重定向落盘 `> render.log 2>&1`，再看文件。

### C6 依赖安装卡死

**根因**：npm 官方源不通。

**修法**：一律 `--registry=https://registry.npmmirror.com`（`project/.npmrc` 里已写死）。

### C7 ★ 渲染其实失败了，但脚本报"成功"（复用上一次的 mp4）

**症状**：探针/分块渲染日志最后一行是 `Encoded 750/750`、`+ out/probe/probe.mp4 8.5 MB` 之类，看起来正常；但**画面是上一版的**，改了图却看不到变化。

**根因**：两个因素叠加——
1. Remotion 在**编译阶段**就失败（例如 `diagrams.tsx` 语法错误）时，可能没走到写文件那一步；
2. 输出路径上**已经有上一轮留下的 `probe.mp4` / `part1.mp4`**，脚本判断 `[ -f "$out" ]` 成立，就当成成功了。

日志被 `| tail -4` / `| tail -6` 截断，Error 行已经被截掉，所以只看到"像成功"的尾巴。

**修法**（技能里的脚本都已按此处理，**自己写渲染命令时也要照做**）：

```bash
rm -f out/probe/probe.mp4          # 渲染前先删旧产物
"$NODE" "$CLI" render ...           # 渲染
if [ ! -f out/probe/probe.mp4 ]; then
  echo "渲染失败。常见原因：diagrams.tsx 编译错误（往上看 Error 行）、Chrome 路径不对、并发过高。"
  exit 1
fi
```

同理 `render_chunks.sh` 每块前先 `rm -f "$out"`，`finalize.sh` 帧数不一致直接 `exit 1`（不要只 warn）。

**判断依据**：不要看日志末尾，要看**产物时间戳**——`ls -la` 一下，时间戳没更新就是没渲染。

---

## D. 验收时的误判（最容易白忙一阵）

### D1 抽帧看到"字幕只有暗色文字、没有底条"

**根因**：字幕整条（含深色底）共用同一个 `opacity`，在 `end - 0.16s ~ end` 之间淡出。抽帧正好落在淡出瞬间。

**修法**：**换一帧（间隔 ≥ 5 帧）即可确认正常**。不要误判成渲染缺陷去改代码。

### D2 静音检测报出多个"断音点"

**根因**：段间本来就插了 `gap = 0.7s` 静音，是有意留白。

**修法**：只关注落在**块边界**（各块累加时长）上的静音。段间留白不用管。

### D3 拼接后帧数不一致

**根因**：某块渲染失败被跳过，或块范围有重叠/缺口。

**修法**：`finalize.sh` 会打印「期望帧数 vs 实际帧数」。不等就回去看 `render_chunks.sh` 的日志，确认每块都产出了 mp4。

### D4 `make_props.py` 报一堆「+0.70s 缝隙/重叠」

**根因**：解说段之间本来就插了 `gap = 0.7s` 静音（见 `timing.json` 的 `gap`），**这是设计留白，不是 bug**。自检脚本如果只按"上一场结束 == 下一场开始"判断，就会把每段都报成问题。

**修法**：判据要**排除段间设计留白**：

```python
seg_gap = float(timing.get("gap") or 0.7)
d = sc["start"] - scenes[i - 1]["end"]
if abs(d) > 0.02 and abs(d - seg_gap) > 0.05:
    warn.append(...)      # 只有既不为 0 也不是 gap 的，才是真问题
```

技能里的 `make_props.py` 已按此处理。看到这类告警先核对 `timing.json` 里的 `gap` 值，别急着改分镜。

---

## E. 内容与成片质量

### E1 声画错位（最刺眼，且只在成片里才看得见）

**症状**：画面在讲 A，字幕在讲 B。

**根因**：分镜的 `f0/f1` 是按段内比例估的，而解说段内部的**语义分界**不一定落在那个比例上。典型场景：解说后半段在讲某张图里的细节，而分镜已经把画面切到截图了。

**修法**：
1. 分镜前先**逐句核对每段解说的落点**——把字幕按场景标注出来看一遍（写个小脚本读 `timing.json` 的 captions，按场景起止时间打标签）
2. 凡是一句话在讲「图里的东西」，那张图必须铺到这句话结束
3. 出成片后**必须抽帧复核**（`references/05-pipeline.md` 第 5 步），这是唯一的兜底

### E2 图表文字溢出 / 被裁

**根因**：中文比英文宽，估算不足；或者元素坐标超出 1600×826 被静默裁掉。

**修法**：中文按 `字号 × 1.0` 估宽；`ChipS` 用 `chipW()` 算。写完在探针帧里逐张确认。宁可缩小字号或换行，不要让它溢出。

### E3 图表同时出现，没有节奏

**根因**：所有元素用同一个 `op`。

**修法**：每个元素用 `seqAt(f, fps, index, step, delay)` 错峰，`delay` 按讲解顺序递增（约 0.35~0.5s 一个）。

### E4 ★ 一排标签互相压字（`规则引擎` 和 `状态机` 叠成 `规则引擎状态机`）

**症状**：探针帧里一排 chip 的后半段叠在一起，字看不清。

**根因**：用**当前标签的宽度**去推下一个标签的 x 坐标，比如 `x + j * (chipW(items[j], 24) + 18)`。标签长度不等时，步长按短的算就会追尾。这是最典型的 off-by-one 式排版 bug。

**修法**：改成**按每个标签自己实际宽度累加**，并且**在超出画布时给出可见警告**（否则它会安静地画到画布外面）：

```tsx
let cx = x;
items.forEach((t, i) => {
  out.push(<ChipS key={t + i} x={cx} y={y} text={t} op={ops[i] ?? 1} tone={tone} size={size} />);
  cx += chipW(t, size) + gap;          // ← 用 t 自己的宽度
});
if (cx - gap > maxRight) out.push(<text ... fill={C.danger}>⚠ 标签超出画布（宽 xxxpx，可用 xxxpx），请减少数量或缩小字号</text>);
```

技能里的 `ChipRow` 组件就是这么写的，**优先用它，不要手写 for 循环排 chip**。改完必须回探针帧确认。

### E5 `diagrams.tsx` 编译不过：`The character ">" is not valid inside a JSX element`

**根因**：JSX 文本节点里出现裸的 `>` 或 `}`。中文文案里想写"大于"很容易顺手打 `>`，例如 `可用 {n}px` 前面接一个 `>`。

**修法**：把整段折成**字符串拼接**，不要混着 JSX 插值：

```tsx
// ✗ 报错
<text>宽 {w}px > 可用 {m}px</text>
// ✓
<text>{'宽 ' + w + 'px，可用 ' + m + 'px'}</text>
```

中文文案里要写"大于"就用「大于」或「→」，别用 `>`。**注意 `>` 在 JSX 属性里是合法的**（如 `x > 0`），只在文本节点里非法。

---

## F. 环境与工程

### F1 不要打包 node_modules

Remotion 依赖约 **570MB**，不可能塞进技能包/市场。技能里只放源代码模板，运行时用 `setup_remotion.sh` 复用或安装。

### F2 中文路径与脚本文件

Windows 下脚本里避免写含中文的可执行脚本文件（`.ps1` / `.bat`）——编码会破坏文件名。用 `execute_command` 直接跑命令，或者写 UTF-8 的 `.py` / `.sh`。

### F3 删除操作会被拦

受限环境里删除走回收站并 fail-closed。写清理逻辑时用 `ignore_errors=True` 兜底，或干脆"另存新文件、不覆盖旧文件"。

### F4 素材来源要先确认

用户目录里常有几十张同名或近似的截图。**开工前先问清用哪一张**，别猜。
