import sys, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

old_path = """                output_dir = os.path.join(self.base_dir, f"三合一單產出_{formatted_date}")
                os.makedirs(output_dir, exist_ok=True)
                new_file_path = os.path.join(output_dir, new_base + ext)"""

new_path = """                output_dir = os.path.join(self.base_dir, f"三合一單產出_{formatted_date}")
                
                tank_str = row["tank_var"].get().strip()
                date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date
                safe_loc = "".join(c for c in loc_str if c.isalnum() or c in (' ', '_', '-')).rstrip()
                if not safe_loc: safe_loc = "未命名地點"
                loc_sub_dir = f"{date_MMDD} {safe_loc} {tank_str}".strip()
                
                loc_folder = os.path.join(output_dir, loc_sub_dir)
                os.makedirs(loc_folder, exist_ok=True)
                
                new_file_path = os.path.join(loc_folder, new_base + ext)"""

content = content.replace(old_path, new_path)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("COA path updated with loc_folder.")
