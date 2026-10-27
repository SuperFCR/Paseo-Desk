# shellcheck shell=bash
# 公共环境：读取工作站配置与可选代理变量，并提供启动前检查。
# 由包装脚本 source，不直接执行。
PW_ETC=/etc/paseo-workstation
# shellcheck source=/dev/null
. "$PW_ETC/workstation.conf"
# shellcheck disable=SC2034  # 供 source 本文件的入口脚本使用
PW_PASEO_CLI="$PW_PASEO_PREFIX/node_modules/@getpaseo/cli/dist/index.js"

# 可选：统一代理环境（例如 optional/egress-proxy 安装的本地入口）
if [ -r "$PW_ETC/proxy.env" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$PW_ETC/proxy.env"
  set +a
fi

# 依次运行 pre-launch.d 中的可执行检查；任一失败则拒绝启动。
# 检查的输出全部写到 stderr，保证 Claude/Codex 的协议输出干净。
pw_pre_launch() {
  local tool=$1 hook
  if [ -n "${PW_GROUP:-}" ] && ! id -nG | tr ' ' '\n' | grep -qx "$PW_GROUP"; then
    echo "请以 $PW_GROUP 组成员身份运行 $tool（不要用 sudo）。" >&2
    exit 1
  fi
  for hook in "$PW_ETC"/pre-launch.d/*; do
    [ -x "$hook" ] || continue
    if ! "$hook" "$tool" >&2; then
      echo "启动前检查失败：$hook，已拒绝启动 $tool。" >&2
      exit 1
    fi
  done
}
