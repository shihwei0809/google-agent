@echo off
schtasks /create /tn "環境溫度監控通報系統" /tr "\"C:\Python313\pythonw.exe\" \"D:\GOOGLE ANGET\溫度通報\weather_monitor.py\"" /sc minute /mo 10 /st 00:00 /ru "SYSTEM" /f
pause
