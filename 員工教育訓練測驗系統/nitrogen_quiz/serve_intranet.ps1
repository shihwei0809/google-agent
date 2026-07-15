$port = 8000

# 使用 UDP 連線獲取本機對外的內網 IP (最穩定且不影響網路)
$socket = New-Object System.Net.Sockets.UdpClient
$ip = $null
try {
    $socket.Connect("8.8.8.8", 80)
    $ip = $socket.Client.LocalEndPoint.Address.IPAddressToString
} catch {
    # 失敗時的備用方案
} finally {
    if ($socket) { $socket.Close() }
}

if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'InterNetwork' -and $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.254\.' } | Select-Object -First 1).IPAddress
}

if (-not $ip) {
    $ip = '127.0.0.1'
}

$localIP = [System.Net.IPAddress]::Parse($ip)
$listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)

try {
    $listener.Start()
} catch {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ 啟動失敗！" -ForegroundColor Red
    Write-Host "  可能原因：" -ForegroundColor Red
    Write-Host "  1. 連接埠 $($port) 已被其他程式佔用（例如您已經啟動了另一個伺服器）。" -ForegroundColor Red
    Write-Host "  2. 網路卡未啟用或防火牆阻擋。" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host "按 Enter 鍵結束..."
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📋 員工教育訓練測驗系統 — 內網網頁伺服器" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
Write-Host "  伺服器正在運行中..."
Write-Host "  💡 注意事項："
Write-Host "  1. 請【勿】關閉此視窗，關閉後內網服務將會中斷。"
Write-Host "  2. 同仁的手機或電腦必須連線至與您【相同】的 Wi-Fi 或公司網路。`n"
Write-Host "  📢 同仁請在瀏覽器輸入以下網址開啟測驗（或使用瀏覽器分享功能產生的 QR 碼）："
Write-Host "  👉 http://$($ip):$($port)/index.html" -ForegroundColor Green
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  提示：在視窗中按 [Ctrl + C] 即可關閉伺服器。`n"

$currentDir = $PSScriptRoot
if (-not $currentDir) {
    $currentDir = (Get-Location).Path
}

while ($true) {
    try {
        if (-not $listener.Pending()) {
            Start-Sleep -Milliseconds 100
            continue
        }
        $client = $listener.AcceptTcpClient()
        $stream = $client.GetStream()
        
        $reader = New-Object System.IO.StreamReader($stream)
        $requestLine = $reader.ReadLine()
        
        if ($requestLine -match '^(GET|POST)\s+(/[^\s\?]*)\??[^\s]*\s+HTTP') {
            $method = $Matches[1]
            $urlPath = $Matches[2]
            if ($urlPath -eq "/") { $urlPath = "/index.html" }
            $urlPath = [System.Uri]::UnescapeDataString($urlPath)
            
            if ($method -eq "POST" -and $urlPath -eq "/api/submit") {
                # 處理 POST /api/submit 接收作答紀錄
                $headers = @{}
                while ($line = $reader.ReadLine()) {
                    if ($line -eq "") { break }
                    if ($line -match '^([^:]+):\s*(.*)$') {
                        $headers[$Matches[1].ToLower()] = $Matches[2].Trim()
                    }
                }
                
                $contentLength = 0
                if ($headers.ContainsKey("content-length")) {
                    [int]::TryParse($headers["content-length"], [ref]$contentLength) | Out-Null
                }
                
                $body = ""
                if ($contentLength -gt 0) {
                    $buffer = New-Object System.Char[] $contentLength
                    $read = $reader.Read($buffer, 0, $contentLength)
                    $body = New-Object System.String($buffer, 0, $read)
                }
                
                # 寫入 results.csv
                try {
                    $record = $body | ConvertFrom-Json
                    $csvPath = Join-Path $currentDir "results.csv"
                    
                    # 建立 CSV 標頭如果檔案不存在
                    if (-not (Test-Path $csvPath)) {
                        $headersLine = "時間戳記,姓名,答對題數,得分"
                        # 動態加上所有第 N 題的標題
                        $qCount = 0
                        foreach ($prop in $record.PSObject.Properties) {
                            if ($prop.Name -match '^q\d+$') { $qCount++ }
                        }
                        for ($i = 1; $i -le $qCount; $i++) {
                            $headersLine += ",第${i}題"
                        }
                        [System.IO.File]::WriteAllText($csvPath, "$headersLine`r`n", [System.Text.Encoding]::UTF8)
                    }
                    
                    # 組合內容
                    $qCount = 0
                    foreach ($prop in $record.PSObject.Properties) {
                        if ($prop.Name -match '^q\d+$') { $qCount++ }
                    }
                    $correctStr = "$($record.correctCount) / $($record.total)"
                    $scoreStr = "$($record.score) 分"
                    
                    # 處理逗號防止 CSV 跑格
                    $nameClean = $record.name -replace '"', '""'
                    $tsClean = $record.timestamp -replace '"', '""'
                    $row = """$tsClean"",""$nameClean"",""$correctStr"",""$scoreStr"""
                    
                    for ($i = 1; $i -le $qCount; $i++) {
                        $val = $record."q$i" -replace '"', '""'
                        $row += ",""$val"""
                    }
                    
                    [System.IO.File]::AppendAllText($csvPath, "$row`r`n", [System.Text.Encoding]::UTF8)
                    
                    # 回應成功 JSON
                    $respBody = '{"status":"ok","message":"saved locally"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($respBody)
                    $header = "HTTP/1.1 200 OK`r`nContent-Type: application/json; charset=utf-8`r`nContent-Length: $($respBytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                    Write-Host "📥 [本機紀錄] 收到同仁 $($record.name) 的測驗結果，已成功寫入 results.csv" -ForegroundColor Yellow
                } catch {
                    $err = '{"status":"error","message":"' + $_.Exception.Message.Replace('"', '\"') + '"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($err)
                    $header = "HTTP/1.1 500 Internal Error`r`nContent-Type: application/json; charset=utf-8`r`nContent-Length: $($respBytes.Length)`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                }
            } else {
                # 處理 GET 請求載入靜態檔案
                $filePath = Join-Path $currentDir $urlPath
                if (Test-Path $filePath -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                    $contentType = switch ($ext) {
                        ".html" { "text/html; charset=utf-8" }
                        ".css"  { "text/css; charset=utf-8" }
                        ".js"   { "application/javascript; charset=utf-8" }
                        ".json" { "application/json; charset=utf-8" }
                        ".png"  { "image/png" }
                        ".jpg"  { "image/jpeg" }
                        ".jpeg" { "image/jpeg" }
                        ".gif"  { "image/gif" }
                        default { "application/octet-stream" }
                    }
                    
                    $bytes = [System.IO.File]::ReadAllBytes($filePath)
                    $header = "HTTP/1.1 200 OK`r`nContent-Type: $contentType`r`nContent-Length: $($bytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($bytes, 0, $bytes.Length)
                } else {
                    $errText = "404 Not Found"
                    $errBytes = [System.Text.Encoding]::UTF8.GetBytes($errText)
                    $header = "HTTP/1.1 404 Not Found`r`nContent-Type: text/plain`r`nContent-Length: $($errBytes.Length)`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($errBytes, 0, $errBytes.Length)
                }
            }
        }
        $stream.Close()
        $client.Close()
    } catch {
        # 捕捉連線中斷等例外，確保伺服器持續運行不崩潰
    }
}
