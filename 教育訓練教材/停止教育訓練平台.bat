@echo off
chcp 65001 >nul
title Stop Platform
color 0C
echo Stopping services...
powershell -NoProfile -Command "$ports = @(8000, 5173, 5174); foreach ($p in $ports) { $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; if ($conns) { foreach ($c in $conns) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } } }"
echo Done! All services stopped.
ping -n 3 127.0.0.1 >nul
