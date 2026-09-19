import os
import re
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Remove anything between const deployPsCode (inclusive) and const batShortcutCode (exclusive)
html = re.sub(r'const deployPsCode =.*?const batShortcutCode = ', 'const batShortcutCode = ', html, flags=re.DOTALL)
html = re.sub(r'const deployPsCode =.*?const batShortcutCode = ', 'const batShortcutCode = ', html, flags=re.DOTALL)

# Remove the previously injected zip.file lines
html = html.replace('zip.file("deploy.ps1", deployPsCode);', '')
html = html.replace('zip.file("一鍵自動部署上雲端.bat", deployBatCode);', '')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Cleaned!")
