path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
import re
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.finditer(r'\$\{.*?loggedInUser.*?\??.*?\}', text)
for m in matches:
    print(m.group(0))
