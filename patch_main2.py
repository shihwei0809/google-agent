# -*- coding: utf-8 -*-
import codecs
import os

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# 1. Remove the while loop in generate_files
idx_while = -1
for i, l in enumerate(lines):
    if 'while os.path.exists(output_path):' in l and 'base_filename =' in lines[i+1]:
        idx_while = i
        break

if idx_while != -1:
    del lines[idx_while-1 : idx_while+4]

# 2. Rewrite the file saving logic in load_coa_forms
start_idx = -1
for i, l in enumerate(lines):
    if 'new_file_path = os.path.join(loc_folder, new_base + ext)' in l:
        start_idx = i
        break

end_idx = -1
for i in range(start_idx, len(lines)):
    if 'success_count += 1' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    replacement = [
        '                new_file_path = os.path.join(loc_folder, new_base + ext)',
        '                ',
        '                col_b, col_g, col_c = \"\", \"\", \"\"',
        '                # 產生生產履歷 (不受 COA 檔案類型限制)',
        '                if hasattr(self, \"imported_lorry_files\") and self.imported_lorry_files:',
        '                    try:',
        '                        src_wb_l = openpyxl.load_workbook(self.imported_lorry_files[0], data_only=True)',
        '                        src_ws_l = src_wb_l.active',
        '                        batch_row_map = {}',
        '                        for r in range(7, src_ws_l.max_row + 1):',
        '                            val = str(src_ws_l.cell(row=r, column=1).value or \"\").strip().upper()',
        '                            if val and val not in batch_row_map:',
        '                                batch_row_map[val] = r',
        '                        ',
        '                        matched_r = batch_row_map.get(matched_batch)',
        '                        if matched_r:',
        '                            col_b = str(src_ws_l.cell(row=matched_r, column=2).value or \"\").strip()',
        '                            col_c = str(src_ws_l.cell(row=matched_r, column=3).value or \"\").strip()',
        '                            col_g = str(src_ws_l.cell(row=matched_r, column=7).value or \"\").strip()',
        '                            ',
        '                            wb_l = build_single_row_lorry_workbook(src_ws_l, matched_r)',
        '                            lorry_out_name = f\"Chemical_Lorry_{new_base}{ext}\"',
        '                            out_l_path = os.path.join(loc_folder, lorry_out_name)',
        '                            wb_l.save(out_l_path)',
        '                            wb_l.close()',
        '                        src_wb_l.close()',
        '                    except Exception as le:',
        '                        error_msgs.append(f\"產生生產履歷失敗: {le}\")',
        '                ',
        '                # 處理 COA 本身',
        '                if ext.lower() in [\'.xlsx\', \'.xls\']:',
        '                    wb = openpyxl.load_workbook(file_path)',
        '                    ws = wb.active',
        '                    if col_b or col_g or col_c:',
        '                        if col_b: ws[\"B6\"] = col_b',
        '                        if col_g: ws[\"B7\"] = col_g',
        '                        if col_c: ws[\"B11\"] = col_c',
        '                    else:',
        '                        ws[\"B6\"] = factory_code',
        '                        ws[\"B17\"] = date_str',
        '                    wb.save(new_file_path)',
        '                    try: wb.close() except: pass',
        '                elif ext.lower() == \'.csv\':',
        '                    import csv',
        '                    with open(file_path, \'r\', encoding=\'utf-8-sig\', errors=\'ignore\') as f:',
        '                        reader = list(csv.reader(f))',
        '                    while len(reader) <= 16: reader.append([])',
        '                    for r in reader: ',
        '                        while len(r) <= 11: r.append(\"\")',
        '                    if col_b or col_g or col_c:',
        '                        if col_b: reader[5][1] = col_b',
        '                        if col_g: reader[6][1] = col_g',
        '                        if col_c: reader[10][1] = col_c',
        '                    else:',
        '                        reader[5][1] = factory_code',
        '                        reader[16][1] = date_str',
        '                    with open(new_file_path, \'w\', encoding=\'utf-8-sig\', newline=\'\') as f:',
        '                        writer = csv.writer(f)',
        '                        writer.writerows(reader)'
    ]
    lines[start_idx:end_idx] = replacement

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
