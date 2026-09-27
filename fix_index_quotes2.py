path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Fix CREATE TABLE
text = re.sub(r'await env\.DB\.prepare\("CREATE TABLE(.*?)"\)\)', r'await env.DB.prepare("CREATE TABLE\1)")', text)

# Fix INSERT INTO
text = re.sub(r'await env\.DB\.prepare\("INSERT INTO(.*?)"\) VALUES', r'await env.DB.prepare("INSERT INTO\1) VALUES', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
