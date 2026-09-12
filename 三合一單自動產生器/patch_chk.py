import re, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. modify columns definition
content = content.replace(
    'columns = ("idx", "sheet", "date", "time", "batch", "tank", "loc", "long_code")',
    'columns = ("chk", "idx", "sheet", "date", "time", "batch", "tank", "loc", "long_code")'
)

# 2. modify col_defs
old_col_defs = """        col_defs = [
            ("idx", "項次", 50, "center"),
            ("sheet", "來源分頁", 150, "w"),"""
new_col_defs = """        col_defs = [
            ("chk", "✅選取", 50, "center"),
            ("idx", "項次", 50, "center"),
            ("sheet", "來源分頁", 150, "w"),"""
content = content.replace(old_col_defs, new_col_defs)

# 3. bind tree click
content = content.replace(
    'self.tree.tag_configure("oddrow", background="#F2F7FA")',
    'self.tree.tag_configure("oddrow", background="#F2F7FA")\n        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)'
)

# 4. update_preview insert
old_insert = """            self.tree.insert(
                "",
                "end",
                values=(
                    f"[{idx+1:02d}]","""
new_insert = """            self.tree.insert(
                "",
                "end",
                values=(
                    "☑",
                    f"[{idx+1:02d}]","""
content = content.replace(old_insert, new_insert)

# 5. add on_tree_click method and modify confirm_import
old_confirm = """    def confirm_import(self):
        cnt = self.count_var.get()
        cnt = max(1, min(cnt, len(self.current_filtered_records)))
        self.selected_records = self.current_filtered_records[-cnt:]
        self.destroy()"""

new_confirm = """    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    vals = list(self.tree.item(item_id, "values"))
                    vals[0] = "☐" if vals[0] == "☑" else "☑"
                    self.tree.item(item_id, values=vals)
                    
                    # Update button text based on count
                    checked = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "☑")
                    self.btn_confirm.config(text=f"🚀 確認將這 {checked} 筆匯入系統")

    def confirm_import(self):
        cnt = self.count_var.get()
        cnt = max(1, min(cnt, len(self.current_filtered_records)))
        slice_records = self.current_filtered_records[-cnt:]
        
        selected_recs = []
        for idx, item in enumerate(self.tree.get_children()):
            vals = self.tree.item(item, "values")
            if vals[0] == "☑" and idx < len(slice_records):
                selected_recs.append(slice_records[idx])
                
        self.selected_records = selected_recs
        self.destroy()"""
content = content.replace(old_confirm, new_confirm)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Checkbox patch applied.")
