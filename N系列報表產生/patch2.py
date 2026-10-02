import os

filepath = r"d:\GOOGLE ANGET\N系列報表產生\生產履歷與COA_系統\main.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('台積電槽車 Barcode 三合一單與運輸通知表', '生產履歷與COA 批次處理系統 (本地直出)')
content = content.replace('title_label.config(text="🌐 台積電槽車 Barcode 三合一單與運輸通知表 (架機專用伺服器)")', 'title_label.config(text="🌐 生產履歷與COA 批次處理系統 (本地直出)")')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Title patched.")
