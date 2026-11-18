import os
from PIL import Image, ImageDraw, ImageFont

def render_packaging_table_image():
    # Width 2200, 16:9 ratio style
    w = 2200
    h = 1150
    img = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    font_path_bold = "C:/Windows/Fonts/msjhbd.ttc"
    font_path_reg = "C:/Windows/Fonts/msjh.ttc"

    font_title = ImageFont.truetype(font_path_bold, 30)
    font_sub = ImageFont.truetype(font_path_reg, 18)
    font_unit = ImageFont.truetype(font_path_reg, 16)
    font_th = ImageFont.truetype(font_path_bold, 18)
    font_td_bold = ImageFont.truetype(font_path_bold, 18)
    font_td_reg = ImageFont.truetype(font_path_reg, 18)
    font_card_title = ImageFont.truetype(font_path_bold, 20)
    font_card_text = ImageFont.truetype(font_path_reg, 17)
    font_note = ImageFont.truetype(font_path_reg, 16)

    margin_x = 70
    start_y = 45

    # Top Accent Line
    draw.rectangle([margin_x, start_y, w - margin_x, start_y + 6], fill="#1E3A8A")

    # Title & Subtitle
    draw.text((margin_x, start_y + 16), "包材儲位中長期供需推估與因應對策", fill="#0F172A", font=font_title)
    draw.text((margin_x, start_y + 60), "含 6 座包材帳篷 (742板) 及完全露天 (86板) 空間之可用儲位與需求缺口推估", fill="#64748B", font=font_sub)

    # Unit Label
    unit_text = "單位：板"
    b_u = font_unit.getbbox(unit_text)
    draw.text((w - margin_x - (b_u[2] - b_u[0]), start_y + 60), unit_text, fill="#64748B", font=font_unit)

    # Table Geometry
    tbl_top = start_y + 98
    tbl_w = w - 2 * margin_x
    
    col_name_w = 680
    num_years = 5
    year_w = (tbl_w - col_name_w) / num_years # (2060 - 680)/5 = 276 px each

    years = ["2026", "2027", "2028", "2029", "2030"]

    # Table Data
    table_rows = [
        # (type, row_name, [2026, 2027, 2028, 2029, 2030])
        ("normal", "　• 6座包材帳篷 (742板) + 露天空間 (86板) 等", ["1,004", "890", "890", "890", "890"]),
        ("supply", "總可用儲位數 (供給)", ["1,004", "890", "890", "890", "890"]),
        ("demand", "預估需求儲位數", ["520", "756", "918", "1,098", "1,313"]),
        ("diff", "供需差額 (可用 - 需求)", ["+484", "+134", "-28", "-208", "-423"]),
        ("status", "儲位是否足夠", ["充足", "充足", "不足", "不足", "不足"]),
        ("judgement", "儲位充足性綜合判定", ["安全充裕", "安全 (餘量收窄)", "出現赤字缺口", "嚴重不足", "嚴重不足"])
    ]

    th_h = 52
    td_h = 48
    
    # Draw Table Header (Dark Navy #1E3A8A)
    draw.rectangle([margin_x, tbl_top, margin_x + tbl_w, tbl_top + th_h], fill="#1E3A8A")
    draw.text((margin_x + 25, tbl_top + 14), "項目 ＼ 年度", fill="#FFFFFF", font=font_th)

    for i, yr in enumerate(years):
        cx = margin_x + col_name_w + i * year_w
        b_yr = font_th.getbbox(yr)
        tw_yr = b_yr[2] - b_yr[0]
        draw.text((cx + (year_w - tw_yr) / 2, tbl_top + 14), yr, fill="#FFFFFF", font=font_th)

    # Draw Data Rows
    curr_y = tbl_top + th_h
    for r_idx, (r_type, r_name, vals) in enumerate(table_rows):
        ry1 = curr_y
        ry2 = ry1 + td_h
        mid_y = ry1 + 13

        # Row Background Fill matching Image 2
        bg_color = "#FFFFFF"
        if r_type == "supply":
            bg_color = "#EFF6FF" # Light blue
        elif r_type == "demand":
            bg_color = "#F8FAFC" # Slate tint
        elif r_type == "diff":
            bg_color = "#FAF5FF" # Light purple
        elif r_idx % 2 == 1:
            bg_color = "#FDFEFE"
        
        draw.rectangle([margin_x, ry1, margin_x + tbl_w, ry2], fill=bg_color)
        # Bottom divider
        draw.line([margin_x, ry2, margin_x + tbl_w, ry2], fill="#E2E8F0", width=1)

        # Row Title Text
        use_bold = (r_type != "normal")
        font_to_use = font_td_bold if use_bold else font_td_reg
        title_color = "#1E40AF" if r_type == "supply" else ("#0F172A" if use_bold else "#334155")
        draw.text((margin_x + 25, mid_y), r_name, fill=title_color, font=font_to_use)

        # Values
        for i, val in enumerate(vals):
            cx = margin_x + col_name_w + i * year_w
            
            # Value Color logic
            val_color = "#1E293B"
            if "-" in val or "不足" in val or "赤字" in val:
                val_color = "#DC2626" # Red
            elif "+" in val or "充足" in val or "安全" in val:
                val_color = "#16A34A" # Green
            
            val_font = font_td_bold if use_bold else font_td_reg
            b_v = val_font.getbbox(val)
            tw_v = b_v[2] - b_v[0]
            draw.text((cx + (year_w - tw_v) / 2, mid_y), val, fill=val_color, font=val_font)

        curr_y = ry2

    # Outer table border
    draw.rectangle([margin_x, tbl_top, margin_x + tbl_w, curr_y], outline="#CBD5E1", width=1)

    # 3 Insight Cards matching Image 2
    cards_top = curr_y + 40
    card_h = 240
    card_w = (tbl_w - 2 * 40) / 3 # ~646 px each

    cards = [
        {
            "title": "短期現況（2026～2027）",
            "body": "• 包含 6 座包材帳篷（742板）及露天空間（86板），現行可用儲位充裕。\n• 2026 年盈餘 +484 板、2027 年隨產線成長盈餘收窄至 +134 板，短期營運無立即性短缺風險。",
            "border": "#2563EB",
            "bg": "#F8FAFC"
        },
        {
            "title": "瓶頸警訊（2028 起轉為不足）",
            "body": "• 2028 年因產線正式放量，包材需求跳升至 918 板，可用儲位首度出現 -28 板缺口。\n• 2029～2030 年需求持續攀升至 1,098 及 1,313 板，赤字將迅速擴大至 -208 與 -423 板！",
            "border": "#F59E0B",
            "bg": "#FFFBEB"
        },
        {
            "title": "中長期因應對策（Next Steps）",
            "body": "• 導入包材 PWA 系統與安全水位即時預警，落實呆滯料清整與高周轉控管。\n• 評估帳篷區擴建立體貨架，或於 2027 年底前規劃新廠/外租空間，以化解 2028 年後之空間瓶頸。",
            "border": "#10B981",
            "bg": "#F0FDF4"
        }
    ]

    for j, c in enumerate(cards):
        card_x = margin_x + j * (card_w + 40)
        draw.rounded_rectangle([card_x, cards_top, card_x + card_w, cards_top + card_h], radius=16, fill=c["bg"], outline=c["border"], width=3)
        draw.text((card_x + 30, cards_top + 24), c["title"], fill="#0F172A", font=font_card_title)
        
        # Divider line inside card
        draw.line([card_x + 30, cards_top + 60, card_x + card_w - 30, cards_top + 60], fill="#E2E8F0", width=1)
        
        # Body text lines
        lines = c["body"].split("\n")
        line_y = cards_top + 75
        for line in lines:
            # Word wrap line if too long
            if len(line) > 34:
                l1 = line[:34]
                l2 = "  " + line[34:]
                draw.text((card_x + 30, line_y), l1, fill="#475569", font=font_card_text)
                draw.text((card_x + 30, line_y + 28), l2, fill="#475569", font=font_card_text)
                line_y += 56
            else:
                draw.text((card_x + 30, line_y), line, fill="#475569", font=font_card_text)
                line_y += 32

    # Bottom Note
    note_y = cards_top + card_h + 35
    draw.text((margin_x, note_y), "說明：可用儲位基準包含 6 座包材帳篷 742 板及完全露天 86 板空間；2027 年起調整為常態安全存放總計 890 板。", fill="#64748B", font=font_note)

    out_png = os.path.abspath("包材儲位供需推估簡報圖_圖二風格.png")
    if os.path.exists(out_png):
        try:
            os.remove(out_png)
        except:
            pass
    img.save(out_png, quality=95)
    print(f"High-res PNG image saved successfully: {out_png}")

if __name__ == "__main__":
    render_packaging_table_image()
