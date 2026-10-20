Stop-Service chromoting -Force -ErrorAction SilentlyContinue
$exe = "C:\Program Files (x86)\Google\Chrome Remote Desktop\154.0.8037.40\remoting_host.exe"
$cfg = "C:\ProgramData\Google\Chrome Remote Desktop\host.json"
$log = "d:\GOOGLE ANGET\crd_console.log"

$p = Start-Process -FilePath $exe -ArgumentList "--console", "--host-config=$cfg" -RedirectStandardOutput $log -RedirectStandardError "d:\GOOGLE ANGET\crd_err.log" -PassThru
Start-Sleep -Seconds 12
if (!$p.HasExited) {
    Stop-Process -Id $p.Id -Force
}
Start-Service chromoting
