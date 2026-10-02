import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix records.append dict
old_dict = '''
                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "tank": t_val,
                                "loc": clean_loc,
'''
new_dict = '''
                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "qty": qty_val,
                                "loc": clean_loc,
'''
content = content.replace(old_dict.strip(), new_dict.strip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
