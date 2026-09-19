import os

dir1 = r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\C50110-INV-02_進出貨作業管理辦法_教材"
dir2 = r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\C50110-INV-02-01_儲槽進出貨作業方法_教材"

def fix_html(d):
    path = os.path.join(d, 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Fix the JS escapes
    html = html.replace('\\', '')
    html = html.replace('\\$', '$')
    html = html.replace('\\\\', '\\')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Fixed {path}")

fix_html(dir1)
fix_html(dir2)
