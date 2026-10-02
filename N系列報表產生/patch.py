import os

filepath = r"d:\GOOGLE ANGET\N系列報表產生\生產履歷與COA_系統\main.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the specific block
target = '''        if not do_3in1:
            messagebox.showwarning("提示", "請勾選產生三合一單！")
            return'''
            
content = content.replace(target, '')

# Also let's set do_3in1 = False by default if it's there
# wait, the user says "少一個沒有產出三合一單而已".
# That means we shouldn't even have the checkbox on the UI, or we just leave the checkbox but it does nothing?
# If we just leave it and let them uncheck it, it works. 
# But let's force do_3in1 = False
content = content.replace('do_3in1 = self.gen_3in1_var.get()', 'do_3in1 = False # Disable 3-in-1 generation')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied.")
