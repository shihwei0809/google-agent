import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Headers
content = re.sub(
    r'\(\s*8\s*,\s*"修正到廠時間"\s*\)\s*,\s*\(\s*9\s*,\s*"單列清空"\s*\)',
    r'(8, "修正到廠時間"),\n            (9, "採購單號"),\n            (10, "單列清空")',
    content
)

# 2. UI Generation
old_ui = r'# Col 9: 單列清空按鈕\s*btn_clear_row = tk\.Button\(.*?\)\s*btn_clear_row\.grid\(row=row_grid_idx, column=9, padx=4, pady=2\)'
new_ui = """# Col 9: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=18, font=("Arial", 10), fg="#333")
            po_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")

            # Col 10: 單列清空按鈕
            btn_clear_row = tk.Button(
                self.scrollable_frame, 
                text="清空", 
                command=lambda r=row_idx-1: self.clear_single_row(r), 
                font=("Microsoft JhengHei", 9, "bold"), 
                bg="#FFEBEE", 
                fg="#C62828", 
                cursor="hand2", 
                width=6,
                pady=1
            )
            btn_clear_row.grid(row=row_grid_idx, column=10, padx=4, pady=2)"""
content = re.sub(old_ui, new_ui, content, flags=re.DOTALL)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("PO UI restored!")
