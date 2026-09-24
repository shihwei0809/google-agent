path = r'D:\GOOGLE ANGET\勝一三合一單產生系統\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix load_mapping call to on_loc_change
load_map_call_old = r'''            for entry in self\.entries:
                loc_val = entry\["loc_var"\]\.get\(\)\.strip\(\)\.upper\(\)
                if loc_val:
                    self\.on_loc_change\(entry\["loc_var"\], entry\["long_code_var"\]\)'''
load_map_call_new = r'''            for entry in self.entries:
                loc_val = entry["loc_var"].get().strip().upper()
                if loc_val:
                    self.on_loc_change(entry)'''
text = re.sub(load_map_call_old, load_map_call_new, text)

# Update generate_files
gen_old = r'''                    ws\['C5'\] = tank_with_prefix
                    ws\['C7'\] = batch_with_prefix
                    ws\['C11'\] = loc_code

                    mat_no = str\(ws\['C3'\]\.value or "4L12C53161"\)\.strip\(\)'''

gen_new = r'''                    ws['C5'] = tank_with_prefix
                    ws['C7'] = batch_with_prefix
                    ws['C11'] = loc_code

                    part_no = entry["part_var"].get().strip()
                    if part_no:
                        ws['C3'] = part_no
                    mat_no = str(ws['C3'].value or "4L12C53161").strip()'''
text = re.sub(gen_old, gen_new, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
