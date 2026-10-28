#!/usr/bin/env bash
# 合成音乐（缺失或 --music 时）并组装 video/：bash scripts/build.sh [--music]
set -euo pipefail
# shellcheck source=env.sh
source "$(dirname "$0")/env.sh"
cd "$P"
# 音乐段落跟随场景：s04 进入主段，s09 收鼓点，s11 尾声
read -r TOTAL MAIN CALM OUTRO < <("$PY" -c "
import json
sc = json.load(open('scenes.json')); t = 0; at = {}
for s in sc: at[s['id']] = t; t += s['dur']
print(t, at['s04'], at['s09'], at['s11'])")
if [ "${1:-}" = --music ] || [ ! -f audio/music.wav ]; then
  nice -n 10 "$PY" tools/music.py --seconds "$TOTAL" --main "$MAIN" --calm "$CALM" --outro "$OUTRO" --out audio/music.wav
fi
"$PY" tools/build.py
cd video && hyperframes lint . 2>&1 | tail -20 || true
