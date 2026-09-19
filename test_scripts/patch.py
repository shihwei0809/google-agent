import os
def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove .csv from imported_lorry_files logic
    content = content.replace("fp.lower().endswith(('.xlsx', '.xls', '.csv'))", "fp.lower().endswith(('.xlsx', '.xls'))")

    # 2. Add long_code_var assignment in import_from_excel (for 三合一單自動產生器)
    if 'entry["long_code_var"].set(rec.get("long_code", ""))' not in content:
        content = content.replace(
            'entry["loc_var"].set(rec.get("loc", ""))',
            'entry["loc_var"].set(rec.get("loc", ""))\n                    if "long_code" in rec: entry["long_code_var"].set(rec["long_code"])'
        )

    # 3. Add generate_files to the end of load_coa_forms
    old_msg = 'messagebox.showinfo("完成", msg)'
    new_msg = '''
        if success_count > 0:
            self.generate_files()
        else:
            messagebox.showinfo("完成", msg)
'''
    if 'self.generate_files()' not in content.split('def upload_coa(self):')[0]:
        content = content.replace(old_msg, new_msg)

    # 4. Fix clear_single_row and clear_all_rows
    old_clear1 = '''        if 0 <= r_idx < len(self.entries):
            entry = self.entries[r_idx]
            entry["batch_var"].set("")
            entry["loc_var"].set("")
            entry["long_code_var"].set("")
            entry["tank_var"].set("")
            entry["date_var"].set("")
            if "po_var" in entry: entry["po_var"].set("")
            if "po_var" in entry: entry["po_var"].set("")'''
    new_clear1 = '''        if 0 <= r_idx < len(self.entries):
            entry = self.entries[r_idx]
            for k, v in entry.items():
                if k.endswith("_var"):
                    try:
                        v.set("")
                    except: pass'''
    content = content.replace(old_clear1, new_clear1)
    
    old_clear2 = '''        if messagebox.askyesno("確認清空", "確定要清空所有已填寫的批號、地點與時間資料嗎？"):
            for entry in self.entries:
                entry["batch_var"].set("")
                entry["loc_var"].set("")
                entry["long_code_var"].set("")
                entry["tank_var"].set("")
                entry["date_var"].set("")
                if "po_var" in entry: entry["po_var"].set("")
                if "po_var" in entry: entry["po_var"].set("")'''
    new_clear2 = '''        if messagebox.askyesno("確認清空", "確定要清空所有已填寫的批號、地點與時間資料嗎？"):
            for entry in self.entries:
                for k, v in entry.items():
                    if k.endswith("_var"):
                        try:
                            v.set("")
                        except: pass'''
    content = content.replace(old_clear2, new_clear2)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_file(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py')
patch_file(r'C:\GOOGLE ANGET\勝一三合一單產生系統\main.py')
print("Patched both files successfully")
