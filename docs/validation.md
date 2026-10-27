# 验证记录与本地检查

本仓库从一套 Windows + WSL2 参考部署整理而来。参考部署运行正常，与从空白系统执行仓库安装器是两项不同的验证。Linux / macOS 的平台说明和自动检查不能替代目标设备上的部署验收。

## 本次本地运行结果（2026-10-26）

- 15 项 Python 回归检查全部通过，包含模拟的 Linux / Darwin 安装流程。
- ShellCheck 0.11.0 检查公共脚本与可选出口模块，全部通过。
- Windows PowerShell 5.1 解析 5 个 `.ps1` 文件，全部通过；保留 UTF-8 BOM / CRLF。
- 使用本机已安装的 Paseo 0.13.2 模块，在临时目录验证生成配置通过其真实 schema，正确密码通过 bcrypt 校验、错误密码被拒绝；没有启动服务或调用模型。
- 当时的 53 个待公开文件与已有提交历史的私有路径、已知部署地址、密钥模式扫描无命中；JSON、SVG 和文档相对链接检查通过。

## 发布验证（2026-10-27）

- 仓库已发布为 [SuperFCR/Paseo-Desk](https://github.com/SuperFCR/Paseo-Desk)，包含虚构界面重建的手机 / Mac 短片；原始截图和私人部署记录未入库。
- 初次 macOS CI 暴露了 Shell 变量紧邻中文标点时的输出编码问题；使用 `${变量}` 明确边界后修复，保留严格 UTF-8 解码，并补充缺少 Node 与组权限拒绝的回归检查。
- 17 项检查在 Ubuntu 与 macOS CI 上全部通过；ShellCheck / Python 语法和 Windows PowerShell 解析也通过。对应代码提交为 `9aff302`，见[成功运行记录](https://github.com/SuperFCR/Paseo-Desk/actions/runs/40468792764)。
- 后续提交的状态以 [GitHub Actions](https://github.com/SuperFCR/Paseo-Desk/actions) 为准。CI 使用模拟用户、模拟下载与临时目录，不代表系统部署或真实网络验收。
- [Shadowrocket 内置 Tailscale 教程](ios-shadowrocket.md)已核对官方发布说明与相关文档；具体字段、真实手机入网和成员授权仍待实机验收。

## 不改动部署的检查

在仓库根目录执行，只需 Python 3、Bash 和系统自带的安装/归档工具：

```bash
python3 -m unittest discover -s tests -v
```

检查在临时目录复制脚本，把安装目标重定位到临时目录，以模拟命令替代 root 身份、下载与 systemctl；退出后自动清理。不安装真实 Node 或 npm 包，不连接模型、不创建真实用户、不修改服务或网络。检查覆盖：

- Linux 安装分支，以及 macOS arm64 / x64 的归档选择和公共文件安装。
- SHA256 错误时保留现有 Node；重复安装保留配置和上一份 Node；拒绝不完整版本、未知架构和系统目录。
- 固定 Paseo 版本、macOS 跳过 systemd。
- 非交互 CLI 使用配置的 Node，参数保留空格和空字符串，启动检查的输出只写 stderr，失败时拒绝启动。
- 缺少 Node、组权限拒绝和启动检查失败时，中文提示保留完整路径、工具名和 UTF-8 编码。
- Paseo 配置合并保留个人 provider 设置，新用户关闭本地语音、开启网页，文件权限正确，端口冲突在创建用户前被拒绝。
- 工作站约定同步的私有权限与幂等性、macOS plist 内容、文档相对链接。

ShellCheck（需另行安装）：

```bash
shellcheck -x linux/install.sh linux/bin/* linux/libexec/env.sh linux/libexec/paseo-daemon \
  linux/sbin/paseo-workstation-keepalive linux/share/sync-agent-policy.sh \
  optional/egress-proxy/install.sh optional/egress-proxy/sbin/*
```

GitHub Actions 配置了 Ubuntu 的 ShellCheck、Ubuntu/macOS 的上述检查，以及 Windows PowerShell 5.1 的脚本解析；已运行的结果见上方发布验证。

## 平台验收状态

| 项目 | 状态 |
| --- | --- |
| Windows + WSL2 参考部署 | 已有运行环境，作为方案来源 |
| 仓库静态检查与临时目录模拟 | 本地及 Ubuntu / macOS CI 通过；临时目录模拟不等于系统部署验收 |
| 空白 Linux / WSL 系统执行 root 安装 | 待验收 |
| macOS 实机安装、launchd 与后台模型认证 | 待验收 |
| Windows 冷启动无人登录、WSL 常驻恢复 | 待在部署设备验收 |
| 从成员客户端验证 tailnet 授权和跨用户拒绝 | 待在实际 tailnet 验收 |
| iPhone Shadowrocket 内置 Tailscale | 文档已核对，具体界面与完整接入流程待实机验收 |
| 可选出口网关真实节点、断网与恢复 | 待在独立测试环境验收；不要在本机 tailscaled 场景启用 |

正式交付时按[验收清单](acceptance-checklist.md)记录设备、系统、版本、日期和结果。macOS 特别核对 FileVault 解锁、休眠、钥匙串及后台认证，不能只检查进程存在。
