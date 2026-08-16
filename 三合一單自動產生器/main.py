import tkinter as tk
from tkinter import ttk, messagebox
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import os
from datetime import datetime
import qrcode
from io import BytesIO

# ================= 核心邏輯 =================

def get_tank_from_batch(batch):
    batch = batch.strip()
    if not batch:
        return ""
    if len(batch) != 10:
        return "長度錯誤"
    # 如果是 J1 結尾，槽號是 5~7 碼 (長度 3)
    if batch.endswith('J1'):
        return batch[5:8]
    # 否則槽號是 5~8 碼 (長度 4)
    return batch[5:9]

def find_row_by_label(ws, labels):
    for r in range(1, 20):
        val = ws.cell(row=r, column=2).value
        if val and isinstance(val, str):
            for label in labels:
                if label in val:
                    return r
    return None

# ================= 介面與操作 =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("三合一單自動產生器")
        self.geometry("850x700")
        self.configure(padx=15, pady=15)
        
        # 檔案路徑預設為目前目錄
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.base_dir, "台積電槽車barcode三合一單-範本.xlsx")
        self.mapping_path = os.path.join(self.base_dir, "地點代號對照表.xlsx")
        
        self.mapping_dict = {}
        self.load_mapping()
        
        self.setup_ui()
        self.entries = []
        self.add_input_rows(20) # 預設 20 列

    def load_mapping(self):
        if os.path.exists(self.mapping_path):
            try:
                map_wb = openpyxl.load_workbook(self.mapping_path, data_only=True)
                map_ws = map_wb.active
                for row in map_ws.iter_rows(values_only=True):
                    if row and len(row) >= 2 and row[0] and row[1]:
                        loc_key = str(row[0]).strip().upper()
                        loc_val = str(row[1]).strip()
                        self.mapping_dict[loc_key] = loc_val
                map_wb.close()
            except Exception as e:
                pass

    def setup_ui(self):
        # 檔案狀態區
        status_frame = tk.LabelFrame(self, text="系統狀態", font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill="x", pady=(0, 10))
        
        t_color = "green" if os.path.exists(self.template_path) else "red"
        t_text = "✅ 已找到" if os.path.exists(self.template_path) else "❌ 未找到 (請將檔案放入資料夾)"
        tk.Label(status_frame, text=f"範本檔案 (台積電槽車barcode三合一單-範本.xlsx): {t_text}", fg=t_color).pack(anchor="w")
        
        m_color = "green" if os.path.exists(self.mapping_path) else "red"
        m_text = f"✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "❌ 未找到 (請將檔案放入資料夾)"
        tk.Label(status_frame, text=f"對照表檔案 (地點代號對照表.xlsx): {m_text}", fg=m_color).pack(anchor="w")

        # 提示區與匯入按鈕
        top_ctrl_frame = tk.Frame(self)
        top_ctrl_frame.pack(fill="x", pady=(0, 5))
        tk.Label(top_ctrl_frame, text="可以直接在「批號」欄位按下 Ctrl+V，貼上從 Excel 複製的多筆資料\n或點擊右方按鈕直接匯入 Excel 檔案：", fg="#555", justify="left").pack(side="left")
        tk.Button(top_ctrl_frame, text="📥 從 Excel 匯入", command=self.import_from_excel, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), padx=10).pack(side="right")

        # 標題列
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="項次", width=5, font=("Arial", 10, "bold")).pack(side="left", padx=2)
        tk.Label(header_frame, text="批號 (請輸入10碼)", width=20, font=("Arial", 10, "bold")).pack(side="left", padx=2)
        tk.Label(header_frame, text="槽號 (自動帶出)", width=15, font=("Arial", 10, "bold")).pack(side="left", padx=2)
        tk.Label(header_frame, text="地點 (如 15P5)", width=15, font=("Arial", 10, "bold")).pack(side="left", padx=2)
        tk.Label(header_frame, text="長代號 (自動帶出)", width=18, font=("Arial", 10, "bold")).pack(side="left", padx=2)

        # 滾動輸入區
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 產生按鈕
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="開始批次產生三合一單", command=self.generate_files, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=8).pack(fill="x")

    def add_input_rows(self, count):
        for i in range(count):
            row_idx = len(self.entries) + 1
            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill="x")
            
            # 項次
            tk.Label(row_frame, text=str(row_idx), width=5).pack(side="left", padx=2)
            
            # 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(row_frame, textvariable=batch_var, width=20, font=("Arial", 10))
            batch_entry.pack(side="left", padx=2)
            
            # 槽號
            tank_var = tk.StringVar()
            tk.Entry(row_frame, textvariable=tank_var, state="readonly", width=15, font=("Arial", 10), fg="blue").pack(side="left", padx=2)
            
            # 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(row_frame, textvariable=loc_var, width=15, font=("Arial", 10))
            loc_entry.pack(side="left", padx=2)
            
            # 長代號
            long_code_var = tk.StringVar()
            tk.Entry(row_frame, textvariable=long_code_var, state="readonly", width=18, font=("Arial", 10), fg="purple").pack(side="left", padx=2)
            
            # 綁定事件
            batch_var.trace_add("write", lambda name, index, mode, bv=batch_var, tv=tank_var: self.on_batch_change(bv, tv))
            loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, lcv=long_code_var: self.on_loc_change(lv, lcv))
            
            batch_entry.bind("<<Paste>>", lambda e, r=row_idx-1: self.on_paste(e, r, 'batch'))
            loc_entry.bind("<<Paste>>", lambda e, r=row_idx-1: self.on_paste(e, r, 'loc'))
            
            # 相容部分環境的 Ctrl+V 綁定
            batch_entry.bind("<Control-v>", lambda e, r=row_idx-1: self.on_paste(e, r, 'batch'))
            batch_entry.bind("<Control-V>", lambda e, r=row_idx-1: self.on_paste(e, r, 'batch'))
            loc_entry.bind("<Control-v>", lambda e, r=row_idx-1: self.on_paste(e, r, 'loc'))
            loc_entry.bind("<Control-V>", lambda e, r=row_idx-1: self.on_paste(e, r, 'loc'))
            
            self.entries.append({
                "batch_var": batch_var,
                "tank_var": tank_var,
                "loc_var": loc_var,
                "long_code_var": long_code_var
            })

    def on_batch_change(self, batch_var, tank_var):
        batch = batch_var.get().upper().strip()
        tank = get_tank_from_batch(batch)
        tank_var.set(tank)

    def on_loc_change(self, loc_var, long_code_var):
        loc = loc_var.get().strip().upper()
        if not loc:
            long_code_var.set("")
            return
            
        if loc in self.mapping_dict:
            long_code_var.set(self.mapping_dict[loc])
        else:
            long_code_var.set("❌ 未知代號")

    def on_paste(self, event, start_row_idx, target_col):
        try:
            clipboard = self.clipboard_get()
            lines = clipboard.split('\n')
            
            # 如果貼上的行數超過現有行數，自動增加
            valid_lines = [l for l in lines if l.strip()]
            if not valid_lines:
                return "break"
                
            needed_rows = start_row_idx + len(valid_lines)
            if needed_rows > len(self.entries):
                self.add_input_rows(needed_rows - len(self.entries))
            
            curr_row = start_row_idx
            for line in lines:
                if not line.strip(): continue
                # Excel 複製預設是以 Tab 分隔
                parts = line.split('\t')
                if len(parts) == 1:
                    # 避免沒有 tab 時，改用空白分割嘗試
                    parts = line.split()
                    
                if len(parts) >= 2:
                    # 不管來源有幾欄(是否包含項次/槽號)，都取最後兩欄作為 批號 與 地點
                    batch = parts[-2].strip()
                    loc = parts[-1].strip()
                    
                    self.entries[curr_row]["batch_var"].set(batch)
                    self.entries[curr_row]["loc_var"].set(loc)
                    curr_row += 1
                elif len(parts) == 1:
                    # 如果只有單獨一欄，判斷使用者是貼在哪個欄位就填入哪個
                    val = parts[0].strip()
                    if target_col == 'loc':
                        self.entries[curr_row]["loc_var"].set(val)
                    else:
                        self.entries[curr_row]["batch_var"].set(val)
                    curr_row += 1
                    
            return "break" # 阻止預設的貼上行為
        except Exception as e:
            messagebox.showerror("貼上失敗", f"解析貼上內容時發生錯誤:\n{e}")
            return "break"

    def import_from_excel(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="選擇要匯入的 Excel 檔案",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not filepath:
            return
            
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active
            
            # 尋找批號與地點所在的欄位 (假設在第一列到第十列之間)
            batch_col = -1
            loc_col = -1
            start_row = -1
            
            for r in range(1, 11):
                row_vals = [ws.cell(row=r, column=c).value for c in range(1, 15)]
                for c_idx, val in enumerate(row_vals):
                    if not val or not isinstance(val, str): continue
                    if "批號" in val:
                        batch_col = c_idx + 1
                    if "地點" in val or "送達地點" in val:
                        loc_col = c_idx + 1
                if batch_col != -1 and loc_col != -1:
                    start_row = r + 1
                    break
                    
            if batch_col == -1 or loc_col == -1:
                # 找不到明確標題，退而求其次預設抓 C 跟 D (對應項次,槽號,批號,地點)
                batch_col = 3
                loc_col = 4
                start_row = 2 # 假設第一列是隱式標題
            
            # 讀取資料
            records = []
            for r in range(start_row, ws.max_row + 1):
                b_val = ws.cell(row=r, column=batch_col).value
                l_val = ws.cell(row=r, column=loc_col).value
                if b_val: # 有批號才算有效資料
                    records.append((str(b_val).strip(), str(l_val).strip() if l_val else ""))
                    
            if not records:
                messagebox.showinfo("提示", "在檔案中找不到任何有效資料！")
                wb.close()
                return
                
            # 尋找第一個空行以接續填入
            start_idx = 0
            for idx, entry in enumerate(self.entries):
                if not entry["batch_var"].get().strip():
                    start_idx = idx
                    break
            else:
                start_idx = len(self.entries)
                
            needed_rows = start_idx + len(records)
            if needed_rows > len(self.entries):
                self.add_input_rows(needed_rows - len(self.entries))
                
            # 將資料填入介面
            for i, (b, l) in enumerate(records):
                self.entries[start_idx + i]["batch_var"].set(b)
                self.entries[start_idx + i]["loc_var"].set(l)
                
            wb.close()
            messagebox.showinfo("匯入成功", f"成功匯入 {len(records)} 筆資料！")
            
        except Exception as e:
            messagebox.showerror("匯入失敗", f"讀取 Excel 失敗:\n{e}")

    def generate_files(self):
        if not os.path.exists(self.template_path):
            messagebox.showerror("錯誤", f"找不到範本檔案:\n{self.template_path}")
            return
        if not os.path.exists(self.mapping_path):
            messagebox.showerror("錯誤", f"找不到對照表檔案:\n{self.mapping_path}")
            return
            
        # 收集有效資料
        valid_data = []
        for idx, row in enumerate(self.entries):
            batch = row["batch_var"].get().strip().upper()
            loc = row["loc_var"].get().strip().upper()
            tank = row["tank_var"].get().strip()
            
            if not batch and not loc:
                continue # 空白行略過
            if not batch or not loc:
                messagebox.showerror("錯誤", f"第 {idx+1} 項資料不齊全！")
                return
            if len(batch) != 10:
                messagebox.showerror("錯誤", f"第 {idx+1} 項的批號長度錯誤！\n批號必須剛好 10 碼，目前輸入: {batch} (長度 {len(batch)})")
                return
                
            valid_data.append({"batch": batch, "tank": tank, "loc": loc})
            
        if not valid_data:
            messagebox.showinfo("提示", "請輸入至少一筆資料")
            return

        # 在開始產生檔案前，先檢查所有的地點是否都在對照表中
        missing_locs = []
        for data in valid_data:
            if data["loc"] not in self.mapping_dict:
                missing_locs.append(data["loc"])
        
        if missing_locs:
            missing_str = ", ".join(set(missing_locs))
            messagebox.showerror("錯誤", f"地點代號對照表中找不到以下地點：\n{missing_str}\n\n請先更新對照表後再試！")
            return

        output_dir = os.path.join(self.base_dir, f"三合一單輸出_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        success_count = 0
        error_msgs = []
        
        for data in valid_data:
            batch_no = data["batch"]
            tank_no = data["tank"]
            loc = data["loc"]
            loc_code = self.mapping_dict[loc] # 轉換代號
            
            try:
                wb = openpyxl.load_workbook(self.template_path)
                ws = wb.worksheets[0] # 強制使用第一個分頁，避免使用者存檔時停留在其他分頁
                
                # 動態尋找欄位列數
                tank_row = find_row_by_label(ws, ['槽號']) or 5
                batch_row = find_row_by_label(ws, ['批號']) or 7
                loc_row = find_row_by_label(ws, ['送達地點', '地點']) or 11
                mat_row = find_row_by_label(ws, ['料號']) or 3
                sup_row = find_row_by_label(ws, ['供應商']) or 9
                
                # 自動補上前綴 (依據廠商規定)
                final_tank_no = "5" + tank_no
                final_batch_no = "6" + batch_no
                
                # 寫入欄位
                ws.cell(row=tank_row, column=3).value = final_tank_no
                ws.cell(row=batch_row, column=3).value = final_batch_no
                ws.cell(row=loc_row, column=3).value = loc_code
                
                # 清除舊的 QR Code
                images_to_keep = []
                for img in ws._images:
                    if img.width > 0 and img.height > 0:
                        ratio = img.width / img.height
                        if 0.8 < ratio < 1.2 and img.width < 300:
                            continue 
                    images_to_keep.append(img)
                ws._images = images_to_keep
                
                # 產生新 QR Code
                c3_val = ws.cell(row=mat_row, column=3).value or ""
                c6_val = ws.cell(row=sup_row, column=3).value or ""
                qr_str = f"||{c3_val}||{final_tank_no}||{final_batch_no}||{c6_val}||{loc_code}"
                
                qr = qrcode.QRCode(box_size=4, border=2)
                qr.add_data(qr_str)
                qr.make(fit=True)
                raw_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                
                # 為了將 QR Code 往右下微調，我們在圖片的左方與上方加上白邊
                from PIL import Image
                offset_x = 35 # 往右移 35 像素
                offset_y = 25 # 往下移 25 像素
                new_width = raw_img.width + offset_x
                new_height = raw_img.height + offset_y
                img_qr = Image.new('RGB', (new_width, new_height), 'white')
                img_qr.paste(raw_img, (offset_x, offset_y))
                
                img_byte_arr = BytesIO()
                img_qr.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                new_qr = OpenpyxlImage(img_byte_arr)
                new_qr.anchor = 'F2'
                ws.add_image(new_qr)
                
                safe_loc = "".join(c for c in loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                if not safe_loc:
                    safe_loc = "未命名地點"
                
                output_path = os.path.join(output_dir, f"{safe_loc}_{batch_no}.xlsx")
                wb.save(output_path)
                wb.close()
                success_count += 1
            except Exception as e:
                error_msgs.append(f"處理 {loc}_{batch_no} 失敗: {e}")

        # 完成提示
        msg = f"成功產生 {success_count} 份檔案！\n儲存於: {output_dir}"
        if error_msgs:
            msg += "\n\n部分錯誤:\n" + "\n".join(error_msgs[:5])
            if len(error_msgs) > 5:
                msg += "\n...(還有更多錯誤)"
            messagebox.showwarning("完成 (但有錯誤)", msg)
        else:
            messagebox.showinfo("成功", msg)
            
        os.startfile(output_dir)

if __name__ == "__main__":
    app = App()
    app.mainloop()
