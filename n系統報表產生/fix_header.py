import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix header search logic for qty_col
content = content.replace('["數量", "QTY", "QUANTITY", "AMOUNT", "排程量", "需求量"]',
                          '["數量", "QTY", "QUANTITY", "AMOUNT", "排程量", "需求量", "總重"]')

# Fix fallback logic
fallback_old = '''                        if batch_col == -1 or loc_col == -1:
                            batch_col = 2
                            date_col = 1
                            qty_col = 3
                            loc_col = 4
                            start_row = 2'''

fallback_new = '''                        if batch_col == -1 or loc_col == -1:
                            batch_col = 2
                            date_col = 1
                            qty_col = 4
                            loc_col = 5
                            start_row = 2'''
content = content.replace(fallback_old, fallback_new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
