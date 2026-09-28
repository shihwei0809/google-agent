path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<input type="hidden" id="currentId">', '<input type="hidden" id="currentId">\n    <div id="judgeApproverText" style="font-weight:bold; color:#2563eb; margin-bottom:15px; background:#eff6ff; padding:8px; border-radius:6px;"></div>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
