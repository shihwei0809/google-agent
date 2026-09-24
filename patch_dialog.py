path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Update columns list
text = text.replace(
    'columns = ("chk", "idx", "sheet", "date", "time", "batch", "tank", "loc", "long_code")',
    'columns = ("chk", "idx", "sheet", "date", "time", "batch", "tank", "origin", "loc", "long_code")'
)

# Update col_defs
col_defs_old = r'''        col_defs = \[
            \("chk", ".*?", 50, "center"\),
            \("idx", ".*?", 50, "center"\),
            \("sheet", ".*?", 150, "w"\),
            \("date", ".*?", 105, "center"\),
            \("time", ".*?", 85, "center"\),
            \("batch", ".*?", 125, "center"\),
            \("tank", ".*?", 75, "center"\),
            \("loc", ".*?", 95, "center"\),
            \("long_code", ".*?", 250, "w"\)
        \]'''

m = re.search(col_defs_old, text, re.DOTALL)
if m:
    col_defs_new = m.group(0).replace('("loc",', '("origin", "出貨區", 85, "center"),\n            ("loc",')
    text = text.replace(m.group(0), col_defs_new)
else:
    print('col_defs NOT FOUND')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
