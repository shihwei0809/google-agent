$port = 18080

# 取得本機對外內網 IP
$socket = New-Object System.Net.Sockets.UdpClient
$ip = $null
try {
    $socket.Connect('8.8.8.8', 80)
    $ip = $socket.Client.LocalEndPoint.Address.IPAddressToString
} catch {} finally { if ($socket) { $socket.Close() } }
if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object {
        $_.AddressFamily -eq 'InterNetwork' -and
        $_.IPAddress -notmatch '^127\.' -and
        $_.IPAddress -notmatch '^169\.254\.'
    } | Select-Object -First 1).IPAddress
}
if (-not $ip) { $ip = '127.0.0.1' }

$localIP = [System.Net.IPAddress]::Any
$listener = $null
$bound = $false
while (-not $bound -and $port -lt 19000) {
    try {
        $listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)
        $listener.Start()
        $bound = $true
    } catch { $port++ }
}
if (-not $bound) {
    Write-Host '  找不到可用連接埠 (18080-19000)。' -ForegroundColor Red
    Read-Host '按 Enter 結束'; exit
}

Write-Host '==================================================' -ForegroundColor Cyan
Write-Host '  員工教育訓練測驗系統 -- 本機內網伺服器' -ForegroundColor Cyan
Write-Host '==================================================' -ForegroundColor Cyan
Write-Host '  請勿關閉此視窗，關閉即結束服務。'
Write-Host '  同仁需連至同一 Wi-Fi 或公司內網。'
Write-Host ''
Write-Host "  http://$($ip):$($port)/index.html" -ForegroundColor Green
Write-Host '==================================================' -ForegroundColor Cyan

$currentDir = $PSScriptRoot
if (-not $currentDir) { $currentDir = (Get-Location).Path }

function EscCsv($s) { return '"' + ($s -replace '"','""') + '"' }

while ($true) {
    try {
        if (-not $listener.Pending()) { Start-Sleep -Milliseconds 100; continue }
        $client  = $listener.AcceptTcpClient()
        $stream  = $client.GetStream()
        $reader  = New-Object System.IO.StreamReader($stream)
        $reqLine = $reader.ReadLine()

        if ($reqLine -match '^(GET|POST)\s+(/[^\s\?]*)\??[^\s]*\s+HTTP') {
            $method  = $Matches[1]
            $urlPath = [System.Uri]::UnescapeDataString($Matches[2])
            if ($urlPath -eq '/') { $urlPath = '/index.html' }

            if ($method -eq 'POST' -and $urlPath -eq '/api/submit') {
                $hdrs = @{}
                while ($line = $reader.ReadLine()) {
                    if ($line -eq '') { break }
                    if ($line -match '^([^:]+):\s*(.*)$') { $hdrs[$Matches[1].ToLower()] = $Matches[2].Trim() }
                }
                $cLen = 0
                if ($hdrs.ContainsKey('content-length')) { [int]::TryParse($hdrs['content-length'], [ref]$cLen) | Out-Null }
                $body = ''
                if ($cLen -gt 0) {
                    $buf  = New-Object System.Char[] $cLen
                    $read = $reader.Read($buf, 0, $cLen)
                    $body = New-Object System.String($buf, 0, $read)
                }
                try {
                    $rec     = $body | ConvertFrom-Json
                    $csvPath = Join-Path $currentDir 'results.csv'
                    $enc     = New-Object System.Text.UTF8Encoding($true)
                    # 計算題目數
                    $qCount = ($rec.PSObject.Properties | Where-Object { $_.Name -match '^q\d+_answer$' }).Count
                    # 若 CSV 不存在，建立標頭列
                    if (-not (Test-Path $csvPath)) {
                        $hdr = '時間戳記,姓名,對題數,得分'
                        for ($i = 1; $i -le $qCount; $i++) {
                            $qt   = $rec."q${i}_question"
                            $hdr += ',' + (EscCsv "第${i}題: $qt")
                        }
                        [System.IO.File]::WriteAllText($csvPath, "$hdr`r`n", $enc)
                    }
                    # 組資料列
                    $row  = (EscCsv $rec.timestamp) + ',' + (EscCsv $rec.name)
                    $row += ',' + (EscCsv "$($rec.correctCount) / $($rec.total)")
                    $row += ',' + (EscCsv "$($rec.score) 分")
                    for ($i = 1; $i -le $qCount; $i++) {
                        $row += ',' + (EscCsv $rec."q${i}_answer")
                    }
                    [System.IO.File]::AppendAllText($csvPath, "$row`r`n", $enc)
                    $rb  = [System.Text.Encoding]::UTF8.GetBytes('{"status":"ok"}')
                    $rh  = "HTTP/1.1 200 OK`r`nContent-Type: application/json`r`nContent-Length: $($rb.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $stream.Write([System.Text.Encoding]::UTF8.GetBytes($rh), 0, $rh.Length)
                    $stream.Write($rb, 0, $rb.Length)
                    Write-Host "[收到] $($rec.name) -- 得分: $($rec.score)分  已寫入 results.csv" -ForegroundColor Yellow
                } catch {
                    $eb = [System.Text.Encoding]::UTF8.GetBytes('{"status":"error"}')
                    $eh = "HTTP/1.1 500 Error`r`nContent-Length: $($eb.Length)`r`nConnection: close`r`n`r`n"
                    $stream.Write([System.Text.Encoding]::UTF8.GetBytes($eh), 0, $eh.Length)
                    $stream.Write($eb, 0, $eb.Length)
                    Write-Host "[錯誤] $($_.Exception.Message)" -ForegroundColor Red
                }
            } else {
                $fp = Join-Path $currentDir $urlPath
                if (Test-Path $fp -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($fp).ToLower()
                    $ct  = switch ($ext) {
                        '.html' { 'text/html; charset=utf-8' }
                        '.mp3'  { 'audio/mpeg' }
                        '.wav'  { 'audio/wav' }
                        '.css'  { 'text/css' }
                        '.js'   { 'application/javascript' }
                        '.json' { 'application/json' }
                        default { 'application/octet-stream' }
                    }
                    $bytes = [System.IO.File]::ReadAllBytes($fp)
                    $rh    = "HTTP/1.1 200 OK`r`nContent-Type: $ct`r`nContent-Length: $($bytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $stream.Write([System.Text.Encoding]::UTF8.GetBytes($rh), 0, $rh.Length)
                    $stream.Write($bytes, 0, $bytes.Length)
                } else {
                    $e4 = [System.Text.Encoding]::UTF8.GetBytes('404 Not Found')
                    $h4 = "HTTP/1.1 404 Not Found`r`nContent-Length: $($e4.Length)`r`nConnection: close`r`n`r`n"
                    $stream.Write([System.Text.Encoding]::UTF8.GetBytes($h4), 0, $h4.Length)
                    $stream.Write($e4, 0, $e4.Length)
                }
            }
        }
        $stream.Close(); $client.Close()
    } catch { Write-Host "[例外] $_" -ForegroundColor DarkGray }
}