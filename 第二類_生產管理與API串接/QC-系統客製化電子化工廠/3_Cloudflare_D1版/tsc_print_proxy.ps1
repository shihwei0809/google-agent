$printerIp = '192.168.3.128'
$printerPort = 9100
$listenPort = 8099

# 取得本機 IP
$localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.254*' } | Select-Object -First 1).IPAddress
if (-not $localIp) { $localIp = 'localhost' }

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   鴻勝化學 QC 看板 - TSC 標籤機行動列印代理服務" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[資訊] 目標 TSC 印表機 IP : $printerIp (Port: $printerPort)" -ForegroundColor Gray
Write-Host "[資訊] 預設標籤貼紙規格    : 90mm x 60mm (Label with Gap)" -ForegroundColor Gray
Write-Host "[監聽] 列印代理服務位址   : http://${localIp}:${listenPort}/" -ForegroundColor Green
Write-Host "[說明] 手機/iPad 在看板填入此電腦 IP ($localIp)，即可一鍵出紙！" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

try {
    $tcpListener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $listenPort)
    $tcpListener.Start()
    Write-Host "[SUCCESS] 服務已成功於 Port $listenPort 啟動 (無需系統管理員權限)！" -ForegroundColor Green
    Write-Host "請保持此視窗開啟 (縮小即可，請勿關閉)...`n" -ForegroundColor Green
} catch {
    Write-Host "[錯誤] 無法啟動 Port $listenPort：$($_.Exception.Message)" -ForegroundColor Red
    Read-Host "請按 Enter 鍵結束..."
    exit
}

while ($true) {
    try {
        $client = $tcpListener.AcceptTcpClient()
        $stream = $client.GetStream()
        $buffer = New-Object byte[] 65536
        $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
        if ($bytesRead -gt 0) {
            $rawRequest = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)

            # 處理 CORS 預檢請求 OPTIONS
            if ($rawRequest.StartsWith("OPTIONS")) {
                $responseStr = "HTTP/1.1 200 OK`r`nAccess-Control-Allow-Origin: *`r`nAccess-Control-Allow-Methods: GET, POST, OPTIONS`r`nAccess-Control-Allow-Headers: Content-Type`r`nContent-Length: 0`r`n`r`n"
                $respBytes = [System.Text.Encoding]::ASCII.GetBytes($responseStr)
                $stream.Write($respBytes, 0, $respBytes.Length)
                $stream.Close()
                $client.Close()
                continue
            }

            # 解析 HTTP 內文 JSON
            $bodyIdx = $rawRequest.IndexOf("`r`n`r`n")
            if ($bodyIdx -ge 0) {
                $body = $rawRequest.Substring($bodyIdx + 4)
            } else {
                $body = ""
            }

            if ($rawRequest.StartsWith("POST") -and $body) {
                try {
                    $json = $body | ConvertFrom-Json
                    $tspl = $json.tspl
                    $timeStr = Get-Date -Format 'HH:mm:ss'
                    Write-Host "[$timeStr] 收到列印請求：單號 $($json.barcode) ($($json.productName))" -ForegroundColor Cyan

                    # 傳送 TSPL 至 TSC 印表機 (Port 9100)
                    $printerClient = New-Object System.Net.Sockets.TcpClient
                    $printerClient.Connect($printerIp, $printerPort)
                    $pStream = $printerClient.GetStream()
                    $tsplBytes = [System.Text.Encoding]::GetEncoding('big5').GetBytes($tspl)
                    $pStream.Write($tsplBytes, 0, $tsplBytes.Length)
                    $pStream.Flush()
                    $printerClient.Close()

                    Write-Host "[$timeStr] [OK] 90x60mm 標籤已成功傳送至 TSC 印表機！`n" -ForegroundColor Green

                    $jsonResp = '{"success":true}'
                    $jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonResp)
                    $headerStr = "HTTP/1.1 200 OK`r`nAccess-Control-Allow-Origin: *`r`nContent-Type: application/json`r`nContent-Length: $($jsonBytes.Length)`r`n`r`n"
                    $headBytes = [System.Text.Encoding]::ASCII.GetBytes($headerStr)
                    $stream.Write($headBytes, 0, $headBytes.Length)
                    $stream.Write($jsonBytes, 0, $jsonBytes.Length)
                } catch {
                    Write-Host "[錯誤] 傳送至 TSC 印表機失敗：$($_.Exception.Message)" -ForegroundColor Red
                    $jsonResp = "{`"success`":false,`"error`":`"$($_.Exception.Message)`"}"
                    $jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonResp)
                    $headerStr = "HTTP/1.1 500 Internal Error`r`nAccess-Control-Allow-Origin: *`r`nContent-Type: application/json`r`nContent-Length: $($jsonBytes.Length)`r`n`r`n"
                    $headBytes = [System.Text.Encoding]::ASCII.GetBytes($headerStr)
                    $stream.Write($headBytes, 0, $headBytes.Length)
                    $stream.Write($jsonBytes, 0, $jsonBytes.Length)
                }
            } else {
                $jsonResp = "{`"status`":`"running`",`"printer`":`"${printerIp}:${printerPort}`"}"
                $jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonResp)
                $headerStr = "HTTP/1.1 200 OK`r`nAccess-Control-Allow-Origin: *`r`nContent-Type: application/json`r`nContent-Length: $($jsonBytes.Length)`r`n`r`n"
                $headBytes = [System.Text.Encoding]::ASCII.GetBytes($headerStr)
                $stream.Write($headBytes, 0, $headBytes.Length)
                $stream.Write($jsonBytes, 0, $jsonBytes.Length)
            }
        }
        $stream.Close()
        $client.Close()
    } catch {
        # 忽略單次連線例外
    }
}
