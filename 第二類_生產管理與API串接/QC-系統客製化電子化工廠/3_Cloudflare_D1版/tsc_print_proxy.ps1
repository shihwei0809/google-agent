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
Write-Host "服務已就緒，請保持此視窗開啟 (縮小即可，請勿關閉)...`n" -ForegroundColor Green

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:$listenPort/")

try {
    $listener.Start()
} catch {
    # 若無管理員權限無法綁定 +，改綁 localhost 與本機 IP
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$listenPort/")
    $listener.Prefixes.Add("http://${localIp}:$listenPort/")
    try {
        $listener.Start()
    } catch {
        Write-Host "[錯誤] 無法啟動 HTTP 監聽服務：$($_.Exception.Message)" -ForegroundColor Red
        Write-Host "提示：請嘗試『以系統管理員身分執行』此批次檔。" -ForegroundColor Yellow
        Read-Host "請按 Enter 鍵結束..."
        exit
    }
}

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $req = $context.Request
        $res = $context.Response

        $res.Headers.Add('Access-Control-Allow-Origin', '*')
        $res.Headers.Add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        $res.Headers.Add('Access-Control-Allow-Headers', 'Content-Type')

        if ($req.HttpMethod -eq 'OPTIONS') {
            $res.StatusCode = 200
            $res.Close()
            continue
        }

        if ($req.HttpMethod -eq 'POST' -and $req.Url.AbsolutePath -eq '/print') {
            $reader = New-Object System.IO.StreamReader($req.InputStream, [System.Text.Encoding]::UTF8)
            $body = $reader.ReadToEnd()
            try {
                $json = $body | ConvertFrom-Json
                $tspl = $json.tspl
                $timeStr = Get-Date -Format 'HH:mm:ss'
                Write-Host "[$timeStr] 收到列印請求：單號 $($json.barcode) ($($json.productName))" -ForegroundColor Cyan

                $client = New-Object System.Net.Sockets.TcpClient
                $client.Connect($printerIp, $printerPort)
                $stream = $client.GetStream()
                $bytes = [System.Text.Encoding]::GetEncoding('big5').GetBytes($tspl)
                $stream.Write($bytes, 0, $bytes.Length)
                $stream.Flush()
                $client.Close()

                Write-Host "[$timeStr] [OK] 90x60mm 標籤已成功傳送至 TSC 印表機！`n" -ForegroundColor Green

                $msg = '{"success":true}'
                $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg)
                $res.ContentType = 'application/json'
                $res.OutputStream.Write($resBytes, 0, $resBytes.Length)
            } catch {
                Write-Host "[錯誤] 傳送至 TSC 印表機失敗：$($_.Exception.Message)" -ForegroundColor Red
                $msg = "{`"success`":false,`"error`":`"$($_.Exception.Message)`"}"
                $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg)
                $res.StatusCode = 500
                $res.OutputStream.Write($resBytes, 0, $resBytes.Length)
            }
        } else {
            $msg = "{`"status`":`"running`",`"printer`":`"${printerIp}:${printerPort}`"}"
            $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg)
            $res.ContentType = 'application/json'
            $res.OutputStream.Write($resBytes, 0, $resBytes.Length)
        }
        $res.Close()
    } catch {
        # 忽略單次連線異常以保持常駐
    }
}
