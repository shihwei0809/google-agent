import sys, re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the col_b, col_g, col_c extraction in process_coa
# The current code looks like:
#                    col_b, col_g, col_c = "", "", ""
#                    if matched_batch in lorry_data_map:
#                        l_info = lorry_data_map[matched_batch]
#                        col_b = l_info.get("b", "")
#                        col_c = l_info.get("c", "")
#                        col_g = l_info.get("g", "")

# We want to replace it to also extract from matched_row.

new_code = '''
                    col_b, col_g, col_c = "", "", ""
                    if matched_batch in lorry_data_map:
                        l_info = lorry_data_map[matched_batch]
                        col_b = l_info.get("b", "")
                        col_c = l_info.get("c", "")
                        col_g = l_info.get("g", "")
                    
                    # 優先使用介面 (出貨表) 的資料
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
                        if "mfg_var" in matched_row:
                            col_c = matched_row["mfg_var"].get().strip() or col_c
                        
                        long_code = matched_row.get("long_code_var", type("X", (), {"get": lambda: ""})()).get().strip()
                        loc_str = matched_row.get("loc_var", type("X", (), {"get": lambda: ""})()).get().strip()
                        
                        if long_code or loc_str:
                            col_g = long_code or loc_str  # FabPhase
                            # col_b = loc_str # (Optional) TSMCFab
'''

old_code = '''
                    col_b, col_g, col_c = "", "", ""
                    if matched_batch in lorry_data_map:
                        l_info = lorry_data_map[matched_batch]
                        col_b = l_info.get("b", "")
                        col_c = l_info.get("c", "")
                        col_g = l_info.get("g", "")
                        
                    # 找出排程中的採購單號前 10 碼

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

content = content.replace(old_code.strip(), new_code.strip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
