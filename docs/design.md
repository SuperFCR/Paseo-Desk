# 设计方案

本机负责开发与查看，远程节点负责计算与完整产物；每个用户拥有自己的运行身份，公共程序与网络作为共享资源。

## 1. 用户隔离与共享边界

| 对象 | 安排 | 边界 |
| --- | --- | --- |
| 程序安装与版本 | 共用公共安装 | 管理员维护，普通用户只读执行 |
| Paseo / Claude Code / Codex 进程 | 每人独立 | 真实 `User=<user>`，不以 root 共跑 |
| 项目 / 会话 / 配置 / SSH | 每人独立 | 私有 HOME，不共用可写配置目录 |
| 模型账号登录 | 每人独立 | 各自登录，凭据不共写、不复制 |
| 网络 / 代理 / CPU / 内存 | 宿主共享 | 按需增加每用户资源上限 |
| 存储容量 | 按权限分配 | 私人区 + 显式共享项目区 + 结果缓存 |

每人独立保存的目录：

```text
/home/<user>/projects/   本人项目
/home/<user>/results/    从计算节点拉回的小型结果
/home/<user>/.paseo/     Paseo 状态、配置（含密码哈希）、client.env
/home/<user>/.claude/    Claude Code 配置与登录
/home/<user>/.codex/     Codex 配置与登录
/home/<user>/.ssh/       本人 SSH 密钥与计算节点配置
```

HOME 与状态目录 700、私钥和凭据文件 600，Paseo 服务以 `UMask=0077` 运行。`PASEO_HOME`、`CLAUDE_CONFIG_DIR`、`CODEX_HOME` 若设置，都必须解析到本人目录；改变这些变量只改变状态位置，不能替代真实 Linux 用户身份。

边界说明：

- 保护的是普通用户之间的本地文件与会话。root、sudo 管理员、Windows 宿主管理员属于可信管理方。
- WSL 中可访问的 Windows 挂载盘（`/mnt/c` 等）不受 `chmod 700` 约束，私人数据放在 Linux 原生文件系统。
- git worktree 用于分开修改，不提供凭据或进程隔离。
- 本机用户之间仍可能连到彼此的端口（都在 127.0.0.1），因此每个实例必须使用独立密码，不能只靠端口区分。

### 模型账号

推荐每位成员使用自己的个人订阅、团队/企业席位或 API Key，在本人 Linux 用户下登录。这样个人用量、额度与审计天然分开，也不会出现多个进程同时刷新同一份 OAuth 凭据的问题。本项目不提供复制他人登录凭据的功能。

## 2. 网络入口

**Windows + WSL2（Tailscale 装在 Windows）**

WSL 不能直接绑定 Windows 的 Tailscale 地址。各实例在 WSL 内监听 `127.0.0.1:<端口>`，Windows 用 `netsh portproxy` 把 `<Tailscale IP>:<端口>` 转到 Windows 的 `127.0.0.1:<端口>`，再经 WSL localhost forwarding 进入 Linux。防火墙只放行本机 Tailscale 地址上的这些端口，来源限定 `100.64.0.0/10`。SSH 同理：`<Tailscale IP>:2222 → 127.0.0.1:2223`。

`windows/Start-PaseoWorkstation.ps1` 每 30 秒执行一轮：保持 WSL 存活、读取 WSL 中 `paseo-user list --json`、增删转发与防火墙规则。Tailscale 地址变化、新增或停用用户都会自动跟进。

**原生 Linux（Tailscale 装在本机）**

把 `PW_LISTEN_HOST` 设为本机 Tailscale 地址，实例直接监听该地址；或保持 127.0.0.1，用 `tailscale serve` 的 TCP 转发暴露端口。

**授权**

Tailscale ACL / grants 按成员身份放行到其专属端口和 SSH 端口。加入同一个 tailnet 不代表能访问所有端口；新增窄规则前先检查是否存在旧的全放行规则。Paseo 连接走 Tailscale 加密，客户端 Use SSL 关闭。

## 3. 程序接入

Paseo 的 provider command 显式指向公共包装脚本 `/usr/local/lib/paseo-workstation/bin/claude` 与 `codex`。后台服务不读取交互式 shell 的 alias，所以免确认参数等个人偏好在 Paseo 中按任务设置。包装脚本：

1. 检查调用者属于 `ai-cli-users` 组；
2. 依次运行 `/etc/paseo-workstation/pre-launch.d/` 中的检查（输出写 stderr，保持协议输出干净），任一失败即拒绝启动；
3. 原样传参 `exec` 真实程序。

代理变量统一放在 `/etc/paseo-workstation/proxy.env`，包装脚本与服务都会加载。核对模型子进程、用量插件和元数据请求都按预期路由，同时 Tailscale、计算节点内网和 DNS 保持可达。程序启动检查不等于系统级网络隔离；需要系统级“防直连”时使用[可选出口网关模块](egress-proxy.md)。

## 4. 从需求到结果的固定流程

1. **进入本人工作区**：客户端连接本人 Paseo 实例，代理在本人 `~/projects` 下工作。
2. **编辑与确定代码版本**：本地完成编辑和轻量检查；提交或明确本次代码版本，再同步到计算节点。协作通过 Git 分支与合并交换代码。
3. **远程提交计算任务**：Skill 或脚本显式指定 SSH 主机、远程用户、工作目录、资源参数和任务 ID。使用节点调度器、服务管理或可恢复会话，使任务不依赖前端连接。
4. **拉回必要结果**：完整数据和模型留在节点；本地只缓存日志摘要、图像、指标和小型结果。可用 SCP；大批量增量传输可选 rsync。
5. **查看与继续**：结果写入 `~/results/<project>/<job-id>/`；网页展示使用经授权的端口转发，为每人或任务分配独立端口。

### Skills 的统一约定

公共模板由管理员维护，每个用户复制到自己的配置目录。模板固定四件事：远程提交、状态查询、结果同步、可视化连接；每项输入带项目 / 节点 / job-id，输出带代码版本、日志位置或可访问地址。模板中不保存密码或私钥。参考 [skills/remote-compute](../skills/remote-compute/SKILL.md)。

用户级 Skills 和插件不会因为共用程序而自动一致。确需统一时，把审核过的内容放到 root 管理的公共目录，再分别链接到各用户的工具目录；不要链接整个 `.claude` 或 `.codex`。

## 5. 用量统计

两组指标分别记录：

- **个人用量**：各实例读取本人日志，按用户 / 项目 / 模型 / 日期统计普通输入、输出、缓存写入、缓存读取和 API 等价费用，可用 [ccusage](https://ccusage.com) 或 Paseo 用量插件。只汇总允许上报的计数与金额。
- **账号额度**：订阅账号的 5 小时或周额度以服务商显示为准；剩余百分比不能稳定换算为固定美元额度。

API 等价费用 = Σ按模型（普通输入 × 单价 + 输出 × 单价 + 缓存写入 × 对应单价 + 缓存读取 × 单价）/ 1,000,000。区分缓存时长，记录价格表版本。金额是已用请求的估值，不是订阅实际扣款。

## 6. 分阶段上线

每一步保留验收结果（见[验收清单](acceptance-checklist.md)）。

1. **确认既有环境**：公共安装位置、包装脚本、用户权限、各自 HOME 与模型登录。
2. **接入两个 Paseo 实例**：分别以两位成员身份启动；验证调用成功且会话写入本人目录；从外部客户端验证专属端口、独立密码与跨用户拒绝访问；验证启动前检查仍被执行。
3. **跑通一个完整远程任务**：Git 版本同步、提交、断开客户端、重新连接、查询及结果拉回。再测试登录刷新、撤销授权与每人用量归属。

常驻另测：冷启动、无人登录、关闭终端、休眠恢复及 WSL 重启。systemd 服务本身不会保持 WSL 实例存活。CPU / 内存 / 进程与磁盘上限按实测设置；共享容量不代表每人独占。

首期采用每用户独立实例。需要事件触发、团队自动化和共享运行记录时，再评估 Paseo Hub；Hub 不替代 Linux、容器或虚拟机的隔离。

## 参考

- Paseo：[配置](https://paseo.sh/docs/configuration) · [连接方式](https://paseo.sh/docs/connectivity) · [安全模型](https://paseo.sh/docs/security) · [CLI](https://paseo.sh/docs/cli) · [自定义 provider](https://paseo.sh/docs/custom-providers)
- Tailscale：[grants 语法](https://tailscale.com/docs/reference/syntax/grants) · [Windows 与 WSL2](https://tailscale.com/docs/install/windows/wsl2)
- WSL：[systemd 与实例存活](https://learn.microsoft.com/windows/wsl/systemd) · [文件权限](https://learn.microsoft.com/windows/wsl/file-permissions)
- [ccusage 费用计算](https://ccusage.com/guide/cost-modes)
