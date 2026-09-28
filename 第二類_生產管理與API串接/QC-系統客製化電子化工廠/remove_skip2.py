import os
files = [
    r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\1_Web_網頁版\index.html',
    r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\2_PWA_App版\index.html',
    r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
]

import re

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Remove the Skip button
    text = re.sub(r'<button[^>]+id="skipBtn"[^>]*>.*?</button>', '', text)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Removed skip button from all files.")
