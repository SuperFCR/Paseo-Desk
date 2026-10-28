---
name: paseo-desk-setup
description: 在自己一台常开的电脑（Windows + WSL2、原生 Linux 或 macOS）上从零装好 Paseo Desk，并为自己创建第一个 Paseo 实例。用户说“安装 Paseo Desk”“把这台电脑变成工作站”“给我自己建一个 Paseo 实例”“set up Paseo Desk”时使用；多人管理用 paseo-desk-team，常驻与开机自启用 paseo-desk-always-on。
---

# paseo-desk-setup：单人起步

目标：工作站上跑着属于你自己的 Paseo 实例，Claude Code / Codex 以你的系统用户运行。完成后接着用 [paseo-desk-connect](../paseo-desk-connect/SKILL.md) 让手机和 Mac 连进来。

## 先确认

逐项问清，缺一项就停下来问，不要猜：

| 项 | 说明 |
| --- | --- |
| 宿主平台 | Windows + WSL2 / 原生 Linux / macOS（macOS 走 [平台文档](../../docs/platforms.md) 第三节，不执行下面的 Linux 步骤） |
| 运行用户 | 你自己的系统用户（通常 `$USER`），不要用 root |
| Paseo 端口 | 默认 6767，先确认空闲 |
| sudo | 安装与创建实例需要 sudo；没有就停下 |
| 仓库位置 | 已有克隆就用，没有则 `git clone https://github.com/SuperFCR/Paseo-Desk.git` |

## 步骤（Linux / WSL）

1. **前提检查**（只读）：
   ```bash
   systemctl is-system-running || true      # WSL 需在 /etc/wsl.conf 启用 systemd
   command -v python3 curl tar gzip sshd
   ss -ltn | grep -w 6767 || echo 端口空闲
   ```
   WSL 未启用 systemd 时，告诉用户在 `/etc/wsl.conf` 加 `[boot] systemd=true`，再在 Windows 执行 `wsl --shutdown`；这一步会中断 WSL 中所有进程，必须先征得同意。
2. **安装公共部分**（可重复执行，不覆盖已有配置）：
   ```bash
   cd Paseo-Desk
   sudo ./linux/install.sh --install-node 24.22.1 --install-packages
   ```
   已有公共 Node 时去掉 `--install-node`，并在 `/etc/paseo-workstation/workstation.conf` 中设置 `PW_NODE`。Paseo 固定为 `PW_PASEO_VERSION`（默认 0.13.2），不要擅自升级。
3. **为自己创建实例**：
   ```bash
   sudo paseo-user add "$USER" 6767
   ```
   会生成随机连接密码（`~/.paseo/client.env`，600）、启用 `paseo@$USER`、把 provider 指向公共包装脚本。
4. **登录自己的模型账号**（用户本人在终端完成，不要代填、不要复制他人凭据）：
   ```bash
   claude auth login
   codex login
   ```
5. **SSH（可选，但手机终端和隧道需要）**：参考 [`linux/sshd-00-paseo-workstation.conf.example`](../../linux/sshd-00-paseo-workstation.conf.example)，先把自己写进 `AllowUsers`，再 `sudo sshd -t && sudo systemctl reload ssh`。

## 验证

```bash
sudo paseo-user list
systemctl is-active "paseo@$USER"
paseo daemon status
paseo provider diagnostic claude
```

Resolved path 应指向 `/usr/local/lib/paseo-workstation/bin/claude`。全部通过后告诉用户：端口、密码所在文件（不要在对话里回显密码）、下一步用 paseo-desk-connect。

## 停下来问用户的情况

- `install.sh` 或 `paseo-user` 报错：贴出错误与相关日志，不要改脚本绕过。
- 报找不到 Paseo 内部 `auth.js`：见 [故障排查](../../docs/troubleshooting.md) 的对应条目。
- 需要重启 WSL、修改 sshd、改防火墙：先说明影响再执行。

参考：[管理员部署指南](../../docs/admin-guide.md) · [按宿主平台部署](../../docs/platforms.md) · [设计方案](../../docs/design.md)
