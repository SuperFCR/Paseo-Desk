---
name: pocketrig-team
description: 把单人 PocketRig 扩展给家人或小团队：为每人创建独立系统用户与 Paseo 实例、分配端口、重设密码、停用成员、生成交付单、配置按人授权。用户说“给 alice 开一个 Paseo”“新增成员”“重设某人的 Paseo 密码”“停用成员”“多人共用工作站”时使用。单人起步用 pocketrig-setup。
---

# pocketrig-team：扩展给小团队

适用于**相互信任**的小团队：隔离依靠系统 UID 与文件权限，root/sudo 管理员、宿主管理员与共享网络都在共同信任边界内，不是面向恶意租户的隔离。开始前把这条边界告诉用户。

## 新增成员

1. 选端口并确认空闲：`sudo paseo-user list`，`ss -ltn | grep -w <port> || echo 空闲`。
2. 创建：`sudo paseo-user add <user> <port>`（可重复执行；已有密码保留，配置合并更新）。
3. SSH 凭据：`sudo passwd <user>` 或写入其 `~/.ssh/authorized_keys`。不要复制管理员私钥。
4. 成员**本人**登录模型账号：`claude auth login`、`codex login`。不复制他人 `~/.claude`、`~/.codex`。
5. Tailscale：按 [`templates/tailscale-policy.example.hujson`](../../templates/tailscale-policy.example.hujson) 只放行该成员到其端口与 SSH 端口；WSL 部署的转发由 Windows 计划任务在下一轮自动加入。
6. 用 [交付单模板](../../templates/handover.md) 私下交付连接参数；密码不写进共享文档或群聊。

## 日常操作

| 操作 | 命令 |
| --- | --- |
| 列出实例 | `sudo paseo-user list`（`--json` 供脚本使用） |
| 重设连接密码 | `sudo paseo-user reset-password <user>`，通知本人更新所有客户端 |
| 改端口 | `sudo paseo-user add <user> <新端口>` |
| 停用实例 | `sudo paseo-user remove <user>` |
| 同时移出 CLI 组与 SSH 白名单 | `sudo paseo-user remove <user> --revoke-cli --revoke-ssh` |

停用不删除用户、HOME、项目或凭据；删除数据前必须先确认备份并取得明确同意。

## 验收

每位成员按 [验收清单](../../docs/acceptance-checklist.md) “每位成员”一节验证，重点是**跨用户拒绝**：A 的密码连不上 B 的端口、A 读不到 B 的 HOME。

参考：[管理员部署指南](../../docs/admin-guide.md) 第 2、6、7 节 · [设计方案](../../docs/design.md)
