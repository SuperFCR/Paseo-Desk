# 可选模块：出口网关

为工作站上**所有用户**提供统一、可验证的网络出口：公网 TCP/UDP 与 DNS 透明经过一个代理节点，代理不可用时**阻断而不是回落直连**；Claude Code / Codex 启动前检查出口状态，不满足时拒绝启动。适合需要固定出口、统一审计出口或公司要求经指定网关上网的场景。

> 使用须知：本模块是通用的网络出口控制工具。使用者须自行确保代理节点来源合法，并遵守所在地法律法规及各服务商的使用条款与支持地区政策。

## 组成

| 文件 | 作用 |
| --- | --- |
| `/etc/paseo-workstation/egress.conf` | 模块配置：系统用户、TUN 名、DNS 端口、直连网段、检查地址、期望出口地区 |
| `/etc/paseo-workstation/egress/config.yaml` | mihomo 配置（含节点凭据，root:pw-egress 640） |
| `pw-egress-guard.service` → `/usr/local/sbin/pw-egress-guard` | 开机早期装 nftables 防直连规则 |
| `pw-egress-proxy.service` | 以 `pw-egress` 用户运行 mihomo（TUN + 本地 mixed 端口 + DNS） |
| `/usr/local/sbin/pw-egress-check` | 出口检查；链接为 `pre-launch.d/50-egress` |
| `/usr/local/sbin/pw-egress-repair` | 不重启 WSL 的恢复 |
| `/etc/paseo-workstation/proxy.env` | 应用代理变量 → `127.0.0.1:17899` |
| `paseo@.service.d/egress.conf` | Paseo 实例在网关之后启动并加载代理变量 |

数据路径：

```text
透明 TCP/UDP（所有用户，含不识别代理变量的程序）→ TUN pw-egress → mihomo → 代理节点 → 目标
显式代理变量 → 127.0.0.1:17899 → 同一 mihomo 与节点
任何进程的 53 端口 DNS → 重定向到 127.0.0.1:1053 → mihomo DNS（上游 DoH 经节点）
```

防直连规则（`inet pw_egress_guard` 表）只放行：回环、已建立连接的回包（SSH / Paseo 入站不受影响）、TUN 上的 TCP/UDP、代理用户到节点地址端口、`EGRESS_DIRECT_CIDRS` 中的网段。其余出站一律拒绝。开机时先装“只允许回环与 TUN”的基线，再读配置装完整规则，因此读取配置失败也不会直连。

## 安装

1. 自行从 mihomo 官方发布页下载与系统架构对应的二进制并校验。
2. 安装文件（此时不改变网络）：
   ```bash
   sudo apt install nftables python3-yaml
   sudo ./optional/egress-proxy/install.sh --mihomo ./mihomo-linux-amd64
   ```
3. 编辑 `/etc/paseo-workstation/egress/config.yaml` 中 `proxies` 的节点参数（`server` 必须是 IPv4 字面地址），以及 `/etc/paseo-workstation/egress.conf`：
   - 计算节点在内网时，把其网段写进 `EGRESS_DIRECT_CIDRS`，否则 SSH 到节点会被拦截；
   - 需要校验出口地区时填写 `EGRESS_EXPECT_COUNTRY`。
4. 启用：
   ```bash
   sudo ./optional/egress-proxy/install.sh --enable
   sudo systemctl restart 'paseo@*'
   ```
5. WSL 部署：把 `optional/egress-proxy/windows/Repair-EgressProxy.ps1` 复制到 Windows 脚本目录（与 `Common.ps1` 同级），用于远程恢复。`paseo-workstation-keepalive` 会在每次拉起 WSL 时自动启动网关服务。

## 验证

```bash
pw-egress-check                              # 显示出口 IP / 地区
sudo nft list table inet pw_egress_guard     # 规则与计数器
sudo systemctl stop pw-egress-proxy          # 断开测试：以下命令都应失败
curl -m 5 --noproxy '*' https://example.com
claude --version                              # 应被启动前检查拒绝
sudo pw-egress-repair                         # 恢复
```

## 运维

- 查看状态：`systemctl status pw-egress-proxy`，`journalctl -u pw-egress-proxy -n 50`
- 只重启核心：`sudo systemctl restart pw-egress-proxy && pw-egress-check`
- 规则或联网异常：`sudo pw-egress-repair`；Windows 侧运行 `Repair-EgressProxy.ps1`
- 更换节点：编辑 `config.yaml` 后执行 `sudo pw-egress-repair`（guard 会按新节点地址重建放行规则）
- **不要通过删除防火墙规则排障**，那会失去防直连保护。
- 停用模块：`sudo systemctl disable --now pw-egress-proxy pw-egress-guard`，`sudo nft delete table inet pw_egress_guard`，删除 `pre-launch.d/50-egress`、`proxy.env`、`paseo@.service.d/egress.conf`，然后 `daemon-reload` 并重启 `paseo@*`。

## 边界

- 仅支持 Linux（依赖 nftables），macOS 不适用。已验证环境：WSL2 NAT 网络模式，Tailscale 运行在 Windows。**原生 Linux 上若 tailscaled 也在本机，其出站会被规则拦截**，本模块未提供该场景的放行，需要自行为 tailscaled 增加例外后再用。
- IPv6 默认关闭；ICMP 和其他原始 IP 协议被阻断，不要用 `ping` 判断网络是否正常。
- 在 WSL 中执行的 Windows `.exe` 使用 Windows 网络栈，不受这些规则约束。
- root 可以修改或删除规则，本模块不防管理员。
- WSL 中同一网络命名空间的其他发行版共享这些规则。
