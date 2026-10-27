---
name: remote-compute
description: 在工作站与计算节点之间提交、查询、同步和可视化远程任务。本机只做代码编辑、Git、SSH、轻量检查和小文件查看；数据、模型、训练、评估、推理都在计算节点执行。提交或查询远程任务、同步代码、拉取日志或指标、查看节点网页服务时使用。
---

# remote-compute

管理员维护的公共模板。复制到本人目录后按项目填写，例如 `~/.claude/skills/remote-compute/SKILL.md`；Codex 按其 Skills 加载方式放置。模板中不写密码、令牌或私钥。

## 连接信息

每个项目在仓库根目录的 `CLAUDE.local.md`（不提交，加入 `.git/info/exclude`）中记录：

```text
host: compute-node-1          # ~/.ssh/config 中的别名
dir: /data/<user>/<project>   # 远程工作目录
env: source ~/venvs/<project>/bin/activate   # 远程环境激活命令
scheduler: slurm | systemd-run | tmux
```

缺少任何一项时先问用户，不要退回本机执行。

## 1. 远程提交

1. `git status` 确认本地已提交；`git push`。
2. `ssh <host> 'cd <dir> && git status --short && git fetch && git checkout <commit>'`；远程有未提交修改时先告诉用户。
3. 按 scheduler 提交，命令中写明资源参数，日志写到 `<dir>/logs/<job-id>.log`，日志首行记录 commit。
4. 返回：任务 ID、commit、日志路径、产物目录。

预计超过几分钟的任务一律后台提交，提交后不要在前台等待。

## 2. 状态查询

输入任务 ID，返回调度状态、日志末尾 20 行和产物目录列表。停止任务（`scancel`、`kill` 等）前必须先征得用户同意；Paseo 中代理停止不代表远程作业已结束。

## 3. 结果同步

- 先在远程聚合或抽样，只拉指标、日志片段、少量样例和图片。
- 拉取前用 `du -sh` 查看大小；超过 50 MB 先告诉用户。
- 存到 `~/results/<project>/<job-id>/`，并记录远程路径与时间。
- 不拉数据集、权重、检查点和大批量结果；rsync 默认不加 `--delete`。

## 4. 可视化连接

节点上的网页服务通过两段 SSH 隧道给本人电脑查看，端口按人或任务错开：

```bash
# 工作站
ssh -N -L 127.0.0.1:<工作站端口>:127.0.0.1:<服务端口> <host>
# 本人电脑
ssh -p 2222 -N -L 127.0.0.1:<本地端口>:127.0.0.1:<工作站端口> <user>@<WS_IP>
```

返回可访问地址 `http://127.0.0.1:<本地端口>` 以及关闭方式。

## 规则

- 远程数据、权重和检查点不删除、不覆盖。
- 只使用本人 SSH 身份；连接失败或需要密码时停下来告诉用户。
- 大改前先提交或打快照；已推送的历史用 `git revert` 回退。
