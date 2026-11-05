$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$frontend = (Resolve-Path -LiteralPath (Join-Path $repo 'frontend')).Path
$logDir = (Resolve-Path -LiteralPath (Join-Path $repo 'reports/module_ui_qa_20261103')).Path
$attempt = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$oldId = '31Tsz2vLf5JymYeu5kmDw'
$newId = 'H7eQgDZ8u5vo-N2SW_pLT'
$node = (Get-Command node.exe -ErrorAction Stop).Source
if (!(Test-Path -LiteralPath (Join-Path $frontend 'node_modules/next/dist/bin/next') -PathType Leaf)) { throw 'Không có Next CLI.' }
$handler = New-Object Net.Http.HttpClientHandler
$handler.AllowAutoRedirect = $false
$client = New-Object Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromSeconds(6)
$sha = [Security.Cryptography.SHA256]::Create()
function Read-Page([string]$url) {
    $response = $client.GetAsync('http://127.0.0.1:3000' + $url).GetAwaiter().GetResult()
    try {
        $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
        [pscustomobject]@{ status=[int]$response.StatusCode; bytes=$bytes; sha=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','') }
    } finally { $response.Dispose() }
}
function Text-Of($response) { [Text.Encoding]::UTF8.GetString($response.bytes) }
function Listener([int]$port) {
    @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
}
function Proxy-Health {
    $page = Read-Page '/api/health'
    if ($page.status -ne 200 -or ((Text-Of $page | ConvertFrom-Json).status -ne 'ok')) { throw 'Proxy /api/health chưa hoạt động.' }
    return $page.status
}
function Verify-Page([string]$base,[string]$id,[string]$url,[string]$file) {
    $response = Read-Page $url
    $reference = Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $base ('server/app/'+$file+'.html'))
    if ($response.status -ne 200 -or $response.sha -ne $reference.Hash -or !(Text-Of $response).Contains($id)) {
        throw "HTML tại $url không khớp bản dựng $id."
    }
    return [ordered]@{http=$response.status; sha256=$response.sha}
}
function Start-Frontend([string]$dist,[string]$label) {
    $env:OPTIMAT_NEXT_DIST_DIR = $dist
    $stdout = Join-Path $logDir ("frontend_404_${label}_${attempt}.log")
    $stderr = Join-Path $logDir ("frontend_404_${label}_${attempt}.err.log")
    return Start-Process -FilePath $node -ArgumentList 'node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','3000' -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
}
function Wait-Ready($started) {
    $until = [DateTime]::UtcNow.AddSeconds(50)
    do {
        $started.Refresh()
        if ($started.HasExited) { throw "Frontend $($started.Id) đã thoát, mã $($started.ExitCode)." }
        try { $rootResponse = Read-Page '/' } catch { $rootResponse = $null }
        if ($rootResponse -and $rootResponse.status -eq 200) {
            $owner = @(Listener 3000)
            if ($owner.Count -ne 1 -or $owner[0] -ne $started.Id) { throw 'PID trả trang không phải frontend vừa mở.' }
            return
        }
        Start-Sleep -Milliseconds 400
    } while ([DateTime]::UtcNow -lt $until)
    throw 'Frontend không sẵn sàng trong thời gian chờ.'
}
$oldBase = Join-Path $frontend '.next'
$newBase = Join-Path $frontend '.next-404-stage'
$record = [ordered]@{time=(Get-Date -Format o); oldPid=27012; oldBuild=$oldId; candidateBuild=$newId; cwd=$frontend; bind='127.0.0.1:3000'; logSuffix=$attempt; status='preflight'}
$receiptPath = Join-Path $logDir ("frontend_404_cutover_${attempt}.json")
$stopped = $false
$newServer = $null
try {
    foreach ($item in @(@($oldBase,$oldId),@($newBase,$newId))) {
        if ((Get-Content -Raw -LiteralPath (Join-Path $item[0] 'BUILD_ID')).Trim() -ne $item[1]) { throw 'BUILD_ID thay đổi.' }
    }
    $verified = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $logDir 'frontend_404_clean_candidate.json') | ConvertFrom-Json
    if ($verified.status -ne 'clean_candidate_verified_not_deployed' -or $verified.verified.id -ne $newId) { throw 'Sai bản dựng đã kiểm.' }
    foreach ($file in $verified.verified.manifestSha256.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath (Join-Path $newBase $file.Name)).Hash -ne $file.Value) { throw 'Manifest staging đã đổi.' }
    }
    $pageFile = Join-Path $newBase 'server/app/du-an-cua-toi.html'
    if ((Get-FileHash -LiteralPath $pageFile).Hash -ne $verified.verified.pageHtmlSha256) { throw 'Trang staging đã đổi.' }
    $record.oldHome = Verify-Page $oldBase $oldId '/' 'index'
    $record.oldProjectStatus = (Read-Page '/du-an-cua-toi?ho-so=1').status
    if ($record.oldProjectStatus -ne 404) { throw 'Trạng thái trang dự án đã đổi trước khi triển khai.' }
    $record.proxyBefore = Proxy-Health
    $record.apiPidBefore = @(Listener 8000)
    $ports = @(Get-NetTCPConnection -LocalPort 3000 -State Listen)
    $old = Get-Process -Id 27012 -ErrorAction Stop
    $oldStarted = (Get-CimInstance Win32_Process -Filter 'ProcessId=27012').CreationDate
    if ($ports.Count -ne 1 -or $ports[0].OwningProcess -ne $old.Id -or $ports[0].LocalAddress -ne '127.0.0.1' -or
        $old.ProcessName -ne 'node' -or $oldStarted.ToString('yyyyMMddHHmmssfff') -ne '20261104082454484') { throw 'PID, giờ khởi động hoặc địa chỉ của frontend cũ đã đổi.' }
    $record.oldStarted = $oldStarted.ToString('o')
    Stop-Process -InputObject $old -ErrorAction Stop
    $stopped = $true
    if (!$old.WaitForExit(10000)) { throw 'Frontend cũ chưa dừng.' }
    $newServer = Start-Frontend '.next-404-stage' 'live'
    $record.newPid = $newServer.Id
    $record.newStarted = $newServer.StartTime.ToString('o')
    Wait-Ready $newServer
    $record.root = Verify-Page $newBase $newId '/' 'index'
    $record.login = Verify-Page $newBase $newId '/dang-nhap' 'dang-nhap'
    $record.project = Verify-Page $newBase $newId '/du-an-cua-toi?ho-so=1' 'du-an-cua-toi'
    $html = [IO.File]::ReadAllText($pageFile)
    $assets = @([regex]::Matches($html,'(?:src|href)="(/_next/static/[^"?#]+)(?:[?#][^"]*)?"') | ForEach-Object {$_.Groups[1].Value} | Sort-Object -Unique)
    if ($assets.Count -ne $verified.verified.staticAssets) { throw 'Số tài nguyên trang khác với bản đã kiểm.' }
    $assetHashes = [ordered]@{}
    foreach ($url in $assets) {
        $response = Read-Page $url
        $local = Join-Path $newBase ([uri]::UnescapeDataString($url.Substring('/_next/'.Length)))
        if ($response.status -ne 200 -or $response.sha -ne (Get-FileHash -LiteralPath $local).Hash) { throw "Tài nguyên không khớp: $url" }
        $assetHashes[$url]=$response.sha
    }
    $record.projectAssets = $assetHashes
    $record.proxyAfter = Proxy-Health
    $record.apiPidAfter = @(Listener 8000)
    $record.status='deployed_verified'
} catch {
    $failure = $_.Exception.Message
    $record.error = $failure
    $record.status='failed_before_stop'
    if ($stopped) {
        try {
            if ($newServer -and !$newServer.HasExited) {
                Stop-Process -InputObject $newServer -ErrorAction Stop
                if (!$newServer.WaitForExit(10000)) { throw 'Không dừng được frontend thử.' }
            }
            if (@(Listener 3000).Count -ne 0) { throw 'Cổng 3000 đã có tiến trình khác, không được dừng tiến trình đó.' }
            $restored = Start-Frontend '.next' 'rollback'
            Wait-Ready $restored
            $record.rollbackPid=$restored.Id
            $record.rollbackHome=Verify-Page $oldBase $oldId '/' 'index'
            $record.rollbackLogin=Verify-Page $oldBase $oldId '/dang-nhap' 'dang-nhap'
            $record.rollbackProxy=Proxy-Health
            $record.status='rolled_back_verified'
        } catch { $record.status='rollback_needs_attention';$record.rollbackError=$_.Exception.Message }
    }
    throw $failure
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 -LiteralPath $receiptPath
    Write-Output ('Receipt '+$receiptPath)
    Write-Output ('Status '+$record.status+'; frontend PID '+$record.newPid)
    $sha.Dispose();$client.Dispose();$handler.Dispose()
}
