import codecs
with codecs.open(r"C:\GOOGLE ANGET\三合一單自動產生器\main.py", "r", "utf-8") as f:
    content = f.read()

content = content.replace("            entry[\"mod_time_var\"].set(\"\")\n                if \"po_var\" in entry: entry[\"po_var\"].set(\"\")", "            entry[\"mod_time_var\"].set(\"\")\n            if \"po_var\" in entry: entry[\"po_var\"].set(\"\")")

with codecs.open(r"C:\GOOGLE ANGET\三合一單自動產生器\main.py", "w", "utf-8") as f:
    f.write(content)
