import os

fpath = r'C:\GOOGLE ANGET\n系統報表產生\main.py'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. UI Headers
c1_old = """        headers = [
            (0, "產生"),
            (1, "項次"),
            (2, "批號 (請輸入10碼)"),
            (3, "數量 (ShipQty)"),
            (4, "地點 (如 15P5)"),
            (5, "長代號 (自動)"),
            (6, "出貨日期 📅"),
            (7, "採購單號"),
            (8, "料號 (自動)"),
            (9, "製造日"),
            (10, "保存期限"),
            (11, "剩餘天數"),
            (12, "清空單列")
        ]"""
c1_new = """        headers = [
            (0, "產生"),
            (1, "項次"),
            (2, "批號 (請輸入10碼)"),
            (3, "數量 (ShipQty)"),
            (4, "地點 (如 15P5)"),
            (5, "長代號 (自動)"),
            (6, "出貨日期 📅"),
            (7, "採購單號"),
            (8, "料號 (自動)"),
            (9, "品名"),
            (10, "製造日"),
            (11, "保存期限"),
            (12, "剩餘天數"),
            (13, "剩餘天數寫入COA"),
            (14, "清空單列")
        ]"""
content = content.replace(c1_old, c1_new)

# 2. Add input rows UI
c2_old = """            # Col 1: 項次
            lbl_num = tk.Label(self.scrollable_frame, text=str(row_idx), font=("Arial", 10))
            lbl_num.grid(row=row_grid_idx, column=1, padx=2, pady=2)
            
            # Col 2: 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(self.scrollable_frame, textvariable=batch_var, width=16, font=("Arial", 10))
            batch_entry.grid(row=row_grid_idx, column=2, padx=2, pady=2, sticky="ew")
            
            # Col 3: 槽號
            qty_var = tk.StringVar()
            qty_entry = tk.Entry(self.scrollable_frame, textvariable=qty_var, width=10, font=("Arial", 10), fg="blue")
            qty_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")
            
            # Col 4: 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(self.scrollable_frame, textvariable=loc_var, width=12, font=("Arial", 10))
            loc_entry.grid(row=row_grid_idx, column=4, padx=2, pady=2, sticky="ew")
            
            # Col 5: 長代號
            long_code_var = tk.StringVar()
            from tkinter import ttk
            long_code_combo = ttk.Combobox(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=16, font=("Arial", 10))
            long_code_combo.grid(row=row_grid_idx, column=5, padx=2, pady=2, sticky="ew")
            
            # Col 6: 出貨日期 (Entry + 📅 日曆按鈕)
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")
            
            date_var = tk.StringVar(value="")
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=11, font=("Arial", 10))
            date_entry.pack(side="left", fill="x", expand=True)
            
            btn_cal = tk.Button(date_frame, text="📅", command=lambda dv=date_var: self.open_calendar_dialog(dv), font=("Arial", 8), cursor="hand2")
            btn_cal.pack(side="right", padx=(2, 0))
            
            # Col 7: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=18, font=("Arial", 10), fg="#333")
            po_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")

            # Col 8: 料號
            part_var = tk.StringVar()
            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, width=12, font=("Arial", 10), fg="purple")
            part_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")

            # Col 9: 製造日
            mfg_var = tk.StringVar()
            mfg_entry = tk.Entry(self.scrollable_frame, textvariable=mfg_var, width=12, font=("Arial", 10), fg="black")
            mfg_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")

            # Col 10: 保存期限
            exp_var = tk.StringVar()
            exp_entry = tk.Entry(self.scrollable_frame, textvariable=exp_var, width=12, font=("Arial", 10), fg="black")
            exp_entry.grid(row=row_grid_idx, column=10, padx=2, pady=2, sticky="ew")

            # Col 11: 剩餘天數
            rem_var = tk.StringVar()
            rem_entry = tk.Entry(self.scrollable_frame, textvariable=rem_var, width=8, font=("Arial", 10), fg="red", state="readonly")
            rem_entry.grid(row=row_grid_idx, column=11, padx=2, pady=2, sticky="ew")

            # Col 12: 單列清空按鈕
            btn_clear_row = tk.Button(
                self.scrollable_frame, 
                text="清空", 
                command=lambda r=row_idx-1: self.clear_single_row(r), 
                font=("Microsoft JhengHei", 9, "bold"), 
                bg="#FFEBEE", 
                fg="#C62828", 
                cursor="hand2", 
                width=6,
                pady=1
            )
            btn_clear_row.grid(row=row_grid_idx, column=12, padx=4, pady=2)"""
c2_new = """            # Col 1: 項次
            lbl_num = tk.Label(self.scrollable_frame, text=str(row_idx), font=("Arial", 10), width=3)
            lbl_num.grid(row=row_grid_idx, column=1, padx=2, pady=2)
            
            # Col 2: 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(self.scrollable_frame, textvariable=batch_var, width=16, font=("Arial", 10))
            batch_entry.grid(row=row_grid_idx, column=2, padx=2, pady=2, sticky="ew")
            
            # Col 3: 槽號
            qty_var = tk.StringVar()
            qty_entry = tk.Entry(self.scrollable_frame, textvariable=qty_var, width=10, font=("Arial", 10), fg="blue")
            qty_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")
            
            # Col 4: 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(self.scrollable_frame, textvariable=loc_var, width=12, font=("Arial", 10))
            loc_entry.grid(row=row_grid_idx, column=4, padx=2, pady=2, sticky="ew")
            
            # Col 5: 長代號
            long_code_var = tk.StringVar()
            from tkinter import ttk
            long_code_combo = ttk.Combobox(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=12, font=("Arial", 10))
            long_code_combo.grid(row=row_grid_idx, column=5, padx=2, pady=2, sticky="ew")
            
            # Col 6: 出貨日期 (Entry + 📅 日曆按鈕)
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")
            
            date_var = tk.StringVar(value="")
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=11, font=("Arial", 10))
            date_entry.pack(side="left", fill="x", expand=True)
            
            btn_cal = tk.Button(date_frame, text="📅", command=lambda dv=date_var: self.open_calendar_dialog(dv), font=("Arial", 8), cursor="hand2")
            btn_cal.pack(side="right", padx=(2, 0))
            
            # Col 7: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=18, font=("Arial", 10), fg="#333")
            po_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")

            # Col 8: 料號
            part_var = tk.StringVar()
            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, width=9, font=("Arial", 10), fg="purple")
            part_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")

            # Col 9: 品名
            name_var = tk.StringVar()
            name_entry = tk.Entry(self.scrollable_frame, textvariable=name_var, width=15, font=("Arial", 10), fg="purple")
            name_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")

            # Col 10: 製造日
            mfg_var = tk.StringVar()
            mfg_entry = tk.Entry(self.scrollable_frame, textvariable=mfg_var, width=10, font=("Arial", 10), fg="black")
            mfg_entry.grid(row=row_grid_idx, column=10, padx=2, pady=2, sticky="ew")

            # Col 11: 保存期限
            exp_var = tk.StringVar()
            exp_entry = tk.Entry(self.scrollable_frame, textvariable=exp_var, width=10, font=("Arial", 10), fg="black")
            exp_entry.grid(row=row_grid_idx, column=11, padx=2, pady=2, sticky="ew")

            # Col 12: 剩餘天數
            rem_var = tk.StringVar()
            rem_entry = tk.Entry(self.scrollable_frame, textvariable=rem_var, width=6, font=("Arial", 10), fg="red", state="readonly")
            rem_entry.grid(row=row_grid_idx, column=12, padx=2, pady=2, sticky="ew")

            # Col 13: 剩餘天數寫入COA
            coa208_var = tk.BooleanVar(value=False)
            coa208_chk = tk.Checkbutton(self.scrollable_frame, variable=coa208_var)
            coa208_chk.grid(row=row_grid_idx, column=13, padx=2, pady=2)

            # Col 14: 單列清空按鈕
            btn_clear_row = tk.Button(
                self.scrollable_frame, 
                text="清空", 
                command=lambda r=row_idx-1: self.clear_single_row(r), 
                font=("Microsoft JhengHei", 9, "bold"), 
                bg="#FFEBEE", 
                fg="#C62828", 
                cursor="hand2", 
                width=6,
                pady=1
            )
            btn_clear_row.grid(row=row_grid_idx, column=14, padx=4, pady=2)"""
content = content.replace(c2_old, c2_new)

# 3. entries.append
c3_old = """                "part_var": part_var,
                "mfg_var": mfg_var,
                "exp_var": exp_var,
                "rem_var": rem_var
            })"""
c3_new = """                "part_var": part_var,
                "name_var": name_var,
                "mfg_var": mfg_var,
                "exp_var": exp_var,
                "rem_var": rem_var,
                "coa208_var": coa208_var
            })"""
content = content.replace(c3_old, c3_new)

# 4. clear_all_rows
c4_old = """                if "part_var" in entry: entry["part_var"].set("")
                if "mfg_var" in entry: entry["mfg_var"].set("")
                if "exp_var" in entry: entry["exp_var"].set("")
                if "rem_var" in entry: entry["rem_var"].set("")"""
c4_new = """                if "part_var" in entry: entry["part_var"].set("")
                if "name_var" in entry: entry["name_var"].set("")
                if "mfg_var" in entry: entry["mfg_var"].set("")
                if "exp_var" in entry: entry["exp_var"].set("")
                if "rem_var" in entry: entry["rem_var"].set("")
                if "coa208_var" in entry: entry["coa208_var"].set(False)"""
content = content.replace(c4_old, c4_new)

# 5. clear_single_row
c5_old = """            if "part_var" in entry: entry["part_var"].set("")
            if "mfg_var" in entry: entry["mfg_var"].set("")
            if "exp_var" in entry: entry["exp_var"].set("")
            if "rem_var" in entry: entry["rem_var"].set("")"""
c5_new = """            if "part_var" in entry: entry["part_var"].set("")
            if "name_var" in entry: entry["name_var"].set("")
            if "mfg_var" in entry: entry["mfg_var"].set("")
            if "exp_var" in entry: entry["exp_var"].set("")
            if "rem_var" in entry: entry["rem_var"].set("")
            if "coa208_var" in entry: entry["coa208_var"].set(False)"""
content = content.replace(c5_old, c5_new)

# 6. import_from_excel CSV horizontal
c6_old = """                        batch_col, loc_col, date_col, qty_col, time_col, mod_time_col, po_col, origin_col, mfg_col, exp_col = -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
                        start_row = 0"""
c6_new = """                        batch_col, loc_col, date_col, qty_col, time_col, mod_time_col, po_col, origin_col, mfg_col, exp_col = -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
                        name_col = -1
                        start_row = 0"""
content = content.replace(c6_old, c6_new)

c6_2_old = """                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx
                            if batch_col != -1 and (loc_col != -1 or date_col != -1):"""
c6_2_new = """                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx
                                if name_col == -1 and any(k in v for k in ["品名", "產品名稱", "PRODUCT", "NAME", "描述", "SPEC"]): name_col = c_idx
                            if batch_col != -1 and (loc_col != -1 or date_col != -1):"""
content = content.replace(c6_2_old, c6_2_new)

c6_3_old = """                            exp_val = str(get_c(exp_col) or "").strip()
                            if len(b_val) != 10 or not re.search(r'[0-9]', b_val):"""
c6_3_new = """                            exp_val = str(get_c(exp_col) or "").strip()
                            name_val = str(get_c(name_col) or "").strip() if name_col != -1 else ""
                            if len(b_val) != 10 or not re.search(r'[0-9]', b_val):"""
content = content.replace(c6_3_old, c6_3_new)

c6_4_old = """                                "origin": origin_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })"""
c6_4_new = """                                "origin": origin_val,
                                "name": name_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })"""
content = content.replace(c6_4_old, c6_4_new)

# 7. import_from_excel Excel horizontal
c7_old = """                        batch_col = -1
                        loc_col = -1
                        date_col = -1
                        qty_col = -1
                        time_col = -1
                        mod_time_col = -1
                        cust_col = -1
                        po_col = -1
                        origin_col = -1
                        mfg_col = -1
                        exp_col = -1
                        start_row = 0"""
c7_new = """                        batch_col = -1
                        loc_col = -1
                        date_col = -1
                        qty_col = -1
                        time_col = -1
                        mod_time_col = -1
                        cust_col = -1
                        po_col = -1
                        origin_col = -1
                        mfg_col = -1
                        exp_col = -1
                        name_col = -1
                        start_row = 0"""
content = content.replace(c7_old, c7_new)

c7_2_old = """                                if exp_col == -1 and any(k in v for k in ["到期", "保存", "EXP"]): exp_col = c_idx

                            if batch_col != -1 and (loc_col != -1 or date_col != -1):"""
c7_2_new = """                                if exp_col == -1 and any(k in v for k in ["到期", "保存", "EXP"]): exp_col = c_idx
                                if name_col == -1 and any(k in v for k in ["品名", "產品名稱", "PRODUCT", "NAME", "描述", "SPEC"]): name_col = c_idx

                            if batch_col != -1 and (loc_col != -1 or date_col != -1):"""
content = content.replace(c7_2_old, c7_2_new)

c7_3_old = """                            mfg_val = str(get_cell_val(mfg_col) or "").strip()
                            exp_val = str(get_cell_val(exp_col) or "").strip()

                            # 若預設欄位非 10 碼批號"""
c7_3_new = """                            mfg_val = str(get_cell_val(mfg_col) or "").strip()
                            exp_val = str(get_cell_val(exp_col) or "").strip()
                            name_val = str(get_cell_val(name_col) or "").strip() if name_col != -1 else ""

                            # 若預設欄位非 10 碼批號"""
content = content.replace(c7_3_old, c7_3_new)

c7_4_old = """                                "origin": origin_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })"""
c7_4_new = """                                "origin": origin_val,
                                "name": name_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })"""
content = content.replace(c7_4_old, c7_4_new)

# 8. Set name_var in import target_records loop
c8_old = """                    if rec.get("po"): row_e.get("po_var", tk.StringVar()).set(rec["po"])
                    if rec.get("mfg_date") and "mfg_var" in row_e: row_e["mfg_var"].set(rec["mfg_date"])
                    if rec.get("exp_date") and "exp_var" in row_e: row_e["exp_var"].set(rec["exp_date"])
                    
                total_imported += len(target_records)"""
c8_new = """                    if rec.get("po"): row_e.get("po_var", tk.StringVar()).set(rec["po"])
                    if rec.get("name") and "name_var" in row_e: row_e["name_var"].set(rec["name"])
                    if rec.get("mfg_date") and "mfg_var" in row_e: row_e["mfg_var"].set(rec["mfg_date"])
                    if rec.get("exp_date") and "exp_var" in row_e: row_e["exp_var"].set(rec["exp_date"])
                    
                total_imported += len(target_records)"""
content = content.replace(c8_old, c8_new)

# 9. COA generation for XLSX
c9_old = """                    if ext.lower() in ['.xlsx', '.xls']:
                        wb = openpyxl.load_workbook(file_path)
                        ws = wb.active
                        
                        ws["B6"] = long_code_val
                        if col_g: ws["B7"] = col_g
                        if qty_str: ws["B8"] = qty_str
                        if col_c_fmt: ws["B11"] = col_c_fmt
                        if date_str_fmt: ws["B12"] = date_str_fmt
                        if po_no: ws["B14"] = po_no

                        wb.save(new_file_path)"""
c9_new = """                    if ext.lower() in ['.xlsx', '.xls']:
                        wb = openpyxl.load_workbook(file_path)
                        ws = wb.active
                        
                        ws["B6"] = long_code_val
                        if col_g: ws["B7"] = col_g
                        if qty_str: ws["B8"] = qty_str
                        if col_c_fmt: ws["B11"] = col_c_fmt
                        if date_str_fmt: ws["B12"] = date_str_fmt
                        if po_no: ws["B14"] = po_no

                        if matched_row and matched_row.get('coa208_var') and matched_row['coa208_var'].get():
                            rem_days = matched_row.get('rem_var', tk.StringVar()).get().strip()
                            if rem_days:
                                ws['B208'] = rem_days

                        wb.save(new_file_path)"""
content = content.replace(c9_old, c9_new)

# 10. COA generation for CSV
c10_old = """                        reader[5][1] = long_code_val
                        if col_g: reader[6][1] = col_g
                        if qty_str: reader[7][1] = qty_str
                        if col_c_fmt: reader[10][1] = col_c_fmt
                        if date_str_fmt: reader[11][1] = date_str_fmt
                        if po_no: reader[13][1] = po_no
                            
                        with open(new_file_path, 'w', encoding='big5', errors='ignore', newline='') as f:"""
c10_new = """                        reader[5][1] = long_code_val
                        if col_g: reader[6][1] = col_g
                        if qty_str: reader[7][1] = qty_str
                        if col_c_fmt: reader[10][1] = col_c_fmt
                        if date_str_fmt: reader[11][1] = date_str_fmt
                        if po_no: reader[13][1] = po_no
                            
                        if matched_row and matched_row.get('coa208_var') and matched_row['coa208_var'].get():
                            rem_days = matched_row.get('rem_var', tk.StringVar()).get().strip()
                            if rem_days:
                                while len(reader) <= 207:
                                    reader.append([''] * 8)
                                while len(reader[207]) <= 1:
                                    reader[207].append("")
                                reader[207][1] = rem_days

                        with open(new_file_path, 'w', encoding='big5', errors='ignore', newline='') as f:"""
content = content.replace(c10_old, c10_new)


with open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
