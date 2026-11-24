$printerIp = '192.168.3.128'
$printerPort = 9100
$startPort = 8099
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

# 取得本機所有實體 IPv4 位址
$localIps = @(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notlike '*Loopback*' -and
    $_.IPAddress -notlike '169.254*' -and
    $_.IPAddress -ne '127.0.0.1'
} | Select-Object -ExpandProperty IPAddress -Unique)
if ($localIps.Count -eq 0) { $localIps = @('127.0.0.1') }

# 自動搜尋可用 Port (Rule 6: Port Fallback)
$listenPort = $null
$tcpListener = $null
for ($p = $startPort; $p -lt ($startPort + 50); $p++) {
    try {
        $testListener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $p)
        $testListener.Start()
        $tcpListener = $testListener
        $listenPort = $p
        if ($p -ne $startPort) {
            Write-Host "[提示] 預設 Port $startPort 已被佔用，已自動切換至可用 Port: $listenPort" -ForegroundColor Yellow
        }
        break
    } catch {
        continue
    }
}

if (-not $tcpListener) {
    Write-Host "[錯誤] 無法在 Port ${startPort}~$($startPort+49) 啟動服務！" -ForegroundColor Red
    Read-Host "請按 Enter 鍵結束..."
    exit 1
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   鴻勝化學 QC 看板 - TSC 純內網行動列印代理伺服器" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[資訊] 目標 TSC 印表機 IP : $printerIp (Port: $printerPort)" -ForegroundColor Gray
Write-Host "[資訊] 預設標籤貼紙規格    : 90mm x 60mm (Label with Gap)" -ForegroundColor Gray
Write-Host "[本機] 電腦本機網址       : http://localhost:${listenPort}/" -ForegroundColor Green
foreach ($ip in $localIps) {
    Write-Host "[內網] 手機純內網看板網址  : http://${ip}:${listenPort}/" -ForegroundColor Green
}
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "[重要說明] iPhone / Android 手機請直接開啟上方「手機純內網看板網址」" -ForegroundColor Yellow
Write-Host "           (HTTP 同源直連，100% 不會被 iOS 安全機制封鎖！)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] 服務已成功於 Port $listenPort 啟動 (無需系統管理員權限)！" -ForegroundColor Green
Write-Host "請保持此視窗開啟 (縮小即可，請勿關閉)...`n" -ForegroundColor Green

function Send-HttpResponse {
    param(
        [System.Net.Sockets.NetworkStream]$Stream,
        [int]$StatusCode = 200,
        [string]$StatusText = "OK",
        [string]$ContentType = "application/json; charset=utf-8",
        [byte[]]$BodyBytes
    )
    if (-not $BodyBytes) { $BodyBytes = [byte[]]::new(0) }
    $headers = "HTTP/1.1 $StatusCode $StatusText`r`n" +
               "Access-Control-Allow-Origin: *`r`n" +
               "Access-Control-Allow-Methods: GET, POST, OPTIONS`r`n" +
               "Access-Control-Allow-Headers: Content-Type`r`n" +
               "Access-Control-Allow-Private-Network: true`r`n" +
               "Cache-Control: no-cache`r`n" +
               "Content-Type: $ContentType`r`n" +
               "Content-Length: $($BodyBytes.Length)`r`n" +
               "Connection: close`r`n`r`n"
    $headBytes = [System.Text.Encoding]::ASCII.GetBytes($headers)
    $Stream.Write($headBytes, 0, $headBytes.Length)
    if ($BodyBytes.Length -gt 0) {
        $Stream.Write($BodyBytes, 0, $BodyBytes.Length)
    }
    $Stream.Flush()
}

function Send-TsplToPrinter {
    param([string]$Tspl, [string]$Barcode, [string]$ProductName)
    $timeStr = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timeStr] 收到列印請求：單號 $Barcode ($ProductName)" -ForegroundColor Cyan
    $printerClient = New-Object System.Net.Sockets.TcpClient
    $async = $printerClient.BeginConnect($printerIp, $printerPort, $null, $null)
    if (-not $async.AsyncWaitHandle.WaitOne(5000, $false)) {
        $printerClient.Close()
        throw "無法連線至 TSC 印表機 (${printerIp}:${printerPort})，連線逾時"
    }
    $printerClient.EndConnect($async)
    $pStream = $printerClient.GetStream()
    $tsplBytes = [System.Text.Encoding]::GetEncoding('big5').GetBytes($Tspl)
    $pStream.Write($tsplBytes, 0, $tsplBytes.Length)
    $pStream.Flush()
    $printerClient.Close()
    Write-Host "[$timeStr] [OK] 標籤已成功傳送至 TSC 印表機！`n" -ForegroundColor Green
}

function Read-FullHttpRequest {
    param([System.Net.Sockets.NetworkStream]$Stream)
    $Stream.ReadTimeout = 5000
    $ms = New-Object System.IO.MemoryStream
    $buf = New-Object byte[] 8192
    $headerEnd = -1
    $contentLength = 0

    while ($true) {
        try {
            $n = $Stream.Read($buf, 0, $buf.Length)
        } catch {
            break
        }
        if ($n -le 0) { break }
        $ms.Write($buf, 0, $n)

        $allBytes = $ms.ToArray()
        if ($headerEnd -lt 0) {
            # 尋找 \r\n\r\n (13, 10, 13, 10)
            for ($i = 0; $i -le ($allBytes.Length - 4); $i++) {
                if ($allBytes[$i] -eq 13 -and $allBytes[$i+1] -eq 10 -and $allBytes[$i+2] -eq 13 -and $allBytes[$i+3] -eq 10) {
                    $headerEnd = $i + 4
                    $headerText = [System.Text.Encoding]::ASCII.GetString($allBytes, 0, $headerEnd)
                    if ($headerText -match '(?i)Content-Length:\s*(\d+)') {
                        $contentLength = [int]$Matches[1]
                    }
                    break
                }
            }
        }
        if ($headerEnd -ge 0) {
            $bodyLen = $allBytes.Length - $headerEnd
            if ($bodyLen -ge $contentLength) { break }
        }
        if ($allBytes.Length -gt 2097152) { break }
    }

    $rawBytes = $ms.ToArray()
    $ms.Dispose()
    if ($rawBytes.Length -eq 0) { return $null }
    if ($headerEnd -lt 0) { $headerEnd = $rawBytes.Length }

    $headerStr = [System.Text.Encoding]::ASCII.GetString($rawBytes, 0, $headerEnd)
    $bodyStr = ""
    if ($rawBytes.Length -gt $headerEnd) {
        $bodyStr = [System.Text.Encoding]::UTF8.GetString($rawBytes, $headerEnd, $rawBytes.Length - $headerEnd)
    }

    $firstLine = ($headerStr -split "`r`n")[0]
    $parts = $firstLine -split ' '
    $method = if ($parts.Length -ge 1) { $parts[0] } else { "" }
    $rawPath = if ($parts.Length -ge 2) { $parts[1] } else { "/" }
    $pathOnly = ($rawPath -split '\?')[0]

    return [PSCustomObject]@{
        Method = $method
        Path   = $pathOnly
        Body   = $bodyStr
    }
}

$mimeMap = @{
    '.html' = 'text/html; charset=utf-8'
    '.js'   = 'application/javascript; charset=utf-8'
    '.json' = 'application/json; charset=utf-8'
    '.css'  = 'text/css; charset=utf-8'
    '.png'  = 'image/png'
    '.jpg'  = 'image/jpeg'
    '.svg'  = 'image/svg+xml'
    '.ico'  = 'image/x-icon'
}

while ($true) {
    $client = $null
    $stream = $null
    try {
        $client = $tcpListener.AcceptTcpClient()
        $stream = $client.GetStream()
        $req = Read-FullHttpRequest -Stream $stream
        if (-not $req) { continue }

        # 1. CORS 預檢 (含 Private Network Access)
        if ($req.Method -eq "OPTIONS") {
            Send-HttpResponse -Stream $stream -StatusCode 200 -StatusText "OK" -ContentType "text/plain" -BodyBytes ([byte[]]::new(0))
            continue
        }

        # 2. JSON 直印 API (POST /print)
        if ($req.Method -eq "POST" -and $req.Path -eq "/print") {
            try {
                $json = $req.Body | ConvertFrom-Json
                Send-TsplToPrinter -Tspl $json.tspl -Barcode $json.barcode -ProductName $json.productName
                $respBytes = [System.Text.Encoding]::UTF8.GetBytes('{"success":true}')
                Send-HttpResponse -Stream $stream -StatusCode 200 -BodyBytes $respBytes
            } catch {
                $errMsg = $_.Exception.Message -replace '"', '\"'
                Write-Host "[錯誤] 傳送至 TSC 印表機失敗：$($_.Exception.Message)" -ForegroundColor Red
                $respBytes = [System.Text.Encoding]::UTF8.GetBytes("{`"success`":false,`"error`":`"$errMsg`"}")
                Send-HttpResponse -Stream $stream -StatusCode 500 -StatusText "Internal Server Error" -BodyBytes $respBytes
            }
            continue
        }

        # 3. 跨頁表單直印救援 (POST /quick-print，供 HTTPS 頁面突破 Mixed Content)
        if ($req.Method -eq "POST" -and $req.Path -eq "/quick-print") {
            try {
                $payloadEncoded = ""
                if ($req.Body -match '(?:^|&)payload=([^&]*)') {
                    $payloadEncoded = $Matches[1]
                }
                $payloadJson = [System.Uri]::UnescapeDataString($payloadEncoded.Replace('+', ' '))
                $json = $payloadJson | ConvertFrom-Json
                Send-TsplToPrinter -Tspl $json.tspl -Barcode $json.barcode -ProductName $json.productName
                $html = @"
<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSC 列印成功</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f0fdf4;color:#14532d;text-align:center;padding:20px;}
.box{background:#fff;padding:28px 24px;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,0.08);max-width:360px;width:100%;}
.btn{display:inline-block;margin-top:16px;padding:12px 22px;background:#16a34a;color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:bold;text-decoration:none;cursor:pointer;}</style>
</head><body><div class="box"><div style="font-size:48px;">🎉</div><h2>TSC 標籤機已出紙！</h2>
<p>單號：<b>$($json.barcode)</b><br>品名：$($json.productName)</p>
<p style="font-size:13px;color:#64748b;">建議改用本機純內網網址開啟看板，免跳頁更順暢：</p>
<a class="btn" href="/">開啟純內網看板</a>
<button class="btn" style="background:#64748b;margin-left:8px;" onclick="window.close()">關閉視窗</button>
</div></body></html>
"@
                $respBytes = [System.Text.Encoding]::UTF8.GetBytes($html)
                Send-HttpResponse -Stream $stream -StatusCode 200 -ContentType "text/html; charset=utf-8" -BodyBytes $respBytes
            } catch {
                $errMsg = [System.Net.WebUtility]::HtmlEncode($_.Exception.Message)
                Write-Host "[錯誤] 跨頁直印失敗：$($_.Exception.Message)" -ForegroundColor Red
                $html = "<!DOCTYPE html><html lang='zh-TW'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='font-family:sans-serif;padding:30px;text-align:center;color:#991b1b;background:#fef2f2;'><h2>⚠️ 列印失敗</h2><p>$errMsg</p><button onclick='history.back()' style='padding:10px 20px;font-size:16px;'>返回</button></body></html>"
                $respBytes = [System.Text.Encoding]::UTF8.GetBytes($html)
                Send-HttpResponse -Stream $stream -StatusCode 500 -StatusText "Internal Server Error" -ContentType "text/html; charset=utf-8" -BodyBytes $respBytes
            }
            continue
        }

        # 4. 健康檢查 API (GET /status)
        if ($req.Method -eq "GET" -and $req.Path -eq "/status") {
            $respBytes = [System.Text.Encoding]::UTF8.GetBytes("{`"status`":`"running`",`"printer`":`"${printerIp}:${printerPort}`",`"port`":$listenPort}")
            Send-HttpResponse -Stream $stream -StatusCode 200 -BodyBytes $respBytes
            continue
        }

        # 5. 純內網靜態網頁服務 (GET / -> index.html 等)
        if ($req.Method -eq "GET") {
            $relPath = if ($req.Path -eq "/" -or [string]::IsNullOrWhiteSpace($req.Path)) { "index.html" } else { $req.Path.TrimStart('/') }
            $relPath = $relPath -replace '\.\.', '' -replace '/', '\'
            $fullPath = Join-Path $scriptDir $relPath
            if ((Test-Path $fullPath -PathType Leaf) -and $fullPath.StartsWith($scriptDir, [System.StringComparison]::OrdinalIgnoreCase)) {
                $ext = [System.IO.Path]::GetExtension($fullPath).ToLower()
                $ctype = if ($mimeMap.ContainsKey($ext)) { $mimeMap[$ext] } else { 'application/octet-stream' }
                $fileBytes = [System.IO.File]::ReadAllBytes($fullPath)
                Send-HttpResponse -Stream $stream -StatusCode 200 -ContentType $ctype -BodyBytes $fileBytes
            } else {
                $respBytes = [System.Text.Encoding]::UTF8.GetBytes('{"error":"Not Found"}')
                Send-HttpResponse -Stream $stream -StatusCode 404 -StatusText "Not Found" -BodyBytes $respBytes
            }
            continue
        }
    } catch {
        # 忽略單次連線例外
    } finally {
        if ($stream) { try { $stream.Close() } catch {} }
        if ($client) { try { $client.Close() } catch {} }
    }
}
