# 工作站连接交付单（私下发送，不要放进共享文档或群聊）

成员：`<user>`　　交付日期：`<YYYY-MM-DD>`　　交付人：`<管理员>`

| 项目 | 内容 |
| --- | --- |
| 工作站 Host（Tailscale） | `100.x.y.z` |
| 工作站平台 | Windows + WSL2 / 原生 Linux / macOS |
| SSH | `ssh -p <SSH端口> <user>@100.x.y.z`；WSL 示例 2222，Linux / macOS 通常 22 |
| SSH 主机指纹（ED25519） | `SHA256:...` |
| SSH 初始凭据 | 另行告知 / 已登记公钥 |
| Paseo 端口 | `67xx` |
| Paseo Use SSL | 关闭 |
| Paseo 密码 | 登录 SSH 后 `cat ~/.paseo/client.env` |
| 工作根目录 | Linux / WSL：`/home/<user>/projects`；macOS：`/Users/<user>/projects` |
| 结果目录 | `~/results/<project>/<job-id>/`（工作站本人 HOME 下） |
| 模型账号 | 个人订阅 / 团队席位 / API Key（本人登录） |
| 计算节点 | `<别名>`：`<地址>`，远程用户 `<name>`，授权目录 `<path>` |

首次使用请按《成员使用教程》第 1–3 节完成：核对指纹 → 检查 whoami / HOME → 登录模型账号 → 添加 Paseo Host → 完成首个任务。
