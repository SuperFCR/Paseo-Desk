# 常驻循环：保持 WSL 实例存活，运行可选钩子，并定期同步 Tailscale 入口。
# 由 Install-PaseoWorkstationTask.ps1 注册为开机计划任务；也可在管理员 PowerShell 中直接运行调试。
. (Join-Path $PSScriptRoot 'Common.ps1')
$wslProcess = $null
$loopSeconds = 30

while ($true) {
    try {
        $config = Get-PwConfig
        if ($config.LoopSeconds) { $loopSeconds = [int]$config.LoopSeconds }
        if ($config.KeepAlive -and ($null -eq $wslProcess -or $wslProcess.HasExited)) {
            $logDir = Join-Path $PwRoot 'logs'
            if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
            $wslProcess = Start-Process -FilePath $config.WslExe -ArgumentList @('-d', $config.Distro, '-u', 'root', '--exec', '/usr/local/sbin/paseo-workstation-keepalive') -WindowStyle Hidden -RedirectStandardOutput "$logDir\wsl-out.log" -RedirectStandardError "$logDir\wsl-error.log" -PassThru
            Write-PwLog "已启动 WSL keepalive，PID $($wslProcess.Id)"
        }
        # 可选模块的 Windows 侧逻辑放在 hooks\*.ps1，每轮按文件名顺序执行
        $hooks = Join-Path $PwRoot 'hooks'
        if (Test-Path -LiteralPath $hooks) {
            Get-ChildItem -LiteralPath $hooks -Filter '*.ps1' | Sort-Object Name | ForEach-Object {
                & $_.FullName | ForEach-Object { Write-PwLog $_ }
            }
        }
        & (Join-Path $PwRoot 'Sync-WorkstationEndpoints.ps1')
    } catch {
        Write-PwLog $_.Exception.Message
    }
    Start-Sleep -Seconds $loopSeconds
}
