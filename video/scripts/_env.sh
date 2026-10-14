#!/usr/bin/env bash
# 共用环境探测 —— 被 render_chunks.sh / probe_render.sh / finalize.sh source
# 不要直接执行本文件。

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${CW_VIDEO_DIR:-$PWD}"

# Git Bash 下 $PWD 是 MSYS 风格（/e/tmp/xxx）。作为独立参数传给 python.exe 时 MSYS 会自动
# 转成 E:\tmp\xxx，但**嵌在 `python -c "..."` 字符串里**就不会被转换，Python 会把 /e/tmp/xxx
# 当成「当前盘符下的 \e\tmp\xxx」，静默读不到文件（表现成「srt 用不上真名」这类怪现象）。
# 所以这里统一规范成 Windows 正斜杠路径，脚本里可以安全地拼进任何字符串。
if command -v cygpath >/dev/null 2>&1; then
  SKILL_DIR="$(cygpath -m "$SKILL_DIR" 2>/dev/null || echo "$SKILL_DIR")"
  BASE="$(cygpath -m "$BASE" 2>/dev/null || echo "$BASE")"
fi

PROJ="$BASE/remotion"
mkdir -p "$PROJ/out/parts"

# ---------- node ----------
NODE=""
for d in "$HOME"/.workbuddy/binaries/node/versions/*/node.exe "C:/Program Files/nodejs/node.exe"; do
  if [ -f "$d" ]; then NODE="$d"; break; fi
done
[ -z "$NODE" ] && NODE="$(command -v node || true)"

# ---------- python（优先用装了 edge_tts 的 venv）----------
PY=""
for p in "$HOME"/.workbuddy/binaries/python/envs/default/Scripts/python.exe "$HOME"/.workbuddy/binaries/python/versions/*/python.exe "C:/Python313/python.exe"; do
  if [ -f "$p" ]; then PY="$p"; break; fi
done
[ -z "$PY" ] && PY="$(command -v python3 || command -v python || true)"

# ---------- 无头浏览器（用系统 Chrome；Remotion 自带的 headless shell 在部分机器上不可用）----------
CHROME=""
for c in \
  "C:/Users/$USERNAME/AppData/Local/Google/Chrome/Application/chrome.exe" \
  "C:/Program Files/Google/Chrome/Application/chrome.exe" \
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"; do
  if [ -f "$c" ]; then CHROME="$c"; break; fi
done

# ---------- ffmpeg ----------
FF=""
for base in "C:/Users/$USERNAME/AppData/Local/Microsoft/WinGet/Packages" "C:/ffmpeg"; do
  if [ -d "$base" ]; then
    found=$(find "$base" -name ffmpeg.exe -print -quit 2>/dev/null)
    if [ -n "$found" ]; then FF="$(dirname "$found")"; break; fi
  fi
done

# ---------- 渲染 CLI ----------
CLI="$PROJ/node_modules/@remotion/cli/remotion-cli.js"

env_report() {
  echo "工程目录 : $BASE"
  echo "node     : ${NODE:-未找到}"
  echo "python   : ${PY:-未找到}"
  echo "chrome   : ${CHROME:-未找到}"
  echo "ffmpeg   : ${FF:-未找到}"
  echo "cli      : $CLI"
}

check_env_die() {
  [ -f "$CLI" ] || { echo "缺少 Remotion 依赖。先执行：bash \"$SKILL_DIR/scripts/setup_remotion.sh\" \"$BASE\""; exit 1; }
  [ -n "$NODE" ] || { echo "找不到 node.exe"; exit 1; }
  [ -f "$PROJ/props.json" ] || { echo "缺少 $PROJ/props.json，先跑 make_props.py"; exit 1; }
}
