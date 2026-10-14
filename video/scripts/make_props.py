# -*- coding: utf-8 -*-
"""
分镜生成：script/storyboard.json + timing.json -> remotion/props.json

设计要点：**分镜时间按「段内比例」切分**，不写绝对秒数。
配音重合成后每段时长会变（改文案、换语速都会变），按比例切就自动跟随，
不用回头改分镜。这是三支成片反复踩过的地方。

storyboard.json：
{
  "brand": "XX 平台",                     // 右上角水印，"" 则不显示
  "endTitle": "XX 平台 · 订单模块",
  "endSubtitle": "从下单到履约，全链路可追溯",
  "endFooter": "PRODUCT V1.0",
  "chapters": [                            // 章节角标（顺序即编号）
    {"name": "订单受理", "from": "订单受理"},        // to 省略 → 到下一章开头
    {"name": "库存校验", "from": "库存校验", "to": "履约跟踪"}
  ],
  "scenes": [
    {"seg": "片头", "f0": 0, "f1": 1, "kind": "cover",
     "shot": "shots/00-cover.png", "title": "订单模块", "subtitle": "……", "chapter": ""},

    {"seg": "订单受理", "f0": 0.0, "f1": 0.45, "kind": "diagram", "id": "ARCH",
     "chapter": "订单受理", "callout": "一句话概括", "note": "边界提示（可省）"},

    {"seg": "订单受理", "f0": 0.45, "f1": 1.0, "kind": "shot", "shot": "shots/01-list.png",
     "chapter": "订单受理",
     "focus": [{"x":0.10,"y":0.09,"w":0.30,"h":0.05,"label":"已登记的数据源"}],
     "callout": "看这里", "note": "可省"}
  ]
}

用法：python make_props.py --dir <工程目录>
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.environ.get("CW_VIDEO_DIR") or os.getcwd())
    args = ap.parse_args()
    base = os.path.abspath(args.dir)

    tpath = os.path.join(base, "timing.json")
    spath = os.path.join(base, "script", "storyboard.json")
    if not os.path.exists(tpath):
        raise SystemExit("找不到 %s，先跑 build_audio.py" % tpath)
    if not os.path.exists(spath):
        raise SystemExit("找不到 %s，先按 references/04-diagrams.md 写分镜" % spath)

    timing = json.load(open(tpath, encoding="utf-8"))
    sb = json.load(open(spath, encoding="utf-8"))
    seg = {s["name"]: s for s in timing["segments"]}
    TOTAL = round(timing["total"], 3)
    FPS = timing["fps"]

    def st(name):
        if name not in seg:
            raise SystemExit("storyboard 引用了不存在的段名「%s」；可用段名：%s" % (name, list(seg)))
        return seg[name]["start"]

    def en(name):
        s = seg[name]
        return round(s["start"] + s["dur"], 3)

    # ---------------- 章节角标 ----------------
    ch_def = sb.get("chapters") or []
    chapters = []
    for i, c in enumerate(ch_def):
        a = st(c["from"])
        if c.get("to"):
            b = st(c["to"])
        elif i + 1 < len(ch_def):
            b = st(ch_def[i + 1]["from"])
        else:
            b = TOTAL
        chapters.append({"name": c["name"], "start": round(a, 3), "end": round(b, 3)})

    # ---------------- 分镜 ----------------
    scenes = []
    for s in sb.get("scenes") or []:
        segname = s["seg"]
        if segname not in seg:
            raise SystemExit("分镜引用了不存在的段名「%s」" % segname)
        a, b = st(segname), en(segname)
        dur = b - a
        f0 = float(s.get("f0", 0.0))
        f1 = float(s.get("f1", 1.0))
        sc = {k: v for k, v in s.items() if k not in ("seg", "f0", "f1")}
        sc["start"] = round(a + dur * f0, 3)
        sc["end"] = round(a + dur * f1, 3)
        sc.setdefault("chapter", "")
        scenes.append(sc)

    scenes.sort(key=lambda x: x["start"])

    # ---------------- 自检 ----------------
    warn = []
    seg_gap = float(timing.get("gap") or 0.7)   # 段间设计留白，属于预期
    for i, sc in enumerate(scenes):
        if sc["end"] <= sc["start"]:
            warn.append("分镜 %d 时长 <= 0：%s" % (i, sc))
        if i:
            d = sc["start"] - scenes[i - 1]["end"]
            if abs(d) > 0.02 and abs(d - seg_gap) > 0.05:
                # 段间留白不算问题；其它缝隙/重叠要报
                warn.append("分镜 %d/%d 之间有 %+.2fs 缝隙/重叠（段 %.2f→%.2f）"
                            % (i, i + 1, d, scenes[i - 1]["end"], sc["start"]))
    for sc in scenes:
        if sc["kind"] == "diagram" and not sc.get("id"):
            warn.append("diagram 分镜缺 id：%.2fs" % sc["start"])
        if sc["kind"] == "shot":
            if not sc.get("shot"):
                warn.append("shot 分镜缺 shot 路径：%.2fs" % sc["start"])
            else:
                p = os.path.join(base, "remotion", "public", sc["shot"])
                if not os.path.exists(p):
                    warn.append("截图不存在：%s" % p)
            for r in sc.get("focus") or []:
                for k in ("x", "y", "w", "h"):
                    if k not in r:
                        warn.append("focus 缺字段 %s：%.2fs" % (k, sc["start"]))
                if r.get("x", 0) + r.get("w", 0) > 1.0001 or r.get("y", 0) + r.get("h", 0) > 1.0001:
                    warn.append("focus 超出画布：%.2fs %s" % (sc["start"], r))

    props = {
        "fps": FPS,
        "total": TOTAL,
        "width": 1920,
        "height": 1080,
        "audio": [{"src": s["file"], "start": s["start"], "dur": s["dur"]} for s in timing["segments"]],
        "captions": timing["captions"],
        "chapters": chapters,
        "scenes": scenes,
        "brand": sb.get("brand", ""),
        "endTitle": sb.get("endTitle", ""),
        "endSubtitle": sb.get("endSubtitle", ""),
        "endFooter": sb.get("endFooter", ""),
    }
    out = os.path.join(base, "remotion", "props.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(props, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    S = "shots/"
    print("分镜 %d ｜ 章节 %d ｜ 字幕 %d" % (len(scenes), len(chapters), len(props["captions"])))
    print("总时长 %.2fs -> %d 帧 (%dfps)" % (TOTAL, round(TOTAL * FPS), FPS))
    for s in scenes:
        print("  %-8s %7.2f-%7.2f %5.1fs  %-6s %-12s %s"
              % (s["kind"], s["start"], s["end"], s["end"] - s["start"],
                 s.get("id") or "", s.get("chapter") or "-",
                 (s.get("shot") or "").replace(S, "") or (s.get("title") or "")))
    if warn:
        print("\n⚠ 自检提示 %d 条：" % len(warn))
        for w in warn:
            print("   -", w)
    print("\n写出:", out)


if __name__ == "__main__":
    main()
