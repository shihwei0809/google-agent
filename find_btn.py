import re
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

lines = html.split('\n')
for i, line in enumerate(lines):
    if 'btn-voice' in line and 'textContent' in line:
        print(f"Line {i+1}: {repr(line)}")
