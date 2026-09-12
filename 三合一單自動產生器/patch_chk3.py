import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = re.sub(
    r'self\.tree\.insert\(\s*"",\s*"end",\s*values=\(\s*f"\[\{idx\+1:02d\}\]",',
    r'self.tree.insert(\n                "",\n                "end",\n                values=(\n                    "☑",\n                    f"[{idx+1:02d}]",',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Treeview values restored.")
