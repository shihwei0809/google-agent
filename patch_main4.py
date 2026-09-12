# -*- coding: utf-8 -*-
import codecs
import os

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# 1. Fix generate_files loc_folder bug
# In generate_files, under if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get():
# there is a loop or item in valid_data:. We need to calculate loc_folder there.

start_idx = -1
for i, l in enumerate(lines):
    if 'for item in valid_data:' in l and 'b_no = item["batch"]' in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    # Let's insert the folder calculation logic right after d_str = item["date"]
    insert_idx = start_idx + 5
    
    insert_lines = [
        '                                # 重新計算 loc_folder，避免全部擠在最後一個',
        '                                date_MMDD = "0000"',
        '                                if d_str:',
        '                                    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):',
        '                                        try:',
        '                                            dt_l = datetime.strptime(d_str.split()[0], fmt)',
        '                                            date_MMDD = f"{dt_l.month:02d}{dt_l.day:02d}"',
        '                                            break',
        '                                        except ValueError:',
        '                                            pass',
        '                                if date_MMDD == "0000":',
        '                                    now_l = datetime.now()',
        '                                    date_MMDD = f"{now_l.month:02d}{now_l.day:02d}"',
        '                                safe_loc = "".join(c for c in l_loc if c.isalnum() or c in (\' \', \'_\', \'-\')).rstrip()',
        '                                safe_tank = str(t_no).strip() if t_no else ""',
        '                                loc_sub_dir = f"{date_MMDD} {safe_loc} {safe_tank}".strip()',
        '                                current_loc_folder = os.path.join(output_dir, loc_sub_dir)',
        '                                os.makedirs(current_loc_folder, exist_ok=True)'
    ]
    lines = lines[:insert_idx] + insert_lines + lines[insert_idx:]
    
    # Now replace out_l_path = os.path.join(loc_folder, lorry_out_name)
    # with out_l_path = os.path.join(current_loc_folder, lorry_out_name)
    for i in range(insert_idx, insert_idx + 50):
        if 'out_l_path = os.path.join(loc_folder, lorry_out_name)' in lines[i]:
            lines[i] = lines[i].replace('loc_folder', 'current_loc_folder')
            break

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
