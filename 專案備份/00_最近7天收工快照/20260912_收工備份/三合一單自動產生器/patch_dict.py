import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = re.sub(
    r'"mod_time_var": mod_time_var\s*\}\)',
    r'"mod_time_var": mod_time_var,\n                "po_var": po_var\n            })',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Entries dict patched.")
