#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rects.py —— 读界面元素的真实 rect，供截图标注精确对齐（不要目测估坐标）。

做法：给界面 HTML 注入一段探测 JS，用无头浏览器的 --dump-dom 把结果吐回来。
输出已经换算到截图本地坐标系（1316 × 740），可直接抄进标注定义。

用法:
    python rects.py --in <工程>/ui                          # 目录下全部 html
    python rects.py --in <工程>/ui/<页面>.html              # 单个文件
    python rects.py --in <工程>/ui > <工程>/_build/rects.txt

输出行:
    panel  单据上下文：选择单据后…  x=248 y=372 w=1334 h=434 | 槽 x=204 y=306 w=1097 h=357
                                                    ↑ 直接抄这一段
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

CHROME_CANDIDATES = [
    r"C:\Users\%s\AppData\Local\Google\Chrome\Application\chrome.exe" % os.environ.get("USERNAME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

PROBE = r"""
<script>
(function(){
  var out=[];
  var all=document.querySelectorAll('*');
  for(var i=0;i<all.length;i++){
    var el=all[i];
    var r=el.getBoundingClientRect();
    if(r.width<10||r.height<8) continue;
    var t=(el.textContent||'').replace(/\s+/g,'').slice(0,16);
    var c=(typeof el.className==='string'&&el.className)?el.className.split(' ')[0]:el.tagName.toLowerCase();
    out.push([c,t,Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)].join('\t'));
  }
  var pre=document.createElement('pre');
  pre.id='__rects__';
  pre.textContent='@@R@@\n'+out.join('\n')+'\n@@E@@';
  document.body.appendChild(pre);
})();
</script>
"""


def find_chrome(explicit: str | None) -> str:
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        raise SystemExit(f"[错误] 指定的浏览器不存在: {explicit}")
    for p in CHROME_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    raise SystemExit("[错误] 没找到 Chrome/Chromium/Edge，用 --chrome 指定可执行文件")


def main() -> int:
    ap = argparse.ArgumentParser(description="读界面元素 rect（标注对齐用）")
    ap.add_argument("--in", dest="indir", required=True,
                    help="界面 html 所在目录，或单个 html 文件")
    ap.add_argument("--chrome", default=None, help="Chrome/Edge 可执行文件路径")
    ap.add_argument("--w", type=int, default=1600, help="视口宽（默认 1600）")
    ap.add_argument("--h", type=int, default=900, help="视口高（默认 900）")
    ap.add_argument("--only", default=None, help="只处理文件名含该串的页面")
    args = ap.parse_args()

    chrome = find_chrome(args.chrome)

    if os.path.isfile(args.indir):
        files = [args.indir]
        base = os.path.dirname(args.indir)
    else:
        base = args.indir
        files = [os.path.join(base, f) for f in sorted(os.listdir(base)) if f.endswith(".html")]

    if args.only:
        files = [f for f in files if args.only in f]
    if not files:
        raise SystemExit("[错误] 没找到要处理的 html")

    K = 1316.0 / args.w  # 宿主编译尺寸 -> 1316 槽坐标

    for path in files:
        html = open(path, encoding="utf-8").read()
        html = html.replace("</body>", PROBE + "</body>") if "</body>" in html else html + PROBE
        # 探测页写到同目录，保证相对图片/字体路径不变
        tmp = os.path.join(base, "_rects_" + os.path.basename(path))
        open(tmp, "w", encoding="utf-8").write(html)
        url = "file:///" + os.path.abspath(tmp).replace("\\", "/").replace(" ", "%20")
        try:
            r = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                 f"--window-size={args.w},{args.h}", "--virtual-time-budget=3000", "--dump-dom", url],
                capture_output=True, timeout=90,
            )
            dom = r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            print(f"[超时] {os.path.basename(path)}", file=sys.stderr)
            os.remove(tmp)
            continue
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

        # 脚本文本里也含 @@R@@ 字面量，必须锚定到 <pre id="__rects__"> 之后
        m = re.search(r'<pre id="__rects__">@@R@@(.*?)@@E@@', dom, re.S)
        if not m:
            print(f"[无数据] {os.path.basename(path)}", file=sys.stderr)
            continue

        print(f"\n===== {os.path.basename(path)} =====")
        for line in m.group(1).strip().splitlines():
            p = line.split("\t")
            if len(p) != 6:
                continue
            cls, txt, x, y, w, h = p
            x, y, w, h = int(x), int(y), int(w), int(h)
            print("%-14s %-18s x=%-5d y=%-5d w=%-5d h=%-5d | 槽 x=%-4d y=%-4d w=%-4d h=%-4d"
                  % (cls[:14], txt[:18], x, y, w, h,
                     round(x * K), round(y * K), round(w * K), round(h * K)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
