# 管理员部署指南

本章由管理员执行。示例成员 `alice`（端口 6767）、`bob`（端口 6768），SSH 对外端口 2222。所有尖括号内容替换为实际值。

## 0. 前提

- 一台常开的 PC：原生 Linux，或 Windows 10/11 + WSL2 发行版（Ubuntu 等）。
- 已启用 systemd。WSL 在 `/etc/wsl.conf` 中加入以下内容，然后在 Windows 执行 `wsl --shutdown` 并重新进入：
  ```ini
  [boot]
  systemd=true
  ```
- 管理员拥有 sudo；已安装 `openssh-server`、`python3`、`curl`、`xz-utils`。
- Tailscale：WSL 场景装在 Windows，原生 Linux 装在本机。管理员能编辑 tailnet 的访问策略。

## 1. 安装公共部分

```bash
git clone <本仓库地址> && cd paseo-multiuser-workstation
sudo ./linux/install.sh --install-node 24.22.1 --install-packages
```

- `--install-node` 下载官方 Node 并校验 SHA256，装到 `/usr/local/lib/node-shared`。已有公共 Node 时省略，并在 `/etc/paseo-workstation/workstation.conf` 中修改 `PW_NODE`。
- `--install-packages` 用 npm 把 `@getpaseo/cli`、`@openai/codex`、`@anthropic-ai/claude-code` 装到各自的公共前缀。也可以用其他方式安装，只要把配置中的 `PW_CLAUDE_BIN`、`PW_CODEX_BIN` 指向实际可执行文件。
- 脚本可重复运行，不会覆盖已有的 `workstation.conf`。

安装结果：

| 路径 | 作用 |
| --- | --- |
| `/etc/paseo-workstation/workstation.conf` | 公共路径、用户组、监听地址、sshd 片段位置 |
| `/etc/paseo-workstation/users/<user>.env` | 每个实例的 HOME、PASEO_HOME、PASEO_LISTEN（root 600） |
| `/etc/paseo-workstation/pre-launch.d/` | 启动 CLI 前的检查钩子（可执行文件） |
| `/etc/paseo-workstation/proxy.env` | 可选：统一代理变量 |
| `/usr/local/lib/paseo-workstation/bin/{claude,codex}` | Paseo provider 与终端共用的入口 |
| `/usr/local/bin/paseo` | 自动加载本人 `client.env` 的 Paseo CLI |
| `/usr/local/sbin/paseo-user` | 每用户实例管理 |
| `/etc/systemd/system/paseo@.service` | 每用户服务模板 |

### SSH

参考 [`linux/sshd-00-paseo-workstation.conf.example`](../linux/sshd-00-paseo-workstation.conf.example)，写入 `/etc/ssh/sshd_config.d/00-paseo-workstation.conf`。**先把管理员自己写进 `AllowUsers`**，然后：

```bash
sudo sshd -t && sudo systemctl reload ssh
```

之后 `paseo-user add` / `remove --revoke-ssh` 会自动维护 `AllowUsers`，修改前执行 `sshd -t` 校验，失败自动还原。把主机指纹（`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`）记进交付单，供成员首次连接时核对。

### 让终端也走公共入口（可选）

成员在 SSH 终端中直接输入 `claude` / `codex` 时，若希望同样经过启动前检查，可在 `/etc/profile.d/paseo-workstation.sh` 中加入：

```bash
export PATH="/usr/local/lib/paseo-workstation/bin:$PATH"
```

## 2. 新增成员

先确认端口未被占用：

```bash
sudo paseo-user list
ss -ltn | grep -w 6767 || echo 端口空闲
```

创建并启用实例：

```bash
sudo paseo-user add alice 6767
sudo passwd alice          # 或为其写入 ~/.ssh/authorized_keys
```

`paseo-user add` 会：创建缺失的用户；建立 `~/.paseo`、`~/projects`、`~/results`（700）；生成随机连接密码写入 `~/.paseo/client.env`（600）并把 bcrypt 哈希写入 `~/.paseo/config.json`；关闭 relay、开启网页、关闭本地语音；把 provider 指向公共包装脚本；加入 `ai-cli-users` 组；写入 `/etc/paseo-workstation/users/alice.env`；同步工作站使用约定到成员的 `CLAUDE.md` / `AGENTS.md`；加入 SSH 白名单；启用并重启 `paseo@alice`。

脚本可以重复运行：已有密码会保留，已有配置会合并更新。修改端口时直接用新端口再执行一次 `add`。

### 成员登录模型账号

由成员本人在自己的 SSH 终端执行（无浏览器环境按提示使用设备码或复制链接的方式）：

```bash
claude auth login
codex login
claude auth status
codex login status
```

不要把管理员或他人的 `~/.claude`、`~/.codex` 凭据复制给新成员。

### 计算节点 SSH

每位成员维护自己的 `~/.ssh/config`、私钥和计算节点授权（模板见 [`templates/ssh_config.example`](../templates/ssh_config.example)）。不要复制管理员私钥。未配置计算节点前，不应在工作站代替执行重计算。

## 3. Windows + WSL 入口

在 Windows 上把仓库的 `windows/` 目录复制到 `C:\PaseoWorkstation\`（路径可自选），然后：

```powershell
cd C:\PaseoWorkstation
Copy-Item config.example.json config.json
notepad config.json       # 填写发行版名称 Distro，核对 wsl.exe 与 tailscale.exe 路径
```

| 字段 | 含义 |
| --- | --- |
| `Distro` | `wsl -l -v` 中的发行版名称 |
| `SshListenPort` / `SshTargetPort` | Tailscale 地址上对外的 SSH 端口 / WSL 内 sshd 端口 |
| `LoopSeconds` | 同步周期 |
| `KeepAlive` | 是否由任务保持 WSL 实例常驻 |

在**管理员 PowerShell** 中先手动同步一次，再注册开机任务：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Sync-WorkstationEndpoints.ps1
netsh interface portproxy show all
.\Install-PaseoWorkstationTask.ps1
```

同步脚本从 WSL 读取 `paseo-user list --json`，为 SSH 与每个 Paseo 端口建立 `<Tailscale IP>:端口 → 127.0.0.1:端口` 的转发和名为 `PaseoWorkstation-<端口>` 的防火墙规则（仅本机 Tailscale 地址、来源 `100.64.0.0/10`）。已移除的用户端口、旧 Tailscale 地址上的转发会被清理。日志在 `C:\PaseoWorkstation\logs\workstation.log`。

如果不希望 Windows 访问 WSL 读取用户列表，可以在同目录放一个 `paseo-endpoints.json`（`[{"User":"alice","Port":6767}]`），脚本会以它为准。

计划任务以当前 Windows 用户、“不管用户是否登录”、最高权限运行（WSL 发行版按 Windows 用户注册，SYSTEM 账户无法启动它）。若冷启动后 WSL 未拉起，在任务计划程序中把该任务改为“使用密码运行”再测。

PC 的电源与休眠策略由管理员按实际安排：休眠期间任务和连接都会中断。

## 4. 原生 Linux 入口

两种方式任选其一：

- **直接监听 Tailscale 地址**：在 `workstation.conf` 中设置 `PW_LISTEN_HOST=<本机 100.x.y.z>`，对每位成员重新执行一次 `paseo-user add <user> <port>`。tailscaled 尚未就绪时服务会按 `Restart=on-failure` 自动重试。
- **保持 127.0.0.1，用 `tailscale serve` 转发 TCP**：对每个端口配置 TCP 转发到 `127.0.0.1:<port>`（具体参数以 `tailscale serve --help` 为准），并用 `tailscale serve status` 核对。

## 5. Tailscale 授权

参考 [`templates/tailscale-policy.example.hujson`](../templates/tailscale-policy.example.hujson)：给工作站打上 `tag:paseo-ws`，按成员身份只放行其 Paseo 端口和 SSH 端口。

- 外部协作者也可以通过 Tailscale 控制台的设备共享（Share）接入：对方用自己的 Tailscale 账号接受邀请，共享设备在对方客户端中可能显示不同的 IP，以对方客户端为准。
- 新增窄规则前，检查并移除旧的全放行规则（例如 `"src": ["*"], "dst": ["*:*"]`），否则窄规则不会生效。

## 6. 日常运维

统一用 systemd 管理实例，不要再执行 `paseo daemon start` 启动额外的后台实例：

```bash
sudo paseo-user list
sudo systemctl status paseo@alice
sudo systemctl restart paseo@alice
sudo journalctl -u paseo@alice -n 80 --no-pager
```

| 操作 | 方法 |
| --- | --- |
| 重设连接密码 | `sudo paseo-user reset-password alice`，随后通知本人在所有客户端更新 |
| 修改端口 | `sudo paseo-user add alice <新端口>`；Windows 同步任务自动跟进，客户端改填新端口 |
| 开启某人的语音听写 | 本人终端 `paseo daemon config set features.dictation.enabled true`，管理员重启其服务。本地模型会占用工作站存储与 CPU，中文需选择支持中文的模型 |
| 升级公共程序 | `sudo ./linux/install.sh --install-packages`，再 `sudo systemctl restart 'paseo@*'`，按验收清单复测 |
| 更新工作站约定 | 编辑 `linux/share/workstation-policy.md` 后重新运行 `install.sh`，各成员执行 `/usr/local/share/paseo-workstation/sync-agent-policy.sh` |

成员在本人 HOME 中自行安装的旧版本不会影响公共副本，反之亦然。

`~/.paseo/config.json` 中的监听地址会被服务环境文件 `/etc/paseo-workstation/users/<user>.env` 中的 `PASEO_LISTEN` 覆盖，修改端口必须通过 `paseo-user add`。

## 7. 停用成员

```bash
sudo paseo-user remove bob                              # 只停用 Paseo 实例
sudo paseo-user remove bob --revoke-cli --revoke-ssh    # 同时移出公共 CLI 组与 SSH 白名单
```

Windows 同步任务会在下一轮删除对应的转发与防火墙规则；同时在 Tailscale 策略中移除其授权。停用不删除用户、HOME、项目或凭据；确认数据已备份后再由管理员手动处理。

## 8. 可选模块

- [出口网关](egress-proxy.md)：全用户透明代理 + 防直连 + CLI 启动前出口检查。
- 其他启动前检查：任何可执行文件放进 `/etc/paseo-workstation/pre-launch.d/` 即生效，参数为工具名（`claude` / `codex`），退出码非 0 即拒绝启动。
