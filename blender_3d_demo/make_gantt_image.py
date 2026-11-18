import os
from PIL import Image, ImageDraw, ImageFont

def render_gantt_image_perfect():
    width = 2200
    
    font_path = "C:/Windows/Fonts/msjhbd.ttc"   # 微軟正黑體 粗體
    font_path_reg = "C:/Windows/Fonts/msjh.ttc" # 微軟正黑體 常規

    font_meta = ImageFont.truetype(font_path, 19)
    font_tbl_hdr = ImageFont.truetype(font_path, 19)
    font_month_hdr = ImageFont.truetype(font_path, 17)
    font_task_name = ImageFont.truetype(font_path, 18)
    font_owner = ImageFont.truetype(font_path_reg, 17)
    font_note_title = ImageFont.truetype(font_path, 19)
    font_note_text = ImageFont.truetype(font_path_reg, 17)

    # Margins
    margin_x = 45
    margin_top = 35

    # Top Header Metadata Box
    hdr_box_top = margin_top
    hdr_box_bottom = hdr_box_top + 90
    hdr_box_right = width - margin_x

    # Table Geometry
    tbl_top = hdr_box_bottom + 12
    
    # Let's give proper width to "狀態" (col_status_w) so "預計待辦事項" fits perfectly
    col_status_w = 110 # Increased from 90 to 110
    col_task_w = 640
    
    # 19 months: 2026 (11, 12), 2027 (1~12), 2028 (1~5)
    num_months = 19
    timeline_w = 1064
    month_w = timeline_w / num_months # Exactly 56.0 px each
    
    col_mat_w = 110
    col_other_w = 186

    # Coordinates
    x_status = margin_x
    x_task = x_status + col_status_w
    x_timeline = x_task + col_task_w
    x_mat = x_timeline + timeline_w
    x_other = x_mat + col_mat_w
    x_end = x_other + col_other_w

    h_r1 = tbl_top + 45
    h_r2 = h_r1 + 40
    task_row_h = 58
    side_box_bottom = h_r2 + 6 * task_row_h

    # Bottom Notes
    note_top = side_box_bottom + 20
    notes = [
        "1. 重要資產與設備需等圍籬建置完成及保全設置好以後才能入場放置。",
        "2. 線條為工程標準進度線，置中於儲存格正中央；原 35 項繁細工項已精簡整併為 6 大模組，排程完全對齊原案。",
        "3. 關鍵死線（Critical Path）：使用執照與正式送電必須於 2027 年 12 月底前完成，以利 2028 Q1 展開台積 PCN 審查。",
        "4. 產線對接保證：本專案預計 2028 Q1 取得台積認證並合法啟用 1,776 儲位，正好即時承接 2028 年新產線放量暴增之 3,445 板需求！"
    ]
    
    note_bottom = note_top + 32 + len(notes) * 27
    total_height = note_bottom + 25

    img = Image.new("RGB", (width, total_height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # 1. Header Box
    draw.rectangle([margin_x, hdr_box_top, hdr_box_right, hdr_box_bottom], outline="#000000", width=2)
    mid_h = (hdr_box_top + hdr_box_bottom) // 2
    draw.line([margin_x, mid_h, hdr_box_right, mid_h], fill="#000000", width=1)

    col_c_x = margin_x + 720
    col_t_x = margin_x + 1680
    draw.line([col_c_x, hdr_box_top, col_c_x, hdr_box_bottom], fill="#000000", width=1)
    draw.line([col_t_x, hdr_box_top, col_t_x, hdr_box_bottom], fill="#000000", width=1)

    draw.text((margin_x + 15, hdr_box_top + 10), "專案經理：", fill="#000000", font=font_meta)
    draw.text((col_c_x + 15, hdr_box_top + 10), "專案名稱：鴻勝危物倉庫專案新建工程", fill="#000000", font=font_meta)
    draw.text((col_t_x + 15, hdr_box_top + 10), "更新日期：20261113", fill="#000000", font=font_meta)

    draw.text((margin_x + 15, mid_h + 10), "專案目標：新增危險品庫存空間 (1,776儲位)", fill="#000000", font=font_meta)
    draw.text((col_c_x + 15, mid_h + 10), "專案期間：2026/11/01〜2028/05/31", fill="#000000", font=font_meta)
    draw.text((col_t_x + 15, mid_h + 10), "填表人：", fill="#000000", font=font_meta)

    # 2. Table Headers Background
    draw.rectangle([margin_x, tbl_top, x_end, h_r2], fill="#E5E7EB")

    # 狀態
    draw.rectangle([x_status, tbl_top, x_task, h_r2], outline="#000000", width=1)
    # Perfectly center "狀態"
    b_st = font_tbl_hdr.getbbox("狀態")
    tw_st = b_st[2] - b_st[0]
    th_st = b_st[3] - b_st[1]
    draw.text((x_status + (col_status_w - tw_st)/2, tbl_top + (85 - th_st)/2 - 3), "狀態", fill="#000000", font=font_tbl_hdr)

    # 主要任務 (6大核心工程模組)
    draw.rectangle([x_task, tbl_top, x_timeline, h_r2], outline="#000000", width=1)
    b_tm = font_tbl_hdr.getbbox("主要任務 (6大核心工程模組)")
    tw_tm = b_tm[2] - b_tm[0]
    draw.text((x_task + (col_task_w - tw_tm)/2, tbl_top + (85 - th_st)/2 - 3), "主要任務 (6大核心工程模組)", fill="#000000", font=font_tbl_hdr)

    # 2026 (2 months)
    x_2026_end = x_timeline + 2 * month_w
    draw.rectangle([x_timeline, tbl_top, x_2026_end, h_r1], outline="#000000", width=1)
    b_y26 = font_tbl_hdr.getbbox("2026年")
    draw.text((x_timeline + (2*month_w - (b_y26[2]-b_y26[0]))/2, tbl_top + 10), "2026年", fill="#000000", font=font_tbl_hdr)

    # 2027 (12 months)
    x_2027_end = x_2026_end + 12 * month_w
    draw.rectangle([x_2026_end, tbl_top, x_2027_end, h_r1], outline="#000000", width=1)
    b_y27 = font_tbl_hdr.getbbox("2027年")
    draw.text((x_2026_end + (12*month_w - (b_y27[2]-b_y27[0]))/2, tbl_top + 10), "2027年", fill="#000000", font=font_tbl_hdr)

    # 2028 (5 months)
    draw.rectangle([x_2027_end, tbl_top, x_timeline + timeline_w, h_r1], outline="#000000", width=1)
    b_y28 = font_tbl_hdr.getbbox("2028年")
    draw.text((x_2027_end + (5*month_w - (b_y28[2]-b_y28[0]))/2, tbl_top + 10), "2028年", fill="#000000", font=font_tbl_hdr)

    # Owners header
    draw.rectangle([x_mat, tbl_top, x_end, h_r1], outline="#000000", width=1)
    b_own = font_tbl_hdr.getbbox("任務負責人")
    draw.text((x_mat + ((col_mat_w + col_other_w) - (b_own[2]-b_own[0]))/2, tbl_top + 10), "任務負責人", fill="#000000", font=font_tbl_hdr)

    # Months
    months_labels = ["11月", "12月"] + [f"{m}月" for m in range(1, 13)] + ["1月", "2月", "3月", "4月", "5月"]
    for i, m_str in enumerate(months_labels):
        mx1 = x_timeline + i * month_w
        mx2 = mx1 + month_w
        draw.rectangle([mx1, h_r1, mx2, h_r2], outline="#000000", width=1)
        bbox = font_month_hdr.getbbox(m_str)
        tw = bbox[2] - bbox[0]
        draw.text((mx1 + (month_w - tw)/2, h_r1 + 10), m_str, fill="#000000", font=font_month_hdr)

    draw.rectangle([x_mat, h_r1, x_other, h_r2], outline="#000000", width=1)
    b_mat = font_month_hdr.getbbox("資材負責者")
    draw.text((x_mat + (col_mat_w - (b_mat[2]-b_mat[0]))/2, h_r1 + 10), "資材負責者", fill="#000000", font=font_month_hdr)

    draw.rectangle([x_other, h_r1, x_end, h_r2], outline="#000000", width=1)
    b_oth = font_month_hdr.getbbox("其他單位負責者")
    draw.text((x_other + (col_other_w - (b_oth[2]-b_oth[0]))/2, h_r1 + 10), "其他單位負責者", fill="#000000", font=font_month_hdr)

    # 3. Left box "預計待辦事項" -> Vertical 4 chars!
    draw.rectangle([x_status, h_r2, x_task, side_box_bottom], outline="#000000", width=1)
    # Render 4 characters vertically centered:
    chars = ["預", "計", "待", "辦", "事", "項"]
    # Total height of 6 chars with spacing
    char_spacing = 38
    start_char_y = h_r2 + (6 * task_row_h - len(chars) * char_spacing) / 2 + 5
    for idx_c, ch in enumerate(chars):
        b_ch = font_tbl_hdr.getbbox(ch)
        tw_ch = b_ch[2] - b_ch[0]
        draw.text((x_status + (col_status_w - tw_ch)/2, start_char_y + idx_c * char_spacing), ch, fill="#000000", font=font_tbl_hdr)

    # 4. Tasks Rows
    tasks = [
        ("一、發包規劃、建築設計與建照申報 (決標/定稿/開工申報)", "", "工務課 / 採購課", 0, 3.8),
        ("二、土木營造與全區結構施工 (整地/主體結構/降溫雨遮/排水圍牆)", "", "工務課 (營造廠)", 2, 8.8),
        ("三、機電、廠區水電與貨架專用消防系統 (水電/消防施作/送電)", "", "工務課 / 機電商", 5, 11.8),
        ("四、高架貨架系統與倉儲物流設備 (Layout/備料/安裝/充電站/堆高機)", "資材課", "設備商 / 採購課", 5, 12.8),
        ("五、法定查驗與使用執照取得 (消防現勘/建管竣工查驗/使照核發)", "", "工務課 / 環安課", 11, 13.8),
        ("六、監控保全、台積 PCN 審查與合法合規啟用 (對接2028新產線放量)", "資材課", "業務部 / IT室", 14, 17.8)
    ]

    for i, (t_name, o1, o2, m_start, m_end) in enumerate(tasks):
        ry1 = h_r2 + i * task_row_h
        ry2 = ry1 + task_row_h
        mid_y = (ry1 + ry2) // 2

        # Task Name
        draw.rectangle([x_task, ry1, x_timeline, ry2], outline="#000000", width=1)
        draw.text((x_task + 12, ry1 + 17), t_name, fill="#000000", font=font_task_name)

        # Timeline Grid cells
        for m_idx in range(num_months):
            cx1 = x_timeline + m_idx * month_w
            cx2 = cx1 + month_w
            draw.rectangle([cx1, ry1, cx2, ry2], outline="#000000", width=1)

        # Centered line
        line_x1 = x_timeline + m_start * month_w + 3
        line_x2 = x_timeline + m_end * month_w - 3
        line_color = "#1D4ED8"
        draw.line([line_x1, mid_y, line_x2, mid_y], fill=line_color, width=5)
        r_pt = 3
        draw.ellipse([line_x1 - r_pt, mid_y - r_pt, line_x1 + r_pt, mid_y + r_pt], fill=line_color)
        draw.ellipse([line_x2 - r_pt, mid_y - r_pt, line_x2 + r_pt, mid_y + r_pt], fill=line_color)

        # Owners
        draw.rectangle([x_mat, ry1, x_other, ry2], outline="#000000", width=1)
        if o1:
            b_o1 = font_owner.getbbox(o1)
            tw_o1 = b_o1[2] - b_o1[0]
            draw.text((x_mat + (col_mat_w - tw_o1)/2, ry1 + 18), o1, fill="#000000", font=font_owner)

        draw.rectangle([x_other, ry1, x_end, ry2], outline="#000000", width=1)
        if o2:
            b_o2 = font_owner.getbbox(o2)
            tw_o2 = b_o2[2] - b_o2[0]
            draw.text((x_other + (col_other_w - tw_o2)/2, ry1 + 18), o2, fill="#000000", font=font_owner)

    # Outer border
    draw.rectangle([margin_x, tbl_top, x_end, side_box_bottom], outline="#000000", width=2)

    # 5. Bottom Notes Section (Compact)
    draw.text((margin_x + 10, note_top), "備註說明與關鍵管制重點：", fill="#000000", font=font_note_title)
    for j, n in enumerate(notes):
        draw.text((margin_x + 15, note_top + 32 + j * 27), n, fill="#374151", font=font_note_text)

    out_img = os.path.abspath("危險品新倉精簡甘特圖_PPT專用圖.png")
    if os.path.exists(out_img):
        try:
            os.remove(out_img)
        except:
            pass
    img.save(out_img, quality=95)
    print(f"Perfect PNG saved successfully at: {out_img}")

if __name__ == "__main__":
    render_gantt_image_perfect()
