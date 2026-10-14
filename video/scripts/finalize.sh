#!/usr/bin/env bash
# 拼接分块 + 验收 + 产出交付物
#
# 用法：bash finalize.sh
# 环境变量：
#   FINAL_NAME  交付文件名（不含扩展名），默认「演示视频」
#   SRT_NAME    srt 文件名，默认取 timing.json 里 meta.srtName 的落盘结果，兜底「演示视频.srt」
set -u
. "$(dirname "$0")/_env.sh"
check_env_die
cd "$PROJ" || exit 1

CHUNKS=$(ls -1 out/parts/part*.mp4 2>/dev/null | wc -l | tr -d ' ')
[ "$CHUNKS" -lt 1 ] && { echo "out/parts 下没有分块，先跑 render_chunks.sh"; exit 1; }
echo "发现 $CHUNKS 个分块"

rm -f out/concat.txt
for ((i = 1; i <= CHUNKS; i++)); do echo "file 'parts/part$i.mp4'" >> out/concat.txt; done
"$FF/ffmpeg.exe" -y -loglevel error -f concat -safe 0 -i out/concat.txt -c copy out/full.mp4 || exit 1

EXPECT="$("$PY" -c "import json;d=json.load(open('props.json',encoding='utf-8'));print(round(d['total']*d['fps']))")"
# 注意：ffprobe 的 csv=p=0 在部分版本上会带尾逗号（"1419,"），必须清洗后再比对
GOT="$("$FF/ffprobe.exe" -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -of csv=p=0 out/full.mp4 | tr -cd '0-9')"
DUR="$("$FF/ffprobe.exe" -v error -show_entries format=duration -of csv=p=0 out/full.mp4 | tr -cd '0-9.')"
echo "--- 核对 ---"
echo "期望帧数 $EXPECT ｜ 实际帧数 $GOT"
echo "时长 $DUR s"
if [ "$EXPECT" != "$GOT" ]; then
  echo "⛔ 帧数不一致：某一块渲染失败或被截断，检查 out/parts/ 下每个块的时间戳与大小"
  ls -la out/parts/
  exit 1
fi

echo "--- 拼接点断音检查（>0.8s 静音即需人工确认）---"
"$FF/ffmpeg.exe" -hide_banner -i out/full.mp4 -af "silencedetect=n=-42dB:d=0.8" -f null - 2>&1 | grep -i silence | head -12 || true
echo "   注：段间留白本就会触发，重点看落在「块边界 ≈ 累加块时长」上的静音"

# ---------- 交付物 ----------
# 注意：此刻当前目录已经是 $PROJ，读 timing.json 必须带 $BASE 前缀，否则静默读不到
#       就会退化成默认名，最后表现成「srt 没产出」——这个坑踩过。
NAME="${FINAL_NAME:-演示视频}"
if [ -z "${SRT_NAME:-}" ]; then
  SRT_NAME="$("$PY" -c "
import json,sys
try:
    print(json.load(open(r'$BASE/timing.json',encoding='utf-8')).get('srtName') or '演示视频.srt')
except Exception:
    print('演示视频.srt')
")"
fi

cp out/full.mp4 "$BASE/${NAME}.mp4"
[ -f "$BASE/$SRT_NAME" ] && cp "$BASE/$SRT_NAME" "$BASE/${NAME}.srt"
[ -f "$BASE/解说稿.md" ] && cp "$BASE/解说稿.md" "$BASE/${NAME}_解说稿.md"

echo
echo "=== 交付物 ==="
missing=0
for f in "${NAME}.mp4" "${NAME}.srt" "${NAME}_解说稿.md"; do
  if [ -f "$BASE/$f" ]; then
    echo "  ✓ $f"
  else
    echo "  ⛔ 缺失 $f"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  echo
  echo "交付物不齐。常见原因：timing.json 不在 $BASE 下（srt 用不上真名）、解说稿.md 未生成。"
  exit 1
fi
ls -la "$BASE" | grep -E "\.mp4|\.srt|解说稿"
echo "FINALIZE_DONE"
