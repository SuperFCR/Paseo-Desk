---
name: paseo-desk-always-on
description: 让 Paseo Desk 工作站 24 小时在线：开机自启、断开客户端不影响任务、WSL 不被回收、电源与休眠设置，并做冷启动验收。用户说“让工作站一直开着”“关掉终端/锁屏后任务别停”“WSL 老是自己退出”“开机自动启动 Paseo”“24 小时在线”时使用。
---

# paseo-desk-always-on：24 小时在线

工作站不在线，手机就连不上，节点上的结果也拉不回来。这个 skill 把“常驻”拆成三层逐层确认：**机器不睡、宿主不回收、服务自启**。

## 先确认

- 宿主平台：Windows + WSL2 / 原生 Linux / macOS。
- 已完成 [paseo-desk-setup](../paseo-desk-setup/SKILL.md)，`paseo@<user>`（macOS 为 `sh.paseo.workstation.<user>`）已存在。
- 改电源、计划任务、重启机器都会影响正在跑的东西，执行前说明并征得同意。

## 1. 机器不睡

| 平台 | 做法 |
| --- | --- |
| Windows | 电源计划把“睡眠”设为“从不”；`powercfg /a` 查看支持的睡眠状态，`powercfg /requests` 查看阻止睡眠的请求 |
| Linux | `systemctl status sleep.target suspend.target`；桌面环境里关闭自动挂起；需要时 `sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target`（先征得同意） |
| macOS | `pmset -g` 查看；接电源时 `sudo pmset -c sleep 0`，按 [平台文档](../../docs/platforms.md) 第三节处理 FileVault 与登录前可用性 |

## 2. 宿主不回收（仅 WSL）

systemd 服务本身**不能**让 WSL 实例常驻。由 Windows 计划任务启动 [`paseo-workstation-keepalive`](../../linux/sbin/paseo-workstation-keepalive) 保持实例：

```powershell
# 管理员 PowerShell，目录为复制出的 windows\
Copy-Item config.example.json config.json    # 填 Distro，KeepAlive 设为 true
Set-ExecutionPolicy -Scope Process Bypass
.\Sync-WorkstationEndpoints.ps1
.\Install-PaseoWorkstationTask.ps1
```

任务以当前 Windows 用户“不管是否登录”运行；冷启动后 WSL 没拉起时，把任务改为“使用密码运行”再测。

## 3. 服务自启

```bash
# Linux / WSL
systemctl is-enabled "paseo@$USER" && systemctl is-active "paseo@$USER"
# macOS
sudo launchctl print "system/sh.paseo.workstation.$USER" | grep -E 'state|pid'
```

不要再用 `paseo daemon start` 另起后台实例，否则会和 systemd / launchd 抢同一个端口。

## 4. 任务不依赖前台

- Paseo 会话属于工作站上的实例：手机锁屏、Mac 合盖不会停止 Agent。
- 节点上的长任务一律交给调度器或托管方式提交（见 [remote-compute](../remote-compute/SKILL.md)），不要挂在前台 SSH 上。

## 验收（逐条记录结果）

1. 手机断开 Tailscale 5 分钟再连回，原会话仍在、任务继续。
2. 关闭所有终端窗口后，从手机仍能连接。
3. 重启工作站，**不登录桌面**，从手机连接本人实例。
4. WSL：`wsl -l -v` 显示发行版 Running；`netsh interface portproxy show all` 有本人端口。

完整清单见 [验收清单](../../docs/acceptance-checklist.md) 的“整机常驻”一节；失败时转 [paseo-desk-doctor](../paseo-desk-doctor/SKILL.md)。
