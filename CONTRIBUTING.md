# 参与开发

修改前先阅读 [README](README.zh-CN.md)（[English](README.md)）、[设计方案](docs/design.md)与[验证记录](docs/validation.md)。本项目使用 Paseo 作为控制端、Tailscale 组网；工作站只承载开发与轻量检查，数据和模型计算留在远程计算节点。

## 本地检查

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

ShellCheck 与 PowerShell 解析方法见验证记录。脚本修改应说明目标平台；涉及安装、权限、配置合并和网络行为的修复请添加可在临时目录执行的回归检查。端到端验证放在独立测试设备上。

## 提交内容

- 文档使用中文（README 同时维护英文 `README.md` 与中文 `README.zh-CN.md`，修改时两份同步），示例用户使用 alice / bob，域名使用 example.com。
- 不提交真实 IP、节点凭据、SSH 密钥、账号登录文件或个人部署记录。`.gitignore` 只是辅助，提交前检查暂存内容。
- 保持公共程序安装与每用户状态分开，不引入复制他人模型登录凭据的功能。
- PowerShell 保留 UTF-8 BOM 和 CRLF，以兼容 Windows PowerShell 5.1；Shell 文件使用 LF。
- Skill（`skills/<name>/SKILL.md`）：目录名与 frontmatter 的 `name` 一致；description 写清“什么时候用”和典型说法；正文写步骤、验证与停止条件，涉及 sudo、网络策略、电源、重启或删除数据的步骤要求先征得同意。新增 skill 同步更新 `skills/README.md`，并运行 `claude plugin validate .`。
- PR 描述说明问题、修改后的行为、验证方法和平台限制；没有实机运行过的平台应明确标注。
