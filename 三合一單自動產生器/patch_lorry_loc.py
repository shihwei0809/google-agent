import sys, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

old_lorry_out = """                                    t_part = f"{t_no} " if t_no else ""
                                    lorry_out_name = f"{base_lorry_name}-{mmdd} {t_part}{l_loc}{orig_ext}"
                                    out_l_path = os.path.join(output_dir, lorry_out_name)"""
new_lorry_out = """                                    t_part = f"{t_no} " if t_no else ""
                                    lorry_out_name = f"{base_lorry_name}-{mmdd} {t_part}{l_loc}{orig_ext}"
                                    
                                    safe_loc_l = "".join(c for c in l_loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                                    if not safe_loc_l: safe_loc_l = "未命名地點"
                                    safe_tank_l = str(t_no).strip() if t_no else ""
                                    loc_sub_dir_l = f"{mmdd} {safe_loc_l} {safe_tank_l}".strip()
                                    loc_folder_l = os.path.join(output_dir, loc_sub_dir_l)
                                    if not os.path.exists(loc_folder_l):
                                        os.makedirs(loc_folder_l)
                                        
                                    out_l_path = os.path.join(loc_folder_l, lorry_out_name)"""
content = content.replace(old_lorry_out, new_lorry_out)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Lorry output path updated with loc_folder.")
