#!/usr/bin/env bash
# 把仓库中的 PocketRig skills 复制到本人 skills 目录。
# 用法：skills/install.sh [--codex | --target DIR]
set -euo pipefail

src=$(cd "$(dirname "$0")" && pwd)
target="$HOME/.claude/skills"
case "${1:-}" in
  "") ;;
  --codex) target="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  --target) target="${2:?--target 需要目录参数}" ;;
  -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
  *) echo "未知参数：$1" >&2; exit 2 ;;
esac

mkdir -p "$target"
stamp=$(date +%Y%m%d%H%M%S)
count=0
for dir in "$src"/*/; do
  [ -f "${dir}SKILL.md" ] || continue
  name=$(basename "$dir")
  if [ -e "$target/$name" ]; then
    mv "$target/$name" "$target/$name.bak-$stamp"
    echo "已备份：$target/$name.bak-$stamp"
  fi
  cp -R "$dir" "$target/$name"
  echo "已安装：$target/$name"
  count=$((count + 1))
done
echo "共 ${count} 个 skill → ${target}"
