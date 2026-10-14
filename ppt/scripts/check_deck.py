#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_deck.py —— deck 质检。按 references/04-layouts.md 的清单逐项扫。

用法:
    python check_deck.py "某某系统-产品介绍.html"
    python check_deck.py deck.html --blueprint blueprint.md --traceability traceability.csv

判定: error 必须清零；warn 要逐条判断是否为真问题。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

PAGE_RE = re.compile(r'<section\s+class="page"(.*?)</section>', re.S | re.I)
ATTR_RE = re.compile(r'data-(\w[\w-]*)\s*=\s*"([^"]*)"')
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"')
RECT_RE = re.compile(r'<rect\b[^>]*>', re.I)
CIRCLE_RE = re.compile(r'<circle\b[^>]*>', re.I)
NUM_RE = re.compile(r'(-?\d+(?:\.\d+)?)')

DECK_W = 1920
SHOT_SLOT_W, SHOT_SLOT_H = 1316, 740
LCOL_W = 504
GUTTER = 60
CORE_MIN, CORE_MAX = 8, 15
SHOT_RUN_MAX = 4
ANNO_MIN, ANNO_MAX = 2, 4

SENSITIVE = [
    (r"api[_-]?key", "疑似 API Key"),
    (r"secret[_-]?key", "疑似 secret_key"),
    (r"password\s*[:=]", "疑似明文密码"),
    (r"sk-[A-Za-z0-9]{16,}", "疑似 OpenAI/DeepSeek 风格密钥"),
    (r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "疑似内网 IP（10.x）"),
    (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "疑似内网 IP（192.168.x）"),
    (r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b", "疑似内网 IP（172.16-31.x）"),
]


class Report:
    def __init__(self):
        self.errs: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []

    def err(self, m: str):
        self.errs.append(m)

    def warn(self, m: str):
        self.warns.append(m)

    def info(self, m: str):
        self.infos.append(m)

    def dump(self) -> int:
        for m in self.infos:
            print("[信息]", m)
        for m in self.warns:
            print("[警告]", m)
        for m in self.errs:
            print("[错误]", m)
        print()
        print(f"结果: 错误 {len(self.errs)} · 警告 {len(self.warns)}")
        if self.errs:
            print(">>> 错误必须清零后再交付。")
            return 1
        if self.warns:
            print(">>> 警告请逐条判断是否为真问题。")
        else:
            print(">>> 全项通过。")
        return 0


def attr_of(block: str, key: str) -> str | None:
    m = re.search(rf'data-{key}\s*=\s*"([^"]*)"', block, re.I)
    return m.group(1) if m else None


def nums_in(tag: str) -> list[float]:
    out = []
    for a in ("x", "y", "width", "height", "cx", "cy", "r"):
        m = re.search(rf'\b{a}\s*=\s*"(-?\d+(?:\.\d+)?)"', tag, re.I)
        if m:
            out.append((a, float(m.group(1))))
    return out


def is_shot_page(block: str) -> bool:
    return "shot-slot" in block


def is_cover(block: str) -> bool:
    return "cover-inner" in block or "end-inner" in block or "toc" in block


def main() -> int:
    ap = argparse.ArgumentParser(description="deck 质检")
    ap.add_argument("deck", help="deck html 路径")
    ap.add_argument("--blueprint", default=None, help="blueprint.md（校验页数一致）")
    ap.add_argument("--traceability", default=None, help="traceability.csv（校验行数）")
    args = ap.parse_args()

    if not os.path.isfile(args.deck):
        print(f"[错误] 文件不存在: {args.deck}")
        return 2

    with open(args.deck, "r", encoding="utf-8") as fh:
        html = fh.read()

    r = Report()
    pages = PAGE_RE.findall(html)
    if not pages:
        print("[错误] 未找到任何 <section class=\"page\">，deck 可能是空的。")
        return 1

    r.info(f"页数: {len(pages)}")

    core_pages = 0
    shot_flags, anno_counts = [], []

    for i, p in enumerate(pages, 1):
        title = attr_of(p, "title") or "(无 data-title)"
        notes = attr_of(p, "notes")
        head = f"P{i}「{title[:22]}」"

        # 2) 必备元素
        if 'class="ptitle"' not in p:
            if is_cover(p):
                pass  # 封面/落版用 h1，不强制 ptitle
            else:
                r.err(f"{head} 缺 <h2 class=\"ptitle\">")
        if 'class="hr"' not in p and "hr" not in p and not is_cover(p):
            r.err(f"{head} 缺 y=170 的 5px 分隔线 (.hr)")
        if not notes:
            r.warn(f"{head} 未写 data-notes（演讲备注）")

        shot = is_shot_page(p)
        shot_flags.append(shot)

        if shot:
            core_pages += 1
            # 3) 三数之和
            if f"width:{SHOT_SLOT_W}px" not in p.replace(" ", "") and \
               f"width: {SHOT_SLOT_W}px" not in p:
                r.warn(f"{head} 截图槽宽不是 {SHOT_SLOT_W}px（左 {LCOL_W} + 间距 {GUTTER} + 右 {SHOT_SLOT_W} = 1880）")
            # 4) 图片存在
            base = os.path.dirname(os.path.abspath(args.deck))
            for ref in IMG_RE.findall(p):
                if ref.startswith(("http", "data:")):
                    continue
                if not os.path.isfile(os.path.join(base, ref.replace("/", os.sep))):
                    r.err(f"{head} 图片缺失: {ref}")
            # 顶部总结条禁令
            if "summary-bar" in p or "总结条" in p:
                r.warn(f"{head} 截图页不应有顶部总结条")
            # 5) 标注越界 + 数量
            boxes, circles = 0, 0
            for tag in RECT_RE.findall(p):
                d = dict(nums_in(tag))
                if {"x", "y", "width", "height"} <= set(d):
                    if d["x"] + d["width"] > SHOT_SLOT_W + 0.5 or d["y"] + d["height"] > SHOT_SLOT_H + 0.5:
                        r.err(f"{head} 标注框越界: {tag.strip()[:90]}")
                    boxes += 1
            for tag in CIRCLE_RE.findall(p):
                d = dict(nums_in(tag))
                if {"cx", "cy", "r"} <= set(d):
                    if not (d["r"] - 1 <= d["cx"] <= SHOT_SLOT_W - d["r"] + 1 and
                            d["r"] - 1 <= d["cy"] <= SHOT_SLOT_H - d["r"] + 1):
                        r.err(f"{head} 标注圆标越界: {tag.strip()[:90]}")
                    circles += 1
            n_anno = max(boxes, circles)
            anno_counts.append(n_anno)
            if not (ANNO_MIN <= n_anno <= ANNO_MAX):
                r.warn(f"{head} 标注数 {n_anno}，建议 {ANNO_MIN}–{ANNO_MAX} 个")
            # 8) 与左栏要点数一致
            n_pts = len(re.findall(r'class="pt"', p))
            if n_pts and n_anno and n_pts != n_anno:
                r.warn(f"{head} 左栏要点 {n_pts} 条 vs 截图标注 {n_anno} 个，应一一对应")
        else:
            anno_counts.append(0)

    # 6) 红色唯一性（粗略：统计含 #CC0000 的不同"块"）
    red_hits = len(re.findall(r"#CC0000", html, re.I))
    if red_hits == 0:
        r.warn("全 deck 未出现 #CC0000（主色缺失？）")
    else:
        r.info(f"#CC0000 出现 {red_hits} 处（截图页的标注圆标/框/引线属同一语义，不算多个）")

    # 7) 截图页连续长度
    run, worst, start = 0, 0, 0
    for k, s in enumerate(shot_flags, 1):
        if s:
            run += 1
            if run > worst:
                worst, start = run, k - run + 1
        else:
            run = 0
    if worst > SHOT_RUN_MAX:
        r.err(f"截图页连续 {worst} 页（P{start} 起），超过上限 {SHOT_RUN_MAX} 页。"
              f"在第 {SHOT_RUN_MAX + 1} 页前插一页架构图/流程图/数据页。")
    elif worst:
        r.info(f"截图页最长连续 {worst} 页（上限 {SHOT_RUN_MAX}）")

    # 核心功能页数
    if core_pages:
        if not (CORE_MIN <= core_pages <= CORE_MAX):
            r.err(f"核心功能页（截图页）{core_pages} 页，应在 {CORE_MIN}–{CORE_MAX} 之间。")
        else:
            r.info(f"核心功能页: {core_pages} 页（区间 {CORE_MIN}–{CORE_MAX}）")

    # 10) 敏感串
    for pat, label in SENSITIVE:
        for m in re.finditer(pat, html, re.I):
            line = html[:m.start()].count("\n") + 1
            r.err(f"疑似敏感内容（{label}）在第 {line} 行: {m.group(0)[:40]}")
            break

    # 1) 与 blueprint 页数一致
    if args.blueprint and os.path.isfile(args.blueprint):
        with open(args.blueprint, "r", encoding="utf-8") as fh:
            bp = fh.read()
        n_bp = len(re.findall(r"^###\s*P?\s*\d+", bp, re.M)) or len(re.findall(r"^\|\s*\d+\s*\|", bp, re.M))
        if n_bp and n_bp != len(pages):
            r.err(f"blueprint 记录 {n_bp} 页，deck 实际 {len(pages)} 页，不一致。")
        elif n_bp:
            r.info(f"blueprint 页数一致（{n_bp}）")

    # 9) 可追溯表行数
    if args.traceability and os.path.isfile(args.traceability):
        with open(args.traceability, "r", encoding="utf-8") as fh:
            rows = [ln for ln in fh.read().splitlines() if ln.strip()]
        n = max(0, len(rows) - 1)
        if n < core_pages:
            r.warn(f"traceability.csv 有 {n} 行，但核心功能页有 {core_pages} 页，建议逐页补齐源码落点。")
        else:
            r.info(f"traceability.csv {n} 行")

    return r.dump()


if __name__ == "__main__":
    sys.exit(main())
