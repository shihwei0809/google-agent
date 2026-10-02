import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix process_coa logic
po_logic = r'''
                    po_no = ""
                    date_str = ""
                    qty_str = ""
                    matched_row = valid_batches.get(matched_batch)
                    if matched_row:
                        if "po_var" in matched_row:
                            full_po = matched_row["po_var"].get().strip()
                            po_no = full_po[:10] if len(full_po) >= 10 else full_po
                        if "date_var" in matched_row:
                            date_str = matched_row["date_var"].get().strip()
                        if "qty_var" in matched_row:
                            qty_str = matched_row["qty_var"].get().strip()
'''
content = content.replace('                    po_no = ""\n                    matched_row = valid_batches.get(matched_batch)\n                    if matched_row and "po_var" in matched_row:\n                        full_po = matched_row["po_var"].get().strip()\n                        po_no = full_po[:10] if len(full_po) >= 10 else full_po', po_logic)

# Replace ws["B12"] = po_no with the correct mapping for COA
ws_logic = r'''
                            if col_b: ws["B6"] = col_b
                            if col_g: ws["B7"] = col_g
                            if qty_str: ws["B8"] = qty_str
                            if col_c: ws["B11"] = col_c
                            if date_str: ws["B12"] = date_str
                            if po_no: ws["B14"] = po_no
'''
content = content.replace('                            if col_b: ws["B6"] = col_b\n                            if col_g: ws["B7"] = col_g\n                            if col_c: ws["B11"] = col_c\n                            if \'po_no\' in locals() and po_no: ws["B12"] = po_no', ws_logic)

# Replace reader for CSV COA
csv_logic = r'''
                        # 僅針對會修改的行補齊欄位，避免破壞 SchemaName 等標題行結構
                        for r_idx in [5, 6, 7, 10, 11, 13]:
                            while len(reader[r_idx]) <= 1: reader[r_idx].append("")
                            
                        if col_b or col_g or col_c or date_str or po_no or qty_str:
                            if col_b: reader[5][1] = col_b
                            if col_g: reader[6][1] = col_g
                            if qty_str: reader[7][1] = qty_str
                            if col_c: reader[10][1] = col_c
                            if date_str: reader[11][1] = date_str
                            if po_no: reader[13][1] = po_no
'''
content = content.replace('                        # 僅針對會修改的行補齊欄位，避免破壞 SchemaName 等標題行結構\n                        for r_idx in [5, 6, 10, 11]:\n                            while len(reader[r_idx]) <= 1: reader[r_idx].append("")\n                            \n                        if col_b or col_g or col_c:\n                            if col_b: reader[5][1] = col_b\n                            if col_g: reader[6][1] = col_g\n                            if col_c: reader[10][1] = col_c\n                            if \'po_no\' in locals() and po_no: reader[11][1] = po_no', csv_logic)

# Also fix the folder naming in process_coa since tank_str is now qty_str
content = content.replace('tank_str = row["tank_var"].get().strip()\n                    date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date\n                    safe_loc = "".join(c for c in loc_str if c.isalnum() or c in (\' \', \'_\', \'-\')).rstrip()\n                    if not safe_loc: safe_loc = "未命名地點"\n                    loc_sub_dir = f"{date_MMDD} {safe_loc} {tank_str}".strip()',
                          'qty_str = row["qty_var"].get().strip()\n                    date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date\n                    safe_loc = "".join(c for c in loc_str if c.isalnum() or c in (\' \', \'_\', \'-\')).rstrip()\n                    if not safe_loc: safe_loc = "未命名地點"\n                    loc_sub_dir = f"{date_MMDD} {safe_loc}".strip()')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
