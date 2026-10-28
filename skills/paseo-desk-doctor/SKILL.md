---
name: paseo-desk-doctor
description: 诊断与验收 Paseo Desk：按“服务 → 程序与登录 → 宿主转发 → 网络授权 → 客户端”的顺序只读排查连不上、Claude/Codex 启动失败、密码错误、WSL 被回收、任务中断等问题，并按验收清单逐项确认。用户说“手机连不上 Paseo”“Paseo 连接超时/被拒绝”“Claude 在 Paseo 里起不来”“帮我验收部署”“检查工作站状态”时使用。
---

# paseo-desk-doctor：诊断与验收

原则：**先只读，后修改**。每一步给出命令输出的结论，定位到具体层后再提出修复，修复前征得同意。不为排错开放全部权限、不把监听地址改成 `0.0.0.0`、不共享整个 HOME。

## 诊断顺序

以 `<user>` / `<port>` 代替实际用户与端口。

1. **服务与端口**（Linux / WSL）
   ```bash
   sudo paseo-user list
   systemctl is-active "paseo@<user>"
   ss -ltnp | grep -w <port>
   sudo journalctl -u "paseo@<user>" -n 80 --no-pager
   ```
   macOS：`sudo launchctl print system/sh.paseo.workstation.<user>`、`sudo lsof -nP -iTCP:<port> -sTCP:LISTEN`、`sudo tail -n 80 /var/log/paseo-workstation/<user>.log`。
2. **程序、登录与启动前检查**（以该用户身份）
   ```bash
   sudo -iu <user>
   paseo daemon status
   paseo provider diagnostic claude
   paseo provider diagnostic codex
   ```
   Resolved path 应为 `/usr/local/lib/paseo-workstation/bin/*`；登录过期让用户本人重新 `claude auth login` / `codex login`。
3. **宿主转发**（仅 WSL，管理员 PowerShell）
   ```powershell
   netsh interface portproxy show all
   Get-NetFirewallRule -Name 'PaseoWorkstation-*' | Format-Table Name, Enabled
   Get-Content C:\PaseoWorkstation\logs\workstation.log -Tail 30
   curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:<port>/
   ```
   最后一条应返回 200。
4. **网络授权**：设备的 Tailscale 是否已连接、身份是否正确、ACL / grants 是否放行该端口、是否残留全放行规则。
5. **客户端**：Host、端口、Use SSL 关闭、密码是否误填 SSH 密码或 Auth key。

## 常见结论速查

| 现象 | 多半是 |
| --- | --- |
| SSH 通、Paseo 超时 | Paseo 端口未授权或未转发 |
| 连接被拒绝 | 实例没运行，或被手动 `paseo daemon start` 的实例抢占 |
| 冷启动后全不通（WSL） | 常驻计划任务没跑，WSL 被回收 |
| 改了 config.json 端口不生效 | 服务环境 `PASEO_LISTEN` 优先，改端口用 `paseo-user add` |
| 关窗口后节点任务结束 | 任务挂在前台 SSH，改用调度器重提 |

完整表格见 [故障排查](../../docs/troubleshooting.md)。

## 验收

按 [验收清单](../../docs/acceptance-checklist.md) 逐项执行，每项记录“命令 / 结果 / 时间”。没有实机执行过的项目明确标注“未验证”，不要写成通过。
