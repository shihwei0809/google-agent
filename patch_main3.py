# -*- coding: utf-8 -*-
import codecs
path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
content = codecs.open(path, 'r', 'utf-8').read()
content = content.replace('lorry_out_name = f"Chemical_Lorry_{new_base}{ext}"', 'lorry_out_name = f"Chemical_Lorry_{new_base}.xlsx"')
with codecs.open(path, 'w', 'utf-8') as f:
    f.write(content)
print('Fixed lorry extension')
