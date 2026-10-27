#!/usr/bin/env bash
# 安装工作站公共部分（Linux / macOS，以 root 执行，可重复运行）。
#
#   sudo ./linux/install.sh [--install-node VERSION] [--install-packages]
#
#   --install-node 24.x.y   下载官方 Node 二进制包到 /usr/local/lib/node-shared
#   --install-packages      用 npm 把 Paseo、Codex、Claude Code 安装/更新到各自的公共前缀
#
# 不会创建用户、不会修改网络。Linux 新增用户使用 paseo-user add；
# macOS 只安装公共部分，每用户实例按 docs/platforms.md 用 launchd 配置。
set -euo pipefail
os=$(uname -s)
case $os in
  Linux) node_os=linux ;;
  Darwin) node_os=darwin ;;
  *) echo "不支持的系统：$os" >&2; exit 1 ;;
esac

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
if [ -n "$node_version" ] && ! [[ $node_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo 'Node 版本必须是完整版本号，例如 24.22.1（不带 v）' >&2
  exit 2
fi
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
  case $arch in
    x86_64) arch=x64 ;;
    aarch64|arm64) arch=arm64 ;;
    *) echo "不支持的 Node 架构：$arch" >&2; exit 1 ;;
  esac
  # 只替换专用安装目录，避免 PW_NODE=/usr/bin/node 时意外移动整个 /usr。
  if ! [[ $PW_NODE =~ ^(/usr/local/lib|/opt)/[a-zA-Z0-9][a-zA-Z0-9._-]*/bin/node$ ]]; then
    echo '--install-node 要求 PW_NODE 位于 /usr/local/lib 或 /opt 下的专用目录，并以 /bin/node 结尾' >&2
    exit 1
  fi
  node_dir=$(dirname "$(dirname "$PW_NODE")")
  sha256_check() { if command -v sha256sum >/dev/null; then sha256sum -c -; else shasum -a 256 -c -; fi; }
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  archive="node-v$node_version-$node_os-$arch.tar.gz"
  url="https://nodejs.org/dist/v$node_version/$archive"
  echo "下载 $url"
  curl -fsSL "$url" -o "$tmp/node.tar.gz"
  curl -fsSL "https://nodejs.org/dist/v$node_version/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
  (cd "$tmp" && awk -v name="$archive" '$2 == name {print $1 "  node.tar.gz"; found=1} END {if (!found) exit 1}' SHASUMS256.txt | sha256_check)
  rm -rf "$node_dir.new"
  install -d -m 755 "$node_dir.new"
  tar -xzf "$tmp/node.tar.gz" -C "$node_dir.new" --strip-components=1 --no-same-owner
  rm -rf "$node_dir.old"
  if [ -e "$node_dir" ]; then mv "$node_dir" "$node_dir.old"; fi
  mv "$node_dir.new" "$node_dir"
  install -d -m 755 /usr/local/bin
  ln -sfn "$PW_NODE" /usr/local/bin/node
fi
[ -x "$PW_NODE" ] || { echo "找不到 Node：$PW_NODE（可加 --install-node 版本号）" >&2; exit 1; }

if [ "$install_packages" = 1 ]; then
  npm_bin="$(dirname "$PW_NODE")/npm"
  PATH="$(dirname "$PW_NODE"):$PATH"
  export PATH
  install_pkg() {
    install -d -m 755 "$1"
    "$npm_bin" install --prefix "$1" --no-fund --no-audit "$2"
  }
  install_pkg "$PW_PASEO_PREFIX" "@getpaseo/cli@${PW_PASEO_VERSION:-0.13.2}"
  install_pkg "$PW_CODEX_PREFIX" @openai/codex@latest
  install_pkg "$PW_CLAUDE_PREFIX" @anthropic-ai/claude-code@latest
  chmod -R a+rX "$PW_PASEO_PREFIX" "$PW_CODEX_PREFIX" "$PW_CLAUDE_PREFIX"
fi

install -d -m 755 /usr/local/bin
install -m 755 "$here/bin/claude" "$here/bin/codex" "$lib/bin/"
install -m 755 "$here/bin/paseo" /usr/local/bin/paseo
install -m 644 "$here/libexec/env.sh" "$lib/libexec/env.sh"
install -m 755 "$here/libexec/paseo-daemon" "$lib/libexec/paseo-daemon"
install -m 644 "$here/share/workstation-policy.md" "$share/"
install -m 755 "$here/share/sync-agent-policy.sh" "$share/"
if [ "$os" = Linux ]; then
  install -d -m 755 /usr/local/sbin /etc/systemd/system
  install -m 755 "$here/sbin/paseo-user" /usr/local/sbin/paseo-user
  install -m 755 "$here/sbin/paseo-workstation-keepalive" /usr/local/sbin/paseo-workstation-keepalive
  install -m 644 "$here/systemd/paseo@.service" /etc/systemd/system/paseo@.service
  systemctl daemon-reload
fi

for path in "$PW_PASEO_PREFIX/node_modules/@getpaseo/cli/dist/index.js" "$PW_CLAUDE_BIN" "$PW_CODEX_BIN"; do
  [ -e "$path" ] || echo "警告：缺少 $path（可加 --install-packages，或修改 $etc/workstation.conf）" >&2
done
echo "公共部分安装完成。版本："
"$PW_NODE" --version
/usr/local/bin/paseo --version || true
if [ "$os" = Linux ]; then
  echo "下一步：sudo paseo-user add <用户名> <端口>"
else
  echo "下一步：按 docs/platforms.md 的 macOS 一节为每位成员配置 launchd 实例"
fi
