import codecs
import os

with codecs.open(r'd:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    # 1. Buttons
    if 'tk.Button(left_btn_frame' in line and '上傳 COA 截圖' in line: continue
    if 'tk.Button(left_btn_frame' in line and '貼上 COA 截圖' in line: continue
    if 'tk.Button(left_btn_frame' in line and '設定 GCP 金鑰' in line: continue
    
    # 2. Batch Settings
    if 'tk.Label(batch_setting_frame' in line and '預計到廠時間' in line:
        skip = True
    if skip and 'apply_default_mod_time' in line:
        skip = False
        continue
    if skip: continue

    # 3. Header tuples
    if '(7, "預計到廠時間"),' in line: continue
    if '(8, "修正到廠時間"),' in line: continue
    if '(9, "採購單號"),' in line:
        new_lines.append(line.replace('9,', '7,'))
        continue
    if '(10, "單列清空")' in line:
        new_lines.append(line.replace('10,', '8,'))
        continue

    # 4. Table Body
    if '# Col 7: 預計到廠時間' in line:
        skip = True
    if skip and '# Col 9: 採購單號' in line:
        skip = False
    if skip: continue

    if '# Col 9: 採購單號' in line:
        line = line.replace('Col 9', 'Col 7')
    if 'po_entry.grid(row=row_grid_idx, column=9,' in line:
        line = line.replace('column=9', 'column=7')
        
    if '# Col 10: 單列清空' in line:
        line = line.replace('Col 10', 'Col 8')
    if 'clear_btn.grid(row=row_grid_idx, column=10,' in line:
        line = line.replace('column=10', 'column=8')

    # 5. entries.append
    if '"time_var": time_var,' in line: continue
    if '"mod_time_var": mod_time_var,' in line: continue

    # 6. clear_single_row and clear_all_rows
    if 'entry["time_var"].set("")' in line: continue
    if 'entry["mod_time_var"].set("")' in line:
        if 'def clear_all_rows' in ''.join(lines[max(0, i-15):i]):
            new_lines.append('                if "po_var" in entry: entry["po_var"].set("")\n')
        else:
            new_lines.append('            if "po_var" in entry: entry["po_var"].set("")\n')
        continue

    # 7. generate_files reading
    if 'time_str = row["time_var"].get().strip()' in line:
        line = '            time_str = ""\n'
    if 'mod_time_str = row["mod_time_var"].get().strip()' in line:
        line = '            mod_time_str = ""\n'

    new_lines.append(line)

with codecs.open(r'd:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
print(f"Lines remaining: {len(new_lines)}")
