import os
path = r'第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for i, l in enumerate(lines):
    if 'class="tabs"' in l:
        with open('dump.txt', 'w', encoding='utf-8') as fw:
            fw.write("\n".join(lines[i:i+10]))
        break
