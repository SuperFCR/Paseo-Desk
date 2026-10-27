# 公共函数：由其他脚本 dot-source。兼容 Windows PowerShell 5.1。
$ErrorActionPreference = 'Stop'
$PwRoot = $PSScriptRoot
$PwRulePrefix = 'PaseoWorkstation-'
$PwProxyRegPath = 'HKLM:\SYSTEM\CurrentControlSet\Services\PortProxy\v4tov4\tcp'

function Get-PwConfig {
    $path = Join-Path $PwRoot 'config.json'
    if (-not (Test-Path -LiteralPath $path)) { throw "缺少配置文件：$path（从 config.example.json 复制）" }
    Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
}

function Write-PwLog([string]$Message) {
    $dir = Join-Path $PwRoot 'logs'
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    Add-Content -LiteralPath (Join-Path $dir 'workstation.log') -Value ((Get-Date -Format s) + ' ' + $Message) -Encoding UTF8
}

# 返回本机 Tailscale IPv4；未连接时返回 $null
function Get-PwTailscaleAddress($Config) {
    $status = & $Config.TailscaleExe status --json | ConvertFrom-Json
    if ($status.BackendState -ne 'Running') { return $null }
    @($status.TailscaleIPs | Where-Object { $_ -match '^100\.' }) | Select-Object -First 1
}

function Get-PwState {
    $path = Join-Path $PwRoot 'state.json'
    if (Test-Path -LiteralPath $path) {
        try { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch { }
    }
    [pscustomobject]@{ Address = ''; Ports = @() }
}

function Save-PwState($Address, $Ports) {
    $path = Join-Path $PwRoot 'state.json'
    [pscustomobject]@{ Address = $Address; Ports = @($Ports) } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$path.tmp" -Encoding ASCII
    Move-Item -LiteralPath "$path.tmp" -Destination $path -Force
}

# <Tailscale IP>:ListenPort -> 127.0.0.1:ConnectPort，WSL localhost 转发再送到 Linux 服务
function Set-PwForward($Address, [int]$ListenPort, [int]$ConnectPort, [string]$Label) {
    $name = "$Address/$ListenPort"
    $item = Get-ItemProperty -LiteralPath $PwProxyRegPath -Name $name -ErrorAction SilentlyContinue
    if (-not $item -or $item.$name -ne "127.0.0.1/$ConnectPort") {
        & netsh.exe interface portproxy add v4tov4 "listenaddress=$Address" "listenport=$ListenPort" connectaddress=127.0.0.1 "connectport=$ConnectPort" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "端口转发失败：$ListenPort" }
        Write-PwLog "转发 ${Address}:$ListenPort -> 127.0.0.1:$ConnectPort ($Label)"
    }
    # 只放行本机 Tailscale 地址上的该端口，来源限定为 Tailscale CGNAT 网段；实际访问仍受 tailnet ACL 约束
    $rule = $PwRulePrefix + $ListenPort
    if (-not (Get-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -Name $rule -DisplayName "Paseo Workstation $Label via Tailscale" -Direction Inbound -Action Allow -Profile Any -Protocol TCP -LocalPort $ListenPort -LocalAddress $Address -RemoteAddress '100.64.0.0/10' | Out-Null
    } else {
        Set-NetFirewallRule -Name $rule -Enabled True -LocalAddress $Address -RemoteAddress '100.64.0.0/10' | Out-Null
    }
}

function Remove-PwForward($Address, [int]$ListenPort, [switch]$KeepRule) {
    if ($Address) {
        & netsh.exe interface portproxy delete v4tov4 "listenaddress=$Address" "listenport=$ListenPort" 2>&1 | Out-Null
    }
    if (-not $KeepRule) {
        Remove-NetFirewallRule -Name ($PwRulePrefix + $ListenPort) -ErrorAction SilentlyContinue
        Write-PwLog "已移除端口 $ListenPort 的转发与防火墙规则"
    }
}
