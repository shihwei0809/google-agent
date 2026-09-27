path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(
    r'if \(confirm\(發現此車次 \(\) 共有  筆排程單號：\\n\\n\\n是否要自動合併成同一張檢驗單？\)\) \{',
    'if (confirm(`發現此車次 (${item.container}) 共有 ${extraDocs.length + 1} 筆排程單號：\\n${combined}\\n\\n是否要自動合併成同一張檢驗單？`)) {',
    text
)
# Fix the broken one if it was broken across lines
text = re.sub(
    r'if \(confirm\(.*自動合併成同一張檢驗單.*\{',
    'if (confirm(`發現此車次 (${item.container}) 共有 ${extraDocs.length + 1} 筆排程單號：\\n${combined}\\n\\n是否要自動合併成同一張檢驗單？`)) {',
    text
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
