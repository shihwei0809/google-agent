path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
for i, l in enumerate(lines):
    if 'function onT100SelectChange()' in l or 'function onT100Change()' in l or 'function handleT100Selection' in l or 'onchange="onT100SelectChange' in l or 'document.getElementById(\'t100Select\').addEventListener' in l:
        print(l)
