path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_if = "if (result.success && Array.isArray(result.orders) && result.orders.length > 0) {"
new_if = "if (result.success && Array.isArray(result.orders)) {"

text = text.replace(old_if, new_if)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
