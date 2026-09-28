path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
out = []
for i, l in enumerate(lines):
    if 'loggedInUser' in l:
        out.append(f"Line {i+1}: {l.strip()}")
with open('dump_loggedin.txt', 'w', encoding='utf-8') as fw:
    fw.write('\n'.join(out))
