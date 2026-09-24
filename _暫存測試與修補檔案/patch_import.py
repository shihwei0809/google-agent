path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'

with open(path, encoding='utf-8') as f:
    content = f.read()

import re

# Fix the bug I introduced in import_from_excel where it tries to read "part_var" from `row` which is a list
buggy_part_no = r'"part_no": row\["part_var"\].get\(\).strip\(\) if "part_var" in row else ""'
content = re.sub(buggy_part_no, '""', content)

# 1. CSV part
csv_row_scan = r'''                            t_val = str(get_c(tank_col) or "").strip()
                            origin_val = ""
                            for cell in row:
                                cs = str(cell or "").strip().upper()
                                if not origin_val and any(k in cs for k in ["崙尾", "彰濱", "L1", "L2"]):
                                    origin_val = cs
                                    break'''
content = content.replace('                            t_val = str(get_c(tank_col) or "").strip()', csv_row_scan)

# 2. XLSX part
xlsx_row_scan = r'''                            time_val = normalize_time_str(get_cell_val(time_col))
                            origin_val = ""
                            for cell in row:
                                cs = str(cell or "").strip().upper()
                                if not origin_val and any(k in cs for k in ["崙尾", "彰濱", "L1", "L2"]):
                                    origin_val = cs
                                    break'''
content = content.replace('                            time_val = normalize_time_str(get_cell_val(time_col))', xlsx_row_scan)

# 3. Add origin to records
content = content.replace('"po": po_val,', '"po": po_val,\n                                "origin": origin_val,')

# 4. In `import_from_excel` when filling UI entries:
# row_e["loc_var"].set(rec.get("loc", ""))
ui_fill_repl = r'''row_e["loc_var"].set(rec.get("loc", ""))
                    if rec.get("origin"):
                        row_e["origin_var"].set(rec["origin"])'''
content = content.replace('row_e["loc_var"].set(rec.get("loc", ""))', ui_fill_repl)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
