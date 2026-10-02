import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('batch_col, date_col, qty_col, loc_col = 2, 1, 3, 4', 'batch_col, date_col, qty_col, loc_col = 2, 1, 4, 5')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
