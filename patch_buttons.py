# -*- coding: utf-8 -*-
import codecs
import re
path = r'c:\GOOGLE ANGET\勝一三合一單產生系統\main.py'
content = codecs.open(path, 'r', 'utf-8').read()
buttons = re.findall(r'text=[\'"]([^\'"]*)[\'"]', content)
with open('c:/GOOGLE ANGET/out17.txt', 'w', encoding='utf-8') as f:
    for b in buttons:
        f.write(b + '\n')
