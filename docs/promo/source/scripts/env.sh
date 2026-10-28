# shellcheck shell=bash
# source 本文件：运行时状态全部落在本项目目录，只读复用已安装的 hyperframes 工具链。
# 必填：HF_DIR 指向已安装 hyperframes、GSAP、Chrome headless shell 与字体源文件的目录：
#   $HF_DIR/node_modules/.bin/hyperframes   $HF_DIR/node_modules/gsap/dist/gsap.min.js
#   $HF_DIR/models/fonts/{NotoSansSC[wght].ttf,JetBrainsMono[wght].ttf}
# 可选：HF_BROWSER（chrome-headless-shell 路径）、PY（带 numpy 与 fontTools 的 Python）、HF_LIBS（Chrome 依赖库目录）
P=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
: "${HF_DIR:?请先设置 HF_DIR}"
export HF_DIR
export HOME=$P/.home TMPDIR=$P/.tmp
export XDG_CACHE_HOME=$P/.cache XDG_CONFIG_HOME=$P/.home/.config XDG_DATA_HOME=$P/.home/.local/share XDG_STATE_HOME=$P/.home/.local/state
export npm_config_cache=$P/.cache/npm npm_config_update_notifier=false DO_NOT_TRACK=1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export CUDA_VISIBLE_DEVICES=""
if [ -n "${HF_LIBS:-}" ]; then export LD_LIBRARY_PATH=$HF_LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}; fi
export PATH=$HF_DIR/env/bin:$HF_DIR/node_modules/.bin:$PATH
if [ -n "${HF_BROWSER:-}" ]; then export HYPERFRAMES_BROWSER_PATH=$HF_BROWSER; fi
PY=${PY:-python3}
mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME"
