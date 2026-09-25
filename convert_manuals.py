import os
import re

md_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\SOP操作說明書.md'
html_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\SOP操作說明書.html'
txt_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\SOP操作說明書.txt'

with open(md_path, 'r', encoding='utf-8') as f:
    md_text = f.read()

# Make a rough text version by removing markdown symbols
txt_text = re.sub(r'\*\*(.*?)\*\*', r'\1', md_text)
txt_text = re.sub(r'(.*?)', r'\1', txt_text)
txt_text = re.sub(r'#+\s', '', txt_text)
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(txt_text)

# Make a rough HTML version
html_text = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SOP 操作說明書</title>
    <style>body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; }}</style>
</head>
<body>
    <pre style="white-space: pre-wrap; font-family: inherit;">{txt_text}</pre>
</body>
</html>'''

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_text)

print("Regenerated txt and html manuals.")
