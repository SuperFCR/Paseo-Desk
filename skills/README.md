# Skills：把 Paseo Desk 交给 Agent 来做

每个目录是一个 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)（`SKILL.md` + frontmatter）。装好后直接用自然语言提需求，例如“帮我把这台电脑装成 Paseo Desk 工作站”“手机连不上 Paseo，帮我查一下”，Claude Code / Codex 会按对应 skill 的步骤执行，并在需要 sudo、改网络或重启时先停下来确认。

| Skill | 什么时候用 | 典型说法 |
| --- | --- | --- |
| [paseo-desk-setup](paseo-desk-setup/SKILL.md) | 单人起步：安装公共部分并给自己建实例 | “把这台电脑装成工作站” |
| [paseo-desk-always-on](paseo-desk-always-on/SKILL.md) | 24 小时在线：不睡眠、WSL 不回收、开机自启、冷启动验收 | “锁屏/关终端后任务别停” |
| [paseo-desk-connect](paseo-desk-connect/SKILL.md) | 手机与 Mac 经 Tailscale 连进来，添加 Host，验证会话接续 | “手机怎么连工作站” |
| [remote-compute](remote-compute/SKILL.md) | 提交 GPU 节点任务、查询、拉回小结果，整理成手机能看的摘要 | “提交训练，跑完把结果给我看” |
| [paseo-desk-doctor](paseo-desk-doctor/SKILL.md) | 按层只读诊断与验收 | “Paseo 连接超时” |
| [paseo-desk-team](paseo-desk-team/SKILL.md) | 扩展给家人或小团队：新增、重设密码、停用成员 | “给 alice 开一个 Paseo” |

推荐顺序：setup → always-on → connect → remote-compute；出问题用 doctor，需要多人时再用 team。

## 安装

**Claude Code 插件（推荐）**：在 Claude Code 中执行

```text
/plugin install paseo-desk --marketplace SuperFCR/Paseo-Desk
```

较早版本分两步：`/plugin marketplace add SuperFCR/Paseo-Desk`，再 `/plugin install paseo-desk@paseo-desk`。

**复制到本人 skills 目录**（Claude Code 与 Codex 通用）：

```bash
git clone https://github.com/SuperFCR/Paseo-Desk.git && cd Paseo-Desk
./skills/install.sh                 # → ~/.claude/skills/
./skills/install.sh --codex         # → ${CODEX_HOME:-~/.codex}/skills/
./skills/install.sh --target DIR    # 其他工具的 skills 目录
```

脚本只复制本目录下的 skill，已存在的同名 skill 会先备份为 `<name>.bak-<时间>`。复制安装的 skill 里指向仓库文档的相对链接不可用时，以 GitHub 上的文档为准；插件方式安装保留完整仓库，链接可用。

## 约定

- skill 只写步骤、判断条件和停止条件，不写密码、令牌、私钥或真实地址。
- 涉及 sudo、网络策略、电源、重启、删除数据的步骤一律先说明影响并征得同意。
- `remote-compute` 需要每个项目在 `CLAUDE.local.md` 中填写计算节点连接信息。
