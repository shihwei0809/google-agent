import re

with open('main_patched.py', 'r', encoding='utf-8') as f:
    content = f.read()

func_code = '''
    def load_coa_forms(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇要載入的 COA 表單 (可多選)",
            filetypes=[("Excel 或 CSV", "*.xlsx *.xls *.csv"), ("所有檔案", "*.*")]
        )
        if not file_paths:
            return

        valid_batches = {}
        for row in self.entries:
            if row["chk_var"].get():
                batch = row["batch_var"].get().strip().upper()
                if batch:
                    valid_batches[batch] = row

        if not valid_batches:
            messagebox.showwarning("提示", "請先在列表中填寫並勾選包含批號的資料！")
            return

        success_count = 0
        error_msgs = []

        for file_path in file_paths:
            try:
                base_name, ext = os.path.splitext(os.path.basename(file_path))
                dir_name = os.path.dirname(file_path)
                
                matched_batch = None
                for b in valid_batches:
                    if b in base_name.upper():
                        matched_batch = b
                        break
                
                if not matched_batch:
                    error_msgs.append(f"找不到對應批號: {os.path.basename(file_path)}")
                    continue
                
                row = valid_batches[matched_batch]
                loc_str = row["loc_var"].get().strip()
                # 廠區代號是用長代號的2-5碼 (index 1 to 4)
                factory_code = loc_str[1:5] if len(loc_str) >= 5 else loc_str
                
                date_str = row["date_var"].get().strip()
                formatted_date = date_str.replace("/", "").replace("-", "")
                
                # split on the first occurrence (case-insensitive)
                idx = base_name.upper().find(matched_batch)
                prefix = base_name[:idx]
                suffix = base_name[idx + len(matched_batch):]
                
                # replace date in prefix
                date_pattern = r'\d{4}[-_]?\d{2}[-_]?\d{2}|\d{8}'
                if re.search(date_pattern, prefix):
                    prefix = re.sub(date_pattern, formatted_date, prefix)
                else:
                    if prefix.endswith("_") or prefix.endswith("-"):
                        prefix = formatted_date + prefix
                    else:
                        prefix = formatted_date + "_" + prefix if prefix else formatted_date + "_"
                
                # suffix adds factory_code
                if suffix.startswith("_") or suffix.startswith("-"):
                    new_suffix = f"_{factory_code}{suffix}"
                else:
                    new_suffix = f"_{factory_code}_{suffix}" if suffix else f"_{factory_code}"
                
                new_base = f"{prefix}{base_name[idx:idx+len(matched_batch)]}{new_suffix}"
                new_file_path = os.path.join(dir_name, new_base + ext)
                
                if ext.lower() in ['.xlsx', '.xls']:
                    wb = openpyxl.load_workbook(file_path)
                    ws = wb.active
                    ws['B6'] = factory_code
                    ws['B17'] = date_str
                    wb.save(new_file_path)
                elif ext.lower() == '.csv':
                    import csv
                    # Detect encoding for csv
                    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        reader = list(csv.reader(f))
                    # pad rows if necessary
                    while len(reader) <= 16:
                        reader.append([])
                    for r in reader:
                        while len(r) <= 1:
                            r.append("")
                    
                    reader[5][1] = factory_code
                    reader[16][1] = date_str
                    
                    with open(new_file_path, 'w', encoding='utf-8-sig', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerows(reader)
                
                success_count += 1
            except Exception as e:
                error_msgs.append(f"處理 {os.path.basename(file_path)} 失敗: {str(e)}")

        msg = f"成功處理 {success_count} 份 COA 表單。"
        if error_msgs:
            msg += "\n\n錯誤紀錄:\n" + "\n".join(error_msgs)
            messagebox.showwarning("完成", msg)
        else:
            messagebox.showinfo("完成", msg)

'''

# find def upload_coa(self):
match = re.search(r'    def upload_coa\(self\):', content)
if match:
    start_idx = match.start()
    content = content[:start_idx] + func_code + "\n" + content[start_idx:]

with open('main_patched.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched step 2')
