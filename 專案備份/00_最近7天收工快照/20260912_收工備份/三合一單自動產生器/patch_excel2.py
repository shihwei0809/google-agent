import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Initialize po_col
content = re.sub(
    r'mod_time_col = -1\s*cust_col = -1\s*start_row = 0',
    r'mod_time_col = -1\n                        cust_col = -1\n                        po_col = -1\n                        start_row = 0',
    content
)

# 2. Extract po_col index
content = re.sub(
    r'if mod_time_col == -1 and "修正" in v and \("時間" in v or "TIME" in v\): mod_time_col = c_idx',
    r'if mod_time_col == -1 and "修正" in v and ("時間" in v or "TIME" in v): mod_time_col = c_idx\n                                if po_col == -1 and any(k in v for k in ["採購單", "PO"]): po_col = c_idx',
    content
)

# 3. Get po_val
content = re.sub(
    r'mt_val = normalize_time_str\(get_cell_val\(mod_time_col\)\)\s*cust_val = str\(get_cell_val\(cust_col\) or ""\)\.strip\(\)',
    r'mt_val = normalize_time_str(get_cell_val(mod_time_col))\n                            po_val = str(get_cell_val(po_col) or "").strip()\n                            cust_val = str(get_cell_val(cust_col) or "").strip()',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Excel extraction patched.")
