#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
shoot_page.py —— 把 <工程>/ui/*.html 批量截成 1600×900 @DPR2 的 PNG，并生成拼版。

用法:
    python shoot_page.py --check
    python shoot_page.py --in ui --out images
    python shoot_page.py --in ui --out images --w 1600 --h 900 --dpr 2
    python shoot_page.py --in ui --out images --chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"

关键实现（这三条是踩过的坑，不要删）:
  1. --force-device-scale-factor=<dpr>   Windows 显示缩放会让 --window-size 失效
  2. 窗口开大一圈再裁                      --window-size 是窗口尺寸不是视口尺寸，
                                          标题栏+边框吃掉约 16×95px，页面底部内容会拍不到
  3. 每页独立 profile + --incognito       否则第二次拍同一页会拿到旧缓存

输出: <out>/*.png （w*dpr × h*dpr 物理像素） + <out>/contact_sheet.png
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

WIN_MARGIN_W = 40     # 窗口比视口多出来的宽度余量
WIN_MARGIN_H = 120    # 窗口比视口多出来的高度余量（标题栏+边框）

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    env = os.environ.get("CW_PPT_CHROME")
    if env and os.path.isfile(env):
        return env
    for p in CHROME_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        which = shutil.which(name)
        if which:
            return which
    return None


def check_env() -> int:
    print("=== 环境自检 ===")
    ok = True

    chrome = find_chrome()
    if chrome:
        print("[OK]   浏览器:", chrome)
        try:
            out = subprocess.run([chrome, "--version"], capture_output=True, text=True, timeout=20)
            print("       版本:", (out.stdout or out.stderr).strip())
        except Exception as exc:  # noqa: BLE001
            print("       [警告] 无法获取版本:", exc)
    else:
        ok = False
        print("[缺失] 浏览器（Chrome 或 Edge）")
        print("       修法：用 --chrome 指定可执行文件路径")

    try:
        from PIL import Image  # noqa: F401
        import PIL
        print("[OK]   Pillow:", getattr(PIL, "__version__", "?"))
    except Exception:  # noqa: BLE001
        ok = False
        print("[缺失] Pillow（拼版与裁剪用）")
        print("       修法：<python> -m pip install pillow")

    print("[OK]   Python:", sys.version.split()[0])
    print()
    print("结论:", "环境就绪" if ok else "环境不完整，请先按上面的修法处理")
    return 0 if ok else 1


def shoot_one(chrome: str, html: str, out_png: str, w: int, h: int, dpr: int,
              timeout: int = 120) -> tuple[bool, str]:
    from PIL import Image

    profile = tempfile.mkdtemp(prefix="cwppt_")
    # 必须用绝对路径：Chrome 的 CWD 不等于调用方 CWD，
    # 传相对路径会报 "Failed to write file ... 系统找不到指定的路径 (0x3)"，且白等一整个 timeout。
    raw = os.path.abspath(out_png) + ".raw.png"
    try:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--incognito",
            f"--user-data-dir={profile}",
            f"--force-device-scale-factor={dpr}",
            f"--window-size={w + WIN_MARGIN_W},{h + WIN_MARGIN_H}",
            "--default-background-color=FFFFFFFF",
            "--virtual-time-budget=4000",
            f"--screenshot={raw}",
            "file:///" + os.path.abspath(html).replace("\\", "/"),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if not os.path.isfile(raw):
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()
            return False, "未产出文件；stderr 末尾: " + (" | ".join(tail[-3:]) if tail else "(空)")

        im = Image.open(raw)
        tw, th = w * dpr, h * dpr
        if im.size == (tw, th):
            im.save(out_png, "PNG", optimize=True)
            return True, f"{im.size[0]}x{im.size[1]}"
        if im.width >= tw and im.height >= th:
            im.crop((0, 0, tw, th)).save(out_png, "PNG", optimize=True)
            return True, f"{tw}x{th} (由 {im.size[0]}x{im.size[1]} 裁出)"
        return False, (f"截图过小: 实际 {im.size[0]}x{im.size[1]}，需 ≥ {tw}x{th}。"
                       f"检查 --force-device-scale-factor 是否生效（Windows 显示缩放）")
    except subprocess.TimeoutExpired:
        return False, f"超时（>{timeout}s）"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        shutil.rmtree(profile, ignore_errors=True)
        if os.path.isfile(raw):
            try:
                os.remove(raw)
            except OSError:
                pass


def make_contact_sheet(pngs: list[str], out_path: str, cell_w: int = 640, cols: int = 4) -> bool:
    try:
        from PIL import Image
    except Exception:  # noqa: BLE001
        return False
    if not pngs:
        return False

    from PIL import ImageDraw
    pad, cap = 14, 26
    cell_h = int(cell_w * 9 / 16)
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * pad,
                              rows * (cell_h + cap) + (rows + 1) * pad), (238, 242, 246))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(pngs):
        r, c = divmod(i, cols)
        x = pad + c * (cell_w + pad)
        y = pad + r * (cell_h + cap + pad)
        try:
            im = Image.open(p).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
        except Exception:  # noqa: BLE001
            continue
        sheet.paste(im, (x, y))
        draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(180, 186, 194))
        draw.text((x, y + cell_h + 6), os.path.basename(p), fill=(70, 75, 82))
    sheet.save(out_path, "PNG", optimize=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="HTML → 1600×900 @DPR2 截图 + 拼版")
    ap.add_argument("--check", action="store_true", help="只做环境自检")
    ap.add_argument("--in", dest="indir", default="ui", help="HTML 所在目录")
    ap.add_argument("--out", dest="outdir", default="images", help="PNG 输出目录")
    ap.add_argument("--w", type=int, default=1600, help="CSS 视口宽（默认 1600）")
    ap.add_argument("--h", type=int, default=900, help="CSS 视口高（默认 900）")
    ap.add_argument("--dpr", type=int, default=2, help="设备像素比（默认 2）")
    ap.add_argument("--chrome", default=None, help="Chrome/Edge 可执行文件路径")
    ap.add_argument("--timeout", type=int, default=120, help="单页超时秒数")
    ap.add_argument("--no-sheet", action="store_true", help="不生成拼版")
    args = ap.parse_args()

    if args.check:
        return check_env()

    chrome = find_chrome(args.chrome)
    if not chrome:
        print("[错误] 找不到 Chrome / Edge。用 --chrome 指定路径，或设 CW_PPT_CHROME 环境变量。")
        return 2

    if not os.path.isdir(args.indir):
        print(f"[错误] 输入目录不存在: {args.indir}")
        return 2
    os.makedirs(args.outdir, exist_ok=True)

    htmls = sorted(f for f in os.listdir(args.indir) if f.lower().endswith((".html", ".htm")))
    if not htmls:
        print(f"[错误] {args.indir} 下没有 .html 文件")
        return 2

    print(f"浏览器: {chrome}")
    print(f"规格  : {args.w}×{args.h} CSS px @DPR{args.dpr} → {args.w*args.dpr}×{args.h*args.dpr} PNG")
    print(f"共 {len(htmls)} 页\n")

    ok_list, bad = [], []
    for name in htmls:
        src = os.path.join(args.indir, name)
        dst = os.path.join(args.outdir, os.path.splitext(name)[0] + ".png")
        if os.path.isfile(dst):
            try:
                os.remove(dst)
            except OSError:
                pass
        ok, info = shoot_one(chrome, src, dst, args.w, args.h, args.dpr, args.timeout)
        if ok:
            stamp = os.path.getmtime(dst)
            print(f"[OK]   {name:38s} {info}")
            ok_list.append((dst, stamp))
        else:
            print(f"[失败] {name:38s} {info}")
            bad.append(name)

    print(f"\n完成: 成功 {len(ok_list)} / 失败 {len(bad)}")
    if bad:
        print("失败清单:")
        for b in bad:
            print("  -", b)

    if ok_list and not args.no_sheet:
        sheet = os.path.join(args.outdir, "contact_sheet.png")
        if make_contact_sheet([p for p, _ in ok_list], sheet):
            print(f"拼版: {sheet}")
            print(">>> 先看拼版再往下走：一屏过完所有界面，比逐张点开快得多。")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
