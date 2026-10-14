#!/usr/bin/env bash
# 探针渲染：每个分镜压成 5 秒渲染一遍，逐张抽帧到 preview/probe/
# 版式问题在这里就该被发现，不要等到正式渲染之后。
#
# 用法：bash probe_render.sh
set -u
. "$(dirname "$0")/_env.sh"
check_env_die
cd "$PROJ" || exit 1

"$PY" "$SKILL_DIR/scripts/probe_props.py" --dir "$BASE" || exit 1

N="$("$PY" -c "import json;print(len(json.load(open('probe.json',encoding='utf-8'))['scenes']))")"
FPS="$("$PY" -c "import json;print(json.load(open('probe.json',encoding='utf-8'))['fps'])")"
FRAMES=$(( N * 150 ))
[ "$FPS" != "30" ] && FRAMES="$("$PY" -c "import json;print(round(json.load(open('probe.json',encoding='utf-8'))['total']*json.load(open('probe.json',encoding='utf-8'))['fps']))")"

mkdir -p out/probe "$BASE/preview/probe"
# 先删掉旧产物：渲染失败时不会静默复用上一次的片子（这个坑踩过）
rm -f out/probe/probe.mp4
echo "渲染探针 $FRAMES 帧（$N 个分镜）..."
"$NODE" "$CLI" render src/index.ts CodeWalkthrough out/probe/probe.mp4 \
  --props=probe.json --frames="0-$((FRAMES - 1))" --concurrency=4 \
  --chrome-mode=chrome-for-testing --browser-executable="$CHROME" 2>&1 | tail -6
if [ ! -f out/probe/probe.mp4 ]; then
  echo
  echo "探针渲染失败。常见原因：diagrams.tsx 编译错误（往上看 Error 行）、Chrome 路径不对、并发过高。"
  exit 1
fi

rm -f "$BASE/preview/probe/"*.png
# 每个分镜取两帧：
#   0.5s —— 淡入刚结束的「入场态」。缓推镜头此刻幅度最大，能抓到「边缘被裁」这类问题（见 06-pitfalls B6）；
#          同时能看错峰动画的第一批元素有没有落位。
#   3.5s —— 内容稳定态。看文字溢出、元素被裁、高亮框是否框准。
for ((i = 0; i < N; i++)); do
  base="$("$PY" -c "
import json
s=json.load(open('probe.json',encoding='utf-8'))['scenes'][$i]
name=(s.get('id') or '') if s['kind']=='diagram' else ((s.get('shot') or '').split('/')[-1].replace('.png','') or s['kind'])
print('%02d_%s' % ($i+1, name))
")"
  for pair in "0.5:a" "3.5:b"; do
    off="${pair%%:*}"; suf="${pair##*:}"
    t="$("$PY" -c "print(round($i*5.0+$off,3))")"
    "$FF/ffmpeg.exe" -y -ss "$t" -i out/probe/probe.mp4 -vframes 1 -vsync 0 "$BASE/preview/probe/${base}_${suf}.png" -loglevel error
  done
done

echo
echo "=== 逐张目视确认（顺序即讲解顺序）==="
echo "    _a = 入场态（0.5s，看边缘有没有被裁）  _b = 稳定态（3.5s，看文字与高亮框）"
ls -la "$BASE/preview/probe/"
echo "PROBE_DONE"
