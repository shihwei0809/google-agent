import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix Excel extraction
content = re.sub(
    r'batch_idx = loc_idx = date_idx = tank_idx = time_idx = mod_time_idx = -1',
    r'batch_idx = loc_idx = date_idx = tank_idx = time_idx = mod_time_idx = po_idx = -1',
    content
)

content = re.sub(
    r'if mod_time_idx == -1 and "修正" in h_str and \("時間" in h_str or "TIME" in h_str\): mod_time_idx = c_idx',
    r'if mod_time_idx == -1 and "修正" in h_str and ("時間" in h_str or "TIME" in h_str): mod_time_idx = c_idx\n                                if po_idx == -1 and any(k in h_str for k in ["採購單", "PO"]): po_idx = c_idx',
    content
)

content = re.sub(
    r'mt_val = normalize_time_str\(get_val\(mod_time_idx\)\)',
    r'mt_val = normalize_time_str(get_val(mod_time_idx))\n                            po_val = str(get_val(po_idx) or "").strip()',
    content
)

content = re.sub(
    r'"mod_time": mt_val\s*\}\)',
    r'"mod_time": mt_val,\n                                "po": po_val\n                            })',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("PO Excel logic restored!")
