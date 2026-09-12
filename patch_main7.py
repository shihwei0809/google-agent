# -*- coding: utf-8 -*-
import codecs
from datetime import datetime

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# Find the location of matched_r logic
idx_matched_r = -1
for i, l in enumerate(lines):
    if 'matched_r = batch_row_map.get(matched_batch)' in l:
        idx_matched_r = i
        break

if idx_matched_r != -1:
    # replace col_c logic
    # Original:
    #                             col_b = str(src_ws_l.cell(row=matched_r, column=2).value or "").strip()
    #                             col_c = str(src_ws_l.cell(row=matched_r, column=3).value or "").strip()
    #                             col_g = str(src_ws_l.cell(row=matched_r, column=7).value or "").strip()
    
    replace_start = idx_matched_r + 1
    replace_end = idx_matched_r + 4
    
    lines[replace_start:replace_end] = [
        '                            col_b = str(src_ws_l.cell(row=matched_r, column=2).value or "").strip()',
        '                            raw_c = src_ws_l.cell(row=matched_r, column=3).value',
        '                            if isinstance(raw_c, datetime):',
        '                                col_c = f"{raw_c.year}/{raw_c.month}/{raw_c.day}"',
        '                            else:',
        '                                col_c = str(raw_c or "").strip().split()[0] if raw_c else ""',
        '                            col_g = str(src_ws_l.cell(row=matched_r, column=7).value or "").strip()',
        '                            ',
        '                            # 找出排程中的採購單號前 10 碼',
        '                            po_no = ""',
        '                            for rec in records:',
        '                                if str(rec.get("batch") or "").strip().upper() == matched_batch:',
        '                                    full_po = str(rec.get("po") or "").strip()',
        '                                    po_no = full_po[:10] if len(full_po) >= 10 else full_po',
        '                                    break'
    ]

# Now inject writing po_no into the XLSX and CSV logic
# For XLSX:
idx_xlsx = -1
for i, l in enumerate(lines):
    if 'if col_c: ws["B11"] = col_c' in l:
        idx_xlsx = i
        break

if idx_xlsx != -1:
    lines.insert(idx_xlsx + 1, '                        if \'po_no\' in locals() and po_no: ws["B12"] = po_no')

# For CSV:
idx_csv = -1
for i, l in enumerate(lines):
    if 'if col_c: reader[10][1] = col_c' in l:
        idx_csv = i
        break

if idx_csv != -1:
    # also we need to ensure reader has enough rows, currently it appends to 16, which is row 17.
    # index 11 is row 12.
    lines.insert(idx_csv + 1, '                        if \'po_no\' in locals() and po_no: reader[11][1] = po_no')

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
