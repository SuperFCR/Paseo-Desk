# PocketRig

[English](README.md) | **简体中文**

**口袋里的工作站**。用手机驱动家里那台常开的电脑写代码：工作站 24 小时在线，GPU 节点上的实验结果在手机上直接看。

把一台常开的电脑（Windows + WSL2、原生 Linux 或 macOS）变成自己的 AI 编程工位：手机和 Mac 经 [Tailscale](https://tailscale.com) 连到工作站上**自己的** [Paseo](https://paseo.sh) 实例，驱动 Claude Code / Codex 写代码；训练、推理等重计算通过 SSH 提交到 GPU / 计算节点，跑完把小结果拉回工作站，手机打开就能看。先从一个人用起，需要时再扩展给家人或小团队。

## 4 分钟看懂

[![PocketRig 亮点](docs/promo/pocketrig-highlights.gif)](docs/promo/pocketrig-promo.mp4)

[▶ 观看完整宣传片](docs/promo/pocketrig-promo.mp4) · [分镜与源码](docs/promo/README.md) · [30 秒短片](https://paseo-desk-demo.chic-alder-0364.chatgpt.site)

## 两个亮点

| 工作站 24 小时在线 | 实验结果手机上看 |
| --- | --- |
| 每个实例由 systemd / launchd 托管、开机自启；Windows 计划任务让 WSL 常驻。手机锁屏、Mac 合盖、关掉终端，会话和 Agent 都还在工作站上跑。 | 重计算留在 GPU 节点，跑完只把指标、曲线、日志摘要这类几 MB 的小结果拉回工作站。手机打开同一个 Paseo 会话就能看，并直接发下一条指令。 |

## 交给 Agent 来部署：Skills

仓库的每个部分都整理成了 [Agent Skill](skills/README.md)。装好后直接对 Claude Code / Codex 说“帮我把这台电脑装成 PocketRig 工作站”“手机连不上 Paseo，帮我查一下”，它会按步骤执行，遇到 sudo、改网络、重启时先停下来确认。

```text
/plugin install pocketrig --marketplace SuperFCR/PocketRig
```

较早版本的 Claude Code 分两步：`/plugin marketplace add SuperFCR/PocketRig`，再 `/plugin install pocketrig@pocketrig`。Codex 或其他工具：`./skills/install.sh --codex`（或 `--target <目录>`）。

| Skill | 做什么 |
| --- | --- |
| [pocketrig-setup](skills/pocketrig-setup/SKILL.md) | 单人起步：安装公共部分，给自己建 Paseo 实例 |
| [pocketrig-always-on](skills/pocketrig-always-on/SKILL.md) | 24 小时在线：不睡眠、WSL 不回收、开机自启、冷启动验收 |
| [pocketrig-connect](skills/pocketrig-connect/SKILL.md) | 手机与 Mac 经 Tailscale 连进来，验证会话接续 |
| [remote-compute](skills/remote-compute/SKILL.md) | 提交节点任务、查询、拉回小结果，整理成手机能看的摘要 |
| [pocketrig-doctor](skills/pocketrig-doctor/SKILL.md) | 按层只读诊断与验收 |
| [pocketrig-team](skills/pocketrig-team/SKILL.md) | 扩展给家人或小团队：新增、重设密码、停用成员 |

## 工作方式

![架构示意](docs/architecture.svg)

```text
手机 / Mac（Paseo 客户端或网页）
        │ Tailscale 私有网络：不开放公网端口，只放行自己的设备
常开工作站：本人 Paseo 实例（systemd / launchd 托管，24 小时在线）
        │ 以本人 UID 运行 Claude Code / Codex（公共安装，经包装脚本启动）
        │ 本人 ~/.ssh 配置
GPU / 计算节点：数据、模型、训练与完整产物；只把小结果拉回工作站
```

## 快速开始（一个人）

不想手动操作时，装好上面的插件，让 Agent 按 `pocketrig-setup` → `pocketrig-always-on` → `pocketrig-connect` 依次完成。手动步骤（Linux / WSL；macOS 见[平台文档](docs/platforms.md)）：

1. 安装公共部分，并给自己创建实例：
   ```bash
   git clone https://github.com/SuperFCR/PocketRig.git
   cd PocketRig
   sudo ./linux/install.sh --install-node 24.22.1 --install-packages   # 版本号按需选择
   sudo paseo-user add "$USER" 6767
   claude auth login && codex login                                    # 登录你自己的账号
   ```
2. 保持常驻：WSL 部署在 Windows 侧注册常驻任务（同时维护 Tailscale 入口转发），见[管理员部署指南](docs/admin-guide.md)第 3 节；原生 Linux / macOS 让 Paseo 监听本机 Tailscale 地址。
3. 手机和 Mac 登录 Tailscale，在 Paseo 中添加 Host（`<WS_IP>:6767`，Use SSL 关闭，密码在 `~/.paseo/client.env`），按[使用教程](docs/user-guide.md)完成第一个任务。
4. 计算节点：在本人 `~/.ssh/config` 配好节点，用 [remote-compute](skills/remote-compute/SKILL.md) 提交任务、把结果拉回给手机看。

上线前按[验收清单](docs/acceptance-checklist.md)逐项确认。

## 扩展给家人或小团队

同一台工作站可以给每人一个独立系统用户和 Paseo 实例（`sudo paseo-user add alice 6767`、`sudo paseo-user add bob 6768`），按人授权 Tailscale 端口，用[交付单模板](templates/handover.md)私下交付连接参数。详见 [pocketrig-team](skills/pocketrig-team/SKILL.md) 与[管理员部署指南](docs/admin-guide.md)。

| 对象 | 安排 | 边界 |
| --- | --- | --- |
| Node / Paseo / Claude Code / Codex 程序 | 公共安装，root 维护 | 普通用户只读执行 |
| Paseo、Claude Code、Codex 进程 | 每人独立 | systemd / launchd 以真实 UID 运行 |
| 项目、会话、配置、SSH 密钥 | 每人独立 | 私有 HOME（700），凭据文件 600 |
| Paseo 连接密码 | 每人独立 | 随机生成，仅本人 `~/.paseo/client.env` 可读 |
| 模型账号登录 | 每人独立 | 本人执行 `claude auth login` / `codex login`，不复制他人凭据 |
| 网络、代理、CPU、内存、磁盘 | 宿主共享 | 需要时再加每用户资源上限 |

隔离依靠系统 UID 与文件权限，**适合相互信任的小团队**：root/sudo 管理员、宿主管理员、共享网络都在共同信任边界内。它不是面向恶意租户的容器或虚拟机隔离。

## 仓库内容

```text
skills/                Agent Skills（安装、常驻、连接、远程计算、诊断、多人扩展）+ install.sh
.claude-plugin/        Claude Code 插件与插件市场清单
linux/                 工作站公共部分（root 安装）
  install.sh           安装包装脚本、systemd 模板、管理工具；可选下载 Node、npm 安装三个程序
  bin/                 claude、codex、paseo 公共入口（启动前检查 + 原样传参）
  sbin/paseo-user      add / reset-password / remove / list 每用户实例
  systemd/paseo@.service
  share/               工作站使用约定 + 写入各用户 CLAUDE.md / AGENTS.md 的同步脚本
windows/               Tailscale 在 Windows、Paseo 在 WSL 时的入口转发与常驻任务
macos/                 macOS 每用户实例的 launchd 模板
optional/egress-proxy/ 可选：全用户透明出口网关（mihomo TUN + nftables 防直连）
templates/             SSH 配置、Tailscale ACL、交付单模板
docs/                  设计方案、部署、使用教程、验收、排错；promo/ 宣传片与源码，demo/ 30 秒短片
tests/                 不依赖真实用户、服务或模型的安装、运行与 skills 回归检查
```

## 文档

- [Skills 总览](skills/README.md)：每个 skill 的用途、典型说法与安装方式
- [设计方案](docs/design.md)：隔离边界、任务流、用量统计、分阶段上线
- [按宿主平台部署](docs/platforms.md)：Windows + WSL2 / 原生 Linux / macOS 的差异与完整步骤
- [管理员部署指南](docs/admin-guide.md)：安装、新增/停用用户、Windows 转发、Tailscale 授权、常驻运行
- [使用教程](docs/user-guide.md)：连接、首个任务、远程计算、结果拉回、网页隧道
- [iPhone：Shadowrocket 内置 Tailscale](docs/ios-shadowrocket.md)：可选入网方式（已在 iPhone 实机验证）
- [验收清单](docs/acceptance-checklist.md) · [故障排查](docs/troubleshooting.md) · [验证记录](docs/validation.md)
- [可选：出口网关模块](docs/egress-proxy.md)
- [宣传片分镜与源码](docs/promo/README.md) · [参与开发](CONTRIBUTING.md)

## 已验证环境

参考部署运行在 Windows + WSL2；本仓库脚本有静态检查和临时目录中的模拟测试，尚未从空白系统完成整套部署验收。原生 Linux / macOS 均待实机验收，详见[验证记录](docs/validation.md)和[平台对照](docs/platforms.md)。Skills 与插件清单通过结构测试和 `claude plugin validate`；skill 驱动的端到端部署同样需要在测试设备上验收。

参考版本：Paseo 0.13.2、Node 24、Codex 0.164、Claude Code 2.1.308，Windows 11 + WSL2（Ubuntu，systemd 启用，NAT 网络模式）+ Windows 版 Tailscale。安装器默认固定 Paseo 0.13.2（`PW_PASEO_VERSION`），因为 `paseo-user` 生成密码哈希时使用了内部模块路径。升级后须重新验证；若路径变化，可改由成员在本人终端执行 `paseo daemon set-password`。

## 使用须知

- 每个人应使用自己有权使用的模型账号（个人订阅、团队/企业席位或 API Key），并遵守 Anthropic、OpenAI 等服务商的使用条款（包括其支持地区政策）。本项目不提供、也不鼓励共享登录凭据或规避服务商的限制。
- Tailscale 只负责连接自己的设备，不是代理。可选出口网关模块只是通用的网络出口控制工具；使用者须自行确保符合所在地法律法规及服务商条款。
- 本项目与 Paseo、Tailscale、Anthropic、OpenAI 均无隶属关系。

## 名称

项目原名 Paseo Desk，2026-10-28 更名为 PocketRig；旧地址 `SuperFCR/Paseo-Desk` 会自动跳转到新仓库。系统安装路径与服务名（`paseo-user`、`paseo@<user>`、`/etc/paseo-workstation`）保持不变，已部署的工作站无需迁移。

## 许可证

[MIT](LICENSE)
