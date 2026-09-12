# -*- coding: utf-8 -*-
import codecs
path = r'c:\GOOGLE ANGET\三合一單自動產生器\main.py'
lines = codecs.open(path, 'r', 'utf-8').read().splitlines()
for i, l in enumerate(lines):
    if 'for target_path in' in l and 'session.json' in l and 'output_dir' in l:
        lines[i] = '                for target_path in [os.path.join(self.base_dir, "last_generated_session.json")]:'
        break
with codecs.open(path, 'w', 'utf-8') as f:
    for line in lines:
        f.write(line + '\n')
print('Removed from main.py')
