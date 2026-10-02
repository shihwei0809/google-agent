import sys
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Change UI column 3 from 槽號 to 數量 (ShipQty)
content = content.replace('(3, "槽號 (自動)"),', '(3, "數量 (ShipQty)"),')
content = content.replace('tank_var = tk.StringVar()', 'qty_var = tk.StringVar()')
content = content.replace('tank_entry = tk.Entry(self.scrollable_frame, textvariable=tank_var, state="readonly", width=10, font=("Arial", 10), fg="blue")', 
                          'qty_entry = tk.Entry(self.scrollable_frame, textvariable=qty_var, width=10, font=("Arial", 10), fg="blue")')
content = content.replace('tank_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")',
                          'qty_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")')

# 2. In extract data (valid_data in generate_files)
content = content.replace('tank = row["tank_var"].get().strip()', 'qty = row["qty_var"].get().strip()')
content = content.replace('"tank": tank,', '"qty": qty,')

# 3. In generate_files loop, remove safe_tank from folder names
content = content.replace('safe_tank = str(t_no).strip() if t_no else ""\n                                loc_sub_dir = f"{date_MMDD} {safe_loc} {safe_tank}".strip()',
                          'loc_sub_dir = f"{date_MMDD} {safe_loc}".strip()')
content = content.replace('t_no = item["tank"]', 'qty = item.get("qty", "")')
content = content.replace('t_part = f"{t_no} " if t_no else ""\n                                    lorry_out_name = f"{base_lorry_name}-{mmdd} {t_part}{l_loc}{orig_ext}"',
                          'lorry_out_name = f"{base_lorry_name}-{mmdd} {l_loc}{orig_ext}"')

# 4. In build_single_row_lorry_workbook (Ah, wait, it doesn't do much there, but we need to update lorry file too? 
# Wait, Lorry file (Chemical_Lorry...) is not modified in generate_files? 
# No, wb_l = build_single_row_lorry_workbook(src_ws_l, matched_r)
# We need to inject qty, date, po_no into wb_l!)
# Let's see if wb_l modifies B8, B12, B14.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
