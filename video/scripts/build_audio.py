# -*- coding: utf-8 -*-
"""
配音 + 字幕时间轴生成（微软云扬神经音色，词级时间戳）

输入：<工程目录>/script/narration.json
  {
    "meta": {
      "voice": "zh-CN-YunyangNeural",   // 默认就是这个
      "rate": "+6%",                    // 语速；改变会同步改变全片时长
      "fps": 30,                        // 视频帧率（30 或 25）
      "leadIn": 1.0, "gap": 0.7, "tail": 3.2,
      "title": "某某系统 · 订单模块",     // 解说稿与 SRT 的标题
      "srtName": "订单模块演示视频.srt"
    },
    "segments": [ {"name": "片头", "text": "……"}, … ]
  }

输出：
  <工程目录>/audio/<id><rate>.mp3 + .words.json   逐段音频与词级时间戳（带缓存）
  <工程目录>/timing.json                          全片绝对时间轴（make_props.py 的输入）
  <工程目录>/<srtName>                            硬字幕
  <工程目录>/解说稿.md
  <工程目录>/remotion/public/audio/*.mp3          自动同步给 Remotion

用法：
  python build_audio.py --dir <工程目录>            # 正式合成
  python build_audio.py --dir <工程目录> --dry      # 只估算时长，不调 TTS（改稿时用）
  python build_audio.py --budget 300                # 查「目标秒数能讲多少字」
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 基准语速：云扬 +0% 实测约 5.0 汉字/秒（三支成片 5.09 / 5.25 / 5.29 反推）
BASE_CPS = 5.0
HARD = "。！？"
SOFT = "，；：、"
MAXC = 20          # 单行字幕最大字数


# ══════════════════════════ 工具 ══════════════════════════
def find_ffprobe():
    for base in [
        r"C:\Users\%s\AppData\Local\Microsoft\WinGet\Packages" % os.environ.get("USERNAME", ""),
        r"C:\ffmpeg",
    ]:
        if os.path.isdir(base):
            for root, _dirs, files in os.walk(base):
                if "ffprobe.exe" in files:
                    return os.path.join(root, "ffprobe.exe")
    return shutil.which("ffprobe") or "ffprobe"


FFPROBE = find_ffprobe()


def dur_of(path):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def cps_of(rate):
    """把 rate（如 '+6%'）换算成汉字/秒"""
    pct = 0.0
    try:
        pct = float(str(rate).replace("%", "").replace("+", ""))
    except Exception:
        pass
    return BASE_CPS * (1.0 + pct / 100.0)


def est_total(chars_list, n, rate, lead_in, gap, tail):
    """按语速系数估算全片时长（秒）。不调 TTS，用于改稿时快速判断。"""
    cps = cps_of(rate)
    return sum(c / cps for c in chars_list) + lead_in + gap * max(0, n - 1) + tail


# ══════════════════════════ 合成 ══════════════════════════
async def synth(audio_dir, key, text, voice, rate):
    import edge_tts

    tag = key + ("" if rate in ("+0%", "0%") else rate.replace("%", "pct").replace("+", "u"))
    mp3 = os.path.join(audio_dir, tag + ".mp3")
    cache = os.path.join(audio_dir, tag + ".words.json")
    if os.path.exists(mp3) and os.path.exists(cache) and os.path.getsize(mp3) > 2000:
        return mp3, [tuple(x) for x in json.load(open(cache, encoding="utf-8"))]

    words = []
    last_err = None
    for _ in range(4):
        try:
            words = []
            comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            with open(mp3, "wb") as f:
                async for ch in comm.stream():
                    if ch.get("type") == "audio":
                        f.write(ch["data"])
                    elif ch.get("type") == "WordBoundary":
                        words.append((ch["offset"] / 1e7, ch["text"]))
            if os.path.getsize(mp3) > 2000 and words:
                json.dump(words, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
                return mp3, words
            last_err = "返回内容为空"
        except Exception as e:  # noqa: BLE001
            last_err = e
        await asyncio.sleep(2)
    raise RuntimeError("合成失败 %s：%s" % (key, last_err))


# ══════════════════════════ 字幕切分 ══════════════════════════
def char_times(text, words):
    """词级时间戳 -> 字符级时间戳"""
    ct = [None] * len(text)
    cur = 0
    for off, tok in words:
        idx = text.find(tok, cur)
        if idx < 0:
            idx = text.find(tok)
        if idx < 0:
            continue
        for k in range(idx, min(idx + len(tok), len(text))):
            ct[k] = off
        cur = idx + len(tok)
    last = 0.0
    for i in range(len(ct)):
        if ct[i] is None:
            ct[i] = last
        else:
            last = ct[i]
    return ct


def _even_split(a, b):
    """无标点的超长句按接近均分切段，避免留下 1~2 字的孤行"""
    L = b - a
    n = (L + MAXC - 1) // MAXC
    step = (L + n - 1) // n
    return [(i, min(i + step, b)) for i in range(a, b, step)]


def _ranges(text):
    """按「硬标点 -> 软标点 -> 均分」三级切分，返回字符区间列表"""
    sents, cur = [], 0
    for i, ch in enumerate(text):
        if ch in HARD:
            sents.append((cur, i + 1))
            cur = i + 1
    if cur < len(text):
        sents.append((cur, len(text)))

    out = []
    for a, b in sents:
        if b - a <= MAXC:
            out.append((a, b))
            continue
        parts, p = [], a
        for i in range(a, b):
            if text[i] in SOFT:
                parts.append((p, i + 1))
                p = i + 1
        if p < b:
            parts.append((p, b))
        fi = []
        for qa, qb in parts:
            if qb - qa > MAXC:
                fi += _even_split(qa, qb)
            else:
                fi.append((qa, qb))
        ba, bl = None, 0
        for qa, qb in fi:
            L = qb - qa
            if ba is None:
                ba, bl = qa, L
            elif bl + L <= MAXC:
                bl += L
            else:
                out.append((ba, ba + bl))
                ba, bl = qa, L
        if ba is not None:
            if out and bl < 6 and (out[-1][1] - out[-1][0] + bl) <= MAXC + 4:
                pa, _ = out.pop()
                out.append((pa, ba + bl))
            else:
                out.append((ba, ba + bl))
    return out


def split_lines(text, ct, seg_dur, offset):
    """按标点与长度切句，返回绝对时间的字幕条目"""
    rng = _ranges(text)
    lines = []
    for j, (a, b) in enumerate(rng):
        s = text[a:b]
        if b - a <= 1 and s in "，、；：":
            continue
        disp = s.rstrip("，、；：") or s
        st = ct[a]
        en = ct[rng[j + 1][0]] - 0.10 if j + 1 < len(rng) else seg_dur
        lines.append([offset + st, offset + en, disp])
    for j in range(len(lines)):
        if j + 1 < len(lines) and lines[j][1] > lines[j + 1][0]:
            lines[j][1] = lines[j + 1][0] - 0.05
        if lines[j][1] <= lines[j][0]:
            lines[j][1] = lines[j][0] + 0.6
    return [{"start": round(a, 3), "end": round(b, 3), "text": t} for a, b, t in lines]


# ══════════════════════════ 主流程 ══════════════════════════
def ts(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s2, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s2, ms)


def load_narration(base):
    p = os.path.join(base, "script", "narration.json")
    if not os.path.exists(p):
        raise SystemExit("找不到 %s\n先按 references/03-narrative.md 写好分段解说稿。" % p)
    d = json.load(open(p, encoding="utf-8"))
    meta = {
        "voice": "zh-CN-YunyangNeural",
        "rate": "+6%",
        "fps": 30,
        "leadIn": 1.0,
        "gap": 0.7,
        "tail": 3.2,
        "title": "源码讲解",
        "srtName": "演示视频.srt",
    }
    meta.update(d.get("meta") or {})
    segs = d.get("segments") or []
    if not segs:
        raise SystemExit("narration.json 里 segments 为空")
    return meta, segs


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.environ.get("CW_VIDEO_DIR") or os.getcwd())
    ap.add_argument("--dry", action="store_true", help="只估算时长，不调用 TTS")
    ap.add_argument("--budget", type=float, help="查询：目标秒数能讲多少字（会忽略 --dir）")
    args = ap.parse_args()

    if args.budget:
        secs = args.budget
        # 反解：假设 8~10 段，首尾留白约 10.5s
        for n in (6, 8, 10, 12):
            overhead = 1.0 + 0.7 * (n - 1) + 3.2
            chars = (secs - overhead) * BASE_CPS * 1.06
            print("  %2d 段：约 %.0f 字（留白 %.1fs）" % (n, chars, overhead))
        print("\n  上限校验：600s（10 分钟）最多约 %.0f 字" % ((600 - 10.5) * BASE_CPS * 1.06))
        return

    base = os.path.abspath(args.dir)
    meta, segs = load_narration(base)
    audio_dir = os.path.join(base, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    chars_list = [len(s["text"]) for s in segs]
    est = est_total(chars_list, len(segs), meta["rate"], meta["leadIn"], meta["gap"], meta["tail"])
    print("段数 %d | 总字数 %d | 按 %s 估算时长 %.1fs（%.1f 分）| 语速系数 %.2f 字/秒"
          % (len(segs), sum(chars_list), meta["rate"], est, est / 60, cps_of(meta["rate"])))
    if est > 600:
        print("  ⚠ 预估超过 10 分钟上限，必须先精简文案或提高 rate")

    if args.dry:
        print("\n--dry：未调用 TTS。上面是估算值；正式合成后会以实测时长为准。")
        return

    import edge_tts_patch  # noqa: F401  启用新端点

    seg_out, caps = [], []
    t = meta["leadIn"]
    for i, s in enumerate(segs):
        name, text = s["name"], s["text"]
        key = "s%d" % i
        print("合成 [%d/%d] %s（%d 字）" % (i + 1, len(segs), name, len(text)))
        mp3, words = await synth(audio_dir, key, text, meta["voice"], meta["rate"])
        d = dur_of(mp3)
        caps += split_lines(text, char_times(text, words), d, t)
        seg_out.append({
            "id": key, "name": name, "start": round(t, 3), "dur": round(d, 3),
            "chars": len(text), "file": "audio/" + os.path.basename(mp3),
        })
        print("        实测 %.2fs | 词级 %d | 语速 %.2f 字/秒" % (d, len(words), len(text) / d))
        t += d + meta["gap"]

    total = round(t - meta["gap"] + meta["tail"], 3)
    timing = {
        "fps": meta["fps"], "voice": meta["voice"], "rate": meta["rate"], "total": total,
        "leadIn": meta["leadIn"], "tail": meta["tail"], "gap": meta["gap"],
        "title": meta["title"], "srtName": meta["srtName"],
        "segments": seg_out, "captions": caps,
    }
    json.dump(timing, open(os.path.join(base, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    with open(os.path.join(base, meta["srtName"]), "w", encoding="utf-8") as f:
        for i, c in enumerate(caps, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(c["start"]), ts(c["end"]), c["text"]))

    with open(os.path.join(base, "解说稿.md"), "w", encoding="utf-8") as f:
        f.write("# 《%s》解说稿\n\n" % meta["title"])
        f.write("> 配音：edge-tts `%s`　语速：%s\n> 总时长 %.1fs（%.1f 分）　共 %d 字\n\n"
                % (meta["voice"], meta["rate"], total, total / 60, sum(chars_list)))
        for s, (_, seg) in zip(seg_out, enumerate(segs)):
            f.write("## %s（%s，%.0f 秒，%d 字）\n\n%s\n\n" % (seg["name"], s["id"], s["dur"], s["chars"], seg["text"]))

    # 同步音频到 Remotion public
    pub = os.path.join(base, "remotion", "public", "audio")
    if os.path.isdir(os.path.dirname(pub)):
        os.makedirs(pub, exist_ok=True)
        for s in seg_out:
            shutil.copy2(os.path.join(base, s["file"]), os.path.join(pub, os.path.basename(s["file"])))

    print("\n=== 汇总 ===")
    for s in seg_out:
        print("  %-18s %6.2fs  起 %6.2fs  %d 字" % (s["name"], s["dur"], s["start"], s["chars"]))
    print("  字幕条数: %d ｜ 总字数: %d" % (len(caps), sum(chars_list)))
    print("  全片时长: %.2fs = %d:%02d  （%s 10 分钟上限）"
          % (total, total // 60, total % 60, "未超" if total <= 600 else "⚠ 已超出"))
    print("  帧数: %d" % round(total * meta["fps"]))


if __name__ == "__main__":
    asyncio.run(main())
