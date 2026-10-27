# 复制到 Windows 脚本目录（与 Common.ps1 同级，不要放进 hooks\）后按需手动运行。
# 在 Windows 侧触发 WSL 内的出口网关恢复，不关闭 WSL、不结束 tmux 会话。
. (Join-Path $PSScriptRoot 'Common.ps1')
$config = Get-PwConfig
& $config.WslExe -d $config.Distro -u root -- /usr/local/sbin/pw-egress-repair
if ($LASTEXITCODE -ne 0) { throw "出口网关恢复失败；在 WSL 中查看 journalctl -u pw-egress-proxy" }
