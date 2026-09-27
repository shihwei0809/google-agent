path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'env\.DB\.prepare\(CREATE TABLE(.*?)\)', r'env.DB.prepare("CREATE TABLE\1")', text)
text = re.sub(r'env\.DB\.prepare\(DELETE FROM(.*?)\)', r'env.DB.prepare("DELETE FROM\1")', text)
text = re.sub(r'env\.DB\.prepare\(INSERT INTO(.*?)\)', r'env.DB.prepare("INSERT INTO\1")', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
