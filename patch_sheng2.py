path = r'D:\GOOGLE ANGET\勝一三合一單產生系統\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update add_input_rows to add part_no
add_input_old = r'''            # Col 6: .*?
            long_code_var = tk\.StringVar\(\)
            long_code_entry = tk\.Entry\(self\.scrollable_frame, textvariable=long_code_var, state="readonly", width=16, font=\("Arial", 10\), fg="purple"\)
            long_code_entry\.grid\(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew"\)
            
            # Col 7: .*?
            date_frame = tk\.Frame\(self\.scrollable_frame\)
            date_frame\.grid\(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew"\)'''

add_input_new = r'''            # Col 6: 長代號
            long_code_var = tk.StringVar()
            long_code_entry = tk.Entry(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=16, font=("Arial", 10), fg="purple")
            long_code_entry.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")

            # Col 7: 料號
            part_var = tk.StringVar()
            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, state="readonly", width=12, font=("Arial", 10, "bold"), fg="#D32F2F")
            part_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")
            
            # Col 8: 出貨日期
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")'''
text = re.sub(add_input_old, add_input_new, text)

# Shift po_var and btn_clear
po_old = r'''            po_entry\.grid\(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew"\)
            
            # Col 9: .*?
            btn_clear = tk\.Button\(self\.scrollable_frame, text=".*?", 
                                  command=lambda r=row_idx: self\.clear_single_row\(r\),
                                  bg="#FCE4EC", font=\("Arial", 9\)\)
            btn_clear\.grid\(row=row_grid_idx, column=9, padx=2, pady=2\)'''
po_new = r'''            po_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")
            
            # Col 10: 單列清除
            btn_clear = tk.Button(self.scrollable_frame, text="清除", 
                                  command=lambda r=row_idx: self.clear_single_row(r),
                                  bg="#FCE4EC", font=("Arial", 9))
            btn_clear.grid(row=row_grid_idx, column=10, padx=2, pady=2)'''
text = re.sub(po_old, po_new, text)

# Add part_var and part_entry to row_dict
row_dict_old = r'''                "prod_entry": prod_entry,
                "loc_var": loc_var,
                "loc_entry": loc_entry,
                "long_code_var": long_code_var,
                "long_code_entry": long_code_entry,
                "date_var": date_var,'''
row_dict_new = r'''                "prod_entry": prod_entry,
                "loc_var": loc_var,
                "loc_entry": loc_entry,
                "long_code_var": long_code_var,
                "long_code_entry": long_code_entry,
                "part_var": part_var,
                "part_entry": part_entry,
                "date_var": date_var,'''
text = re.sub(row_dict_old, row_dict_new, text)

# Add clear part_var
clear_old = r'''        if "prod_var" in entry: entry\["prod_var"\]\.set\(""\)
        if "long_code_var" in entry: entry\["long_code_var"\]\.set\(""\)'''
clear_new = r'''        if "prod_var" in entry: entry["prod_var"].set("")
        if "part_var" in entry: entry["part_var"].set("")
        if "long_code_var" in entry: entry["long_code_var"].set("")'''
text = re.sub(clear_old, clear_new, text)

# Clear all rows
clear_all_old = r'''            if "prod_var" in entry: entry\["prod_var"\]\.set\(""\)
            if "long_code_var" in entry: entry\["long_code_var"\]\.set\(""\)'''
clear_all_new = r'''            if "prod_var" in entry: entry["prod_var"].set("")
            if "part_var" in entry: entry["part_var"].set("")
            if "long_code_var" in entry: entry["long_code_var"].set("")'''
text = re.sub(clear_all_old, clear_all_new, text)

# Tracing
trace_old = r'''            loc_var\.trace\("w", lambda \*args, r=row_idx: self\.on_loc_change\(self\.entries\[r-1\]\["loc_var"\], self\.entries\[r-1\]\["long_code_var"\]\)\)
            self\.entries\.append\(row_dict\)'''
trace_new = r'''            loc_var.trace("w", lambda *args, r=row_idx: self.on_loc_change(self.entries[r-1]))
            prod_var.trace("w", lambda *args, r=row_idx: self.on_loc_change(self.entries[r-1]))
            self.entries.append(row_dict)'''
text = re.sub(trace_old, trace_new, text)

# Redefine on_loc_change
on_loc_old = r'''    def on_loc_change\(self, loc_var, long_code_var\):
        loc_val = loc_var\.get\(\)\.strip\(\)\.upper\(\)
        if loc_val:
            long_code_var\.set\(self\.mapping_dict\.get\(loc_val, ""\)\)
        else:
            long_code_var\.set\(""\)'''
on_loc_new = r'''    def on_loc_change(self, entry):
        loc_val = entry["loc_var"].get().strip().upper()
        prod_val = entry["prod_var"].get().strip().upper()
        long_code_var = entry["long_code_var"]
        part_var = entry["part_var"]
        if loc_val:
            long_code_var.set(self.mapping_dict.get(loc_val, ""))
            info = getattr(self, "part_mapping_dict", {}).get(loc_val, {})
            origins = info.get("origins", {})
            default_part = info.get("default", "")
            final_part = ""
            for key, val in origins.items():
                if prod_val and key.upper() in prod_val:
                    final_part = val
                    break
            if not final_part: final_part = default_part
            if not final_part: final_part = "L12C53161"
            part_var.set("4" + final_part)
        else:
            long_code_var.set("")
            part_var.set("")'''
text = re.sub(on_loc_old, on_loc_new, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
