import sys
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('cusqty_val', 'cust_val')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
