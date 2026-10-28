# Chạy bản production: FastAPI 127.0.0.1:8000, Next.js 127.0.0.1:3000, Caddy 80/443.
# .\deploy\start.ps1 -Build   build lại giao diện sau khi sửa mã frontend
param([switch]$Build)
$root = Split-Path $PSScriptRoot
$logs = New-Item -ItemType Directory -Force "$PSScriptRoot\logs"

# khóa cố định: thiếu thì mỗi lần khởi động API sinh khóa mới, mọi người bị đăng xuất
if (-not (Select-String -Path "$root\.env" -Pattern "^OPTIMAT_SECRET_KEY=." -Quiet)) {
    $key = -join ((1..48) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })
    Add-Content "$root\.env" "`nOPTIMAT_SECRET_KEY=$key" -Encoding utf8
}

if ($Build -or -not (Test-Path "$root\frontend\.next\BUILD_ID")) {
    Push-Location "$root\frontend"; npm run build; $ok = $?; Pop-Location
    if (-not $ok) { throw "npm run build lỗi" }
}

Start-Process "$root\.venv\Scripts\python.exe" -WorkingDirectory $root -WindowStyle Hidden `
    -ArgumentList "-m uvicorn optimat.api.main:app --app-dir src --host 127.0.0.1 --port 8000" `
    -RedirectStandardOutput "$logs\api.log" -RedirectStandardError "$logs\api.err.log"
Start-Process "npm.cmd" -WorkingDirectory "$root\frontend" -WindowStyle Hidden `
    -ArgumentList "run start -- -H 127.0.0.1 -p 3000" `
    -RedirectStandardOutput "$logs\web.log" -RedirectStandardError "$logs\web.err.log"
Start-Process "caddy" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden `
    -ArgumentList "run --config Caddyfile --envfile duckdns.env" `
    -RedirectStandardOutput "$logs\caddy.log" -RedirectStandardError "$logs\caddy.err.log"
"Đã chạy. Nhật ký ở $logs"
