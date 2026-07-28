# 🚀 ISO Tank 廠區平面配置系統環境一鍵啟動腳本 (setup_env.ps1)

$ErrorActionPreference = "Stop"

Write-Host "🎨 正在初始化 ISO Tank 45,633 m² 廠區平面配置系統環境..." -ForegroundColor Cyan

# 抓取本機 IP
function Get-LocalIP {
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*", "Ethernet*" -ErrorAction SilentlyContinue | Where-Host IPAddress -notlike "169.254*").IPAddress | Select-Object -First 1
        if (-not $ip) { $ip = "127.0.0.1" }
        return $ip
    } catch {
        return "127.0.0.1"
    }
}

# 尋找可用 Port
function Find-AvailablePort ([int]$startPort) {
    $port = $startPort
    while ($port -lt ($startPort + 50)) {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $port)
        try {
            $listener.Start()
            $listener.Stop()
            return $port
        } catch {
            $port++
        }
    }
    return $startPort
}

$defaultPort = 8085
$port = Find-AvailablePort -startPort $defaultPort
$localIP = Get-LocalIP

if ($port -ne $defaultPort) {
    Write-Host "⚠️ 預設 Port $defaultPort 已被佔用，已自動切換至可用 Port: $port" -ForegroundColor Yellow
}

Write-Host "--------------------------------------------------------" -ForegroundColor Green
Write-Host "🚀 ISO Tank 廠區平面配置系統啟動中..." -ForegroundColor Green
Write-Host "🌐 本機網址: http://localhost:$port" -ForegroundColor Cyan
Write-Host "📡 區網網址: http://${localIP}:$port" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor Green

python -m http.server $port --bind 0.0.0.0
