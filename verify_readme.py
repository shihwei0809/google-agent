import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

if 'Cloudflare 雙軌架構' in html:
    print("Successfully updated index.html with Cloudflare section!")
else:
    print("Failed to find replacement target!")
