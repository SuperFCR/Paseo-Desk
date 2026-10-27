# 验收清单

管理员在把连接参数交给成员前逐项完成，并记录日期与结果。

以下 SSH 示例为 WSL 的 `2222`；原生 Linux / macOS 使用实际 SSH 端口（通常 `22`）。HOME 示例在 Linux / WSL 是 `/home/<user>`，在 macOS 是 `/Users/<user>`。Mac 的服务命令见后面的补充表。

## 每位成员

| 验收项 | 方法 | 结果 |
| --- | --- | --- |
| SSH 可登录，主机指纹与交付单一致 | 成员电脑 `ssh -p 2222 <user>@<WS_IP>` | |
| UID 与 HOME 正确 | `whoami`、`echo $HOME` | |
| 实例由本人 UID 运行 | `ps -o user= -p $(systemctl show -p MainPID --value paseo@<user>)` | |
| 无密码被拒绝 | 不填密码建立会话，应被认证拒绝；静态网页返回 200 不代表已认证 | |
| 错误密码、他人密码被拒绝 | 用另一成员的密码连接本实例 | |
| 正确密码可进入 | 客户端 Direct connection 连接成功 | |
| Claude 真实调用 | 见下方命令，回复包含 `CLAUDE_OK` | |
| Codex 真实调用 | 见下方命令，回复包含 `CODEX_OK` | |
| 会话写入本人目录 | 工作目录为 `/home/<user>/projects/...`，`~/.claude`、`~/.codex` 下出现新会话 | |
| 无法读取另一成员的私有目录 | 以 alice 身份读取 bob 的 Paseo 配置，应被文件权限拒绝 | |
| 成员之间端口授权隔离 | 从 alice 的客户端连接 bob 的端口，应被 tailnet 策略拒绝 | |
| 启动前检查仍被执行 | 临时放一个返回 1 的钩子到 `pre-launch.d`，确认 CLI 被拒绝后移除 | |
| 断开客户端后任务继续 | 发起任务、关闭客户端、重连查看 | |
| 计算节点 SSH 身份 | `ssh compute-node-1 'hostname; whoami'` | |
| 远程任务完整流程 | 提交 → 断开 → 重连 → 查询 → 拉回结果 | |
| 停止代理后单独核对远程作业 | 按任务 ID 查询节点状态 | |

模型调用验收（以成员身份在其终端执行）：

```bash
cd ~/projects
paseo run --provider claude --cwd "$PWD" --wait-timeout 60s '只回复 CLAUDE_OK，不运行工具，不修改文件'
paseo run --provider codex  --cwd "$PWD" --wait-timeout 60s '只回复 CODEX_OK，不运行工具，不修改文件'
paseo logs <agent-id> --tail 5
```

CLI 显示 completed 后用 `paseo logs` 核对实际回复。

## macOS 服务补充

| 验收项 | 方法 | 结果 |
| --- | --- | --- |
| plist 合法且属于 root | `plutil -lint /Library/LaunchDaemons/sh.paseo.workstation.alice.plist`，权限 root:wheel 644 | |
| 服务由成员身份运行 | `sudo launchctl print system/sh.paseo.workstation.alice` 取得 PID，再 `ps -o user= -p <PID>` | |
| 包装脚本路径正确 | 本人执行 `paseo provider diagnostic claude` / `codex`，命令指向公共入口 | |
| 后台认证可用 | 通过 Paseo 执行上面的两个模型调用；不能只验证 SSH 终端里的登录 | |
| 日志与配置私有 | `~/.paseo` 为 700，`client.env`、`config.json` 为 600；macOS 的 `/var/log/paseo-workstation` 为 root 所有、700 | |

## 整机常驻（WSL 部署）

原生 Linux 和 macOS 的整机常驻验收项见[按宿主平台部署](platforms.md)中对应章节的“验收”部分。

| 场景 | 期望 | 结果 |
| --- | --- | --- |
| Windows 冷启动、无人登录 | 计划任务拉起 WSL，SSH 与全部 Paseo 端口可达 | |
| 关闭所有终端窗口 | 服务不受影响 | |
| 休眠后恢复 | 转发与服务恢复，客户端可重连 | |
| `wsl --shutdown` 后 | 一个同步周期内自动恢复 | |
| Tailscale 地址变化（如重新登录） | 转发迁移到新地址，旧地址规则被清理 | |
| 停用成员 | 下一轮同步后其端口转发与防火墙规则被删除 | |

## 交付记录

| 项目 | alice | bob |
| --- | --- | --- |
| Paseo / Node / Claude Code / Codex 版本 | | |
| SSH 端口与主机指纹 | | |
| Paseo 端口 | 6767 | 6768 |
| 计算节点与远程目录 | | |
| 交付日期 | | |
