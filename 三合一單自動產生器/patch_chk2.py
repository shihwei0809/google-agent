import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix col_defs
content = re.sub(
    r'col_defs = \[\s*\("idx", "項次", 50, "center"\),',
    r'col_defs = [\n            ("chk", "✅選取", 50, "center"),\n            ("idx", "項次", 50, "center"),',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Treeview chk restored.")
