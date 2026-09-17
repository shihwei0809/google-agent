import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 'if not matched_batch:' in line and 'continue' in lines[i+1]:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'if not matched_batch:\n')
        new_lines.append(indent + '    found_batch = _extract_batch_from_coa_bytes(coa_file["content"], ext)\n')
        new_lines.append(indent + '    if found_batch:\n')
        new_lines.append(indent + '        for b in valid_records:\n')
        new_lines.append(indent + '            if b == found_batch or b in found_batch or found_batch in b:\n')
        new_lines.append(indent + '                matched_batch = b\n')
        new_lines.append(indent + '                break\n')
    elif 'idx = base_name.upper().find(matched_batch)' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'idx = base_name.upper().find(matched_batch)\n')
        new_lines.append(indent + 'if idx == -1:\n')
        new_lines.append(indent + '    import os\n')
        new_lines.append(indent + '    name_no_ext, ext_part = os.path.splitext(base_name)\n')
        new_lines.append(indent + '    prefix = name_no_ext + "_"\n')
        new_lines.append(indent + '    suffix = ext_part\n')
        new_lines.append(indent + '    idx = len(prefix)\n')
        new_lines.append(indent + '    base_name = prefix + matched_batch + suffix\n')
        new_lines.append(indent + 'else:\n')
        new_lines.append(indent + '    prefix = base_name[:idx]\n')
        new_lines.append(indent + '    suffix = base_name[idx + len(matched_batch):]\n')
    elif 'prefix = base_name[:idx]' in line and 'suffix = base_name[idx + len(matched_batch):]' in lines[i+1]:
        pass # skip old
    elif 'suffix = base_name[idx + len(matched_batch):]' in line and 'prefix = base_name[:idx]' in lines[i-1]:
        pass # skip old
    else:
        new_lines.append(line)

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
