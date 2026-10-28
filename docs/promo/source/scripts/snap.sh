#!/usr/bin/env bash
# 截取检查帧：bash scripts/snap.sh 时间点,时间点,...  → .tmp/snap/
set -euo pipefail
# shellcheck source=env.sh
source "$(dirname "$0")/env.sh"
cd $P/video
rm -rf $P/review/snap && mkdir -p $P/review/snap
nice -n 10 hyperframes snapshot --at "${1:?时间点列表}" --no-end -o $P/review/snap --json > $P/review/snap.json
find $P/review/snap -name "*.jpg" -o -name "*.png" | sort
