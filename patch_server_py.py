import os
import re

def patch_server_py():
    path = r'D:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. UTF-8-SIG to Big5 & Padding Fix
    old_csv_read = '''                                except UnicodeDecodeError:
                                    text_content = coa_file["content"].decode('utf-8-sig', errors='ignore')
                                reader = list(csv.reader(text_content.splitlines()))
                                while len(reader) <= 17: reader.append([])'''
    new_csv_read = '''                                except UnicodeDecodeError:
                                    text_content = coa_file["content"].decode('utf-8-sig', errors='ignore')
                                reader = list(csv.reader(text_content.splitlines()))
                                while len(reader) <= 17: reader.append([])
                                # 僅針對會修改的行補齊欄位，避免產生多餘逗號破壞 TSMC 系統解析
                                for r_idx in [5, 6, 10, 11]:
                                    if r_idx < len(reader):
                                        while len(reader[r_idx]) < 12: reader[r_idx].append("")'''
    content = content.replace(old_csv_read, new_csv_read)
    
    old_csv_write = '''                                output = io.StringIO()
                                writer = csv.writer(output)
                                writer.writerows(reader)
                                new_content = output.getvalue().encode('utf-8-sig')'''
    new_csv_write = '''                                output = io.StringIO()
                                writer = csv.writer(output)
                                writer.writerows(reader)
                                new_content = output.getvalue().encode('big5')'''
    content = content.replace(old_csv_write, new_csv_write)

    # 2. regex for factory code
    content = re.sub(
        r'factory_code\s*=\s*loc\[1:5\]\s*if\s*len\(loc\)\s*>=\s*5\s*else\s*loc', 
        r"import re\n                                    match = re.search(r'[A-Za-z0-9]+', loc)\n                                    factory_code = match.group(0) if match else loc", 
        content
    )
    # wait, the exact original is: factory_code = loc[1:5] if len(loc) >= 5 else loc
    content = content.replace(
        'factory_code = loc[1:5] if len(loc) >= 5 else loc',
        'import re\n                                    match = re.search(r\'[A-Za-z0-9]+\', loc)\n                                    factory_code = match.group(0) if match else loc'
    )
    content = content.replace(
        'factory_code = loc[1:5]',
        'import re\n                                    match = re.search(r\'[A-Za-z0-9]+\', loc)\n                                    factory_code = match.group(0) if match else loc'
    )

    # 4. Multiple files loop in generate_all
    lines = content.split('\n')
    in_lorry_loop = False
    in_coa_loop = False
    new_lines = []

    for idx, line in enumerate(lines):
        if 'extra_file = EXTRA_FILE_CACHE.get("latest_file")' in line and idx + 1 < len(lines) and 'if do_lorry and extra_file and' in lines[idx+1]:
            new_lines.append('            lorry_files = EXTRA_FILE_CACHE.get("files", [])')
        elif 'if do_lorry and extra_file and' in line:
            new_lines.append('            if do_lorry and lorry_files:')
            new_lines.append('                for extra_file in lorry_files:')
            new_lines.append('                    if extra_file["ext"].lower() not in [".xlsx", ".xls"]: continue')
            in_lorry_loop = True
        elif in_lorry_loop and 'src_wb.close()' in line:
            new_lines.append('                    ' + line.rstrip('\r\n'))
            in_lorry_loop = False
        elif in_lorry_loop and 'except Exception as ex:' in line:
            new_lines.append('                    except Exception as ex:')
        elif in_lorry_loop and 'print(f"[Lorry Error] {ex}")' in line:
            new_lines.append('                        print(f"[Lorry Error] {ex}")')
        elif in_lorry_loop:
            if line.strip():
                new_lines.append('    ' + line.rstrip('\r\n'))
            else:
                new_lines.append(line.rstrip('\r\n'))
                
        elif 'extra_file = EXTRA_FILE_CACHE.get("latest_file")' in line and idx + 1 < len(lines) and 'if extra_file and extra_file' in lines[idx+1]:
            new_lines.append('                    lorry_files = EXTRA_FILE_CACHE.get("files", [])')
        elif 'if extra_file and extra_file["ext"].lower() in [".xlsx", ".xls"]:' in line:
            new_lines.append('                    if lorry_files:')
            new_lines.append('                        for extra_file in lorry_files:')
            new_lines.append('                            if extra_file["ext"].lower() not in [".xlsx", ".xls"]: continue')
            in_coa_loop = True
        elif in_coa_loop and 'src_wb_l.close()' in line:
            new_lines.append('                            ' + line.rstrip('\r\n'))
            in_coa_loop = False
        elif in_coa_loop and 'except Exception as e:' in line:
            new_lines.append('                            except Exception as e:')
        elif in_coa_loop and 'print(f"[COA Lorry Extraction Error]' in line:
            new_lines.append('                                ' + line.rstrip('\r\n'))
        elif in_coa_loop:
            if line.strip():
                new_lines.append('    ' + line.rstrip('\r\n'))
            else:
                new_lines.append(line.rstrip('\r\n'))
        else:
            new_lines.append(line.rstrip('\r\n'))

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

patch_server_py()
print("Sheng Yi server.py patched successfully!")
