import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

debug_inject = '''
                    for l_path in lorry_sources:
                        with open(os.path.join(os.path.expanduser('~'), 'Desktop', 'debug_lorry.txt'), 'a', encoding='utf-8') as dfile:
                            dfile.write(f"\\n--- Processing {l_path} ---\\n")
                            dfile.write(f"valid_data has {len(valid_data)} items\\n")
'''
content = content.replace('for l_path in lorry_sources:', debug_inject.strip())

debug_inject_2 = '''
                                    wb_l.close()
                                    with open(os.path.join(os.path.expanduser('~'), 'Desktop', 'debug_lorry.txt'), 'a', encoding='utf-8') as dfile:
                                        dfile.write(f"Saved: {out_l_path}\\n")
                                    success_lorry += 1
'''
content = content.replace('''
                                  wb_l.close()
                                  
                                  success_lorry += 1
'''.strip(), debug_inject_2.strip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("INJECTED DEBUG")
