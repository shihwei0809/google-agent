import sys, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix indentation issue
new_confirm = """def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    vals = list(self.tree.item(item_id, "values"))
                    vals[0] = "☐" if vals[0] == "☑" else "☑"
                    self.tree.item(item_id, values=vals)
                    
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

import re
content = re.sub(r' {4}def on_tree_click.*?self\.destroy\(\)', new_confirm, content, flags=re.DOTALL)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Indentation fixed.")
