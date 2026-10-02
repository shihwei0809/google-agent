import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

debug_code = '''
                            for r in range(7, ws_data.max_row + 1):
                                val = str(ws_data.cell(row=r, column=1).value or "").strip().upper()
                                if val and val not in batch_row_map:
                                    batch_row_map[val] = r
                            wb_data.close()
                            
                            with open("debug_lorry.txt", "a", encoding="utf-8") as df:
                                df.write(f"batch_row_map: {batch_row_map}\\n")

                            src_wb_l = openpyxl.load_workbook(l_path, data_only=False)
'''

content = content.replace('''
                            for r in range(7, ws_data.max_row + 1):
                                val = str(ws_data.cell(row=r, column=1).value or "").strip().upper()
                                if val and val not in batch_row_map:
                                    batch_row_map[val] = r
                            wb_data.close()

                            src_wb_l = openpyxl.load_workbook(l_path, data_only=False)
'''.strip(), debug_code.strip())

debug_code2 = '''
                                    wb_l.save(out_l_path)
                                    wb_l.close()
                                    with open("debug_lorry.txt", "a", encoding="utf-8") as df:
                                        df.write(f"Saved: {out_l_path}\\n")

                                    success_lorry += 1
'''

content = content.replace('''
                                    wb_l.save(out_l_path)
                                    wb_l.close()

                                    success_lorry += 1
'''.strip(), debug_code2.strip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCHED DEBUG")
