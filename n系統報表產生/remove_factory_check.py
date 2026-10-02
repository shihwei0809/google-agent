import sys

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if '# ===== 廠區防呆驗證 =====' in line:
        skip = True
        continue
    if '# ===== 廠區防呆驗證結束 =====' in line:
        skip = False
        continue
    if not skip:
        out.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
