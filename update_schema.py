path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\schema.sql'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'(round INTEGER DEFAULT 1)', r'\1,\n    remark TEXT', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
