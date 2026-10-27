#!/usr/bin/env bash
# 安装工作站公共部分（以 root 执行，可重复运行）。
#
#   sudo ./linux/install.sh [--install-node VERSION] [--install-packages]
#
#   --install-node 22.x.y   下载官方 Node 二进制包到 /usr/local/lib/node-shared
#   --install-packages      用 npm 把 Paseo、Codex、Claude Code 安装/更新到各自的公共前缀
#
# 不会创建用户、不会修改网络；新增用户使用 paseo-user add。
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
etc=/etc/paseo-workstation
lib=/usr/local/lib/paseo-workstation
share=/usr/local/share/paseo-workstation
node_version=''
install_packages=0

while [ $# -gt 0 ]; do
  case $1 in
    --install-node) node_version=${2:?缺少版本号}; shift 2 ;;
    --install-packages) install_packages=1; shift ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done
[ "$(id -u)" = 0 ] || { echo '请用 sudo 执行' >&2; exit 1; }

install -d -m 755 "$etc" "$etc/pre-launch.d" "$lib/bin" "$lib/libexec" "$share"
install -d -m 700 "$etc/users"
if [ ! -e "$etc/workstation.conf" ]; then
  install -m 644 "$here/workstation.conf.example" "$etc/workstation.conf"
  echo "已写入 $etc/workstation.conf，请按实际路径核对"
fi
# shellcheck source=/dev/null
. "$etc/workstation.conf"

if [ -n "$node_version" ]; then
  arch=$(uname -m)
  case $arch in x86_64) arch=x64 ;; aarch64) arch=arm64 ;; esac
  node_dir=$(dirname "$(dirname "$PW_NODE")")
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  url="https://nodejs.org/dist/v$node_version/node-v$node_version-linux-$arch.tar.xz"
  echo "下载 $url"
  curl -fsSL "$url" -o "$tmp/node.tar.xz"
  curl -fsSL "https://nodejs.org/dist/v$node_version/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
  (cd "$tmp" && grep " node-v$node_version-linux-$arch.tar.xz\$" SHASUMS256.txt | sed 's/ [^ ]*$/ node.tar.xz/' | sha256sum -c -)
  rm -rf "$node_dir.new"
  install -d -m 755 "$node_dir.new"
  tar -xJf "$tmp/node.tar.xz" -C "$node_dir.new" --strip-components=1 --no-same-owner
  rm -rf "$node_dir.old"
  if [ -e "$node_dir" ]; then mv "$node_dir" "$node_dir.old"; fi
  mv "$node_dir.new" "$node_dir"
  ln -sfn "$PW_NODE" /usr/local/bin/node
fi
[ -x "$PW_NODE" ] || { echo "找不到 Node：$PW_NODE（可加 --install-node 版本号）" >&2; exit 1; }

if [ "$install_packages" = 1 ]; then
  npm_bin="$(dirname "$PW_NODE")/npm"
  PATH="$(dirname "$PW_NODE"):$PATH"
  export PATH
  install_pkg() {
    install -d -m 755 "$1"
    "$npm_bin" install --prefix "$1" --no-fund --no-audit "$2@latest"
  }
  install_pkg "$PW_PASEO_PREFIX" @getpaseo/cli
  install_pkg "$PW_CODEX_PREFIX" @openai/codex
  install_pkg "$PW_CLAUDE_PREFIX" @anthropic-ai/claude-code
  chmod -R a+rX "$PW_PASEO_PREFIX" "$PW_CODEX_PREFIX" "$PW_CLAUDE_PREFIX"
fi

install -m 755 "$here/bin/claude" "$here/bin/codex" "$lib/bin/"
install -m 755 "$here/bin/paseo" /usr/local/bin/paseo
install -m 644 "$here/libexec/env.sh" "$lib/libexec/env.sh"
install -m 755 "$here/libexec/paseo-daemon" "$lib/libexec/paseo-daemon"
install -m 755 "$here/sbin/paseo-user" /usr/local/sbin/paseo-user
install -m 755 "$here/sbin/paseo-workstation-keepalive" /usr/local/sbin/paseo-workstation-keepalive
install -m 644 "$here/share/workstation-policy.md" "$share/"
install -m 755 "$here/share/sync-agent-policy.sh" "$share/"
install -m 644 "$here/systemd/paseo@.service" /etc/systemd/system/paseo@.service
systemctl daemon-reload

for path in "$PW_PASEO_PREFIX/node_modules/@getpaseo/cli/dist/index.js" "$PW_CLAUDE_BIN" "$PW_CODEX_BIN"; do
  [ -e "$path" ] || echo "警告：缺少 $path（可加 --install-packages，或修改 $etc/workstation.conf）" >&2
done
echo "公共部分安装完成。版本："
"$PW_NODE" --version
/usr/local/bin/paseo --version || true
echo "下一步：sudo paseo-user add <用户名> <端口>"
