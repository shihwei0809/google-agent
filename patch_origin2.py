path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
import re

with open(path, encoding='utf-8') as f:
    content = f.read()

# 1. Update CSV init
csv_init_old = r'batch_col, loc_col, date_col, tank_col, time_col, mod_time_col, po_col = -1, -1, -1, -1, -1, -1, -1'
csv_init_new = r'batch_col, loc_col, date_col, tank_col, time_col, mod_time_col, po_col, origin_col = -1, -1, -1, -1, -1, -1, -1, -1'
content = content.replace(csv_init_old, csv_init_new)

# 2. Update CSV loop
content = re.sub(
    r'(if po_col == -1 and any\(k in v for k in \[".*?", "PO"\]\): po_col = c_idx)',
    r'\1\n                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx',
    content
)

# 3. Update CSV extraction
csv_ext_old = r'''                            origin_val = ""
                            for cell in row:
                                cs = str(cell or "").strip().upper()
                                if not origin_val and any(k in cs for k in ["崙尾", "彰濱", "L1", "L2"]):
                                    origin_val = cs
                                    break'''
csv_ext_new = r'''                            origin_val = str(get_c(origin_col) or "").strip()'''
content = content.replace(csv_ext_old, csv_ext_new)

# 4. Update XLSX init
xlsx_init_old = r'''                        po_col = -1
                        start_row = 0'''
xlsx_init_new = r'''                        po_col = -1
                        origin_col = -1
                        start_row = 0'''
content = content.replace(xlsx_init_old, xlsx_init_new)

# 5. Update XLSX loop
content = re.sub(
    r'(if cust_col == -1 and any\(k in v for k in \[.*?\]\): cust_col = c_idx)',
    r'\1\n                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx',
    content
)


# 6. Update XLSX extraction
xlsx_ext_old = r'''                            origin_val = ""
                            for cell in row:
                                cs = str(cell or "").strip().upper()
                                if not origin_val and any(k in cs for k in ["崙尾", "彰濱", "L1", "L2"]):
                                    origin_val = cs
                                    break'''
xlsx_ext_new = r'''                            origin_val = str(get_cell_val(origin_col) or "").strip()'''
content = content.replace(xlsx_ext_old, xlsx_ext_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
