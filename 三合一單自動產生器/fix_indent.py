import codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'if "po_var" in entry: entry["po_var"].set("")' in line:
        if line.startswith('                if "po_var" in entry:') and 'clear_single_row' not in "".join(lines[max(0, i-20):i]):
            pass # Keep 16 spaces for clear_all_rows
        elif line.startswith('                if "po_var" in entry:'):
            lines[i] = '            if "po_var" in entry: entry["po_var"].set("")\n'

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.writelines(lines)
print("Indentation fixed.")
