# Báo IP public hiện tại cho DuckDNS (Task Scheduler chạy 5 phút một lần, xem install.ps1).
$cfg = Get-Content "$PSScriptRoot\duckdns.env" -Raw | ConvertFrom-StringData
$r = Invoke-RestMethod "https://www.duckdns.org/update?domains=$($cfg.DUCKDNS_DOMAIN)&token=$($cfg.DUCKDNS_TOKEN)&ip=" -TimeoutSec 30
"$(Get-Date -Format s) $r" | Out-File "$PSScriptRoot\duckdns.log" -Encoding utf8
if ($r -ne "OK") { exit 1 }   # KO = sai tên miền hoặc token
