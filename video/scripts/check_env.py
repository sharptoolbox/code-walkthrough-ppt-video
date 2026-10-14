#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境自检：把这条流水线依赖的东西一次查完，缺什么直接给修复命令。

用法：python check_env.py
"""
import importlib.util as iu
import os
import shutil
import subprocess
import sys

OK = "[ OK ]"
NG = "[FAIL]"
WARN = "[WARN]"


def has(mod):
    return bool(iu.find_spec(mod))


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:
        return ""


def find_browser():
    cands = [
        r"C:\Users\%s\AppData\Local\Google\Chrome\Application\chrome.exe" % os.environ.get("USERNAME", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return ""


def find_node():
    cands = [
        r"C:\Users\%s\.workbuddy\binaries\node\versions" % os.environ.get("USERNAME", ""),
        r"C:\Program Files\nodejs",
    ]
    for base in cands:
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base), reverse=True):
            p = os.path.join(base, d, "node.exe")
            if os.path.exists(p):
                return p
        p = os.path.join(base, "node.exe")
        if os.path.exists(p):
            return p
    return shutil.which("node") or ""


def find_ffmpeg():
    for base in [
        r"C:\Users\%s\AppData\Local\Microsoft\WinGet\Packages" % os.environ.get("USERNAME", ""),
        r"C:\ffmpeg",
    ]:
        if os.path.isdir(base):
            for root, dirs, files in os.walk(base):
                if "ffmpeg.exe" in files:
                    return os.path.join(root, "ffmpeg.exe")
    return shutil.which("ffmpeg") or ""


def main():
    print("=" * 68)
    print(" code-walkthrough-ppt-video / 视频模式环境自检")
    print("=" * 68)

    # ---- Python 依赖 ----
    py = sys.executable
    print("Python      : %s" % py)
    for mod, note in [
        ("edge_tts", "配音（微软云扬神经音色）"),
        ("PIL", "截图归一化 / contact sheet"),
    ]:
        print("  %s %-12s %s" % (OK if has(mod) else NG, mod, note))
    if not has("edge_tts"):
        print("       修复：<python> -m pip install edge-tts")
    if not has("PIL"):
        print("       修复：<python> -m pip install pillow")

    # ---- edge-tts 端点连通性 ----
    if has("edge_tts"):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import asyncio
            import edge_tts_patch  # noqa: F401
            import edge_tts

            async def probe():
                c = edge_tts.Communicate("环境自检。", "zh-CN-YunyangNeural", rate="+6%")
                n = 0
                async for ch in c.stream():
                    if ch.get("type") == "audio":
                        n += len(ch["data"])
                return n

            n = asyncio.run(asyncio.wait_for(probe(), timeout=40))
            print("  %s 云扬音色合成   %d 字节" % (OK if n > 2000 else NG, n))
        except Exception as e:
            print("  %s 云扬音色合成   失败：%s" % (NG, str(e)[:120]))
            print("       说明：补丁已启用仍失败 → 多半是网络/端点变更，见 references/06-pitfalls.md")

    # ---- Node / 浏览器 / ffmpeg ----
    node = find_node()
    print("  %s node           %s" % (OK if node else NG, node or "未找到"))
    br = find_browser()
    print("  %s 无头浏览器     %s" % (OK if br else NG, br or "未找到 Chrome/Edge"))
    ff = find_ffmpeg()
    print("  %s ffmpeg         %s" % (OK if ff else NG, ff or "未找到"))

    # ---- 工程依赖 ----
    base = os.environ.get("CW_VIDEO_DIR") or os.getcwd()
    nm = os.path.join(base, "remotion", "node_modules", "@remotion", "cli")
    print("  %s Remotion 依赖  %s" % (OK if os.path.isdir(nm) else WARN, os.path.join(base, "remotion")))
    if not os.path.isdir(nm):
        print("       修复：bash scripts/setup_remotion.sh \"%s\"" % base)
    cli = os.path.join(base, "remotion", "node_modules", "@remotion", "cli", "remotion-cli.js")
    if os.path.isfile(cli):
        print("  %s remotion-cli   %s" % (OK, cli))

    # ---- 中文字体 ----
    fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for fnt in ["msyh.ttc", "msyhbd.ttc"]:
        p = os.path.join(fonts, fnt)
        if os.path.exists(p):
            print("  %s 中文字体       %s" % (OK, fnt))
    print("=" * 68)


if __name__ == "__main__":
    main()
