# 故障排查

## 成员侧

| 现象 | 先检查 | 处理 |
| --- | --- | --- |
| SSH 连不上 | Tailscale 是否连接、是否获授权、端口 2222 | 先查网络与 ACL；新增成员核对 sshd `AllowUsers` |
| SSH 密码被拒绝 | 用户名、认证方式 | 向管理员确认本人凭据，不要尝试别人的账号 |
| Paseo 连接超时 | 本人端口与 Tailscale 授权 | SSH 正常不代表 Paseo 端口已放行；请管理员核对 ACL 与转发 |
| Paseo 连接被拒绝 | 实例是否运行 | 本人终端 `paseo daemon status`；联系管理员 `systemctl status paseo@<user>` |
| Password 错误 | 是否误填 SSH 密码 | 使用 `~/.paseo/client.env` 中的 Paseo 密码；遗失请管理员 `paseo-user reset-password` |
| Claude / Codex 无法启动 | 启动前检查的报错 | 本人终端运行 `paseo provider diagnostic claude`（或 `codex`），把 stderr 中的检查信息发给管理员 |
| 模型登录过期 | 本人登录状态 | 本人终端重新 `claude auth login` / `codex login`，再新建会话验证 |
| 任务停在权限请求 | Paseo 中待处理的操作 | 核对目录和具体动作后处理，不要为排错开放全部权限 |
| 手机打不开 localhost 链接 | 链接属于哪台机器 | 用管理员提供的地址；电脑按使用教程第 6 节建立隧道 |
| 关闭窗口后计算任务结束 | 任务是否依赖前台 SSH | 改用调度器或托管方式重新提交，保存任务 ID |

## 管理员诊断顺序

1. **服务与端口**（WSL / Linux）：
   ```bash
   sudo paseo-user list
   systemctl is-active paseo@alice
   ss -ltnp | grep -w 6767
   sudo journalctl -u paseo@alice -n 80 --no-pager
   ```
2. **程序、登录与代理**（以成员身份）：
   ```bash
   sudo -iu alice
   paseo daemon status
   paseo provider diagnostic claude
   paseo provider diagnostic codex
   ```
   Resolved path 应指向 `/usr/local/lib/paseo-workstation/bin/*`。模型列表首次加载可能较慢。
3. **Windows 转发**（管理员 PowerShell）：
   ```powershell
   netsh interface portproxy show all
   Get-NetFirewallRule -Name 'PaseoWorkstation-*' | Format-Table Name, Enabled
   Get-Content C:\PaseoWorkstation\logs\workstation.log -Tail 30
   C:\PaseoWorkstation\Sync-WorkstationEndpoints.ps1
   ```
   在 Windows 上 `curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:6767/` 应返回 200，确认 WSL localhost 转发正常。
4. **客户端**：Tailscale 连接、ACL / 设备共享权限、端口、密码。
5. **登录失效**：在对应 Linux 用户下重新登录工具，不要为恢复登录而共享整个 HOME。

## 常见坑

- **WSL 实例被回收**：没有常驻任务时，WSL 在无人使用一段时间后会关闭，systemd 服务随之停止。确认 `PaseoWorkstation` 计划任务在运行。
- **Tailscale 地址变化**：同步任务会自动重建转发；客户端里的 Host 需要成员自行更新。
- **两个管理器抢同一个实例**：手动执行过 `paseo daemon start` 时，先 `paseo daemon stop`，再交给 systemd。
- **`paseo-user add` 报找不到 auth.js**：Paseo 升级后内部路径变化。临时办法：成员在本人终端 `paseo daemon set-password`，然后把新密码写进 `~/.paseo/client.env`（`export PASEO_PASSWORD='...'`，权限 600），管理员重启其服务。
- **代理环境不一致**：服务不读取交互 shell 的配置。代理变量统一放在 `/etc/paseo-workstation/proxy.env`，修改后重启 `paseo@*`。
- **改了 config.json 里的监听地址不生效**：服务环境变量 `PASEO_LISTEN` 优先，改端口用 `paseo-user add`。
