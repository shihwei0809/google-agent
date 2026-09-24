path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
import re

with open(path, encoding='utf-8') as f:
    content = f.read()

# 1. Update CSV extraction
content = re.sub(
    r'(\s+)origin_val = ""\s+for cell in row:\s+cs = str\(cell or ""\)\.strip\(\)\.upper\(\)\s+if not origin_val and any\(k in cs for k in \[.*?"L2"\]\):\s+origin_val = cs\s+break',
    r'\1origin_val = str(get_c(origin_col) or "").strip()',
    content,
    count=1
)

# 2. Update XLSX extraction
content = re.sub(
    r'(\s+)origin_val = ""\s+for cell in row:\s+cs = str\(cell or ""\)\.strip\(\)\.upper\(\)\s+if not origin_val and any\(k in cs for k in \[.*?"L2"\]\):\s+origin_val = cs\s+break',
    r'\1origin_val = str(get_cell_val(origin_col) or "").strip()',
    content,
    count=1
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
