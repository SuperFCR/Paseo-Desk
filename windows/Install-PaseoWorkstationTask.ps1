# 注册（或用 -Uninstall 删除）开机常驻计划任务。在管理员 PowerShell 中执行。
# 任务以当前 Windows 用户运行（WSL 发行版按 Windows 用户注册，SYSTEM 无法启动它），
# 不要求用户登录，使用最高权限以便维护 portproxy 和防火墙。
param([switch]$Uninstall, [string]$TaskName = 'PaseoWorkstation')
$ErrorActionPreference = 'Stop'

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "已删除计划任务 $TaskName；portproxy 与防火墙规则保留，可手动清理 PaseoWorkstation-* 规则"
    return
}

$script = Join-Path $PSScriptRoot 'Start-PaseoWorkstation.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Output "已注册并启动计划任务 $TaskName。日志：$(Join-Path $PSScriptRoot 'logs\workstation.log')"
