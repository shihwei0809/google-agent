$port = 18080

# 使用 UDP 連線獲取本機對外的內網 IP
$socket = New-Object System.Net.Sockets.UdpClient
$ip = $null
try {
    $socket.Connect("8.8.8.8", 80)
    $ip = $socket.Client.LocalEndPoint.Address.IPAddressToString
} catch {} finally {
    if ($socket) { $socket.Close() }
}

if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'InterNetwork' -and $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.254\.' } | Select-Object -First 1).IPAddress
}

if (-not $ip) { $ip = '127.0.0.1' }

# 綁定至 0.0.0.0 (所有網路卡界面) 並搜尋可用連接埠以防佔用
$localIP = [System.Net.IPAddress]::Any
$listener = $null
$bound = $false

while (-not $bound -and $port -lt 19000) {
    try {
        $listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)
        $listener.Start()
        $bound = $true
    } catch {
        $port++
    }
}

if (-not $bound) {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ 啟動失敗！" -ForegroundColor Red
    Write-Host "  找不到可用的連接埠 (18080-19000)。請關閉其他伺服器再重試。" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Read-Host "按 Enter 結束..."
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📋 員工教育訓練測驗系統 — 本機內網網頁伺服器" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
Write-Host "  伺服器運行中..."
Write-Host "  💡 注意：請【勿】關閉此視窗，關閉代表結束服務。"
Write-Host "  💡 同仁的手機或電腦，必須與您連線至【同一個 Wi-Fi】或公司網路。`n"
Write-Host "  📢 同仁請在瀏覽器輸入以下網址開啟測驗："
Write-Host "  👉 http://$($ip):$($port)/index.html" -ForegroundColor Green
Write-Host "`n============================================================" -ForegroundColor Cyan

$currentDir = $PSScriptRoot
if (-not $currentDir) { $currentDir = (Get-Location).Path }

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
                
                try {
                    $record = $body | ConvertFrom-Json
                    $csvPath = Join-Path $currentDir "results.csv"
                    
                    $utf8BOM = New-Object System.Text.UTF8Encoding($true)
                    if (-not (Test-Path $csvPath)) {
                        $headersLine = "時間戳記,姓名,對題數,得分"
                        $qCount = 0
                        foreach ($prop in $record.PSObject.Properties) {
                            if ($prop.Name -match '^q\d+_answer$') { $qCount++ }
                        }
                        for ($i = 1; $i -le $qCount; $i++) {
                            $qText = $record."q${i}_question" -replace '"', '""'
                            $headersLine += ",`"第${i}題: ${qText}`""
                        }
                        [System.IO.File]::WriteAllText($csvPath, "$headersLine`r`n", $utf8BOM)
                    }
                    
                    $qCount = 0
                    foreach ($prop in $record.PSObject.Properties) {
                        if ($prop.Name -match '^q\d+_answer$') { $qCount++ }
                    }
                    $correctStr = "$($record.correctCount) / $($record.total)"
                    $scoreStr = "$($record.score) 分"
                    $nameClean = $record.name -replace '"', '""'
                    $tsClean = $record.timestamp -replace '"', '""'
                    
                    $row = """$tsClean"",""$nameClean"",""$correctStr"",""$scoreStr"""
                    for ($i = 1; $i -le $qCount; $i++) {
                        $val = $record."q${i}_answer" -replace '"', '""'
                        $row += ",`"$val`""
                    }
                    
                    [System.IO.File]::AppendAllText($csvPath, "$row`r`n", $utf8BOM)
                    
                    $respBody = '{"status":"ok","message":"saved"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($respBody)
                    $header = "HTTP/1.1 200 OK`r`nContent-Type: application/json; charset=utf-8`r`nContent-Length: $($respBytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                    Write-Host "📥 [本機紀錄] 收到同仁 $($record.name) 的作答結果，已寫入 results.csv" -ForegroundColor Yellow
                } catch {
                    $err = '{"status":"error","message":"' + $_.Exception.Message.Replace('"', '\"') + '"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($err)
                    $header = "HTTP/1.1 500 Error`r`nContent-Type: application/json`r`nContent-Length: $($respBytes.Length)`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                }
            } else {
                $filePath = Join-Path $currentDir $urlPath
                if (Test-Path $filePath -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                    $contentType = switch ($ext) {
                        ".html" { "text/html; charset=utf-8" }
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
                    $header = "HTTP/1.1 404 Not Found`r`nContent-Length: $($errBytes.Length)`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($errBytes, 0, $errBytes.Length)
                }
            }
        }
        $stream.Close()
        $client.Close()
    } catch {}
}