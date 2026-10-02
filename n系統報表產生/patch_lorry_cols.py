import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''
                                    ws_new_l.cell(row=7, column=2).value = item.get("long_code", "") or item.get("loc", "")
                                    ws_new_l.cell(row=7, column=3).value = d_str
                                    ws_new_l.cell(row=7, column=6).value = item.get("mfg_date", "")
'''

new_code = '''
                                    ws_new_l.cell(row=7, column=2).value = item.get("loc", "")
                                    ws_new_l.cell(row=7, column=3).value = d_str
                                    ws_new_l.cell(row=7, column=6).value = item.get("mfg_date", "")
                                    if item.get("long_code", ""):
                                        ws_new_l.cell(row=7, column=7).value = item.get("long_code", "")
'''

content = content.replace(old_code.strip(), new_code.strip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
