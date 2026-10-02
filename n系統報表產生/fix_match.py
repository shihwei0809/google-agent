import os, sys

def fix():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Overwrite the match logic
    new_logic = '''
                            for item in valid_data:
                                b_no = str(item.get("batch", "")).strip().upper()
                                # Just check if batch is in the file name or in A7, robustly
                                if b_no and (b_no in l_batch or b_no in orig_filename.upper()):
                                    matched_item = item
                                    l_batch = b_no
                                    break
'''
    old_logic = '''
                            for item in valid_data:
                                b_no = str(item.get("batch", "")).strip().upper()
                                if b_no == l_batch or b_no in orig_filename.upper():
                                    matched_item = item
                                    l_batch = b_no
                                    break
'''
    content = content.replace(old_logic.strip(), new_logic.strip())

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCHED")
fix()
