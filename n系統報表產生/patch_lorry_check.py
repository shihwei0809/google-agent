import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the factory comparison in load_chemical_lorry_file
old_factory = '''
            wrong_factory_msgs = []
            for b, lc, s_loc in table_entries:
                if b in lorry_batches:
                    l_fac = lorry_factory_info.get(b, "")
                    import re as _re
                    fc_match = _re.search(r'\d+[A-Za-z]+\d+', s_loc)
                    expected_fc = fc_match.group(0).upper() if fc_match else s_loc
                    
                    if not l_fac:
                        wrong_factory_msgs.append(f"• 批號 {b}：在履歷檔中廠區空白，應含 {expected_fc}")
                    elif expected_fc not in l_fac:
                        wrong_factory_msgs.append(f"• 批號 {b}：在履歷檔中廠區為 {l_fac}，未對齊地點 (應含 {expected_fc})")
'''
# Actually let's just do it with a more robust replace, I don't know the exact code there because I didn't print all of it.
