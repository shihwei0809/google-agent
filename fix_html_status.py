path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(
    r'(fetch\(`\$\{GAS_API_URL\}\?action=getSamples`\)\s*\n\s*\.then\(res => res\.json\(\)\)\s*\n\s*\.then\(data => \{\s*\n)',
    r'\1          // 相容舊版中文狀態\n          data.forEach(s => {\n            if (s.status === "待檢驗") s.status = "pending";\n            else if (s.status === "已檢驗") s.status = "completed";\n            else if (s.status === "退件" || s.status === "重取樣") s.status = "failed";\n          });\n',
    text
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
