path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '.bind(status, result, note, approver, id).run();',
    '.bind(status||null, result||null, note||null, approver||null, id||null).run();'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
