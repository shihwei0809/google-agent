import re
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

body_start = html.find('<body>')
body_content = html[body_start:body_start+500]
print(ascii(body_content))
