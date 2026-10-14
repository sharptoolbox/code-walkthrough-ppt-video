# 截图标注层规范

标注层是 **deck 页面上的 SVG 覆盖层**，不是烙进截图的像素。理由：

1. **底图干净可复用** —— 同一张截图能在不同页讲不同重点
2. **矢量不糊** —— deck 有居中缩放，位图上画标记会跟着缩放一起发虚
3. **可调** —— 改坐标不用重截图

---

## 一、DOM 结构

```html
<div class="shot-slot">
  <img src="images/13-【功能名】.png" alt="【功能名】界面示意">
  <svg class="anno" viewBox="0 0 1316 740" preserveAspectRatio="none">
    <!-- 标注元素放这里 -->
  </svg>
</div>
```

`viewBox="0 0 1316 740"` 与截图槽尺寸一致 → **SVG 坐标 = 槽内像素**，可以直接量。

---

## 二、颜色与尺寸

| 元素 | 规格 |
|---|---|
| 编号圆标 | `circle r="17"`，填充 `#CC0000`，白色数字 `font-size:18` `font-weight="500"`，`text-anchor="middle"` `dominant-baseline="central"` |
| 高亮框 | `rect`，`stroke="#CC0000"` `stroke-width="1.5"` `fill="rgba(204,0,0,0.10)"`，`rx="2"` |
| 引线 | `line`，`stroke="#CC0000"` `stroke-width="0.5"` `stroke-dasharray="4 4"` |
| 标注文字（可选） | `font-size="13"` `fill="#CC0000"`，放框上方 6px 或圆标右侧 8px |

**只有一个红**：标注的全部元素（圆标 / 框 / 引线 / 文字）都用 `#CC0000`，它们属于同一个语义——「这是本页要你看的地方」。

界面的系统状态红用低饱和 `#C4320A`，不算 deck 的红，但**同一页里界面红与标注红不能紧邻**，避免观众混淆。

---

## 三、三种标注画法

### ① 区域高亮 + 编号（最常用）

圈出一块界面区域，编号放在框的左上角外侧。

```html
<rect x="86" y="212" width="300" height="44" rx="2"
      fill="rgba(204,0,0,0.10)" stroke="#CC0000" stroke-width="1.5"/>
<circle cx="66" cy="212" r="17" fill="#CC0000"/>
<text x="66" y="212" font-size="18" font-weight="500" fill="#FFFFFF"
      text-anchor="middle" dominant-baseline="central">1</text>
```

### ② 编号 + 引线（指向很窄的目标，如一个按钮）

框画不下（目标太窄）时，用圆标 + 短引线指过去。

```html
<circle cx="1180" cy="540" r="17" fill="#CC0000"/>
<text x="1180" y="540" font-size="18" font-weight="500" fill="#FFFFFF"
      text-anchor="middle" dominant-baseline="central">2</text>
<line x1="1163" y1="540" x2="1120" y2="540" stroke="#CC0000" stroke-width="0.5"
      stroke-dasharray="4 4"/>
```

### ③ 编号 + 引线 + 文字（需要点名具体字段时）

```html
<circle cx="240" cy="150" r="17" fill="#CC0000"/>
<text x="240" y="150" font-size="18" font-weight="500" fill="#FFFFFF"
      text-anchor="middle" dominant-baseline="central">3</text>
<line x1="257" y1="150" x2="330" y2="150" stroke="#CC0000" stroke-width="0.5"
      stroke-dasharray="4 4"/>
<text x="336" y="150" font-size="13" fill="#CC0000" dominant-baseline="central">字段校验提示</text>
```

> 文字标注慎用——文字多了会盖住界面。能靠左栏讲清的就别标在图上。

---

## 四、约束（check_deck.py 会检查）

| # | 约束 | 原因 |
|---|---|---|
| 1 | 每张截图 **2–4 个标注** | 超过 4 个说明这页想讲的事太多，拆页 |
| 2 | 编号 ①②③ 与**左栏要点一一对应**，顺序也一致 | 这是把左右栏"绑"起来的关键 |
| 3 | 标注框 `x+w ≤ 1316`、`y+h ≤ 740` | 越界会画到截图外面 |
| 4 | 引线长度 ≤ 60px | 长了会穿过界面文字 |
| 5 | 标注**不压**关键文字 / 按钮文案 / 表头 | 压住了观众反而看不清 |
| 6 | 引线**不穿**表格文字 | 同上 |
| 7 | 编号从 1 开始连续，不跳号 | 跳号观众会以为漏了 |

---

## 五、标定流程（读真实 rect，不许目测）

坐标只有一个口径：**截图本地坐标系 1316 × 740 的像素值**，deck 里 SVG 直接用，`blueprint.md` 里也用同一套数值。

```bash
python "<skill>/scripts/rects.py" --in "<工程>/ui" > "<工程>/_build/rects.txt"
```

`rects.py` 在无头浏览器里读元素的真实 `getBoundingClientRect()`，输出的 `槽 x/y/w/h` 已经换算到这个坐标系，**直接抄进标注定义**。

> **不要凭记忆或目测写坐标。** 缩略图与渲染图的比例会骗人，估算误差常在 20–40px，足以让圆标压住标题、让框落错区块。越界由 `check_deck.py` 兜底（`x+w ≤ 1316`、`y+h ≤ 740`）。

---

## 六、常见错误

| 症状 | 根因 | 修法 |
|---|---|---|
| 标注整体偏移 | 截图比例不是 16:9，`object-fit:cover` 裁过 | 截图必须先归一化到 1600×900 |
| 标注比预期大一圈 | 把 3200×1800 的物理像素当成了 1600×900 的 CSS 像素 | 坐标一律按 **1316×740 槽尺寸**算，不看 PNG 实际像素 |
| 圆标数字不居中 | 漏了 `dominant-baseline="central"` | 补上 |
| 标注被截图盖住 | SVG 放在 `<img>` 之前 | SVG 必须放在 `<img>` 之后，或给 `.anno` 加 `z-index` |
| 引线穿过表格文字 | 起点选在了文字那一侧 | 把圆标挪到空白处，引线走空白通道 |
