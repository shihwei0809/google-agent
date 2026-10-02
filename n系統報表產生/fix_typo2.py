import sys
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('len(t_val)', 'len(qty_val)')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
