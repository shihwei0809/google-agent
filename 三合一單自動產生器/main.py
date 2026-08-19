import tkinter as tk
from tkinter import ttk, messagebox
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.cell.rich_text import TextBlock, CellRichText
from openpyxl.cell.text import InlineFont
import os
from datetime import datetime, timedelta
import calendar
import qrcode
from io import BytesIO

# ================= 浮動日曆選擇器 =================

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, target_var):
        super().__init__(parent)
        self.title("選擇日期")
        self.resizable(False, False)
        self.target_var = target_var
        self.transient(parent)
        self.grab_set()

        now = datetime.now()
        self.year = now.year
        self.month = now.month

        val = target_var.get().strip()
        if val:
            for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(val, fmt)
                    self.year = dt.year
                    self.month = dt.month
                    break
                except ValueError:
                    pass

        try:
            x = parent.winfo_pointerx()
            y = parent.winfo_pointery()
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self.setup_ui()
        
    def setup_ui(self):
        header = tk.Frame(self, pady=5, bg="#F5F5F5")
        header.pack(fill="x")
        
        tk.Button(header, text="◄", command=self.prev_month, width=3, relief="groove").pack(side="left", padx=5)
        self.lbl_month = tk.Label(header, text="", font=("Arial", 11, "bold"), bg="#F5F5F5", width=12)
        self.lbl_month.pack(side="left", expand=True)
        tk.Button(header, text="►", command=self.next_month, width=3, relief="groove").pack(side="right", padx=5)

        week_frame = tk.Frame(self, bg="#FFFFFF")
        week_frame.pack(fill="x", padx=5, pady=(5, 0))
        for w in ["一", "二", "三", "四", "五", "六", "日"]:
            fg_col = "#D32F2F" if w in ("六", "日") else "#333333"
            tk.Label(week_frame, text=w, width=4, font=("Arial", 9, "bold"), fg=fg_col, bg="#FFFFFF").pack(side="left")

        self.grid_frame = tk.Frame(self, bg="#FFFFFF", padx=5, pady=5)
        self.grid_frame.pack()
        
        btn_frame = tk.Frame(self, pady=5, bg="#F5F5F5")
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="今天", command=self.select_today, bg="#E3F2FD", relief="groove", font=("Arial", 9)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="明天", command=self.select_tomorrow, bg="#E8F5E9", relief="groove", font=("Arial", 9)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="清除", command=self.clear_date, bg="#FFEBEE", relief="groove", font=("Arial", 9)).pack(side="right", padx=5)
        
        self.render_calendar()

    def render_calendar(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        self.lbl_month.config(text=f"{self.year} 年 {self.month} 月")
        cal = calendar.monthcalendar(self.year, self.month)
        
        for r_idx, week in enumerate(cal):
            for c_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(self.grid_frame, text="", width=4, bg="#FFFFFF").grid(row=r_idx, column=c_idx)
                else:
                    date_str = f"{self.year}/{self.month:02d}/{day:02d}"
                    fg_col = "#D32F2F" if c_idx >= 5 else "#000000"
                    btn = tk.Button(
                        self.grid_frame, 
                        text=str(day), 
                        width=4, 
                        bg="#F9F9F9",
                        fg=fg_col,
                        relief="flat",
                        command=lambda d=date_str: self.set_date(d)
                    )
                    btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)

    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.render_calendar()

    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.render_calendar()

    def select_today(self):
        t = datetime.now()
        self.set_date(f"{t.year}/{t.month:02d}/{t.day:02d}")

    def select_tomorrow(self):
        t = datetime.now() + timedelta(days=1)
        self.set_date(f"{t.year}/{t.month:02d}/{t.day:02d}")

    def clear_date(self):
        self.target_var.set("")
        self.destroy()

    def set_date(self, date_str):
        self.target_var.set(date_str)
        self.destroy()

# ================= 核心邏輯 =================

def get_tank_from_batch(batch):
    batch = batch.strip()
    if not batch:
        return ""
    if len(batch) != 10:
        return "長度錯誤"
    if batch.endswith('J1'):
        return batch[5:8]
    return batch[5:9]

def find_row_by_label(ws, labels):
    for r in range(1, 20):
        val = ws.cell(row=r, column=2).value
        if val and isinstance(val, str):
            for label in labels:
                if label in val:
                    return r
    return None

def generate_transport_notice_file(output_path, items, mat_no="L12C53161"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "運輸通知表"
    
    ws.views.sheetView[0].showGridLines = True
    
    # 欄寬設定 (Left Card: A~F, Spacer: G, Right Card: H~M)
    col_widths = {
        'A': 8, 'B': 18, 'C': 18, 'D': 16, 'E': 14, 'F': 16,
        'G': 4,
        'H': 8, 'I': 18, 'J': 18, 'K': 16, 'L': 14, 'M': 16
    }
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width
        
    thin_border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    fill_yellow = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    fill_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_bright_yellow = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    openpyxl_font_dark_blue = Font(name="Microsoft JhengHei", color="002060", size=11)
    openpyxl_font_dark_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True)
    openpyxl_font_strike_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True, strike=True)
    openpyxl_font_red_b13 = Font(name="Microsoft JhengHei", color="C00000", size=13, bold=True)
    openpyxl_font_dark_blue_b14 = Font(name="Microsoft JhengHei", color="002060", size=14, bold=True)
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    def render_notice_card(start_r, start_c, is_modified_card, item):
        r1 = start_r
        r2 = start_r + 1
        r3 = start_r + 2
        r4 = start_r + 3
        r5 = start_r + 4
        r6 = start_r + 5
        
        c1 = start_c
        c2 = start_c + 1
        c3 = start_c + 2
        c4 = start_c + 3
        c5 = start_c + 4
        c6 = start_c + 5
        
        for r in range(r1, r6 + 1):
            ws.row_dimensions[r].height = 24 if r >= r3 else 22
            for c in range(c1, c6 + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.font = openpyxl_font_dark_blue
                cell.alignment = align_center

        # --- Title ---
        ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c3)
        title_suffix = "出貨排程修正通知" if is_modified_card else "出貨排程通知"
        title_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=12, rFont="Microsoft JhengHei"), "Shiny IPA Lorry\n"),
            TextBlock(InlineFont(color="002060", sz=10, rFont="Microsoft JhengHei"), f"(料號：{mat_no}) {title_suffix}")
        ])
        cell_a1 = ws.cell(row=r1, column=c1)
        cell_a1.value = title_rt
        cell_a1.fill = fill_yellow
        cell_a1.alignment = align_center
        
        cell_d1 = ws.cell(row=r1, column=c4, value="廠區")
        cell_d1.fill = fill_yellow
        cell_d1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_e1 = ws.cell(row=r1, column=c5, value="槽號")
        cell_e1.fill = fill_yellow
        cell_e1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        date_raw = item.get("date", "").strip()
        formatted_date = ""
        weekday_str = ""
        if date_raw:
            dt = None
            for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(date_raw, fmt)
                    break
                except ValueError:
                    pass
            if dt:
                weekday_str = weekdays[dt.weekday()]
                formatted_date = f"{dt.year}/{dt.month}/{dt.day}"
            else:
                formatted_date = date_raw
        
        cell_f1 = ws.cell(row=r1, column=c6, value=formatted_date)
        cell_f1.fill = fill_green
        cell_f1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_f2 = ws.cell(row=r2, column=c6, value=weekday_str)
        cell_f2.fill = fill_green
        cell_f2.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

        # --- Body ---
        ws.merge_cells(start_row=r3, start_column=c1, end_row=r6, end_column=c1)
        cell_a3 = ws.cell(row=r3, column=c1, value="IPA")
        cell_a3.font = openpyxl_font_dark_blue_b14
        
        time_val = item.get("time", "").strip()
        mod_time_val = item.get("mod_time", "").strip()
        
        ws.merge_cells(start_row=r3, start_column=c2, end_row=r3, end_column=c3)
        ws.cell(row=r3, column=c2, value="預計到廠時間")
        cell_f3 = ws.cell(row=r3, column=c6, value=time_val)
        
        ws.merge_cells(start_row=r4, start_column=c2, end_row=r4, end_column=c3)
        ws.cell(row=r4, column=c2, value="修正到廠時間")
        cell_f4 = ws.cell(row=r4, column=c6)
        
        if is_modified_card:
            cell_f3.font = openpyxl_font_strike_blue_b13
            cell_f4.value = mod_time_val
            cell_f4.font = openpyxl_font_red_b13
        else:
            cell_f3.font = openpyxl_font_dark_blue_b13
            cell_f4.value = ""
        
        ws.merge_cells(start_row=r5, start_column=c2, end_row=r5, end_column=c3)
        ws.cell(row=r5, column=c2, value="充填數量(KG)")
        ws.cell(row=r5, column=c6, value="4300")
        
        ws.merge_cells(start_row=r2, start_column=c4, end_row=r5, end_column=c4)
        full_loc = item.get("loc", "").strip()
        
        d_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=14, rFont="Microsoft JhengHei"), "台積\n"),
            TextBlock(InlineFont(color="C00000", b=True, sz=14, rFont="Microsoft JhengHei"), full_loc)
        ])
        cell_d2 = ws.cell(row=r2, column=c4)
        cell_d2.value = d_rt
        
        ws.merge_cells(start_row=r2, start_column=c5, end_row=r5, end_column=c5)
        cell_e2 = ws.cell(row=r2, column=c5, value=item.get("tank", "").strip())
        cell_e2.font = openpyxl_font_dark_blue_b14
        cell_e2.fill = fill_bright_yellow
        
        ws.merge_cells(start_row=r6, start_column=c2, end_row=r6, end_column=c5)
        cell_b6 = ws.cell(row=r6, column=c2)
        cell_b6.value = CellRichText([
            TextBlock(InlineFont(color="C00000", b=True, sz=11, rFont="Microsoft JhengHei"), "PFA 500ml"),
            TextBlock(InlineFont(color="002060", sz=11, rFont="Microsoft JhengHei"), " 取樣瓶裝原液 8 分滿放置工具箱內")
        ])
        
        cell_f6 = ws.cell(row=r6, column=c6, value="6 支")
        cell_f6.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

    curr_row = 1
    for item in items:
        # 左側：原始出貨排程通知卡片 (Columns A~F)
        render_notice_card(curr_row, 1, False, item)
        
        # 若該筆有輸入「修正到廠時間」，在右側旁 (Columns H~M) 併排產生「出貨排程修正通知」卡片
        if item.get("mod_time", "").strip():
            render_notice_card(curr_row, 8, True, item)
            
        curr_row += 7

    wb.save(output_path)
    wb.close()

# ================= 介面與操作 =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("三合一單自動產生器 & 運輸通知表產生器")
        self.geometry("1150x750")
        self.configure(padx=15, pady=15)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.base_dir, "台積電槽車barcode三合一單-範本.xlsx")
        self.mapping_path = os.path.join(self.base_dir, "地點代號對照表.xlsx")
        
        self.mapping_dict = {}
        self.load_mapping()
        
        self.setup_ui()
        self.entries = []
        self.add_input_rows(20)

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

    def open_calendar_dialog(self, target_var):
        CalendarDialog(self, target_var)

    def setup_ui(self):
        # 檔案狀態區
        status_frame = tk.LabelFrame(self, text="系統狀態", font=("Arial", 10, "bold"), padx=10, pady=8)
        status_frame.pack(fill="x", pady=(0, 8))
        
        t_color = "green" if os.path.exists(self.template_path) else "red"
        t_text = "✅ 已找到" if os.path.exists(self.template_path) else "❌ 未找到 (請將檔案放入資料夾)"
        tk.Label(status_frame, text=f"範本檔案 (台積電槽車barcode三合一單-範本.xlsx): {t_text}", fg=t_color).pack(anchor="w")
        
        m_color = "green" if os.path.exists(self.mapping_path) else "red"
        m_text = f"✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "❌ 未找到 (請將檔案放入資料夾)"
        tk.Label(status_frame, text=f"對照表檔案 (地點代號對照表.xlsx): {m_text}", fg=m_color).pack(anchor="w")

        # 頂部快捷批次控制與匯入區
        top_ctrl_frame = tk.Frame(self)
        top_ctrl_frame.pack(fill="x", pady=(0, 8))
        
        tk.Label(top_ctrl_frame, text="提示：可在「批號」貼上多筆資料，支援自訂欄位順序（如到貨/批號/槽號/地點），或點右側匯入 Excel。", fg="#555", justify="left").pack(side="left")
        
        tk.Button(top_ctrl_frame, text="📥 從 Excel 匯入", command=self.import_from_excel, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), padx=10).pack(side="right", padx=(5, 0))
        tk.Button(top_ctrl_frame, text="🗑️ 清除全部資料 (全清)", command=self.clear_all_rows, bg="#D32F2F", fg="white", font=("Arial", 9, "bold"), padx=8).pack(side="right", padx=5)

        # 批次設定預設值列
        batch_setting_frame = tk.LabelFrame(self, text="一鍵批次設定 (日期 / 預計時間 / 修正時間)", font=("Arial", 9, "bold"), padx=8, pady=5)
        batch_setting_frame.pack(fill="x", pady=(0, 8))
        
        # 全選
        self.select_all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(batch_setting_frame, text="全選", variable=self.select_all_var, command=self.toggle_select_all, font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))
        
        # 日期
        tk.Label(batch_setting_frame, text="批次日期:").pack(side="left")
        self.default_date_var = tk.StringVar(value="")
        date_batch_entry = tk.Entry(batch_setting_frame, textvariable=self.default_date_var, width=12)
        date_batch_entry.pack(side="left", padx=2)
        tk.Button(batch_setting_frame, text="📅", command=lambda: self.open_calendar_dialog(self.default_date_var), font=("Arial", 8), width=3).pack(side="left", padx=(0, 2))
        tk.Button(batch_setting_frame, text="套用至全列", command=self.apply_default_date, bg="#607D8B", fg="white", font=("Arial", 8)).pack(side="left", padx=(2, 12))
        
        # 預計時間
        tk.Label(batch_setting_frame, text="批次預計時間:").pack(side="left")
        self.default_time_var = tk.StringVar(value="")
        tk.Entry(batch_setting_frame, textvariable=self.default_time_var, width=8).pack(side="left", padx=2)
        tk.Button(batch_setting_frame, text="套用至全列", command=self.apply_default_time, bg="#607D8B", fg="white", font=("Arial", 8)).pack(side="left", padx=(2, 12))

        # 修正時間
        tk.Label(batch_setting_frame, text="批次修正時間:").pack(side="left")
        self.default_mod_time_var = tk.StringVar(value="")
        tk.Entry(batch_setting_frame, textvariable=self.default_mod_time_var, width=8).pack(side="left", padx=2)
        tk.Button(batch_setting_frame, text="套用至全列", command=self.apply_default_mod_time, bg="#607D8B", fg="white", font=("Arial", 8)).pack(side="left", padx=(2, 10))

        # 輸出選項
        opt_frame = tk.Frame(batch_setting_frame)
        opt_frame.pack(side="right")
        self.gen_3in1_var = tk.BooleanVar(value=True)
        self.gen_transport_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="產生三合一單", variable=self.gen_3in1_var, font=("Arial", 9, "bold"), fg="#1B5E20").pack(side="left", padx=5)
        tk.Checkbutton(opt_frame, text="產生運輸通知表", variable=self.gen_transport_var, font=("Arial", 9, "bold"), fg="#0D47A1").pack(side="left", padx=5)

        # 滾動容器
        table_container = tk.Frame(self)
        table_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        
        # 單一 Grid 容器 (scrollable_frame)
        self.scrollable_frame = tk.Frame(self.canvas, padx=5, pady=5)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- Row 0: 表格標題列 (置於滾動區最上方，共享 100% 同一 Grid 欄位規格) ---
        headers = [
            (0, "產生"),
            (1, "項次"),
            (2, "批號 (請輸入10碼)"),
            (3, "槽號 (自動)"),
            (4, "地點 (如 15P5)"),
            (5, "長代號 (自動)"),
            (6, "出貨日期 📅"),
            (7, "預計到廠時間"),
            (8, "修正到廠時間"),
            (9, "單列清空")
        ]
        
        for col_idx, title in headers:
            lbl = tk.Label(
                self.scrollable_frame, 
                text=title, 
                font=("Arial", 10, "bold"), 
                bg="#EAEAEA", 
                fg="#333333",
                padx=6, 
                pady=6,
                relief="groove"
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=(0, 6))

        # 產生按鈕
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="🚀 開始批次產生 Excel 報表", command=self.generate_files, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=8).pack(fill="x")

    def toggle_select_all(self):
        state = self.select_all_var.get()
        for entry in self.entries:
            entry["chk_var"].set(state)

    def apply_default_date(self):
        val = self.default_date_var.get().strip()
        for entry in self.entries:
            if entry["batch_var"].get().strip():
                entry["date_var"].set(val)

    def apply_default_time(self):
        val = self.default_time_var.get().strip()
        for entry in self.entries:
            if entry["batch_var"].get().strip():
                entry["time_var"].set(val)

    def apply_default_mod_time(self):
        val = self.default_mod_time_var.get().strip()
        for entry in self.entries:
            if entry["batch_var"].get().strip():
                entry["mod_time_var"].set(val)

    def add_input_rows(self, count):
        for i in range(count):
            row_idx = len(self.entries) + 1
            row_grid_idx = row_idx
            
            # Col 0: 勾選
            chk_var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(self.scrollable_frame, variable=chk_var)
            chk.grid(row=row_grid_idx, column=0, padx=2, pady=2)

            # Col 1: 項次
            lbl_num = tk.Label(self.scrollable_frame, text=str(row_idx), font=("Arial", 10))
            lbl_num.grid(row=row_grid_idx, column=1, padx=2, pady=2)
            
            # Col 2: 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(self.scrollable_frame, textvariable=batch_var, width=16, font=("Arial", 10))
            batch_entry.grid(row=row_grid_idx, column=2, padx=2, pady=2, sticky="ew")
            
            # Col 3: 槽號
            tank_var = tk.StringVar()
            tank_entry = tk.Entry(self.scrollable_frame, textvariable=tank_var, state="readonly", width=10, font=("Arial", 10), fg="blue")
            tank_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")
            
            # Col 4: 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(self.scrollable_frame, textvariable=loc_var, width=12, font=("Arial", 10))
            loc_entry.grid(row=row_grid_idx, column=4, padx=2, pady=2, sticky="ew")
            
            # Col 5: 長代號
            long_code_var = tk.StringVar()
            long_code_entry = tk.Entry(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=16, font=("Arial", 10), fg="purple")
            long_code_entry.grid(row=row_grid_idx, column=5, padx=2, pady=2, sticky="ew")
            
            # Col 6: 出貨日期 (Entry + 📅 日曆按鈕)
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")
            
            date_var = tk.StringVar(value="")
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=11, font=("Arial", 10))
            date_entry.pack(side="left", fill="x", expand=True)
            
            btn_cal = tk.Button(date_frame, text="📅", command=lambda dv=date_var: self.open_calendar_dialog(dv), font=("Arial", 8), cursor="hand2")
            btn_cal.pack(side="right", padx=(2, 0))
            
            # Col 7: 預計到廠時間
            time_var = tk.StringVar(value="")
            time_entry = tk.Entry(self.scrollable_frame, textvariable=time_var, width=10, font=("Arial", 10))
            time_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")

            # Col 8: 修正到廠時間
            mod_time_var = tk.StringVar(value="")
            mod_time_entry = tk.Entry(self.scrollable_frame, textvariable=mod_time_var, width=10, font=("Arial", 10), fg="red")
            mod_time_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")

            # Col 9: 單列清空按鈕 (🗑️)
            btn_clear_row = tk.Button(
                self.scrollable_frame, 
                text="🗑️ 清", 
                command=lambda r=row_idx-1: self.clear_single_row(r), 
                font=("Arial", 8, "bold"), 
                bg="#FFEBEE", 
                fg="#C62828", 
                cursor="hand2", 
                width=4
            )
            btn_clear_row.grid(row=row_grid_idx, column=9, padx=2, pady=2)

            # 綁定事件
            batch_var.trace_add("write", lambda name, index, mode, bv=batch_var, tv=tank_var: self.on_batch_change(bv, tv))
            loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, lcv=long_code_var: self.on_loc_change(lv, lcv))
            
            for widget in (batch_entry, loc_entry, date_entry):
                widget.bind("<<Paste>>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
                widget.bind("<Control-v>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
                widget.bind("<Control-V>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
            
            self.entries.append({
                "chk_var": chk_var,
                "batch_var": batch_var,
                "tank_var": tank_var,
                "loc_var": loc_var,
                "long_code_var": long_code_var,
                "date_var": date_var,
                "time_var": time_var,
                "mod_time_var": mod_time_var
            })

    def clear_all_rows(self):
        """一鍵清除全部輸入欄位 (全清)"""
        if messagebox.askyesno("確認清空", "確定要清空所有已填寫的批號、地點與時間資料嗎？"):
            for entry in self.entries:
                entry["batch_var"].set("")
                entry["loc_var"].set("")
                entry["long_code_var"].set("")
                entry["tank_var"].set("")
                entry["date_var"].set("")
                entry["time_var"].set("")
                entry["mod_time_var"].set("")

    def clear_single_row(self, r_idx):
        """清空單一列的資料 (單個清)"""
        if 0 <= r_idx < len(self.entries):
            entry = self.entries[r_idx]
            entry["batch_var"].set("")
            entry["loc_var"].set("")
            entry["long_code_var"].set("")
            entry["tank_var"].set("")
            entry["date_var"].set("")
            entry["time_var"].set("")
            entry["mod_time_var"].set("")

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

    def parse_pasted_row_items(self, parts):
        """
        智慧解析貼上行中的元素，自動辨識：出貨日期、批號、槽號、地點、時間。
        支援 Image 1 範例（到貨 + 批號 + 槽號 + 地點）及各式自訂順序！
        """
        res = {"batch": "", "loc": "", "date": "", "time": "", "mod_time": ""}
        clean_parts = [p.strip() for p in parts if p.strip()]
        if not clean_parts:
            return res

        unassigned = []
        for p in clean_parts:
            p_upper = p.upper()
            
            # 1. 日期 (包含 /, -, ., 或月/日，長度 <= 12)
            if not res["date"] and (any(char in p for char in ("/", "-", ".")) or "月" in p or "日" in p):
                if len(p) <= 12 and not p.isalnum():
                    res["date"] = p
                    continue

            # 2. 批號 (8~12 碼英數混合，例如 26817E3051)
            if not res["batch"] and (8 <= len(p_upper) <= 12 and any(c.isdigit() for c in p_upper) and any(c.isalpha() for c in p_upper)):
                res["batch"] = p_upper
                continue

            # 3. 地點 (在 mapping_dict 內或含 18P, 15P, P, 廠等)
            if not res["loc"] and (p_upper in self.mapping_dict or "18P" in p_upper or "15P" in p_upper or "P" in p_upper or "廠" in p):
                res["loc"] = p_upper
                continue

            # 4. 槽號 (3~5 碼以 E/T/P 開頭，例如 E305) -> 可略過，因為寫入批號時微服務會自動算槽號！
            if len(p_upper) <= 5 and p_upper.startswith(("E", "T", "P")):
                continue

            # 其它填入未指派
            unassigned.append(p)

        # 針對缺額自動後補填入
        for item in unassigned:
            if not res["batch"] and len(item) >= 6:
                res["batch"] = item.upper()
            elif not res["loc"] and len(item) <= 10:
                res["loc"] = item.upper()
            elif not res["date"] and ("/" in item or "-" in item or "." in item):
                res["date"] = item
            elif not res["time"]:
                res["time"] = item
            elif not res["mod_time"]:
                res["mod_time"] = item

        return res

    def on_paste(self, event, start_row_idx, widget=None):
        try:
            clipboard = self.clipboard_get()
            lines = clipboard.split('\n')
            
            valid_lines = [l for l in lines if l.strip()]
            if not valid_lines:
                return "break"
                
            needed_rows = start_row_idx + len(valid_lines)
            if needed_rows > len(self.entries):
                self.add_input_rows(needed_rows - len(self.entries))
            
            curr_row = start_row_idx
            for line in lines:
                if not line.strip(): continue
                parts = line.split('\t')
                if len(parts) == 1:
                    parts = line.split()
                    
                if len(parts) >= 2:
                    # 使用智慧元素剖析器！
                    parsed = self.parse_pasted_row_items(parts)
                    
                    if parsed["batch"]:
                        self.entries[curr_row]["batch_var"].set(parsed["batch"])
                    if parsed["loc"]:
                        self.entries[curr_row]["loc_var"].set(parsed["loc"])
                    if parsed["date"]:
                        self.entries[curr_row]["date_var"].set(parsed["date"])
                    if parsed["time"]:
                        self.entries[curr_row]["time_var"].set(parsed["time"])
                    if parsed["mod_time"]:
                        self.entries[curr_row]["mod_time_var"].set(parsed["mod_time"])
                    
                    curr_row += 1
                elif len(parts) == 1:
                    val = parts[0].strip()
                    # 單一欄位貼上：依當前焦點與內容自動指派
                    if val:
                        parsed = self.parse_pasted_row_items([val])
                        if parsed["batch"]:
                            self.entries[curr_row]["batch_var"].set(parsed["batch"])
                        elif parsed["loc"]:
                            self.entries[curr_row]["loc_var"].set(parsed["loc"])
                        elif parsed["date"]:
                            self.entries[curr_row]["date_var"].set(parsed["date"])
                        else:
                            self.entries[curr_row]["batch_var"].set(val)
                    curr_row += 1
                    
            return "break"
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
            
            batch_col = -1
            loc_col = -1
            date_col = -1
            time_col = -1
            mod_time_col = -1
            start_row = -1
            
            for r in range(1, 11):
                row_vals = [ws.cell(row=r, column=c).value for c in range(1, 15)]
                for c_idx, val in enumerate(row_vals):
                    if not val or not isinstance(val, str): continue
                    v_str = val.strip()
                    if "批號" in v_str:
                        batch_col = c_idx + 1
                    if "地點" in v_str or "送達地點" in v_str:
                        loc_col = c_idx + 1
                    if "日期" in v_str:
                        date_col = c_idx + 1
                    if "修正" in v_str and "時間" in v_str:
                        mod_time_col = c_idx + 1
                    elif "時間" in v_str and mod_time_col == -1:
                        time_col = c_idx + 1
                        
                if batch_col != -1 and loc_col != -1:
                    start_row = r + 1
                    break
                    
            if batch_col == -1 or loc_col == -1:
                batch_col = 3
                loc_col = 4
                start_row = 2
            
            records = []
            for r in range(start_row, ws.max_row + 1):
                b_val = ws.cell(row=r, column=batch_col).value
                l_val = ws.cell(row=r, column=loc_col).value
                d_val = ws.cell(row=r, column=date_col).value if date_col != -1 else None
                t_val = ws.cell(row=r, column=time_col).value if time_col != -1 else None
                mt_val = ws.cell(row=r, column=mod_time_col).value if mod_time_col != -1 else None
                
                if b_val:
                    records.append({
                        "batch": str(b_val).strip(),
                        "loc": str(l_val).strip() if l_val else "",
                        "date": str(d_val).strip() if d_val else "",
                        "time": str(t_val).strip() if t_val else "",
                        "mod_time": str(mt_val).strip() if mt_val else ""
                    })
                    
            if not records:
                messagebox.showinfo("提示", "在檔案中找不到任何有效資料！")
                wb.close()
                return
                
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
                
            for i, rec in enumerate(records):
                row_e = self.entries[start_idx + i]
                row_e["batch_var"].set(rec["batch"])
                row_e["loc_var"].set(rec["loc"])
                if rec["date"]: row_e["date_var"].set(rec["date"])
                if rec["time"]: row_e["time_var"].set(rec["time"])
                if rec["mod_time"]: row_e["mod_time_var"].set(rec["mod_time"])
                
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
            
        do_3in1 = self.gen_3in1_var.get()
        do_transport = self.gen_transport_var.get()
        
        if not do_3in1 and not do_transport:
            messagebox.showwarning("提示", "請至少勾選一種報表類型（三合一單 或 運輸通知表）！")
            return

        valid_data = []
        for idx, row in enumerate(self.entries):
            if not row["chk_var"].get():
                continue
                
            batch = row["batch_var"].get().strip().upper()
            loc = row["loc_var"].get().strip().upper()
            tank = row["tank_var"].get().strip()
            date_str = row["date_var"].get().strip()
            time_str = row["time_var"].get().strip()
            mod_time_str = row["mod_time_var"].get().strip()
            
            if not batch and not loc:
                continue
            if not batch or not loc:
                messagebox.showerror("錯誤", f"第 {idx+1} 項資料不齊全！")
                return
            if len(batch) != 10:
                messagebox.showerror("錯誤", f"第 {idx+1} 項的批號長度錯誤！\n批號必須剛好 10 碼，目前輸入: {batch} (長度 {len(batch)})")
                return
                
            valid_data.append({
                "batch": batch,
                "tank": tank,
                "loc": loc,
                "date": date_str,
                "time": time_str,
                "mod_time": mod_time_str
            })
            
        if not valid_data:
            messagebox.showinfo("提示", "請至少勾選並輸入一筆有效資料！")
            return

        missing_locs = [data["loc"] for data in valid_data if data["loc"] not in self.mapping_dict]
        if missing_locs:
            missing_str = ", ".join(set(missing_locs))
            messagebox.showerror("錯誤", f"地點代號對照表中找不到以下地點：\n{missing_str}\n\n請先更新對照表後再試！")
            return

        output_dir = os.path.join(self.base_dir, f"三合一單輸出_{datetime.now().strftime('%Y%m%d')}")
        os.makedirs(output_dir, exist_ok=True)
        
        success_3in1 = 0
        error_msgs = []
        mat_no = "L12C53161"

        if do_3in1:
            for data in valid_data:
                batch_no = data["batch"]
                tank_no = data["tank"]
                loc = data["loc"]
                loc_code = self.mapping_dict[loc]
                
                try:
                    wb = openpyxl.load_workbook(self.template_path)
                    ws = wb.worksheets[0]
                    
                    tank_row = find_row_by_label(ws, ['槽號']) or 5
                    batch_row = find_row_by_label(ws, ['批號']) or 7
                    loc_row = find_row_by_label(ws, ['送達地點', '地點']) or 11
                    mat_row = find_row_by_label(ws, ['料號']) or 3
                    sup_row = find_row_by_label(ws, ['供應商']) or 9
                    
                    raw_mat = str(ws.cell(row=mat_row, column=3).value or "").strip()
                    if raw_mat.startswith("4"):
                        mat_no = raw_mat[1:]
                    elif raw_mat:
                        mat_no = raw_mat
                    
                    final_tank_no = "5" + tank_no
                    final_batch_no = "6" + batch_no
                    
                    ws.cell(row=tank_row, column=3).value = final_tank_no
                    ws.cell(row=batch_row, column=3).value = final_batch_no
                    ws.cell(row=loc_row, column=3).value = loc_code
                    
                    images_to_keep = []
                    for img in ws._images:
                        if img.width > 0 and img.height > 0:
                            ratio = img.width / img.height
                            if 0.8 < ratio < 1.2 and img.width < 300:
                                continue 
                        images_to_keep.append(img)
                    ws._images = images_to_keep
                    
                    c3_val = ws.cell(row=mat_row, column=3).value or ""
                    c6_val = ws.cell(row=sup_row, column=3).value or ""
                    qr_str = f"||{c3_val}||{final_tank_no}||{final_batch_no}||{c6_val}||{loc_code}"
                    
                    qr = qrcode.QRCode(box_size=4, border=2)
                    qr.add_data(qr_str)
                    qr.make(fit=True)
                    raw_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                    
                    from PIL import Image
                    offset_x = 35
                    offset_y = 25
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
                    
                    # 產生檔名規格：[出貨日期]. [地點]台積電槽車barcode三合一單.xlsx (例如: 2026.8.18. 18P3B台積電槽車barcode三合一單.xlsx)
                    date_raw = data.get("date", "").strip()
                    dt_file = None
                    if date_raw:
                        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d"):
                            try:
                                dt_file = datetime.strptime(date_raw, fmt)
                                break
                            except ValueError:
                                pass
                    if not dt_file:
                        dt_file = datetime.now()
                        
                    date_prefix = f"{dt_file.year}.{dt_file.month}.{dt_file.day}. "
                    output_filename = f"{date_prefix}{safe_loc}台積電槽車barcode三合一單.xlsx"
                    
                    output_path = os.path.join(output_dir, output_filename)
                    wb.save(output_path)
                    wb.close()
                    success_3in1 += 1
                except Exception as e:
                    error_msgs.append(f"處理三合一單 {loc}_{batch_no} 失敗: {e}")

        success_transport = False
        if do_transport:
            try:
                transport_path = os.path.join(output_dir, "運輸通知表.xlsx")
                generate_transport_notice_file(transport_path, valid_data, mat_no=mat_no)
                success_transport = True
            except Exception as e:
                error_msgs.append(f"產生運輸通知表失敗: {e}")

        msg_parts = []
        if do_3in1:
            msg_parts.append(f"• 三合一單：成功產生 {success_3in1} 份")
        if do_transport:
            status_str = "成功" if success_transport else "失敗"
            msg_parts.append(f"• 運輸通知表：{status_str} (共 {len(valid_data)} 筆排程卡片)")
            
        msg = "\n".join(msg_parts) + f"\n\n檔案已儲存於資料夾：\n{output_dir}"
        
        if error_msgs:
            msg += "\n\n部分錯誤:\n" + "\n".join(error_msgs[:5])
            messagebox.showwarning("完成 (但有部分錯誤)", msg)
        else:
            messagebox.showinfo("成功", msg)
            
        os.startfile(output_dir)

if __name__ == "__main__":
    app = App()
    app.mainloop()
