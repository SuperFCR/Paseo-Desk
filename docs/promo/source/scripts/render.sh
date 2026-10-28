#!/usr/bin/env bash
# 出片：bash scripts/render.sh draft|1080p   浏览器不用 GPU，限 8 个 worker 并降低优先级
set -euo pipefail
# shellcheck source=env.sh
source "$(dirname "$0")/env.sh"
cd $P/video
mkdir -p $P/output $P/logs
case "${1:?draft|1080p}" in
  draft) OUT=$P/output/draft.mp4; ARGS=(--quality draft) ;;
  1080p) OUT=$P/output/pocketrig-promo-1080p.mp4; ARGS=(--quality high) ;;
  *) echo "用法：render.sh draft|1080p" >&2; exit 2 ;;
esac
start=$(date +%s)
nice -n 10 hyperframes render "${ARGS[@]}" --no-browser-gpu --workers 8 --output "$OUT"
echo "耗时 $(( $(date +%s) - start )) 秒"
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size -of compact "$OUT"
echo RENDER_DONE
