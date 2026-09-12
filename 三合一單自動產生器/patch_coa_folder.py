import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = re.sub(
    r'output_dir = os\.path\.join\(self\.base_dir, f"三合一單產出_\{formatted_date\}"\)',
    r'output_dir = os.path.join(self.base_dir, f"三合一單輸出_{formatted_date}")',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("COA folder name fixed.")
