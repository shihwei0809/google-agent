import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix Lorry save path computation
old_lorry = """                                    t_part = f"{t_no} " if t_no else ""
                                    lorry_out_name = f"{base_lorry_name}-{mmdd} {t_part}{l_loc}{orig_ext}"
                                    out_l_path = os.path.join(loc_folder, lorry_out_name)"""

new_lorry = """                                    t_part = f"{t_no} " if t_no else ""
                                    lorry_out_name = f"{base_lorry_name}-{mmdd} {t_part}{l_loc}{orig_ext}"
                                    
                                    # 動態計算正確的子資料夾
                                    safe_loc_l = "".join(c for c in l_loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                                    if not safe_loc_l: safe_loc_l = "未命名地點"
                                    loc_sub_dir_l = f"{mmdd} {safe_loc_l} {t_no}".strip()
                                    correct_loc_folder = os.path.join(output_dir, loc_sub_dir_l)
                                    os.makedirs(correct_loc_folder, exist_ok=True)
                                    
                                    out_l_path = os.path.join(correct_loc_folder, lorry_out_name)"""
content = content.replace(old_lorry, new_lorry)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Lorry dynamic path fixed.")
