import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'found_batch = _extract_batch_from_coa_bytes(coa_file["content"], ext)' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + "with open(r'd:\\GOOGLE ANGET\\server_debug.log', 'a', encoding='utf-8') as lg: lg.write(f'Extracted: {found_batch}\\n')\n")
    if 'if not matched_batch:' in line and 'continue' in lines[i+1]:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + "with open(r'd:\\GOOGLE ANGET\\server_debug.log', 'a', encoding='utf-8') as lg: lg.write(f'Skipped: {base_name}\\n')\n")
    if 'zip_file.writestr(f"{folder_name}/{sub_folder}/{new_base}"' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + "with open(r'd:\\GOOGLE ANGET\\server_debug.log', 'a', encoding='utf-8') as lg: lg.write(f'Wrote to zip: {new_base}\\n')\n")
    if 'print(f"[COA CSV Error] {e}")' in line or 'print(f"[COA Excel Error] {e}")' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(indent + "with open(r'd:\\GOOGLE ANGET\\server_debug.log', 'a', encoding='utf-8') as lg: lg.write(f'Exception: {e}\\n')\n")

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
