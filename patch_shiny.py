# -*- coding: utf-8 -*-
import codecs
path = r'c:\GOOGLE ANGET\勝一三合一單產生系統\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()

# 1. Fix _1 bug (remove while loop)
start_1 = -1
for i, l in enumerate(lines):
    if 'counter = 1' in l and 'while os.path.exists' in lines[i+1]:
        start_1 = i
        break
if start_1 != -1:
    # Delete the counter and while loop logic
    # lines[i] to lines[i+4]
    del lines[start_1 : start_1 + 5]

# 2. Fix session.json bug (only output to base_dir, not output_dir)
for i, l in enumerate(lines):
    if 'for target_path in' in l and 'session.json' in l and 'output_dir' in l:
        lines[i] = '                for target_path in [os.path.join(self.base_dir, "last_generated_session.json")]:'
        break

with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Patch applied successfully')
