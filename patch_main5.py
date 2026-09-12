# -*- coding: utf-8 -*-
import codecs
import os

path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# Remove lorry generation from load_coa_forms
start_idx = -1
for i, l in enumerate(lines):
    if '# 產生生產履歷 (不受 COA 檔案類型限制)' in l:
        start_idx = i
        break

end_idx = -1
for i in range(start_idx, len(lines)):
    if '# 處理 COA 本身' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    del lines[start_idx : end_idx]

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
