import re
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# find all <script> contents
scripts = re.findall(r'<script.*?>(.*?)</script>', html, re.DOTALL)
with open(r'C:\GOOGLE ANGET\temp_script.js', 'w', encoding='utf-8') as f:
    f.write(scripts[-1])  # the last one is usually the main logic
