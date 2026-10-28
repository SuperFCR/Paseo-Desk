#!/usr/bin/env bash
# 从成片截取亮点片段，生成 README 自动循环播放的 GIF。
# 用法：bash scripts/gif.sh 成片.mp4 输出.gif [宽度=800] [帧率=12]
# 片段：片头标题、24 小时在线表盘、手机看实验结果、结尾；时间点对应 scenes.json 的默认时长。
set -euo pipefail
in=${1:?成片 MP4}
out=${2:?输出 GIF}
width=${3:-800}
fps=${4:-12}
segments=("3 8.5" "101 108.5" "141 150.5" "236.5 241")
chains=""
labels=""
i=0
for seg in "${segments[@]}"; do
  read -r a b <<<"$seg"
  len=$(awk -v a="$a" -v b="$b" 'BEGIN { printf "%.2f", b - a }')
  fout=$(awk -v l="$len" 'BEGIN { printf "%.2f", l - 0.35 }')
  chains+="[0:v]trim=start=${a}:end=${b},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.35,fade=t=out:st=${fout}:d=0.35[s${i}];"
  labels+="[s${i}]"
  i=$((i + 1))
done
filter="${chains}${labels}concat=n=${i}:v=1:a=0,fps=${fps},scale=${width}:-1:flags=lanczos,split[x][y];"
filter+="[x]palettegen=max_colors=128:stats_mode=diff[p];[y][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
nice -n 10 ffmpeg -hide_banner -loglevel error -y -threads 4 -i "$in" -filter_complex "$filter" -loop 0 "$out"
ls -l "$out"
