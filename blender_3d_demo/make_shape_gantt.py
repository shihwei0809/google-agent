import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import win32com.client as win32

def build_gantt_with_shapes():
    # 1. First build the Excel structure with openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "精簡甘特圖"
    ws.views.sheetView[0].showGridLines = True

    font_bold = Font(name="微軟正黑體", size=10, bold=True)
    font_normal = Font(name="微軟正黑體", size=9.5)
    font_small = Font(name="微軟正黑體", size=8.5)
    font_header = Font(name="微軟正黑體", size=10, bold=True)

    thin = Side(border_style="thin", color="000000")
    medium = Side(border_style="medium", color="000000")
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)

    fill_header_gray = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")

    # Header Row 1 & 2
    ws["A1"] = "專案經理："
    ws["A1"].font = font_bold
    ws["C1"] = "專案名稱：鴻勝危物倉庫專案新建工程"
    ws["C1"].font = font_bold
    ws["T1"] = "更新日期：20261113"
    ws["T1"].font = font_bold

    ws["A2"] = "專案目標：新增危險品庫存空間 (1,776儲位)"
    ws["A2"].font = font_bold
    ws["C2"] = "專案期間：2026/11/01〜2028/05/31"
    ws["C2"].font = font_bold
    ws["T2"] = "填表人："
    ws["T2"].font = font_bold

    for r in range(1, 3):
        for c in range(1, 24):
            cell = ws.cell(row=r, column=c)
            top_s = medium if r == 1 else thin
            bot_s = medium if r == 2 else thin
            left_s = medium if c == 1 else thin
            right_s = medium if c == 23 else thin
            cell.border = Border(left=left_s, right=right_s, top=top_s, bottom=bot_s)

    # Headers Row 3 & 4
    ws.merge_cells("A3:A4")
    ws["A3"] = "狀態"
    ws["A3"].font = font_header
    ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["A3"].fill = fill_header_gray

    ws.merge_cells("B3:B4")
    ws["B3"] = "主要任務 (6大核心工程模組)"
    ws["B3"].font = font_header
    ws["B3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["B3"].fill = fill_header_gray

    # Timeline Row 3 (Years)
    ws.merge_cells("C3:D3")
    ws["C3"] = "2026年"
    ws["C3"].font = font_header
    ws["C3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["C3"].fill = fill_header_gray

    ws.merge_cells("E3:P3")
    ws["E3"] = "2027年"
    ws["E3"].font = font_header
    ws["E3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["E3"].fill = fill_header_gray

    ws.merge_cells("Q3:U3")
    ws["Q3"] = "2028年"
    ws["Q3"].font = font_header
    ws["Q3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["Q3"].fill = fill_header_gray

    ws.merge_cells("V3:W3")
    ws["V3"] = "任務負責人"
    ws["V3"].font = font_header
    ws["V3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["V3"].fill = fill_header_gray

    # Row 4 (Months)
    months = ["11月", "12月"] + [f"{m}月" for m in range(1, 13)] + ["1月", "2月", "3月", "4月", "5月"]
    for i, m_name in enumerate(months):
        col_idx = 3 + i
        ws.cell(row=4, column=col_idx, value=m_name).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=4, column=col_idx).font = font_bold
        ws.cell(row=4, column=col_idx).fill = fill_header_gray

    ws["V4"] = "資材負責者"
    ws["V4"].font = font_bold
    ws["V4"].alignment = Alignment(horizontal="center", vertical="center")
    ws["V4"].fill = fill_header_gray

    ws["W4"] = "其他單位負責者"
    ws["W4"].font = font_bold
    ws["W4"].alignment = Alignment(horizontal="center", vertical="center")
    ws["W4"].fill = fill_header_gray

    for r in [3, 4]:
        for c in range(1, 24):
            ws.cell(row=r, column=c).border = border_all

    # 6 Tasks
    tasks = [
        ("一、發包規劃、建築設計與建照申報 (決標/定稿/開工申報)", "", "工務課 / 採購課", 3, 6),    # 2026/11 ~ 2027/2 (Col C to F)
        ("二、土木營造與全區結構施工 (整地/主體結構/降溫雨遮/圍牆排水)", "", "工務課 (營造廠)", 5, 11),  # 2027/1 ~ 2027/7 (Col E to K)
        ("三、機電、廠區水電與貨架專用消防系統 (水電/消防施作/送電)", "", "工務課 / 機電商", 8, 14),   # 2027/4 ~ 2027/10 (Col H to N)
        ("四、高架貨架系統與倉儲物流設備 (Layout/備料/安裝/充電站/堆高機)", "資材課", "設備商 / 採購課", 8, 15), # 2027/4 ~ 2027/11 (Col H to O)
        ("五、法定查驗與使用執照取得 (消防現勘/建管竣工查驗/使照核發)", "", "工務課 / 環安課", 14, 16), # 2027/10 ~ 2027/12 (Col N to P)
        ("六、監控保全、台積 PCN 審查與合法合規啟用 (對接2028新產線放量)", "資材課", "業務部 / IT室", 15, 20)  # 2028/1 ~ 2028/4 (Col Q to T)
    ]

    ws.merge_cells("A5:A10")
    ws["A5"] = "預計\n待辦事項"
    ws["A5"].font = font_bold
    ws["A5"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for idx, (t_name, o1, o2, sc, ec) in enumerate(tasks):
        r = 5 + idx
        ws.row_dimensions[r].height = 25
        ws.cell(row=r, column=2, value=t_name).font = font_normal
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=r, column=22, value=o1).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=23, value=o2).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=22).font = font_small
        ws.cell(row=r, column=23).font = font_small

        for c in range(1, 24):
            ws.cell(row=r, column=c).border = border_all

    # Notes
    ws.cell(row=12, column=2, value="備註說明與關鍵管制重點：").font = font_bold
    notes = [
        "1. 重要資產與設備需等圍籬建置完成及保全設置好以後才能入場放置。",
        "2. 線條為【可自由選取、拖曳、拉長縮短】之工程線條形狀，置中於各任務行正中央，隨時可手動微調！",
        "3. 關鍵死線（Critical Path）：使用執照與正式送電必須於 2027 年 12 月底前取得，以確保 2028 Q1 順利展開台積 PCN 審查。",
        "4. 產線對接保證：本專案預計 2028 Q1 取得台積認證並合法啟用 1,776 儲位，正好即時承接 2028 年新產線放量暴增之 3,445 板需求！"
    ]
    for i, note in enumerate(notes):
        ws.cell(row=13 + i, column=2, value=note).font = font_small

    # Column Widths
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 48
    for c in range(3, 22):
        col_letter = get_column_letter(c)
        ws.column_dimensions[col_letter].width = 4.8
    ws.column_dimensions["V"].width = 12
    ws.column_dimensions["W"].width = 16

    temp_path = os.path.abspath("temp_gantt.xlsx")
    wb.save(temp_path)
    wb.close()

    # 2. Use Excel Automation to insert native Line Shapes that are centered and draggable!
    final_path = os.path.abspath("鴻勝危物倉庫專案新建工程_標準可調線條甘特圖.xlsx")
    
    excel = None
    try:
        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        wb_com = excel.Workbooks.Open(temp_path)
        ws_com = wb_com.Sheets(1)

        # Loop through each task to add a Line Shape centered in the row
        for idx, (t_name, o1, o2, start_col, end_col) in enumerate(tasks):
            r = 5 + idx
            
            # Start cell and End cell
            start_cell = ws_com.Cells(r, start_col)
            end_cell = ws_com.Cells(r, end_col)
            
            x1 = start_cell.Left
            x2 = end_cell.Left + end_cell.Width
            y = start_cell.Top + (start_cell.Height / 2.0) # Exactly in vertical center!
            
            # Add line shape: AddLine(BeginX, BeginY, EndX, EndY)
            line = ws_com.Shapes.AddLine(x1, y, x2, y)
            
            # Format the line: Blue color (RGB 0, 32, 96 or 30, 58, 138), weight 2.25 pt
            line.Line.ForeColor.RGB = 0x802000 # In BGR hex or decimal: 0x802000 is navy/blue in BGR
            # Let's set standard bright navy: RGB(0, 32, 96) -> BGR: 96*65536 + 32*256 + 0 = 6299648
            line.Line.ForeColor.RGB = 6299648
            line.Line.Weight = 2.25
            
            # Allow move and size with cells
            line.Placement = 1 # xlMoveAndSize

        wb_com.SaveAs(final_path)
        wb_com.Close(False)
        print("Shapes successfully added via Excel Automation!")
    except Exception as e:
        print(f"Excel automation warning/fallback: {e}")
        # If excel is not available or blocked, just rename temp_path
        if os.path.exists(temp_path):
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
    finally:
        if excel:
            excel.Quit()
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == "__main__":
    build_gantt_with_shapes()
