path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
out = []
for i, l in enumerate(lines):
    if 'function dispatchTeamsCard' in l:
        out = lines[i:i+40]
        break
with open("dump_teams.txt", 'w', encoding='utf-8') as f:
    f.write("\n".join(out))
