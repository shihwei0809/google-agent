import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def create_gantt_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "精簡工程甘特圖"

    # Ensure grid lines are visible
    ws.views.sheetView[0].showGridLines = True

    # Fonts
    font_main_title = Font(name="微軟正黑體", size=16, bold=True, color="1E3A8A")
    font_sub_title = Font(name="微軟正黑體", size=10, color="475569")
    font_sec_hdr = Font(name="微軟正黑體", size=10, bold=True, color="FFFFFF")
    font_year_hdr = Font(name="微軟正黑體", size=10, bold=True, color="FFFFFF")
    font_month_hdr = Font(name="微軟正黑體", size=9, bold=True, color="1E3A8A")
    font_data = Font(name="微軟正黑體", size=10, color="1E293B")
    font_data_bold = Font(name="微軟正黑體", size=10, bold=True, color="0F172A")
    font_bar_text = Font(name="微軟正黑體", size=9, bold=True, color="FFFFFF")
    font_bar_green_text = Font(name="微軟正黑體", size=9, bold=True, color="FFFFFF")

    # Fills
    fill_navy = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_slate = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    fill_blue_year = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    fill_month_hdr = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # Bar Colors
    fill_bar_blue = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")   # 施作藍
    fill_bar_amber = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")  # 設備黃
    fill_bar_red = PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid")    # 使照紅
    fill_bar_green = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")  # 啟用綠

    # Borders
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_data = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E3A8A"))
    double_bottom = Border(bottom=Side(border_style="double", color="1E3A8A"))

    # Set up Title
    ws["B2"] = "鴻勝 L02-1 危險品新倉庫建置專案 — 決策層精簡工程甘特圖"
    ws["B2"].font = font_main_title
    ws["B3"] = "專案目標：2028 Q1 啟用 1,776 儲位新倉  |  整併原則：將原 35 項繁雜細項整併為 6 大核心工程模組  |  更新日期：2026/11"
    ws["B3"].font = font_sub_title

    # Table Headers: Row 5 (Year & Meta) and Row 6 (Month)
    # Timeline covers: 2026/11 ~ 2028/04 (Total 18 months: 2026 11-12 [2], 2027 1-12 [12], 2028 1-4 [4])
    months_info = [
        ("2026年", ["11月", "12月"]),
        ("2027年", [f"{m}月" for m in range(1, 13)]),
        ("2028年", ["1月", "2月", "3月", "4月"])
    ]

    # Meta headers
    # B5:B6 NO., C5:C6 核心工程模組, D5:D6 包含原細部工項內容, E5:E6 預算/權責單位, F5:F6 狀態
    meta_headers = [
        (2, "項次"),
        (3, "核心工程模組 (整併工項)"),
        (4, "包含原細部工項摘要說明"),
        (5, "主責單位"),
        (6, "協同單位"),
        (7, "工程狀態")
    ]

    for col_idx, text in meta_headers:
        c1 = ws.cell(row=5, column=col_idx, value=text)
        c2 = ws.cell(row=6, column=col_idx)
        ws.merge_cells(start_row=5, start_column=col_idx, end_row=6, end_column=col_idx)
        for r in [5, 6]:
            cell = ws.cell(row=r, column=col_idx)
            cell.fill = fill_navy
            cell.font = font_sec_hdr
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_data

    # Timeline headers in Row 5 & 6
    curr_col = 8
    month_cols = {} # (year, month_str): col_idx

    for year_label, m_list in months_info:
        start_c = curr_col
        end_c = curr_col + len(m_list) - 1
        
        # Merge Year in Row 5
        ws.merge_cells(start_row=5, start_column=start_c, end_row=5, end_column=end_c)
        ws.cell(row=5, column=start_c, value=year_label).alignment = Alignment(horizontal="center", vertical="center")
        
        for c in range(start_c, end_c + 1):
            cell = ws.cell(row=5, column=c)
            cell.fill = fill_blue_year if "2027" in year_label else fill_slate
            cell.font = font_year_hdr
            cell.border = border_data

        # Months in Row 6
        for m_str in m_list:
            cell_m = ws.cell(row=6, column=curr_col, value=m_str)
            cell_m.fill = fill_month_hdr
            cell_m.font = font_month_hdr
            cell_m.alignment = Alignment(horizontal="center", vertical="center")
            cell_m.border = border_data
            
            # save mapping
            year_val = 2026 if "2026" in year_label else (2027 if "2027" in year_label else 2028)
            month_num = int(m_str.replace("月", ""))
            month_cols[(year_val, month_num)] = curr_col
            curr_col += 1

    last_col = curr_col - 1

    # Task Data Definitions
    # Schedule: (start_year, start_month) to (end_year, end_month)
    tasks = [
        {
            "id": "1",
            "name": "一、發包規劃與建築設計",
            "desc": "L02-1 決標、建築物平面與結構設計定稿、建照執照申請與開工申報備查",
            "owner": "工務課",
            "co_owner": "採購課 / 建築師",
            "status": "進行中",
            "start": (2026, 11),
            "end": (2026, 12),
            "bar_fill": fill_bar_blue,
            "bar_text": "決標/設計定稿"
        },
        {
            "id": "2",
            "name": "二、土木營造與基礎工程",
            "desc": "L02 廠區整地道路、危倉主體鋼結構、雨遮與降溫設計、作業區建物、圍牆與排水",
            "owner": "工務課",
            "co_owner": "土木營造廠",
            "status": "尚未進行",
            "start": (2027, 1),
            "end": (2027, 6),
            "bar_fill": fill_bar_blue,
            "bar_text": "整地/鋼構主體施工/排水圍牆"
        },
        {
            "id": "3",
            "name": "三、機電與消防水電工程",
            "desc": "廠區與建物水電工程、全區與貨架區專用消防系統施作、外線正式電送電申請",
            "owner": "工務課",
            "co_owner": "機電商 / 環安課",
            "status": "尚未進行",
            "start": (2027, 5),
            "end": (2027, 9),
            "bar_fill": fill_bar_blue,
            "bar_text": "廠區水電/貨架消防/外線送電"
        },
        {
            "id": "4",
            "name": "四、高架貨架系統與設備",
            "desc": "儲位 Layout 定稿發包、貨架備料安裝、高揚程電動堆高機採購到貨、充電站施作",
            "owner": "資材課",
            "co_owner": "採購課 / 設備商",
            "status": "尚未進行",
            "start": (2027, 8),
            "end": (2027, 11),
            "bar_fill": fill_bar_amber,
            "bar_text": "貨架備料安裝/充電站/堆高機"
        },
        {
            "id": "5",
            "name": "五、法定驗收與使照取得",
            "desc": "消防竣工查驗現勘、建管處現場勘驗審查、使用執照正式核發取得",
            "owner": "工務課",
            "co_owner": "環安課 / 建築師",
            "status": "尚未進行",
            "start": (2027, 10),
            "end": (2027, 12),
            "bar_fill": fill_bar_red,
            "bar_text": "消防竣工/建管現勘/使照取得"
        },
        {
            "id": "6",
            "name": "六、客戶認證與合規啟用",
            "desc": "業務提出台積 PCN 審查、保全與門禁打卡網路啟用、危倉正式合規投產 (無縫對接新產線)",
            "owner": "業務部",
            "co_owner": "資材課 / IT室",
            "status": "尚未進行",
            "start": (2028, 1),
            "end": (2028, 3),
            "bar_fill": fill_bar_green,
            "bar_text": "★ 台積PCN審查/新倉正式投產"
        }
    ]

    start_row = 7
    for idx, t in enumerate(tasks):
        r = start_row + idx
        ws.row_dimensions[r].height = 26
        
        row_fill = fill_zebra if idx % 2 == 1 else fill_white
        
        # Populate Meta info
        ws.cell(row=r, column=2, value=t["id"]).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=3, value=t["name"]).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=r, column=4, value=t["desc"]).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=r, column=5, value=t["owner"]).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=6, value=t["co_owner"]).alignment = Alignment(horizontal="center", vertical="center")
        
        # Status styling
        cell_status = ws.cell(row=r, column=7, value=t["status"])
        cell_status.alignment = Alignment(horizontal="center", vertical="center")
        if t["status"] == "進行中":
            cell_status.font = Font(name="微軟正黑體", size=9.5, bold=True, color="2563EB")
        else:
            cell_status.font = Font(name="微軟正黑體", size=9.5, color="64748B")

        for c in range(2, 8):
            cell = ws.cell(row=r, column=c)
            cell.border = border_data
            if c not in [7]: # keep status white
                cell.font = font_data_bold if c == 3 else font_data
                cell.fill = row_fill

        # Initialize Timeline empty cells
        for c in range(8, last_col + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill = row_fill
            cell.border = border_data

        # Draw Gantt Progress Bar
        start_c = month_cols[t["start"]]
        end_c = month_cols[t["end"]]
        
        # Merge cells for progress bar
        ws.merge_cells(start_row=r, start_column=start_c, end_row=r, end_column=end_c)
        bar_cell = ws.cell(row=r, column=start_c, value=t["bar_text"])
        bar_cell.alignment = Alignment(horizontal="center", vertical="center")
        bar_cell.font = font_bar_text

        for c in range(start_c, end_c + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill = t["bar_fill"]
            cell.border = border_data

    # Bottom Summary & Legend Card
    note_start_row = start_row + len(tasks) + 1
    
    # Summary Table Headers
    ws.cell(row=note_start_row, column=2, value="【高層管理備註與工程管制重點】").font = Font(name="微軟正黑體", size=11, bold=True, color="1E3A8A")
    ws.merge_cells(start_row=note_start_row, start_column=2, end_row=note_start_row, end_column=7)

    notes = [
        ("圖例說明", "■ 藍色：基礎/結構/機電施工   |   ■ 黃色：貨架與設備工程   |   ■ 紅色：使照與法定審查   |   ★ 綠色：客戶認證與正式啟用"),
        ("整併效益", "原甘特圖將 35 項土木、機電及電話/飲水機/標線等庶務分拆過細；精簡後聚焦於 6 大核心模組，方便跨部門權責推動與高層檢視。"),
        ("絕對死線 (Critical Path)", "【使用執照與送電】必須嚴格管制於 2027 年 12 月底前完成，任何延誤將直接衝擊 2028 Q1 台積 PCN 審查期！"),
        ("對接 2028 新產線", "2027 年建置新產線並於 2028 放量，屆時危險品需求暴增至 3,445 板。本新倉（+1,776 板）及時於 2028 Q1 啟用，成功化解千板赤字！")
    ]

    for i, (title, content) in enumerate(notes):
        curr_r = note_start_row + 1 + i
        c_title = ws.cell(row=curr_r, column=2, value=title)
        c_title.font = Font(name="微軟正黑體", size=9.5, bold=True, color="334155")
        c_title.alignment = Alignment(horizontal="center", vertical="center")
        c_title.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        c_title.border = border_data
        
        ws.merge_cells(start_row=curr_r, start_column=3, end_row=curr_r, end_column=last_col)
        c_desc = ws.cell(row=curr_r, column=3, value=content)
        c_desc.font = Font(name="微軟正黑體", size=9.5, color="475569")
        c_desc.alignment = Alignment(horizontal="left", vertical="center")
        c_desc.fill = fill_white
        for c in range(3, last_col + 1):
            ws.cell(row=curr_r, column=c).border = border_data

    # Set Column Widths
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 6   # 項次
    ws.column_dimensions["C"].width = 24  # 模組
    ws.column_dimensions["D"].width = 46  # 包含細部工項
    ws.column_dimensions["E"].width = 12  # 主責單位
    ws.column_dimensions["F"].width = 16  # 協同單位
    ws.column_dimensions["G"].width = 10  # 狀態

    for c in range(8, last_col + 1):
        col_letter = get_column_letter(c)
        ws.column_dimensions[col_letter].width = 6.5 # Monthly timeline columns

    # Row heights for headers
    ws.row_dimensions[5].height = 22
    ws.row_dimensions[6].height = 20

    out_file = os.path.abspath("鴻勝L02-1危物倉庫新建工程_精簡甘特圖.xlsx")
    wb.save(out_file)
    print(f"Excel Gantt successfully created at: {out_file}")

if __name__ == "__main__":
    create_gantt_excel()
