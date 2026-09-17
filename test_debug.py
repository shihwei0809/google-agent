import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'found_batch = _extract_batch_from_coa_bytes(coa_file["content"], ext)' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'try:\n')
        new_lines.append(indent + '    with open("c_log.txt", "a", encoding="utf-8") as f: f.write(f"found_batch: {found_batch}, valid: {list(valid_records.keys())}\\n")\n')
        new_lines.append(indent + 'except: pass\n')
    if 'if not matched_batch:' in line and 'continue' in lines[i+1]:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'try:\n')
        new_lines.append(indent + '    with open("c_log.txt", "a", encoding="utf-8") as f: f.write(f"Skipping {base_name}\\n")\n')
        new_lines.append(indent + 'except: pass\n')
    if 'zip_file.writestr(f"{folder_name}/{sub_folder}/{new_base}"' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + 'try:\n')
        new_lines.append(indent + '    with open("c_log.txt", "a", encoding="utf-8") as f: f.write(f"Wrote {new_base} to zip\\n")\n')
        new_lines.append(indent + 'except: pass\n')

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
