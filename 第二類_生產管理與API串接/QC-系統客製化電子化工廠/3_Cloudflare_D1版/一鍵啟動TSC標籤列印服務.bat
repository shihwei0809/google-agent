@echo off
chcp 65001 >nul
title 鴻勝化學 - TSC 網路標籤機 (192.168.3.128) 行動列印代理服務
color 0b

echo ========================================================
echo   鴻勝化學 QC 看板 - TSC 標籤機行動列印代理服務
echo ========================================================
echo.
echo [資訊] 目標 TSC 印表機 IP : 192.168.3.128 (Port: 9100)
echo [資訊] 預設標籤貼紙規格    : 90mm x 60mm (Label with Gap)
echo.

:: 取得本機 IP 位址供手機與看板連線
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" /c:"IP 位址"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%
echo [監聽] 列印代理服務位址   : http://%LOCAL_IP%:8099/
echo [說明] 手機/iPad 在看板點擊「列印」時，本服務會秒速將 TSPL 丟給 TSC！
echo.
echo ========================================================
echo 服務啟動中，請保持此視窗開啟 (縮小即可，請勿關閉)...
echo ========================================================
echo.

:: 使用 Windows 內建 PowerShell HttpListener，免裝任何 Python/Node.js！
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$printerIp = '192.168.3.128';" ^
"$printerPort = 9100;" ^
"$listenPort = 8099;" ^
"$listener = New-Object System.Net.HttpListener;" ^
"$listener.Prefixes.Add(\"http://*:$listenPort/\");" ^
"try { $listener.Start(); } catch { Write-Host \"[錯誤] 無法監聽 Port $listenPort，請確認是否被佔用或以系統管理員權限執行。\" -ForegroundColor Red; exit; }" ^
"Write-Host \"[SUCCESS] 列印服務已於 Port $listenPort 就緒！等待手機列印請求...\" -ForegroundColor Green;" ^
"while ($listener.IsListening) {" ^
"    $context = $listener.GetContext();" ^
"    $req = $context.Request;" ^
"    $res = $context.Response;" ^
"    $res.Headers.Add('Access-Control-Allow-Origin', '*');" ^
"    $res.Headers.Add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');" ^
"    $res.Headers.Add('Access-Control-Allow-Headers', 'Content-Type');" ^
"    if ($req.HttpMethod -eq 'OPTIONS') { $res.StatusCode = 200; $res.Close(); continue; }" ^
"    if ($req.HttpMethod -eq 'POST' -and $req.Url.AbsolutePath -eq '/print') {" ^
"        $reader = New-Object System.IO.StreamReader($req.InputStream, [System.Text.Encoding]::UTF8);" ^
"        $body = $reader.ReadToEnd();" ^
"        try {" ^
"            $json = $body | ConvertFrom-Json;" ^
"            $tspl = $json.tspl;" ^
"            Write-Host \"[$(Get-Date -Format 'HH:mm:ss')] 收到列印請求：單號 $($json.barcode) ($($json.productName))\" -ForegroundColor Cyan;" ^
"            $client = New-Object System.Net.Sockets.TcpClient;" ^
"            $client.Connect($printerIp, $printerPort);" ^
"            $stream = $client.GetStream();" ^
"            $bytes = [System.Text.Encoding]::GetEncoding('big5').GetBytes($tspl);" ^
"            $stream.Write($bytes, 0, $bytes.Length);" ^
"            $stream.Flush();" ^
"            $client.Close();" ^
"            Write-Host \"[$(Get-Date -Format 'HH:mm:ss')] [OK] 90x60mm 標籤已成功傳送至 TSC 印表機！\" -ForegroundColor Green;" ^
"            $msg = '{\"success\":true}';" ^
"            $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg);" ^
"            $res.ContentType = 'application/json';" ^
"            $res.OutputStream.Write($resBytes, 0, $resBytes.Length);" ^
"        } catch {" ^
"            Write-Host \"[錯誤] 傳送至印表機失敗：$($_.Exception.Message)\" -ForegroundColor Red;" ^
"            $msg = \"{\\\"success\\\":false,\\\"error\\\":\\\"$($_.Exception.Message)\\\"};\";" ^
"            $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg);" ^
"            $res.StatusCode = 500;" ^
"            $res.OutputStream.Write($resBytes, 0, $resBytes.Length);" ^
"        }" ^
"    } else {" ^
"        $msg = '{\"status\":\"running\",\"printer\":\"192.168.3.128:9100\"}';" ^
"        $resBytes = [System.Text.Encoding]::UTF8.GetBytes($msg);" ^
"        $res.ContentType = 'application/json';" ^
"        $res.OutputStream.Write($resBytes, 0, $resBytes.Length);" ^
"    }" ^
"    $res.Close();" ^
"}"

pause
