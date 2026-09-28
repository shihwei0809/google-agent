path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
for i, l in enumerate(lines):
    if 'function renderT100Dropdown' in l:
        with open('dump_t100_2.txt', 'w', encoding='utf-8') as fw:
            fw.write("\n".join(lines[i+30:i+70]))
        break
