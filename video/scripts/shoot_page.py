# -*- coding: utf-8 -*-
"""
把重绘的 HTML 界面截成 1600×900 PNG（视频统一画幅）。

为什么不用 playwright：本机只需要一个无头浏览器跑一次静态截图，
Chrome/Edge 自带的 --screenshot 就够了，零额外依赖。

关键坑：Windows 显示缩放会让 --window-size 失效（本机 150% 缩放时
1600×900 只截出 1080×617）。**必须加 --force-device-scale-factor=1**。

用法：
  python shoot_page.py --in ui --out shots_raw
  python shoot_page.py --in ui/order-list.html --out shots_raw --width 1600 --height 900
"""
import argparse
import os
import shutil
import subprocess
import sys


def find_browser():
    cands = [
        r"C:\Users\%s\AppData\Local\Google\Chrome\Application\chrome.exe" % os.environ.get("USERNAME", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome") or "",
        shutil.which("msedge") or "",
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return ""


def shoot(browser, html, png, w, h, budget_ms, tmpdir):
    """
    关键：--window-size 是**窗口**尺寸，会被窗口装饰吃掉一部分，真实视口约小 16×95px。
    如果按 1600×900 传，视口只有 ~1584×805，页面按 805 高做布局，截图再按 900 出图，
    底部就会留一条空带、分页器之类的底部元素会被切掉。

    做法：窗口开大一圈（宽 +40、高 +120），保证视口 ≥ 目标尺寸；
    脚本拿到图后再精确裁到目标尺寸。页面本身用固定画布（1600×900）所以裁掉的是空白。
    """
    args = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-features=Translate",
        "--incognito",                        # 避免复用 profile 带来的页面缓存
        "--force-device-scale-factor=1",      # ← 不加这行会被系统 DPI 缩放
        "--window-size=%d,%d" % (w + 40, h + 120),
        "--virtual-time-budget=%d" % budget_ms,
        "--user-data-dir=%s" % tmpdir,
        "--screenshot=%s" % png,
        "file:///" + html.replace("\\", "/").lstrip("/"),
    ]
    r = subprocess.run(args, capture_output=True, text=True, timeout=180)
    return r


def crop_to(png, w, h):
    """裁到目标尺寸（左上对齐）。"""
    from PIL import Image

    im = Image.open(png)
    if im.size != (w, h) and im.width >= w and im.height >= h:
        im.crop((0, 0, w, h)).save(png, "PNG", optimize=True)
        return (w, h)
    return im.size


def check_size(png):
    try:
        from PIL import Image

        return Image.open(png).size
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True, help="HTML 文件或目录")
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--budget", type=int, default=3000, help="virtual-time-budget，动画慢的页面调大")
    args = ap.parse_args()

    browser = find_browser()
    if not browser:
        sys.exit("找不到 Chrome / Edge，无法截图。装一个浏览器，或用 --browser 手工指定。")
    print("浏览器:", browser)

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    if os.path.isdir(src):
        htmls = sorted(
            os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith((".html", ".htm"))
        )
    else:
        htmls = [src]
    if not htmls:
        sys.exit("没有找到 .html 文件：%s" % src)

    tmpdir = os.path.join(os.environ.get("TEMP", "/tmp"), "cws_shot_profile")
    ok, bad = [], []
    for html in htmls:
        name = os.path.splitext(os.path.basename(html))[0] + ".png"
        png = os.path.join(out, name)
        if os.path.exists(png):
            os.remove(png)
        # 每个页面用一个干净的 profile：复用同一个会命中页面缓存，截出上一版的内容
        shutil.rmtree(tmpdir, ignore_errors=True)
        r = shoot(browser, html, png, args.width, args.height, args.budget, tmpdir)
        if not os.path.exists(png):
            bad.append((name, r.stderr.strip()[:160] or "未产出文件"))
            print("  [FAIL] %s  %s" % (name, (r.stderr or "").strip()[:120]))
            continue
        size = crop_to(png, args.width, args.height)
        if size != (args.width, args.height):
            print("  [WARN] %s 尺寸 %s ≠ %s（检查页面的 html,body 是否固定为 %d×%d）"
                  % (name, size, (args.width, args.height), args.width, args.height))
            bad.append((name, "尺寸异常 %s" % (size,)))
            ok.append(name)
            continue
        print("  [ OK ] %s  %s  %dKB" % (name, size, round(os.path.getsize(png) / 1024)))
        ok.append(name)

    print("\n成功 %d / 失败 %d  ->  %s" % (len(ok), len(bad), out))
    for n, why in bad:
        print("   !", n, why)
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
