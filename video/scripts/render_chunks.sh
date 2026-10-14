#!/usr/bin/env bash
# 分块渲染（长片一次渲染会卡死，必须拆块 + 无损拼接）
#
# 用法：
#   bash render_chunks.sh              # 帧数/块数自动从 props.json 推断
#   bash render_chunks.sh 6764         # 指定总帧数
#   bash render_chunks.sh 6764 6       # 指定总帧数 + 块数
#
# 每块失败会自动降到 concurrency=2 重试一次。
set -u
. "$(dirname "$0")/_env.sh"
check_env_die
cd "$PROJ" || exit 1

# ---------- 总帧数 ----------
FRAMES="${1:-}"
if [ -z "$FRAMES" ]; then
  FRAMES="$("$PY" -c "import json;d=json.load(open('props.json',encoding='utf-8'));print(round(d['total']*d['fps']))")"
fi
# ---------- 块数：目标每块 ~2000 帧 ----------
CHUNKS="${2:-$(( (FRAMES + 1999) / 2000 ))}"
[ "$CHUNKS" -lt 1 ] && CHUNKS=1
[ "$CHUNKS" -gt 14 ] && CHUNKS=14

STEP=$(( (FRAMES + CHUNKS - 1) / CHUNKS ))
echo "总帧数 $FRAMES -> $CHUNKS 块"
env_report
mkdir -p out/parts

for ((i = 0; i < CHUNKS; i++)); do
  a=$(( i * STEP ))
  b=$(( a + STEP - 1 ))
  [ "$b" -ge "$FRAMES" ] && b=$(( FRAMES - 1 ))
  [ "$a" -gt "$b" ] && continue
  out="out/parts/part$((i + 1)).mp4"
  rm -f "$out"     # 先删旧产物：失败时不会静默复用上一次的块
  ok=0
  for attempt in 1 2; do
    cc=4
    [ "$attempt" -eq 2 ] && cc=2
    echo "=== 块 $((i + 1))/$CHUNKS  帧 $a-$b  尝试 $attempt  concurrency=$cc  $(date +%H:%M:%S) ==="
    "$NODE" "$CLI" render src/index.ts CodeWalkthrough "$out" \
      --props=props.json --frames="$a-$b" --concurrency=$cc \
      --chrome-mode=chrome-for-testing --browser-executable="$CHROME" 2>&1 | tail -4
    if [ -f "$out" ]; then ok=1; break; fi
  done
  [ "$ok" -ne 1 ] && {
    echo "CHUNK_$((i + 1))_FAILED（帧 $a-$b）"
    echo "常见原因：props.json 里引用了不存在的截图 / diagrams 编译错误 / 并发过高。"
    exit 1
  }
  echo "块 $((i + 1)) 完成 $(date +%H:%M:%S)  大小 $(du -m "$out" | cut -f1)MB"
done

echo "ALL_CHUNKS_DONE"
ls -la out/parts
