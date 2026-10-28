# 成员使用教程

你通过 Tailscale 连接工作站，由自己的系统用户运行自己的 Paseo、Claude Code 和 Codex。手机与电脑可以进入同一个用户环境，继续开发、查看运行状态、收取结果。重计算在远程计算节点执行，工作站只用于代码编辑、版本管理和轻量结果查看。

```text
手机或电脑 → Tailscale → 本人 Paseo 实例 → Claude Code / Codex → SSH 计算节点
```

连接与首个任务也可以交给 [paseo-desk-connect](../skills/paseo-desk-connect/SKILL.md)，远程计算与把结果拉回手机查看交给 [remote-compute](../skills/remote-compute/SKILL.md)。

全程只登录自己获授权的环境。下文以 `alice` 为例，`<WS_IP>` 表示工作站的 Tailscale 地址。

目录示例使用 Linux / WSL 的 `/home/alice`；macOS 对应 `/Users/alice`。SSH 命令示例中的 `2222` 在原生 Linux / macOS 上通常改为 `22`，一律以交付单为准。

## 1. 确认连接信息

先从管理员处（私下）取得交付单，包含：

| 项目 | 示例 |
| --- | --- |
| 工作站 Host | `<WS_IP>`（100.x.y.z） |
| SSH 端口 / 用户名 | `2222` / `alice`（端口以交付单为准，原生 Linux / macOS 工作站通常是 22） |
| SSH 主机指纹 | 首次连接时核对 |
| Paseo 端口 | `6767` |
| Paseo 密码 | 管理员私下交付，或从本人 `~/.paseo/client.env` 读取 |
| 工作根目录 | Linux / WSL：`/home/alice/projects`；macOS：`/Users/alice/projects` |
| 计算节点 | 地址、远程用户名、授权目录 |

SSH 密码与 Paseo 密码是两种不同的凭据。共享文档里不会出现任何明文密码。

## 2. 连接 Tailscale 和 SSH

1. 在手机和电脑安装 Tailscale，用管理员批准的本人身份登录（或接受管理员发来的设备共享邀请）。
2. 确认 Tailscale 处于已连接状态，再打开 Paseo 或 SSH。加入 tailnet 不代表能访问所有端口，只能访问为你授权的端口。

**iPhone 已在使用 Shadowrocket？**可参考[内置 Tailscale 接入教程](ios-shadowrocket.md)，用正确成员身份的 Auth key 注册新设备，再连接本人 Paseo 实例。该方案已在 iPhone 实机验证，界面以所用版本为准；Auth key 与 Paseo 密码用途不同，不要互填。

首次接入建议先在电脑上检查 SSH：

```bash
ssh -p 2222 alice@<WS_IP>
```

首次连接出现主机指纹时，与交付单核对。登录后执行只读检查：

```bash
whoami
printf 'HOME=%s\n' "$HOME"
command -v paseo claude codex
```

应看到 `alice`，HOME 为 `/home/alice`（Linux / WSL）或 `/Users/alice`（macOS）。用户或 HOME 不符时立即退出，避免在错误环境中工作。

### 取得 Paseo 密码

```bash
cat ~/.paseo/client.env
```

`PASEO_PASSWORD=` 后面的值就是连接密码；被引号包住时只复制引号内的内容。不要转发整个文件或含密码的截图。该文件只有本人和管理员可读；`paseo` 命令会自动加载它，所以在本人终端里运行 `paseo ls` 等命令不需要再输入密码。

### 登录模型账号

首次使用前，在本人终端登录自己的账号（管理员会告知使用个人订阅、团队席位还是 API Key）：

```bash
claude auth login
codex login
```

## 3. 配置 Paseo 客户端并完成首个任务

### 添加 Host

1. 安装官方 Paseo 客户端（或用浏览器打开 `http://<WS_IP>:6767`），保持 Tailscale 已连接。
2. Settings → Add host → Direct connection，填写：

| 字段 | 内容 |
| --- | --- |
| 名称 | `alice workstation` |
| Host | `<WS_IP>` |
| Port | `6767` |
| Use SSL | 关闭（传输已由 Tailscale 加密） |
| Password | 本人 Paseo 密码（不是 SSH 密码） |

若管理员授权你访问另一个环境，单独添加 Host 并写清名称，避免在会话间误切换。

### 第一个项目

```bash
mkdir -p ~/projects/paseo-demo ~/results/paseo-demo
```

在 Paseo 新建工作区：确认选中本人的 Host，选择 Claude Code 或 Codex 及可用模型，工作目录填**工作站上的**绝对路径 `/home/alice/projects/paseo-demo`（macOS 是 `/Users/alice/projects/paseo-demo`）。

第一条消息：

```text
请只读取当前环境，执行 whoami、pwd，并显示 HOME。告诉我当前用户和工作目录，暂时不要修改文件。
```

确认输出属于本人后：

```text
请在当前目录创建 hello.py，打印 Hello from Paseo，运行它，并告诉我退出状态和输出。
```

代理请求写文件或执行命令时，在 Paseo 中核对项目与操作后再批准。成功标准：用户正确、目录正确、文件出现在本人项目中、返回运行输出。

## 4. 日常使用

- 后续需求继续发在原会话中；换项目时新建工作区，并再次确认 Host 和目录。
- 多个客户端可以查看同一任务，但同一会话尽量只保留一个主要操作入口。
- 手机退到后台或断开连接不代表任务停止，重新连接后进入原工作区查看状态。真正停止前，区分“停止代理”与“停止远程计算作业”。
- 语音输入：工作站默认关闭本地语音模型。优先使用手机输入法的语音转文字；确需 Paseo 听写时联系管理员开启（中文需选择支持中文的模型）。

在本人终端查看代理：

```bash
paseo ls
TASK_AGENT_ID='复制实际代理ID'
paseo logs "$TASK_AGENT_ID" --tail 20
paseo attach "$TASK_AGENT_ID"    # Ctrl+C 退出查看，不会停止代理
```

### 用量与 API 等价费用

```bash
paseo usage
npx -y ccusage@latest claude daily --mode calculate --breakdown --timezone Asia/Shanghai
npx -y ccusage@latest codex daily --mode calculate --breakdown --timezone Asia/Shanghai
```

费用是按模型与缓存类别折算的已用请求估值，不是订阅实际扣款；本地统计只覆盖本机可读的日志。

## 5. 在计算节点执行任务

### 配置本人 SSH 身份

在本人 `~/.ssh/config` 中为节点设置别名（参考 [`templates/ssh_config.example`](../templates/ssh_config.example)）：

```text
Host compute-node-1
    HostName <节点地址>
    User <本人远程用户名>
    IdentityFile ~/.ssh/id_ed25519_compute
```

先在本人终端做只读连通验证，再让 Paseo 会话通过同一别名做一次查询，确认代理实际使用的 SSH 身份正确：

```bash
ssh compute-node-1 'hostname; whoami; pwd'
```

每个人使用自己的远程身份或管理员明确授权的项目身份；工作站上的目录隔离不会自动保护共用远程账号下的文件。

### 代码同步和提交

1. 在本地仓库检查修改，提交本次要运行的版本。
2. 推送到团队 Git 仓库，在远程目录拉取并核对提交号。远程有未提交修改时先处理，不要强制覆盖。
3. 指定节点、远程目录、运行命令、资源需求、日志位置和产物目录，再提交。
4. 使用调度器或管理员选定的托管方式（Slurm、systemd、tmux 等），取得任务 ID，保证手机离线后任务继续运行。

可以把下面的说明填好后发给代理：

```text
项目：<项目名>
节点：compute-node-1
远程目录：<本人获授权的目录>
代码版本：<分支或提交号>
任务命令：<已确认的运行命令>
资源限制：<队列 / GPU / CPU / 内存 / 时长>
结果要求：记录任务 ID、日志路径和产物目录。先确认身份、资源和代码版本，再提交并返回上述信息。
```

### 查询和停止

在原会话中提供任务 ID，要求查询调度状态、最近日志和结果文件。需要停止时明确指出节点和远程任务 ID，再查询终止结果。Paseo 中代理已停止，并不能证明远程作业已经结束。

## 6. 拉回结果和可视化

完整数据集、检查点和大型产物留在计算节点。本地按任务保存小型结果：

```text
/home/alice/results/<project>/<job-id>/
    summary.txt
    metrics.json
    preview.png
```

```bash
scp compute-node-1:/实际远程路径/metrics.json "$HOME/results/paseo-demo/"
```

批量结果用经过确认的 rsync 规则增量同步，默认不加 `--delete`。图片可以在 Paseo 中直接查看或交给代理解释。

### 在电脑查看节点上的网页服务

以节点上监听 `127.0.0.1:6006` 的服务为例（先确认 16006、26006 端口未被占用，多人同时使用时各自换端口）：

1. 工作站本人终端，建立第一段隧道并保持运行：
   ```bash
   ssh -N -L 127.0.0.1:16006:127.0.0.1:6006 compute-node-1
   ```
2. 自己电脑的终端，建立第二段隧道：
   ```bash
   ssh -p 2222 -N -L 127.0.0.1:26006:127.0.0.1:16006 alice@<WS_IP>
   ```
3. 自己电脑的浏览器打开 `http://127.0.0.1:26006`。结束后在两个终端分别按 Ctrl+C。

对端机器上的 `127.0.0.1` 链接不能直接在手机上打开；手机优先在 Paseo 中查看图片与文件。

## 7. 遇到问题

先看 [故障排查](troubleshooting.md)。向管理员反馈时提供：用户名、时间、Host、端口、工作目录、代理 ID 或远程任务 ID、错误截图，以及本人日志中的相关片段（`tail -n 80 ~/.paseo/daemon.log`）。提交前删除密码、令牌等凭据。
