path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update variables parsed in update_preview
update_preview_old = r'''            loc_str = rec.get\("loc"\) or ""
            long_code_str = rec.get\("long_code"\) or getattr\(self.parent_app, "mapping_dict", \{\}\)\.get\(loc_str, ""\)'''
update_preview_new = r'''            loc_str = rec.get("loc") or ""
            origin_str = rec.get("origin") or ""
            long_code_str = rec.get("long_code") or getattr(self.parent_app, "mapping_dict", {}).get(loc_str, "")'''
text = re.sub(update_preview_old, update_preview_new, text)

# 2. Update the values tuple
values_old = r'''                    b_str,
                    tank_str,
                    loc_str,
                    long_code_str'''
values_new = r'''                    b_str,
                    tank_str,
                    origin_str,
                    loc_str,
                    long_code_str'''
text = re.sub(values_old, values_new, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
