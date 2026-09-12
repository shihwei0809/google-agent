import re, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Replace headers
content = re.sub(
    r'\(\s*8,\s*"修正到廠時間"\s*\),\s*\(\s*9,\s*"單列清空"\s*\)',
    r'(8, "修正到廠時間"),\n            (9, "採購單號"),\n            (10, "單列清空")',
    content
)

# Replace mod_time_entry
new_mod_time = r'''            # Col 8: 修正到廠時間
            mod_time_var = tk.StringVar(value="")
            mod_time_entry = tk.Entry(self.scrollable_frame, textvariable=mod_time_var, width=10, font=("Arial", 10), fg="red")
            mod_time_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")

            # Col 9: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=12, font=("Arial", 10), fg="#004D40")
            po_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")'''
content = re.sub(r'            # Col 8: 修正到廠時間.+?sticky="ew"\)', new_mod_time, content, flags=re.DOTALL)

# Replace clear button col
content = re.sub(r'column=9,\s*padx=4,\s*pady=2\)', 'column=10, padx=4, pady=2)', content)

# Write back
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Regex patch applied")
