import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def create_traditional_gantt():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "精簡甘特圖"

    # Show grid lines
    ws.views.sheetView[0].showGridLines = True

    # Fonts
    font_bold = Font(name="微軟正黑體", size=10, bold=True)
    font_normal = Font(name="微軟正黑體", size=9.5)
    font_small = Font(name="微軟正黑體", size=8.5)
    font_title = Font(name="微軟正黑體", size=11, bold=True)
    font_header = Font(name="微軟正黑體", size=10, bold=True)

    # Borders
    thin = Side(border_style="thin", color="000000")
    medium = Side(border_style="medium", color="000000")
    double = Side(border_style="double", color="000000")
    
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    border_box = Border(left=medium, right=medium, top=medium, bottom=medium)

    # Blue bar styling: Thick top border or middle-line styling
    # In Excel, a classic Gantt bar inside the cell is either:
    # 1. A cell with a solid medium top border (blue) and thin black grid, OR
    # 2. A filled thin line / colored background bar.
    # Looking closely at the image: the lines are blue horizontal strokes across the top of the cells (or a border-top / shape).
    # Specifically, it's a solid blue line across the top edge of each cell:
    blue_line_side = Side(border_style="medium", color="002060") # Dark blue
    
    # Let's create border styles for the bar
    # A bar cell has a dark blue top border, and thin vertical borders
    border_bar = Border(left=thin, right=thin, top=blue_line_side, bottom=thin)

    # Background Fills
    fill_header_gray = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # Top metadata block (Rows 1 to 4) exactly matching the user's template
    # Header Row 1
    # Col A: 專案經理
    ws["A1"] = "專案經理："
    ws["A1"].font = font_bold
    ws["A1"].alignment = Alignment(vertical="center")

    # Col C: 專案名稱
    ws["C1"] = "專案名稱：鴻勝危物倉庫專案新建工程"
    ws["C1"].font = font_bold
    ws["C1"].alignment = Alignment(vertical="center")

    # Col T: 更新日期
    ws["T1"] = "更新日期：20261113"
    ws["T1"].font = font_bold
    ws["T1"].alignment = Alignment(vertical="center")

    # Header Row 2
    ws["A2"] = "專案目標：新增危險品庫存空間 (1,776儲位)"
    ws["A2"].font = font_bold
    ws["A2"].alignment = Alignment(vertical="center")

    ws["C2"] = "專案期間：2026/11/01〜2028/05/31"
    ws["C2"].font = font_bold
    ws["C2"].alignment = Alignment(vertical="center")

    ws["T2"] = "填表人："
    ws["T2"].font = font_bold
    ws["T2"].alignment = Alignment(vertical="center")

    # Border outer box for header rows 1-2
    for r in range(1, 3):
        for c in range(1, 23):
            cell = ws.cell(row=r, column=c)
            # Add thin borders for the header frame
            top_s = medium if r == 1 else thin
            bot_s = medium if r == 2 else thin
            left_s = medium if c == 1 else thin
            right_s = medium if c == 22 else thin
            cell.border = Border(left=left_s, right=right_s, top=top_s, bottom=bot_s)

    # Row 3 & 4: Table Headers
    # Col A: 狀態 (待辦事項)
    # Col B: 主要任務
    # Col C to U: Timeline (2026 11~12, 2027 1~12, 2028 1~5 -> 19 months)
    # Col V: 資材負責者
    # Col W: 其他單位負責者

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

    # Timeline in Row 3 (Years)
    # 2026: Col C to D (11, 12月)
    ws.merge_cells("C3:D3")
    ws["C3"] = "2026年"
    ws["C3"].font = font_header
    ws["C3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["C3"].fill = fill_header_gray

    # 2027: Col E to P (1~12月)
    ws.merge_cells("E3:P3")
    ws["E3"] = "2027年"
    ws["E3"].font = font_header
    ws["E3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["E3"].fill = fill_header_gray

    # 2028: Col Q to U (1~5月)
    ws.merge_cells("Q3:U3")
    ws["Q3"] = "2028年"
    ws["Q3"].font = font_header
    ws["Q3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["Q3"].fill = fill_header_gray

    # 任務負責人 in Row 3 (Col V to W)
    ws.merge_cells("V3:W3")
    ws["V3"] = "任務負責人"
    ws["V3"].font = font_header
    ws["V3"].alignment = Alignment(horizontal="center", vertical="center")
    ws["V3"].fill = fill_header_gray

    # Row 4: Months
    months = ["11月", "12月"] + [f"{m}月" for m in range(1, 13)] + ["1月", "2月", "3月", "4月", "5月"]
    month_col_map = {}
    for i, m_name in enumerate(months):
        col_idx = 3 + i # starts at col C (3)
        ws.cell(row=4, column=col_idx, value=m_name).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=4, column=col_idx).font = font_bold
        ws.cell(row=4, column=col_idx).fill = fill_header_gray
        
        # Determine year
        if i < 2:
            yr = 2026
            m_num = 11 + i
        elif i < 14:
            yr = 2027
            m_num = i - 1
        else:
            yr = 2028
            m_num = i - 13
        month_col_map[(yr, m_num)] = col_idx

    ws["V4"] = "資材負責者"
    ws["V4"].font = font_bold
    ws["V4"].alignment = Alignment(horizontal="center", vertical="center")
    ws["V4"].fill = fill_header_gray

    ws["W4"] = "其他單位負責者"
    ws["W4"].font = font_bold
    ws["W4"].alignment = Alignment(horizontal="center", vertical="center")
    ws["W4"].fill = fill_header_gray

    # Set borders for headers Row 3 & 4
    for r in [3, 4]:
        for c in range(1, 24):
            ws.cell(row=r, column=c).border = border_all

    # Tasks definition (Simplified to 6 major modules, exactly as requested)
    tasks = [
        {
            "name": "一、發包規劃、建築設計與建照申報 (決標/定稿/開工申報)",
            "start": (2026, 11),
            "end": (2027, 2),
            "owner1": "",
            "owner2": "工務課 / 採購課",
            "note": "原：L02-1簽呈決標、危倉建物設計定稿、建照申請與開工申報"
        },
        {
            "name": "二、土木營造與全區結構施工 (整地/主體結構/降溫雨遮/圍牆排水)",
            "start": (2027, 1),
            "end": (2027, 7),
            "owner1": "",
            "owner2": "工務課 (營造廠)",
            "note": "原：1期地面道路、地質鑽勘、危倉結構、雨遮、綜合廠房與排水圍牆"
        },
        {
            "name": "三、機電、廠區水電與貨架專用消防系統 (水電/消防施作/送電)",
            "start": (2027, 4),
            "end": (2027, 10),
            "owner1": "",
            "owner2": "工務課 / 機電商",
            "note": "原：水電消防發包、貨架區消防、建物水電、太陽能與送電申請"
        },
        {
            "name": "四、高架貨架系統與倉儲物流設備 (Layout/備料/安裝/充電站/堆高機)",
            "start": (2027, 4),
            "end": (2027, 11),
            "owner1": "資材課",
            "owner2": "設備商 / 採購課",
            "note": "原：貨架Layout定稿、貨架備料安裝、堆高機採購、充電站施作、包膜機"
        },
        {
            "name": "五、法定查驗與使用執照取得 (消防現勘/建管竣工查驗/使照核發)",
            "start": (2027, 10),
            "end": (2027, 12),
            "owner1": "",
            "owner2": "工務課 / 環安課",
            "note": "原：消防竣工現勘、建管竣工現勘、使照申請與現場審查 (關鍵死線)"
        },
        {
            "name": "六、監控保全、台積 PCN 審查與合法合規啟用 (對接2028新產線放量)",
            "start": (2028, 1),
            "end": (2028, 4),
            "owner1": "資材課",
            "owner2": "業務部 / IT室",
            "note": "原：監控保全、電話網路、業務提PCN給台積審查、危倉合法合規啟用"
        }
    ]

    # Side label: 預計待辦事項 (Row 5 to 10)
    ws.merge_cells("A5:A10")
    ws["A5"] = "預計\n待辦事項"
    ws["A5"].font = font_bold
    ws["A5"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Populate Tasks & Draw Progress Bar
    for idx, t in enumerate(tasks):
        r = 5 + idx
        ws.row_dimensions[r].height = 24

        # Task Name
        cell_name = ws.cell(row=r, column=2, value=t["name"])
        cell_name.font = font_normal
        cell_name.alignment = Alignment(horizontal="left", vertical="center")

        # Owners
        ws.cell(row=r, column=22, value=t["owner1"]).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=23, value=t["owner2"]).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r, column=22).font = font_small
        ws.cell(row=r, column=23).font = font_small

        # Timeline cells
        start_col = month_col_map[t["start"]]
        end_col = month_col_map[t["end"]]

        for c in range(3, 22):
            cell = ws.cell(row=r, column=c)
            # Default thin border
            cell.border = border_all

            # Apply blue horizontal bar (line) on the top border of cells in range
            if start_col <= c <= end_col:
                # This matches the user's uploaded picture: blue line running across the cells
                cell.border = Border(left=thin, right=thin, top=blue_line_side, bottom=thin)

        # Set borders for A, B, V, W
        ws.cell(row=r, column=1).border = border_all
        ws.cell(row=r, column=2).border = border_all
        ws.cell(row=r, column=22).border = border_all
        ws.cell(row=r, column=23).border = border_all

    # Notes & Guideline box at bottom (Row 12 to 16)
    ws.cell(row=12, column=2, value="備註說明與關鍵管制重點：").font = font_bold
    notes = [
        "1. 重要資產與設備需等圍籬建置完成及保全設置好以後才能入場放置。",
        "2. 本甘特圖已將原 35 項繁碎工項（如道路/結構/排水/水電/消防/各類庶務）整併為 6 大核心工程模組，進度線完全對齊原排程。",
        "3. 關鍵死線（Critical Path）：使用執照與正式送電必須於 2027 年 12 月底前取得，以確保 2028 Q1 順利展開台積 PCN 審查。",
        "4. 產線對接保證：本專案預計 2028 Q1 取得台積認證並合法啟用 1,776 儲位，正好即時承接 2028 年新產線放量暴增之 3,445 板需求！"
    ]
    for i, note in enumerate(notes):
        ws.cell(row=13 + i, column=2, value=note).font = font_small

    # Column Widths
    ws.column_dimensions["A"].width = 8   # 狀態
    ws.column_dimensions["B"].width = 46  # 主要任務
    for c in range(3, 22):
        col_letter = get_column_letter(c)
        ws.column_dimensions[col_letter].width = 4.8 # Month columns
    ws.column_dimensions["V"].width = 12  # 資材負責者
    ws.column_dimensions["W"].width = 16  # 其他單位負責者

    out_file = os.path.abspath("鴻勝危物倉庫專案新建工程_標準藍線甘特圖.xlsx")
    wb.save(out_file)
    print(f"File created successfully: {out_file}")

if __name__ == "__main__":
    create_traditional_gantt()
