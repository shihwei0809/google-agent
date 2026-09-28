path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
for i, l in enumerate(lines):
    if 'id="tab-grades" class="tab-content"' in l:
        out = "\n".join(lines[i:i+20])
        with open("dump_end.txt", "w", encoding="utf-8") as fw:
            fw.write(out)
        break
