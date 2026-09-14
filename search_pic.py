import re
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8') as f:
    html = f.read()
for line in html.split('\n'):
    if '圖片關鍵字' in line or '圖片' in line:
        print(line.strip())
