path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_line = "const matchDoc = allData.find(s => s.barcode && String(s.barcode).trim().toLowerCase() === targetDoc);"
new_line = "const matchDoc = allData.find(s => s.barcode && String(s.barcode).toLowerCase().includes(targetDoc));"

text = text.replace(old_line, new_line)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
