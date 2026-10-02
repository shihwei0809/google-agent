import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the os.path.exists crash if template_path is None
crash_pattern = r'\s*if not os\.path\.exists\(self\.template_path\):\n\s*messagebox\.showerror\(\"錯誤\", f\"找不到範本檔案:\\n\{self\.template_path\}\"\)\n\s*return'
content = re.sub(crash_pattern, '', content)

# Check for other places where template_path might be used and crash
crash_pattern2 = r'\s*if getattr\(self, \"template_path\", None\) and not os\.path\.exists\(self\.template_path\):.*?\n\s*return'

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
