import sys
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('地點代號對照表.xlsx', 'N系料小包-地點代號對照表.xlsx')
content = content.replace('self.title("三合一單自動產生器")', 'self.title("生產履歷與COA自動產生器")')

# Remove the template path for 3-in-1
content = re.sub(r'self\.template_path\s*=\s*os\.path\.join\([^)]+\"台積電槽車barcode三合一單-範本\.xlsx\"\)', 'self.template_path = None', content)

# Remove the UI that checks template_path in setup_ui
template_check_pattern = r'# 範本狀態\n\s*t_color\s*=\s*\"green\" if os\.path\.exists\(self\.template_path\) else \"red\"\n\s*t_text\s*=\s*\"✅ 已找到\" if os\.path\.exists\(self\.template_path\) else \"❌ 未找到 \(請將檔案放入資料夾\)\"\n\s*tk\.Label\(status_frame, text=f\"範本檔案 \(台積電槽車barcode三合一單-範本\.xlsx\): \{t_text\}\", fg=t_color\)\.pack\(anchor=\"w\"\)'
content = re.sub(template_check_pattern, '', content, flags=re.DOTALL)

# Remove the checkbox for 3in1
checkbox_pattern = r'self\.gen_3in1_var\s*=\s*tk\.BooleanVar\(value=True\)\n\s*self\.gen_lorry_var\s*=\s*tk\.BooleanVar\(value=True\)\n\n\s*tk\.Checkbutton\(report_opt_frame, text=\"✅ 產生三合一單 Excel \(含 Barcode 與 COA\)\", variable=self\.gen_3in1_var, font=\(\"Microsoft JhengHei\", 9, \"bold\"\), fg=\"#1B5E20\"\)\.pack\(side=\"left\", padx=\(0, 20\)\)'
content = re.sub(checkbox_pattern, 'self.gen_3in1_var = tk.BooleanVar(value=False)\n        self.gen_lorry_var = tk.BooleanVar(value=True)', content, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
