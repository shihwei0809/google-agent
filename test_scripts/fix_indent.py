import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'name_no_ext, ext_part = os.path.splitext(base_name)' in line:
        new_lines.append('                            name_no_ext, ext_part = os.path.splitext(base_name)\n')
    elif 'date_pattern = r' in line and '\\d{4}' in line:
        new_lines.append('                        date_pattern = r"\\d{4}[-_]?\\d{2}[-_]?\\d{2}|\\d{8}"\n')
    elif 'text_content = coa_file["content"].decode' in line:
        new_lines.append('                                text_content = coa_file["content"].decode("utf-8-sig", errors="ignore")\n')
    elif 'wb = openpyxl.load_workbook' in line:
        new_lines.append('                                wb = openpyxl.load_workbook(io.BytesIO(coa_file["content"]))\n')
    else:
        new_lines.append(line)

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)
