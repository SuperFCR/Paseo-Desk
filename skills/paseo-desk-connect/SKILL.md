---
name: paseo-desk-connect
description: 让自己的手机（iPhone / Android）和 Mac / 笔记本通过 Tailscale 连到工作站上的本人 Paseo 实例：Tailscale 入网与授权、Paseo 客户端添加 Host、首个任务验证。用户说“手机怎么连工作站”“Paseo 添加 Host”“Tailscale 授权端口”“iPhone 用 Shadowrocket 连”“Mac 接着手机的会话继续”时使用。
---

# paseo-desk-connect：手机与 Mac 连进来

目标：手机和 Mac 都能打开**同一个**本人 Paseo 实例，在手机上发起的会话可以在 Mac 上接着做。

```text
手机 / Mac → Tailscale（私有网络）→ 工作站 <WS_IP>:<端口> → 本人 Paseo 实例
```

## 先确认

| 项 | 来源 |
| --- | --- |
| 工作站 Tailscale 地址 `<WS_IP>` | 工作站 `tailscale ip -4`（WSL 部署在 Windows 侧执行） |
| 本人 Paseo 端口 | `sudo paseo-user list` |
| Paseo 密码 | 本人 `~/.paseo/client.env` 的 `PASEO_PASSWORD`；**只让用户自己查看，不在对话中回显** |
| 设备登录的 Tailscale 身份 | 必须是本人账号，或接受了工作站的设备共享 |

## 1. 工作站侧入口

- **WSL**：确认 Windows 计划任务已同步转发：`netsh interface portproxy show all` 中有 `<WS_IP>:<端口>`；没有就运行 `windows\Sync-WorkstationEndpoints.ps1`（见 [paseo-desk-always-on](../paseo-desk-always-on/SKILL.md)）。
- **原生 Linux / macOS**：实例直接监听 Tailscale 地址，或保持 127.0.0.1 用 `tailscale serve` 转发，按 [平台文档](../../docs/platforms.md) 选择一种。**不要**改成监听 `0.0.0.0`。

## 2. Tailscale 授权

参考 [`templates/tailscale-policy.example.hujson`](../../templates/tailscale-policy.example.hujson)：工作站打 `tag:paseo-ws`，只放行本人身份到本人 Paseo 端口和 SSH 端口。新增窄规则前检查并移除旧的全放行规则（`"src": ["*"], "dst": ["*:*"]`），否则窄规则不起作用。修改 tailnet 策略前先给用户看 diff 并征得同意。

## 3. 添加 Host

在 Paseo 客户端（或浏览器 `http://<WS_IP>:<端口>`）：Settings → Add host → Direct connection。

| 字段 | 值 |
| --- | --- |
| Host / Port | `<WS_IP>` / 本人端口 |
| Use SSL | 关闭（传输已由 Tailscale 加密） |
| Password | Paseo 密码（不是 SSH 密码，也不是 Tailscale Auth key） |

iPhone 已在用 Shadowrocket 时，可按 [内置 Tailscale 教程](../../docs/ios-shadowrocket.md) 入网（已在 iPhone 实机验证），注意 Auth key 的身份归属与审批。

## 4. 首个任务与接续验证

1. 手机新建工作区，目录填**工作站上的**绝对路径（如 `/home/<user>/projects/paseo-demo`），先发只读消息：“执行 whoami、pwd，告诉我当前用户和目录，不要改文件。”
2. 确认用户与目录正确后，让 Agent 创建并运行一个小脚本。
3. 手机锁屏；在 Mac 上用同一 Host 打开同一工作区，确认能看到刚才的会话并继续发消息。

成功标准：两台设备看到同一会话、文件落在本人项目目录、任务不因手机锁屏中断。连不上时转 [paseo-desk-doctor](../paseo-desk-doctor/SKILL.md)。

参考：[成员使用教程](../../docs/user-guide.md) · [交付单模板](../../templates/handover.md)
