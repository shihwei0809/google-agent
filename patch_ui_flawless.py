import os
import re

def patch_main(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update headers
    h_pattern = r'\(7,\s*".*?"\),\s*\(8,\s*".*?"\)\s*\]'
    h_repl = r'''(7, "採購單號"),
            (8, "出貨區 (貼上)"),
            (9, "料號 (自動)"),
            (10, "清空單列")
        ]'''
    content = re.sub(h_pattern, h_repl, content)

    # 2. Update add_input_rows UI creation
    row_pattern = r'(po_entry\.grid\(row=row_grid_idx,\s*column=7,\s*padx=2,\s*pady=2,\s*sticky="ew"\))(.*?)(\# Col 8.*?)(btn_clear_row\.grid\(row=row_grid_idx,\s*column=)8(.*?pady=2\))'
    row_repl = r'\1\n\n            # Col 8: 出貨區\n            origin_var = tk.StringVar()\n            origin_entry = tk.Entry(self.scrollable_frame, textvariable=origin_var, width=12, font=("Arial", 10), fg="orange")\n            origin_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")\n\n            # Col 9: 料號\n            part_var = tk.StringVar()\n            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, width=12, font=("Arial", 10), fg="purple")\n            part_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")\g<2>\g<3>\g<4>10\g<5>'
    content = re.sub(row_pattern, row_repl, content, flags=re.DOTALL)

    # 3. Update dictionary packing
    dict_pattern = r'("po_var": po_var\s*\})'
    dict_repl = r'"po_var": po_var,\n                "origin_var": origin_var,\n                "part_var": part_var\n            }'
    content = re.sub(dict_pattern, dict_repl, content)

    # 4. clear_all_rows and clear_single_row
    for prefix in ['entry', r'self\.entries\[r_idx\]']:
        clear_pattern = rf'if "po_var" in {prefix}: {prefix}\["po_var"\]\.set\(""\)'
        clear_repl = rf'if "po_var" in {prefix}: {prefix}["po_var"].set("")\n            if "origin_var" in {prefix}: {prefix}["origin_var"].set("")\n            if "part_var" in {prefix}: {prefix}["part_var"].set("")'
        content = re.sub(clear_pattern, clear_repl, content)

    # 5. Add update_part_no and bind trace
    trace_pattern = r'loc_var\.trace_add\("write", lambda name, index, mode, lv=loc_var, lcv=long_code_var: self\.on_loc_change\(lv, lcv\)\)'
    trace_repl = r'loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, lcv=long_code_var: self.on_loc_change(lv, lcv))\n            origin_var.trace_add("write", lambda name, index, mode, lv=loc_var, ov=origin_var, pv=part_var: self.update_part_no(lv, ov, pv))\n            loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, ov=origin_var, pv=part_var: self.update_part_no(lv, ov, pv))'
    content = re.sub(trace_pattern, trace_repl, content)

    update_func = r'''    def update_part_no(self, loc_var, origin_var, part_var):
        if not hasattr(self, 'part_mapping_dict'): return
        loc = loc_var.get().strip().upper()
        origin = origin_var.get().strip()
        if loc in self.part_mapping_dict:
            info = self.part_mapping_dict[loc]
            part_no = info["default"]
            for k, v in info["origins"].items():
                if k in origin:
                    part_no = v
                    break
            part_var.set(part_no)
        else:
            part_var.set("")'''
    content = content.replace('    def on_loc_change', update_func + '\n\n    def on_loc_change')

    # 6. parse_pasted_row_items
    parse_pattern = r'(res = \{"batch": "", "loc": "", "date": "", "time": "", "mod_time": "")(\})'
    parse_repl = r'\1, "origin": ""\2'
    content = re.sub(parse_pattern, parse_repl, content)

    ret_res_repl = r'''for p in clean_parts:
            p_upper = p.upper()
            if not res.get("origin") and any(k in p_upper for k in ["崙尾", "彰濱", "L1", "L2"]):
                res["origin"] = p
                
        return res

    def on_paste'''
    content = content.replace('return res\n\n    def on_paste', ret_res_repl)

    on_paste_pattern = r'elif parsed\["loc"\]:\n\s*self\.entries\[curr_row\]\["loc_var"\]\.set\(parsed\["loc"\]\)'
    on_paste_repl = 'elif parsed["loc"]:\n                            self.entries[curr_row]["loc_var"].set(parsed["loc"])\n                            if parsed.get("origin"):\n                                self.entries[curr_row]["origin_var"].set(parsed["origin"])'
    content = re.sub(on_paste_pattern, on_paste_repl, content)

    multi_paste_pattern = r'(if parsed\["loc"\]:\n\s*self\.entries\[curr_row\]\["loc_var"\]\.set\(parsed\["loc"\]\))'
    multi_paste_repl = r'\1\n                    if parsed.get("origin"):\n                        self.entries[curr_row]["origin_var"].set(parsed["origin"])'
    content = re.sub(multi_paste_pattern, multi_paste_repl, content)


    # 7. generate_files
    gen_pattern = r'"po": po_val\n\s*\}\)'
    gen_repl = r'"po": po_val,\n                                "part_no": row["part_var"].get().strip() if "part_var" in row else ""\n                            })'
    content = re.sub(gen_pattern, gen_repl, content)

    override_pattern = r'(mat_row = find_row_by_label\(ws, \[\'料號\'\]\) or 3\s*sup_row = find_row_by_label\(ws, \[\'供應商\'\]\) or 9)'
    override_repl = r'\1\n                        if data.get("part_no"):\n                            ws.cell(row=mat_row, column=3).value = data["part_no"]'
    content = re.sub(override_pattern, override_repl, content)

    # 8. load_mapping
    load_func_pattern = r'    def load_mapping\(self\):.*?if hasattr\(self, "lbl_mapping_status"\):'
    load_func_repl = r'''    def load_mapping(self):
        self.mapping_dict = {}
        self.part_mapping_dict = {}
        if os.path.exists(self.mapping_path):
            try:
                map_wb = openpyxl.load_workbook(self.mapping_path, data_only=True)
                map_ws = map_wb.active
                rows = list(map_ws.iter_rows(values_only=True))
                if rows:
                    headers = [str(h).strip() if h else "" for h in rows[0]]
                    for row in rows[1:]:
                        if row and len(row) >= 2 and row[0] and row[1]:
                            loc_key = str(row[0]).strip().upper()
                            loc_val = str(row[1]).strip()
                            if any(kw in loc_key for kw in ("到貨", "地點", "SHORT", "LOCATION", "KEY", "HEADER")):
                                continue
                            self.mapping_dict[loc_key] = loc_val
                            info = {"default": str(row[2]).strip() if len(row) > 2 and row[2] else "", "origins": {}}
                            for i in range(3, len(headers)):
                                if i < len(row) and row[i] is not None:
                                    h_name = headers[i]
                                    if h_name: info["origins"][h_name] = str(row[i]).strip()
                            self.part_mapping_dict[loc_key] = info
                map_wb.close()
            except Exception as e:
                pass

        if hasattr(self, "lbl_mapping_status"):'''
    content = re.sub(load_func_pattern, load_func_repl, content, flags=re.DOTALL)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

patch_main(r'D:\GOOGLE ANGET\三合一單自動產生器\main.py')
