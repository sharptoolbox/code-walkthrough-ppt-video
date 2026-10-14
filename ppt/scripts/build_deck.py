#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_deck.py —— 把 <工程>/pages/*.html 片段拼成单文件多页 deck。

用法:
    python build_deck.py --parts pages --out "某某系统-产品介绍.html" --images images
    python build_deck.py --parts pages --out deck.html --title "某某系统 · 产品介绍"

片段格式（每个文件一个 <section class="page">）:
    <section class="page" data-title="动作式结论标题" data-notes="讲这页时说的话">
      <h2 class="ptitle">动作式结论标题</h2>
      <div class="kicker">CORE 01 / 08</div>
      <div class="hr"></div>
      ...
    </section>

片段按文件名自然排序（推荐 01-、02-、… 前缀，保证页序 = 文件名序）。

产物：单文件 HTML deck（图片用相对路径 images/ 引用，所以交付必须整目录一起给）。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL_DIR, "assets", "deck", "deck-template.html")

IMG_REF = re.compile(r'<img[^>]+src="([^"]+)"')
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")

# 封面 / 目录 / 落版这类整幅版式本来就没有标题区与 y=170 分隔线，豁免这两项检查
FRAME_EXEMPT = ("cover-inner", "toc", "end-inner")


def natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def load_fragment(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read()
    # 允许片段里带 <style> / <script>，但只取 <section class="page"> 及其后的内容
    m = re.search(r'<section\s+class="page"', txt)
    if not m:
        raise ValueError("片段里找不到 <section class=\"page\">")
    body = txt[m.start():]
    # 去掉片段自己的 </body></html> 结尾
    body = re.sub(r"</body>\s*</html>\s*$", "", body, flags=re.I).strip()
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description="页面片段 → 单文件 deck")
    ap.add_argument("--parts", default="pages", help="页面片段目录")
    ap.add_argument("--out", required=True, help="输出的 deck html 路径")
    ap.add_argument("--images", default="images", help="图片目录（用于校验引用是否存在）")
    ap.add_argument("--title", default=None, help="deck 标题（默认取输出文件名）")
    ap.add_argument("--template", default=TEMPLATE, help="deck 骨架模板路径")
    args = ap.parse_args()

    if not os.path.isfile(args.template):
        print(f"[错误] 骨架模板不存在: {args.template}")
        return 2
    if not os.path.isdir(args.parts):
        print(f"[错误] 片段目录不存在: {args.parts}")
        return 2

    files = sorted(
        (f for f in os.listdir(args.parts) if f.lower().endswith((".html", ".htm"))),
        key=natural_key,
    )
    if not files:
        print(f"[错误] {args.parts} 下没有 .html 片段")
        return 2

    with open(args.template, "r", encoding="utf-8") as fh:
        tpl = fh.read()

    title = args.title or os.path.splitext(os.path.basename(args.out))[0]
    pages, warn, err = [], [], []

    for name in files:
        p = os.path.join(args.parts, name)
        try:
            frag = load_fragment(p)
        except Exception as exc:  # noqa: BLE001
            err.append(f"{name}: {exc}")
            continue
        if not any(k in frag for k in FRAME_EXEMPT):
            if "ptitle" not in frag:
                err.append(f"{name}: 缺 <h2 class=\"ptitle\">")
            if 'class="hr"' not in frag and "class='hr'" not in frag:
                err.append(f"{name}: 缺 <div class=\"hr\"></div>（y=170 分隔线）")
        if "data-notes" not in frag:
            warn.append(f"{name}: 未写 data-notes（演讲备注），按 N 键会提示「本页未写备注」")
        pages.append((name, frag))

    if err:
        print("[错误] 以下片段不合规，已中止：")
        for e in err:
            print("  -", e)
        return 1

    deck = tpl.replace("<!--PAGES-->", "\n\n".join(frag for _, frag in pages))
    deck = deck.replace("__TITLE__", title)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(deck)

    # 校验图片引用
    base = os.path.dirname(os.path.abspath(args.out))
    refs = set()
    for ref in IMG_REF.findall(deck):
        if ref.lower().endswith(IMG_EXT) and not ref.startswith(("http", "data:")):
            refs.add(ref)
    missing = []
    for ref in sorted(refs):
        cand = os.path.join(base, ref.replace("/", os.sep))
        if not os.path.isfile(cand):
            alt = os.path.join(args.images, os.path.basename(ref).replace("/", os.sep))
            if not os.path.isfile(alt):
                missing.append(ref)

    print(f"骨架   : {args.template}")
    print(f"标题   : {title}")
    print(f"片段   : {len(pages)} 页，来自 {args.parts}")
    for i, (name, _) in enumerate(pages, 1):
        print(f"   P{i:>2}  {name}")
    print(f"图片   : 引用 {len(refs)} 张")

    if missing:
        print("\n[错误] 以下图片引用找不到文件（deck 会裂图）：")
        for m in missing:
            print("  -", m)
        print("  修法：确认 --images 目录里有这些文件，或片段里的相对路径写对。")
        return 1

    if warn:
        print("\n[警告]")
        for w in warn:
            print("  -", w)

    size_kb = os.path.getsize(args.out) / 1024
    print(f"\n产物   : {args.out}  ({size_kb:.1f} KB)")
    print(">>> 浏览器打开放映；←/→ 翻页，N 看备注，URL 加 ?all 一次渲染全部页面（供打印/PDF）。")
    print(">>> 交付必须整目录一起给（html + images/），单独发 html 会丢图。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
