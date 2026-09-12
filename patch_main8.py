# -*- coding: utf-8 -*-
import codecs

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# We need to find the po_no logic in load_coa_forms
start_idx = -1
end_idx = -1
for i, l in enumerate(lines):
    if '# 找出排程中的採購單號前 10 碼' in l:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx, start_idx + 20):
        if 'break' in lines[i] and 'if str(rec.get' in lines[i-3]:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    lines[start_idx : end_idx + 1] = [
        '                            # 找出排程中的採購單號前 10 碼',
        '                            po_no = ""',
        '                            matched_row = valid_batches.get(matched_batch)',
        '                            if matched_row and "po_var" in matched_row:',
        '                                full_po = matched_row["po_var"].get().strip()',
        '                                po_no = full_po[:10] if len(full_po) >= 10 else full_po'
    ]

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
