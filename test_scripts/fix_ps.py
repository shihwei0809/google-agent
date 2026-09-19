
import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()
idx1 = html.find('\nconst deployPsCode = \Continue = ')
idx2 = html.find('const batShortcutCode = ')
if idx1 != -1:
    html = html[:idx1] + html[idx2:]
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
