import sys
import os
import subprocess

py_dir = os.path.dirname(sys.executable)
pyw = os.path.join(py_dir, 'pythonw.exe')
pyw = pyw if os.path.exists(pyw) else sys.executable
script = os.path.abspath('weather_monitor.py')

# schtasks command line with correct quote escaping for the /tr argument
schtasks_cmd = f'schtasks /create /tn "環境溫度監控通報系統" /tr "\\"{pyw}\\" \\"{script}\\"" /sc minute /mo 10 /st 00:00 /ru "SYSTEM" /f'

# Write to a temporary batch file
bat_path = 'scratch/run_register.bat'
os.makedirs('scratch', exist_ok=True)
with open(bat_path, 'w', encoding='utf-8') as f:
    f.write('@echo off\n')
    f.write(schtasks_cmd + '\n')
    f.write('pause\n')

print("Generated batch file at:", bat_path)
print("Running command with elevation...")

# Run the batch file elevated via PowerShell
ps_cmd = 'Start-Process cmd -ArgumentList "/c scratch\\run_register.bat" -Verb RunAs'
subprocess.run(['powershell', '-Command', ps_cmd])
