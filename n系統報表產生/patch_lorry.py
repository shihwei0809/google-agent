import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''
                        try:
                            src_wb_l = openpyxl.load_workbook(l_path, data_only=False)
                            src_ws_l = src_wb_l.active

                            batch_row_map = {}
                            for r in range(7, src_ws_l.max_row + 1):
                                val = str(src_ws_l.cell(row=r, column=1).value or "").strip().upper()
                                if val and val not in batch_row_map:
                                    batch_row_map[val] = r
'''

new_block = '''
                        try:
                            wb_data = openpyxl.load_workbook(l_path, data_only=True)
                            ws_data = wb_data.active
                            batch_row_map = {}
                            for r in range(7, ws_data.max_row + 1):
                                val = str(ws_data.cell(row=r, column=1).value or "").strip().upper()
                                if val and val not in batch_row_map:
                                    batch_row_map[val] = r
                            wb_data.close()

                            src_wb_l = openpyxl.load_workbook(l_path, data_only=False)
                            src_ws_l = src_wb_l.active
'''

if old_block.strip() in content:
    content = content.replace(old_block.strip(), new_block.strip())
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCHED LORRY")
else:
    print("NOT FOUND LORRY")

