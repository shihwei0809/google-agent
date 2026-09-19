import os

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\generator_core.js'

with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('if (provider === "gemini")')
print(ascii(js[idx-100:idx+300]))
