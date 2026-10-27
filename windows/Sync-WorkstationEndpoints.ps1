# 按当前 Tailscale 地址同步 SSH 与各用户 Paseo 端口的 portproxy 和防火墙规则（管理员 PowerShell）。
# 用户与端口来自 WSL 中的 `paseo-user list --json`；若存在 paseo-endpoints.json 则以该文件为准。
# 已不再分配的端口、旧 Tailscale 地址上的转发会被清理。
. (Join-Path $PSScriptRoot 'Common.ps1')
$config = Get-PwConfig
$address = Get-PwTailscaleAddress $config
if (-not $address) { Write-PwLog 'Tailscale 未连接，跳过同步'; return }

$override = Join-Path $PwRoot 'paseo-endpoints.json'
if (Test-Path -LiteralPath $override) {
    $endpoints = @(Get-Content -LiteralPath $override -Raw | ConvertFrom-Json | ForEach-Object { $_ })
} else {
    $json = & $config.WslExe -d $config.Distro -u root --exec /usr/local/sbin/paseo-user list --json
    # WSL 未就绪时不要误删已有规则
    if ($LASTEXITCODE -ne 0 -or -not $json) { throw '无法从 WSL 读取 Paseo 用户列表' }
    $endpoints = @(($json -join "`n") | ConvertFrom-Json | ForEach-Object { $_ })
}

$desired = @([pscustomobject]@{ Listen = [int]$config.SshListenPort; Connect = [int]$config.SshTargetPort; Label = 'SSH' })
foreach ($entry in $endpoints) {
    $port = [int]$entry.Port
    if ($port -lt 1024 -or $port -gt 65535) { throw "无效端口：$port" }
    if ($port -eq [int]$config.SshListenPort) { throw "Paseo 端口与 SSH 入口冲突：$port" }
    $desired += [pscustomobject]@{ Listen = $port; Connect = $port; Label = "Paseo $($entry.User)" }
}

$state = Get-PwState
$wanted = @($desired | ForEach-Object { $_.Listen })
foreach ($old in @($state.Ports)) {
    $oldPort = [int]$old
    if ($wanted -notcontains $oldPort) {
        Remove-PwForward $state.Address $oldPort
    } elseif ($state.Address -and $state.Address -ne $address) {
        Remove-PwForward $state.Address $oldPort -KeepRule
    }
}
foreach ($item in $desired) { Set-PwForward $address $item.Listen $item.Connect $item.Label }
Save-PwState $address $wanted
