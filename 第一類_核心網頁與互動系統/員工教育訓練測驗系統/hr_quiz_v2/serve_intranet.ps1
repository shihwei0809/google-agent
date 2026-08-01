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
        
        if ($requestLine -match '^GET\s+(/[^\s\?]*)\??[^\s]*\s+HTTP') {
            $urlPath = $Matches[1]
            if ($urlPath -eq "/") { $urlPath = "/index.html" }
            $urlPath = [System.Uri]::UnescapeDataString($urlPath)
            
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
        $stream.Close()
        $client.Close()
    } catch {
        # 捕捉連線中斷等例外，確保伺服器持續運行不崩潰
    }
}
