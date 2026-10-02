import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('tv=tank_var', 'tv=qty_var')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
