# -*- coding: utf-8 -*-
import codecs
import os
import re

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

target_regex_idx = -1
for i, l in enumerate(lines):
    if 'date_pattern = r\'\d{4}[-_]?\d{2}[-_]?\d{2}|\d{8}\'' in l:
        target_regex_idx = i
        break

if target_regex_idx != -1:
    lines[target_regex_idx-4 : target_regex_idx+15] = [
        '                idx = base_name.upper().find(matched_batch)',
        '                prefix = base_name[:idx]',
        '                suffix = base_name[idx + len(matched_batch):]',
        '                ',
        '                date_pattern = r\'\d{4}[-_]?\d{2}[-_]?\d{2}|\d{8}\'',
        '                mmdd_pattern = r\'\\b\d{4}(?=[-_]$)\'',
        '                date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date',
        '                ',
        '                if re.search(date_pattern, prefix):',
        '                    prefix = re.sub(date_pattern, formatted_date, prefix)',
        '                elif re.search(mmdd_pattern, prefix):',
        '                    prefix = re.sub(mmdd_pattern, date_MMDD, prefix)',
        '                else:',
        '                    if prefix.endswith(\"_\") or prefix.endswith(\"-\"):',
        '                        prefix = formatted_date + prefix',
        '                    else:',
        '                        prefix = formatted_date + \"_\" + prefix if prefix else formatted_date + \"_\"',
        '                ',
        '                new_base = f\"{prefix}{base_name[idx:idx+len(matched_batch)]}{suffix}\"'
    ]

target_wb_idx = -1
for i, l in enumerate(lines):
    if 'if ext.lower() in [\'.xlsx\', \'.xls\']:' in l:
        target_wb_idx = i
        break

if target_wb_idx != -1:
    lines[target_wb_idx : target_wb_idx+6] = [
        '                if ext.lower() in [\'.xlsx\', \'.xls\']:',
        '                    wb = openpyxl.load_workbook(file_path)',
        '                    ws = wb.active',
        '                    ',
        '                    if hasattr(self, \"imported_lorry_files\") and self.imported_lorry_files:',
        '                        col_b, col_g, col_c = \"\", \"\", \"\"',
        '                        try:',
        '                            src_wb_l = openpyxl.load_workbook(self.imported_lorry_files[0], data_only=True)',
        '                            src_ws_l = src_wb_l.active',
        '                            batch_row_map = {}',
        '                            for r in range(7, src_ws_l.max_row + 1):',
        '                                val = str(src_ws_l.cell(row=r, column=1).value or \"\").strip().upper()',
        '                                if val and val not in batch_row_map:',
        '                                    batch_row_map[val] = r',
        '                            ',
        '                            matched_r = batch_row_map.get(matched_batch)',
        '                            if matched_r:',
        '                                col_b = str(src_ws_l.cell(row=matched_r, column=2).value or \"\").strip()',
        '                                col_c = str(src_ws_l.cell(row=matched_r, column=3).value or \"\").strip()',
        '                                col_g = str(src_ws_l.cell(row=matched_r, column=7).value or \"\").strip()',
        '                                ',
        '                                # 產生生產履歷',
        '                                wb_l = build_single_row_lorry_workbook(src_ws_l, matched_r)',
        '                                lorry_out_name = f\"Chemical_Lorry_{new_base}{ext}\"',
        '                                out_l_path = os.path.join(loc_folder, lorry_out_name)',
        '                                wb_l.save(out_l_path)',
        '                                wb_l.close()',
        '                                ',
        '                            src_wb_l.close()',
        '                        except Exception as le:',
        '                            error_msgs.append(f\"產生生產履歷失敗: {le}\")',
        '                            ',
        '                        # 寫入 COA (B, G, C)',
        '                        if col_b: ws[\"B6\"] = col_b',
        '                        if col_g: ws[\"B7\"] = col_g',
        '                        if col_c: ws[\"B11\"] = col_c',
        '                    else:',
        '                        ws[\"B6\"] = factory_code',
        '                        ws[\"B17\"] = date_str',
        '                        ',
        '                    wb.save(new_file_path)',
        '                    try:',
        '                        wb.close()',
        '                    except:',
        '                        pass'
    ]

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
