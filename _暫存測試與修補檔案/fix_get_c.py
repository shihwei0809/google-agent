path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# We need to change the SECOND occurrence of get_c(origin_col) to get_cell_val(origin_col)
occurrences = text.split('origin_val = str(get_c(origin_col) or "").strip()')
if len(occurrences) > 2:
    new_text = occurrences[0] + 'origin_val = str(get_c(origin_col) or "").strip()' + occurrences[1] + 'origin_val = str(get_cell_val(origin_col) or "").strip()' + occurrences[2]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
