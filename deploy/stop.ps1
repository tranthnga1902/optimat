# Tắt API (8000), giao diện (3000) và Caddy (80/443) do start.ps1 chạy.
Get-NetTCPConnection -State Listen -LocalPort 80, 443, 3000, 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force }
"Đã tắt."
