# iPhone：Shadowrocket 内置 Tailscale 接入

适用于已经使用 Shadowrocket（小火箭）、希望同时访问本人 Paseo 工作站的成员。iOS 限制同时运行的 VPN；这里让 Shadowrocket 的内置 Tailscale 接入组网，由 Shadowrocket 建立手机的 VPN 连接。无需此组合时，直接使用[成员教程](user-guide.md)中的官方 Tailscale App 登录方式即可。[Tailscale：与其他 VPN 共用](https://tailscale.com/docs/reference/faq/other-vpns)

Shadowrocket 的 [App Store 更新记录](https://apps.apple.com/us/app/shadowrocket/id932747118)确认支持内置 Tailscale。本页按设置中存在 **Tailscale / Auth Key（认证密钥）** 字段的版本编写；菜单位置、中文译名和可选项以实际界面为准。该组合已于 2026-10-27 在 iPhone 实机完成接入验证：Shadowrocket 内置 Tailscale 入网后可连接本人 Paseo 实例。不同版本的界面可能不同，请以实际设置页为准。

下文统一使用虚构成员 `alice`；`<WS_IP>` 是管理员交付的工作站 Tailscale 地址，`6767` 仅为端口示例。没有真实账号、地址、密钥或截图。

## 1. 准备手机与成员身份

1. 更新 Shadowrocket，确认其中能找到 Tailscale 和认证密钥设置。
2. 在独立的 Tailscale App 中关闭 VPN On Demand（按需连接），再断开连接；保留 Shadowrocket 原有节点与订阅配置。按需连接的切换行为见 [Tailscale 官方说明](https://tailscale.com/docs/features/client/ios-vpn-on-demand)。
3. 确认目标 tailnet 和获授权的成员身份。换成内置客户端后，会注册一个新的 Tailscale 设备；原 App 的设备在线，不代表新设备已入网。

**身份先于密钥：**未带标签的 Auth key 会以生成者身份注册设备；带标签的设备则使用标签身份。本仓库的[授权模板](../templates/tailscale-policy.example.hujson)按 `alice@example.com` 等成员身份放行专属端口。因此，管理员不能把自己生成的未标记密钥直接当作 `alice` 的凭据交付。没有生成权限时，由管理员安排正确的成员接入方式；不要为获取密钥临时提升成员权限，也不要直接套用共享服务器标签。无法使用本人预期身份时，先使用官方 Tailscale App 登录。[Auth key 身份与权限](https://tailscale.com/docs/features/access-control/auth-keys)

## 2. 生成入网用的 Auth key

在具备生成权限、且身份正确的前提下，打开 [Tailscale 密钥管理页](https://console.tailscale.com/admin/settings/keys)，确认目标 tailnet 后选择 **Generate auth key**。下面是单台日常手机的起始设置，具体审批要求由管理员决定。

| 项目 | 示例设置 |
| --- | --- |
| Description | `alice-iphone-shadowrocket` |
| Reusable | 关闭，仅用于本次设备注册 |
| Expiration | 例如 7 天，预留完成注册的时间 |
| Ephemeral | 关闭，作为日常设备保留 |
| Tags | 本页按成员身份接入，不选择标签 |
| Pre-approved | 遵循管理员的设备审批要求 |

生成后只把密钥粘贴到本人的 Shadowrocket，不放入聊天、仓库、截图、订阅链接或 Paseo 密码框。一次性密钥使用后不能再用于另一轮设备注册；重装或清除设备状态时可能需要新密钥。

Auth key 的期限用于入网认证；设备注册后使用自己的节点密钥。Auth key 到期不等于设备立即掉线，也不等于撤销设备权限。[Auth key 的有效期说明](https://tailscale.com/docs/features/access-control/auth-keys)

## 3. 在 Shadowrocket 中配置

在 Shadowrocket 设置中查找 **Tailscale**。仅在实际界面出现相应字段时参考下表；没有这个入口时，不要把 Auth key 填到普通代理节点或订阅设置中。

| 字段（名称可能不同） | 配置方式 |
| --- | --- |
| 启用 Tailscale | 打开 |
| Auth Key / 认证密钥 | 粘贴刚生成的本人入网密钥 |
| 控制服务器 URL | Tailscale 官方服务保持默认；自建 Headscale 另按管理员方案配置，不在本页验证范围内 |
| Exit Node / 出口节点 | 初次连接不选择；访问工作站不需要它 |
| 始终使用 DERP | 先保留默认，不把强制中继作为通用排错步骤 |

保存后重新开启 Shadowrocket 的主连接开关，此时保持独立 Tailscale App 断开。代理节点与订阅服务仍由成员自行配置；本项目不提供它们。

## 4. 核对新设备，再连接 Paseo

在 [Tailscale 设备列表](https://console.tailscale.com/admin/machines)核对新设备，或请管理员代查：设备在线、所属成员符合预期；有设备审批或 Tailnet Lock 签名要求时，由管理员完成。还应确认该身份获准访问 `<WS_IP>:6767`。不要因为另一台设备可连就跳过新设备的授权检查。

打开 Paseo → Settings → Add host → Direct connection，按自己的交付单填写：

| 字段 | 脱敏示例 |
| --- | --- |
| 名称 | `alice workstation` |
| Host | `<WS_IP>`，填工作站地址，不是手机新设备地址 |
| Port | `6767`，实际使用本人专属端口 |
| Use SSL | 本仓库通过 Tailscale 直连的默认方案关闭；管理员另行配置 HTTPS 时按交付单填写 |
| Password | `alice` 本人的 Paseo 密码，来源为本人 `~/.paseo/client.env` 或管理员私下交付 |

**Auth key 只用于 Tailscale 入网；Paseo Password 用于登录本人 Paseo 实例。两者都不是 SSH 密码。**填写直连参数的官方依据见 [Paseo 连接文档](https://paseo.sh/docs/connectivity)。

连接后按[成员教程的首个任务](user-guide.md#第一个项目)检查 `whoami`、工作目录和 HOME；确认属于本人，再继续开发。

## 5. 常见问题与恢复

| 现象 | 检查与处理 |
| --- | --- |
| 没有 Tailscale / Auth Key 入口 | 核对版本与实际设置；先用官方 Tailscale App。反馈版本号和遮盖凭据的设置页即可 |
| Auth key 被拒绝 | 检查是否过期、一次性密钥是否已用过、目标 tailnet 是否正确；按正确身份重新生成 |
| 原 Tailscale App 自动连回 | 再检查 VPN On Demand，保持只由所选客户端建立 VPN |
| 设备在线但 Paseo 超时 | 核对设备所属成员、审批状态、工作站地址、专属端口和 grants/ACL；再按[故障排查](troubleshooting.md)检查服务与转发 |
| IP 可连、名称不可连 | 先使用交付单的 Tailscale IP，另查 MagicDNS；不要为此直接开放全部路由或端口 |
| Password 错误 | 使用本人 Paseo 密码，不能填 Auth key、SSH 密码或模型账号密码 |
| 想退回官方 App | 断开 Shadowrocket，再用官方 Tailscale App 以本人身份连接；稳定后按需恢复 On Demand |

公开反馈应遮盖邮箱、设备名、真实 IP、工作目录、订阅链接、二维码、Auth key 和密码。若入网密钥已经泄露，请管理员撤销并检查新注册设备；撤销 Auth key 不会自动踢掉已注册设备，需在设备列表另行移除不应保留的设备。[撤销密钥与设备](https://tailscale.com/docs/features/access-control/auth-keys#revoke-an-auth-key)
