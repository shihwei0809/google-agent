import re
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'(?s)<script>(.*?)</script>', html)
with open(r'C:\GOOGLE ANGET\temp_script.js', 'w', encoding='utf-8') as f:
    f.write(scripts[-1])
