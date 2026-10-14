# -*- coding: utf-8 -*-
"""
探针 props 生成：把 storyboard 里每个分镜都压成 5 秒，串成一条「速览片」。

目的：在正式渲染（可能十几分钟）之前，用一次 1~2 分钟的短渲染，
把每一张图、每一个截图高亮框都看一遍 —— 版式错了此时改成本最低。

用法：python probe_props.py --dir <工程目录>
输出：<工程目录>/remotion/probe.json
"""
import argparse
import json
import os

SEC = 5.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.environ.get("CW_VIDEO_DIR") or os.getcwd())
    args = ap.parse_args()
    base = os.path.abspath(args.dir)

    src = os.path.join(base, "remotion", "props.json")
    if not os.path.exists(src):
        raise SystemExit("找不到 %s，先跑 make_props.py" % src)
    d = json.load(open(src, encoding="utf-8"))

    scenes = []
    for i, s in enumerate(d["scenes"]):
        c = dict(s)
        c["start"] = round(i * SEC, 3)
        c["end"] = round((i + 1) * SEC, 3)
        # 探针里让说明条尽早出现，方便一帧看全
        c.pop("calloutAt", None)
        c.pop("noteAt", None)
        c["calloutAt"] = 0.5
        if c.get("note"):
            c["noteAt"] = 1.0
        scenes.append(c)

    probe = {
        "fps": d["fps"],
        "total": round(len(scenes) * SEC, 3),
        "width": d["width"],
        "height": d["height"],
        "audio": [],                    # 探针不出声，快
        "captions": [],
        "chapters": [],                 # 不显示角标，避免遮挡
        "scenes": scenes,
        "brand": d.get("brand", ""),
        "endTitle": d.get("endTitle", ""),
        "endSubtitle": d.get("endSubtitle", ""),
        "endFooter": d.get("endFooter", ""),
    }
    out = os.path.join(base, "remotion", "probe.json")
    json.dump(probe, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    fps = d["fps"]
    print("探针分镜 %d 个 × %.1fs = %.1fs -> %d 帧"
          % (len(scenes), SEC, probe["total"], round(probe["total"] * fps)))
    print("取样帧（每个分镜第 3.5s）：", ",".join(str(round((i * SEC + 3.5) * fps)) for i in range(len(scenes))))
    for i, s in enumerate(scenes):
        print("  %2d  %-8s %-6s %s" % (i + 1, s["kind"], s.get("id") or "", (s.get("shot") or "") or (s.get("title") or "")))
    print("写出:", out)


if __name__ == "__main__":
    main()
