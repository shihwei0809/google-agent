# -*- coding: utf-8 -*-
with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '? \t' in line and 'ransform: rotate' in line:
        # It's broken! Replace '? \transform...' with '? 	ransform...'
        lines[i] = line.replace('? \t', '? 	').replace(';', ';')

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
