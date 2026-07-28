$pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pyw) {
    $pyw = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $pyw) {
    Write-Error "找不到 pythonw 或 python 執行檔，請確認已安裝 Python！"
    Exit
}

$script = (Resolve-Path weather_monitor.py).Path

# schtasks command
$schtasksCmd = "schtasks /create /tn `"環境溫度監控通報系統`" /tr `"\`"$pyw\`" \`"$script\`"`" /sc minute /mo 10 /st 00:00 /ru `"SYSTEM`" /f"

Write-Host "正在以管理員權限執行以下指令："
Write-Host $schtasksCmd
Start-Process cmd -ArgumentList "/c $schtasksCmd" -Verb RunAs
