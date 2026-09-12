# -*- coding: utf-8 -*-
import codecs

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# We need to insert the data extraction logic back
insert_idx = -1
for i, l in enumerate(lines):
    if '# 處理 COA 本身' in l:
        insert_idx = i
        break

if insert_idx != -1:
    insert_lines = [
        '                # 提取生產履歷的對應欄位',
        '                if hasattr(self, "imported_lorry_files") and self.imported_lorry_files:',
        '                    try:',
        '                        src_wb_l = openpyxl.load_workbook(self.imported_lorry_files[0], data_only=True)',
        '                        src_ws_l = src_wb_l.active',
        '                        batch_row_map = {}',
        '                        for r in range(7, src_ws_l.max_row + 1):',
        '                            val = str(src_ws_l.cell(row=r, column=1).value or "").strip().upper()',
        '                            if val and val not in batch_row_map:',
        '                                batch_row_map[val] = r',
        '                        ',
        '                        matched_r = batch_row_map.get(matched_batch)',
        '                        if matched_r:',
        '                            col_b = str(src_ws_l.cell(row=matched_r, column=2).value or "").strip()',
        '                            col_c = str(src_ws_l.cell(row=matched_r, column=3).value or "").strip()',
        '                            col_g = str(src_ws_l.cell(row=matched_r, column=7).value or "").strip()',
        '                        src_wb_l.close()',
        '                    except Exception as le:',
        '                        error_msgs.append(f"讀取生產履歷失敗: {le}")'
    ]
    lines = lines[:insert_idx] + insert_lines + lines[insert_idx:]

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
