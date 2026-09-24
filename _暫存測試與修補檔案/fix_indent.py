path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

with open(path, 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines, 1):
        if i in [1740, 1741, 1742, 1743, 1744]:
            pass
        elif i == 1739:
            f.write('                if "po_var" in entry: entry["po_var"].set("")\n')
            f.write('                if "origin_var" in entry: entry["origin_var"].set("")\n')
            f.write('                if "part_var" in entry: entry["part_var"].set("")\n')
        elif 'self.entries[r_idx]["po_var"].set("")' in line:
            f.write('            if "po_var" in self.entries[r_idx]: self.entries[r_idx]["po_var"].set("")\n')
            f.write('            if "origin_var" in self.entries[r_idx]: self.entries[r_idx]["origin_var"].set("")\n')
            f.write('            if "part_var" in self.entries[r_idx]: self.entries[r_idx]["part_var"].set("")\n')
        elif 'self.entries[r_idx]["origin_var"].set("")' in line or 'self.entries[r_idx]["part_var"].set("")' in line:
            pass # clear duplicate if any
        else:
            f.write(line)
