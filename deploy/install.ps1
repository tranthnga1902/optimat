# Chạy MỘT lần trong PowerShell "Run as administrator":
# cài Caddy, mở tường lửa 80/443, tạo tác vụ cập nhật IP DuckDNS và tự chạy ứng dụng khi đăng nhập.
#Requires -RunAsAdministrator
if (-not (Test-Path "$PSScriptRoot\duckdns.env")) { throw "Chép deploy\duckdns.env.example thành duckdns.env rồi điền trước" }

if (-not (Get-Command caddy -ErrorAction SilentlyContinue)) { winget install --id CaddyServer.Caddy -e }

New-NetFirewallRule -DisplayName "OptiMat HTTP/HTTPS" -Direction Inbound -Protocol TCP -LocalPort 80, 443 -Action Allow -ErrorAction SilentlyContinue | Out-Null

$ps = "powershell.exe"
# mặc định Windows bỏ tác vụ khi chạy pin hoặc lỡ giờ do máy ngủ
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
$duck = New-ScheduledTaskAction $ps "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSScriptRoot\duckdns.ps1`""
$every5 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask "OptiMat DuckDNS" -Action $duck -Trigger $every5 -Settings $set -Force | Out-Null

$app = New-ScheduledTaskAction $ps "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSScriptRoot\start.ps1`""
Register-ScheduledTask "OptiMat Start" -Action $app -Trigger (New-ScheduledTaskTrigger -AtLogOn) -RunLevel Highest -Settings $set -Force | Out-Null

& "$PSScriptRoot\duckdns.ps1"; Get-Content "$PSScriptRoot\duckdns.log"
"Xong. Mở port 80, 443 trên router về IP LAN của máy này, rồi chạy deploy\start.ps1"
