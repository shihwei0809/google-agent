import re

path = r'C:\GOOGLE ANGET\第二類_生産管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix status assignment line
text = re.sub(
    r'result === "FAIL" \|\| result === "[^"]{0,20}"\) status = "failed";',
    'result === "FAIL" || result === "需特採") status = "failed";',
    text
)

# Fix finalNote block
text = re.sub(
    r"result === '.' && sample\.qcResult === '.'",
    "result === '特採' && sample.qcResult === '需特採'",
    text
)

# Fix garbled comment
text = re.sub(r'// [\x80-\xff?\ue000-\uf8ff]{2,}Teams', '// 取得原本樣品資訊，為了發送 Teams', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Done')
