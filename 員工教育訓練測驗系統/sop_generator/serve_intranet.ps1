$port = 18082

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

$localIP = [System.Net.IPAddress]::Any
$listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)

try {
    $listener.Start()
} catch {
    Write-Host "  ❌ 啟動失敗！連接埠 $($port) 已被佔用。" -ForegroundColor Red
    Read-Host "按 Enter 鍵結束..."
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📋 員工教育訓練測驗產生器 — 本機伺服器已啟動" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
Write-Host "  💡 請將此視窗保持開啟，關閉後服務將中斷。`n"
Write-Host "  📢 請在瀏覽器輸入以下網址開啟產生器："
Write-Host "  👉 http://localhost:$($port)/index.html" -ForegroundColor Green
if ($ip -ne '127.0.0.1') {
    Write-Host "  👉 http://$($ip):$($port)/index.html" -ForegroundColor Green
}
Write-Host "`n============================================================" -ForegroundColor Cyan

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
        
        if ($requestLine -match '^GET\s+(/[^\s\?]*)\??[^\s]*\s+HTTP') {
            $urlPath = $Matches[1]
            if ($urlPath -eq "/") { $urlPath = "/index.html" }
            $urlPath = [System.Uri]::UnescapeDataString($urlPath)
            
            # 讀取 Headers 直到空行
            while ($line = $reader.ReadLine()) {
                if ($line -eq "") { break }
            }
            
            $filePath = Join-Path $currentDir $urlPath
            if (Test-Path $filePath -PathType Leaf) {
                $bytes = [System.IO.File]::ReadAllBytes($filePath)
                
                $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                $contentType = "application/octet-stream"
                if ($ext -eq ".html") { $contentType = "text/html; charset=utf-8" }
                elseif ($ext -eq ".js") { $contentType = "application/javascript; charset=utf-8" }
                elseif ($ext -eq ".css") { $contentType = "text/css; charset=utf-8" }
                elseif ($ext -eq ".json") { $contentType = "application/json; charset=utf-8" }
                
                $header = "HTTP/1.1 200 OK`r`nContent-Type: $contentType`r`nContent-Length: $($bytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                $stream.Write($headerBytes, 0, $headerBytes.Length)
                $stream.Write($bytes, 0, $bytes.Length)
            } else {
                $body = "404 Not Found"
                $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
                $header = "HTTP/1.1 404 Not Found`r`nContent-Type: text/plain`r`nContent-Length: $($bodyBytes.Length)`r`nConnection: close`r`n`r`n"
                $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                $stream.Write($headerBytes, 0, $headerBytes.Length)
                $stream.Write($bodyBytes, 0, $bodyBytes.Length)
            }
        }
        $stream.Close()
        $client.Close()
    } catch {
        # 忽略單個請求錯誤
    }
}
