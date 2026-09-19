import codecs
import os

path = r'd:\GOOGLE ANGET\銝?銝?株??\main.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'prefix = base_name + "_"' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'import os as _os\n')
        new_lines.append(indent + 'name_no_ext, ext_part = _os.path.splitext(base_name)\n')
        new_lines.append(indent + 'prefix = name_no_ext + "_"\n')
    elif 'suffix = ""' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'suffix = ext_part\n')
    elif 'base_name = prefix + matched_batch' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'base_name = prefix + matched_batch + suffix\n')
    else:
        new_lines.append(line)

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
