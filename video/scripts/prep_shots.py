# -*- coding: utf-8 -*-
"""
截图归一化：把各种来源、各种比例的界面图统一成 1600×900（16:9），并拼一张 contact sheet 供目视确认。

为什么必须归一化：Remotion 里用 objectFit:cover 撑满 1400×788 的画面卡，
比例不一致时会被裁切，而 focus 高亮框是按整图比例给的 —— 不统一，框就必然错位。

裁剪策略：
  比 16:9 宽 → 从右侧裁（左侧通常是导航菜单，必须保住）
  比 16:9 窄 → 从底部补深色底（顶部通常是标题栏，保住）
  想改成左侧裁/上下居中裁，改 norm() 里的注释处即可。

用法：python prep_shots.py --raw shots_raw --out remotion/public/shots
"""
import argparse
import os

from PIL import Image, ImageDraw

W, H = 1600, 900
BG = (11, 16, 24)
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def norm(im, crop_side="right"):
    im = im.convert("RGB")
    w, h = im.size
    target_w = round(h * W / H)
    if w > target_w:
        if crop_side == "right":
            im = im.crop((0, 0, target_w, h))          # 保住左侧导航
        elif crop_side == "left":
            im = im.crop((w - target_w, 0, w, h))      # 保住右侧
        else:
            x = (w - target_w) // 2
            im = im.crop((x, 0, x + target_w, h))      # 居中裁
    elif w < target_w:
        canvas = Image.new("RGB", (target_w, h), BG)
        canvas.paste(im, (0, 0))                       # 不够宽 → 右下补底
        im = canvas
    return im.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="shots_raw", help="原始截图目录")
    ap.add_argument("--out", default=os.path.join("remotion", "public", "shots"))
    ap.add_argument("--side", default="right", choices=["right", "left", "center"])
    ap.add_argument("--sheet", default="contact_sheet.png")
    args = ap.parse_args()

    raw = os.path.abspath(args.raw)
    out = os.path.abspath(args.out)
    if not os.path.isdir(raw):
        raise SystemExit("找不到原始截图目录：%s" % raw)
    os.makedirs(out, exist_ok=True)

    files = sorted(f for f in os.listdir(raw) if f.lower().endswith(EXTS))
    if not files:
        raise SystemExit("目录里没有图片：%s" % raw)

    made = []
    for f in files:
        src = os.path.join(raw, f)
        name = os.path.splitext(f)[0] + ".png"
        dst = os.path.join(out, name)
        try:
            im = norm(Image.open(src), args.side)
        except Exception as e:  # noqa: BLE001
            print("  [FAIL] %s  %s" % (f, e))
            continue
        im.save(dst, "PNG", optimize=True)
        made.append(name)
        print("  %-30s %s  %dKB" % (name, im.size, round(os.path.getsize(dst) / 1024)))

    # contact sheet：一张图看完所有画面，避免逐张点开
    cols, cw, ch = 3, 520, 293
    rows = (len(made) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw + 20, rows * (ch + 34) + 20), (18, 24, 36))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(made):
        im = Image.open(os.path.join(out, name)).resize((cw - 16, ch - 16), Image.LANCZOS)
        r, c = divmod(i, cols)
        x, y = 10 + c * cw, 10 + r * (ch + 34)
        sheet.paste(im, (x + 8, y + 8))
        d.text((x + 10, y + ch + 6), name, fill=(230, 235, 245))
    sheet_path = os.path.abspath(args.sheet)
    sheet.save(sheet_path)
    print("\n归一化 %d 张 -> %s" % (len(made), out))
    print("拼版 -> %s" % sheet_path)


if __name__ == "__main__":
    main()
