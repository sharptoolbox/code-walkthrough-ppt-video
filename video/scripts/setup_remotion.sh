#!/usr/bin/env bash
# 装配 Remotion 渲染依赖到 <工程目录>/remotion/node_modules
# 优先复用本机已有依赖（秒级就绪），没有才联网安装（走国内镜像）。
#
# 用法：bash setup_remotion.sh [工程目录]
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${1:-${CW_VIDEO_DIR:-$PWD}}"
PROJ="$BASE/remotion"
mkdir -p "$PROJ"

# --- 1) 复制模板源码（只在缺失时复制，已存在则保留现场改动）---
for f in package.json remotion.config.ts tsconfig.json .npmrc; do
  [ -f "$PROJ/$f" ] || cp "$SKILL_DIR/project/$f" "$PROJ/$f"
done
mkdir -p "$PROJ/src" "$PROJ/public/shots" "$PROJ/public/audio"
for f in index.ts Root.tsx Video.tsx scenes.tsx overlays.tsx diagrams.tsx anim.ts theme.ts types.ts; do
  [ -f "$PROJ/src/$f" ] || cp "$SKILL_DIR/project/src/$f" "$PROJ/src/$f"
done
echo "模板源码 -> $PROJ"

# --- 2) 找可复用的 node_modules ---
if [ -d "$PROJ/node_modules/@remotion/cli" ]; then
  echo "已就绪：$PROJ/node_modules"
  exit 0
fi

CANDIDATES=(
  "$SKILL_DIR/project/node_modules"
  "$HOME/.codex/skills/code-walkthrough-ppt-video/video/project/node_modules"
  "$HOME/.claude/skills/code-walkthrough-ppt-video/video/project/node_modules"
  "$HOME/.workbuddy/skills/code-walkthrough-ppt-video/video/project/node_modules"
  "$HOME/.workbuddy/skills/koubo-remotion-video/project/node_modules"
  "$HOME/.workbuddy/skills/code-walkthrough-video/project/node_modules"
)
LINKED=0
for c in "${CANDIDATES[@]}"; do
  if [ -d "$c/@remotion/cli" ]; then
    echo "复用已有依赖：$c"
    if cmd //c mklink /J "$(cygpath -w "$PROJ/node_modules" 2>/dev/null || echo "$PROJ/node_modules")" "$(cygpath -w "$c" 2>/dev/null || echo "$c")" >/dev/null 2>&1 \
       || ln -s "$c" "$PROJ/node_modules" 2>/dev/null; then
      if [ -d "$PROJ/node_modules/@remotion/cli" ]; then LINKED=1; echo "已挂载：node_modules -> $c"; break; fi
    fi
  fi
done
[ "$LINKED" -eq 1 ] && exit 0

# --- 3) 联网安装 ---
echo "未找到可复用依赖，开始安装（registry.npmmirror.com，约 1~2 分钟）..."
cd "$PROJ" || exit 1
NPM_BIN="npm"
if command -v npm >/dev/null 2>&1; then NPM_BIN="npm"; fi
"$NPM_BIN" install --no-audit --no-fund --registry=https://registry.npmmirror.com || {
  echo "安装失败。检查网络，或手动执行："
  echo "  cd \"$PROJ\" && npm install --registry=https://registry.npmmirror.com"
  exit 1
}
[ -d "$PROJ/node_modules/@remotion/cli" ] && echo "安装完成" || { echo "安装异常：未找到 @remotion/cli"; exit 1; }
