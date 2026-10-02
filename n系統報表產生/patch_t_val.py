import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''
                            is_valid_tank = (
                                qty_val and 
                                len(qty_val) <= 15 and 
                                not any(sep in t_val for sep in ["-", "/", ":", " "]) and 
                                not (len(qty_val) > 4 and qty_val.isdigit())
                            )
                            if not is_valid_tank:
                                t_val = get_tank_from_batch(b_val)

                            # 格式化時間 (統一為 4 碼如 0900)
'''

new_block = '''
                            # 格式化時間 (統一為 4 碼如 0900)
'''
if old_block.strip() in content:
    content = content.replace(old_block.strip(), new_block.strip())
else:
    print("Old block not found!")

old_dict = '''
                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "tank": t_val,
                                "loc": clean_loc,
                                "_vals": self.mapping_dict.get(clean_loc, []),
                                "long_code": self.mapping_dict.get(clean_loc, [""])[0] if isinstance(self.mapping_dict.get(clean_loc), list) and self.mapping_dict.get(clean_loc) else (self.mapping_dict.get(clean_loc) if isinstance(self.mapping_dict.get(clean_loc), str) else ""),
                                "date": norm_date,
                                "time": t_final,
                                "mod_time": mt_val,
                                "po": po_val,
                                "origin": origin_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val),
                                "qty": qty_val
                            })
'''

new_dict = '''
                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "loc": clean_loc,
                                "_vals": self.mapping_dict.get(clean_loc, []),
                                "long_code": self.mapping_dict.get(clean_loc, [""])[0] if isinstance(self.mapping_dict.get(clean_loc), list) and self.mapping_dict.get(clean_loc) else (self.mapping_dict.get(clean_loc) if isinstance(self.mapping_dict.get(clean_loc), str) else ""),
                                "date": norm_date,
                                "time": t_final,
                                "mod_time": mt_val,
                                "po": po_val,
                                "origin": origin_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val),
                                "qty": qty_val
                            })
'''

if old_dict.strip() in content:
    content = content.replace(old_dict.strip(), new_dict.strip())
else:
    print("Old dict not found!")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
