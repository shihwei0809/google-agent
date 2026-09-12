# -*- coding: utf-8 -*-
import codecs
path = r'c:\GOOGLE ANGET\三合一單網頁架機伺服器\server.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()
for i, l in enumerate(lines):
    if 'zip_file.writestr(f"{folder_name}/session.json"' in l:
        lines[i] = '            # ' + l.strip()
        break
with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Removed from server.py')
