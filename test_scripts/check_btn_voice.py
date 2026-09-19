with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

idx = html.find('textContent =')
print(ascii(html[idx:idx+200]))
