#!/usr/bin/env bash
# 安装可选出口网关模块（root）。先完成 linux/install.sh。
#
#   sudo ./optional/egress-proxy/install.sh --mihomo /path/to/mihomo
#
# mihomo 二进制需自行从官方发布页下载并校验；本仓库不分发二进制。
# 首次安装只写入模板并停在启用之前：填好节点后再加 --enable。
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
etc=/etc/paseo-workstation
mihomo=''
enable=0
while [ $# -gt 0 ]; do
  case $1 in
    --mihomo) mihomo=${2:?缺少路径}; shift 2 ;;
    --enable) enable=1; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done
[ "$(id -u)" = 0 ] || { echo '请用 sudo 执行' >&2; exit 1; }
[ -r "$etc/workstation.conf" ] || { echo '请先运行 linux/install.sh' >&2; exit 1; }
for cmd in nft ip curl python3; do
  command -v "$cmd" >/dev/null || { echo "缺少命令：$cmd" >&2; exit 1; }
done
python3 -c 'import yaml' 2>/dev/null || { echo '缺少 python3-yaml（apt install python3-yaml）' >&2; exit 1; }

[ -e "$etc/egress.conf" ] || install -m 644 "$here/egress.conf.example" "$etc/egress.conf"
# shellcheck source=/dev/null
. "$etc/egress.conf"
id -u "$EGRESS_USER" >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin "$EGRESS_USER"
install -d -m 750 -o root -g "$EGRESS_USER" "$etc/egress"
install -d -m 750 -o "$EGRESS_USER" -g "$EGRESS_USER" /var/lib/pw-egress
if [ ! -e "$etc/egress/config.yaml" ]; then
  install -m 640 -o root -g "$EGRESS_USER" "$here/config.example.yaml" "$etc/egress/config.yaml"
  echo "已写入 $etc/egress/config.yaml 模板：填写 proxies 节点参数后再执行 --enable"
fi
if [ -n "$mihomo" ]; then
  install -d -m 755 /usr/local/libexec/pw-egress
  install -m 755 "$mihomo" /usr/local/libexec/pw-egress/mihomo
fi
[ -x /usr/local/libexec/pw-egress/mihomo ] || { echo '缺少 mihomo，请加 --mihomo 路径' >&2; exit 1; }

install -m 755 "$here/sbin/pw-egress-guard" "$here/sbin/pw-egress-check" "$here/sbin/pw-egress-repair" /usr/local/sbin/
install -m 644 "$here/systemd/pw-egress-guard.service" "$here/systemd/pw-egress-proxy.service" /etc/systemd/system/
systemctl daemon-reload

if [ "$enable" != 1 ]; then
  echo '文件已安装，尚未启用（网络未改动）。核对 egress.conf 与 config.yaml 后执行：'
  echo '  sudo ./optional/egress-proxy/install.sh --enable'
  exit 0
fi

# 以下步骤才真正改变网络与 CLI 启动行为
/usr/local/libexec/pw-egress/mihomo -t -d /var/lib/pw-egress -f "$etc/egress/config.yaml"
systemctl enable pw-egress-guard.service pw-egress-proxy.service
/usr/local/sbin/pw-egress-repair
sed "s#http://127.0.0.1:17899#$EGRESS_HTTP_PROXY#g" "$here/proxy.env.example" > "$etc/proxy.env"
chmod 644 "$etc/proxy.env"
install -d -m 755 /etc/systemd/system/paseo@.service.d
install -m 644 "$here/systemd/paseo@.service.d-egress.conf" /etc/systemd/system/paseo@.service.d/egress.conf
ln -sfn /usr/local/sbin/pw-egress-check "$etc/pre-launch.d/50-egress"
systemctl daemon-reload
echo '出口网关已启用。重启已运行的 Paseo 实例以加载代理变量：systemctl restart "paseo@*"'
