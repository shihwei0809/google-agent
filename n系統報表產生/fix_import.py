import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tank with qty in parsing logic
content = content.replace('tank_col', 'qty_col')
content = content.replace('if qty_col == -1 and any(k in v for k in ["槽號", "槽車", "TANK"]) and not any(k in v for k in ["日", "期", "時間", "TIME", "DATE", "到廠", "出車", "出貨"]): qty_col = c_idx',
                          'if qty_col == -1 and any(k in v for k in ["數量", "QTY", "QUANTITY", "AMOUNT", "排程量", "需求量"]): qty_col = c_idx')

content = content.replace('t_val = str(get_c(qty_col) or "").strip()', 'qty_val = str(get_c(qty_col) or "").strip()')
content = content.replace('t_val = str(get_cell_val(qty_col) or "").strip()', 'qty_val = str(get_cell_val(qty_col) or "").strip()')

# Then it uses t_val to do tank validation. For QTY we don't need tank validation.
remove_tank_valid_logic = r'''
                            if len(b_val) == 10 and re.search(r'[0-9]', b_val):
                                is_valid_tank = (
                                    t_val and 
                                    len(t_val) <= 6 and 
                                    not any(c in t_val for c in ["-", "/", ":", " "]) and
                                    not (len(t_val) > 4 and t_val.isdigit())
                                )
                                tank_final = t_val if is_valid_tank else get_tank_from_batch(b_val)
                                clean_l = clean_location_str(l_val, self.mapping_dict)
                                records.append({
                                    "sheet": "CSV",
                                    "batch": b_val,
                                    "qty": tank_final,
'''
# Actually let's just use string replace to rename the final variable that goes into "qty"
content = content.replace('tank_final = t_val if is_valid_tank else get_tank_from_batch(b_val)', 'tank_final = qty_val')
content = content.replace('t_val and', 'qty_val and')
content = content.replace('len(t_val) <= 6', 'len(qty_val) <= 15')
content = content.replace('t_val.isdigit()', 'qty_val.isdigit()')
content = content.replace('c in t_val', 'c in qty_val')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
