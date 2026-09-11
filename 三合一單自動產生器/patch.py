import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove load_existing_transport_notice button
content = re.sub(r'[ \t]*tk\.Button\(left_btn_frame,\s*text=[^,]*載入既有通知表修訂.*?\)\.pack\(.*?\)\n?', '', content)

# Remove gen_transport_var checkbutton
content = re.sub(r'[ \t]*tk\.Checkbutton\(report_opt_frame,\s*text=[^,]*產生運輸通知表 Excel.*?\)\.pack\(.*?\)\n?', '', content)

# Add COA button before 上傳 COA 截圖
coa_btn = 'tk.Button(left_btn_frame, text="📄 載入 COA 表單", command=self.load_coa_forms, bg="#8E24AA", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=4)\n        '
content = content.replace('tk.Button(left_btn_frame, text="🖼️ 上傳 COA 截圖"', coa_btn + 'tk.Button(left_btn_frame, text="🖼️ 上傳 COA 截圖"')

# Remove self.gen_transport_var initialization
content = re.sub(r'[ \t]*self\.gen_transport_var\s*=\s*tk\.BooleanVar\(value=True\)\n?', '', content)

# Modify generate_files checks
content = re.sub(r'[ \t]*do_transport\s*=\s*self\.gen_transport_var\.get\(\)\n?', '', content)
content = re.sub(r'if not do_3in1 and not do_transport:', 'if not do_3in1:', content)
content = re.sub(r'請至少勾選一種報表類型（三合一單 或 運輸通知表）', '請勾選產生三合一單', content)

# Remove load_existing_transport_notice method
match = re.search(r'    def load_existing_transport_notice\(self\):', content)
if match:
    start_idx = match.start()
    next_def = re.search(r'\n    def ', content[start_idx+1:])
    if next_def:
        end_idx = start_idx + 1 + next_def.start()
        content = content[:start_idx] + content[end_idx:]

with open('main_patched.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully.')
