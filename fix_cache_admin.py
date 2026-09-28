path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("fetch(API + '?action=getConfig', { cache: 'no-store' })", "fetch(API + '?action=getConfig&_t=' + Date.now(), { cache: 'no-store' })")
text = text.replace("fetch(API + '?action=getAccounts', { cache: 'no-store' })", "fetch(API + '?action=getAccounts&_t=' + Date.now(), { cache: 'no-store' })")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
