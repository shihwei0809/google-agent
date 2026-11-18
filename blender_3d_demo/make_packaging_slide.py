import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_packaging_storage_slide():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Top accent line
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = RGBColor(30, 58, 138)
    top_bar.line.fill.background()

    # Title Box
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.9))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = "包材儲位中長期供需推估與因應對策"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = RGBColor(15, 23, 42)
    p.font.name = "Microsoft JhengHei"

    p2 = tf.add_paragraph()
    p2.text = "含6座包材帳篷(742板)與露天空間(86板)之可用儲位供給與需求缺口分析"
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(100, 116, 139)
    p2.font.name = "Microsoft JhengHei"
    p2.space_before = Pt(3)

    # Unit Label
    unit_box = slide.shapes.add_textbox(Inches(10.5), Inches(1.15), Inches(2.0), Inches(0.3))
    utf = unit_box.text_frame
    utf.margin_left = utf.margin_top = utf.margin_right = utf.margin_bottom = 0
    up = utf.paragraphs[0]
    up.text = "單位：板"
    up.font.size = Pt(11)
    up.font.color.rgb = RGBColor(100, 116, 139)
    up.alignment = PP_ALIGN.RIGHT
    up.font.name = "Microsoft JhengHei"

    # Table Shape
    # 7 rows: Header + 6 rows
    rows = 7
    cols = 6
    left = Inches(0.8)
    top = Inches(1.4)
    width = Inches(11.733)
    height = Inches(2.9)

    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    col_widths = [Inches(4.233), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    headers = ["項目 ＼ 年度", "2026", "2027", "2028", "2029", "2030"]
    data = [
        ["　• 6座包材帳篷 (742板) + 露天空間 (86板) 等", "1,004", "890", "890", "890", "890"],
        ["總可用儲位數 (供給)", "1,004", "890", "890", "890", "890"],
        ["預估需求儲位數", "520", "756", "918", "1,098", "1,313"],
        ["供需差額 (可用 - 需求)", "+484", "+134", "-28", "-208", "-423"],
        ["儲位是否足夠", "充足", "充足", "不足", "不足", "不足"],
        ["儲位充足性綜合判定", "安全充裕", "安全 (餘量收窄)", "出現赤字缺口", "嚴重不足", "嚴重不足"]
    ]

    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = "Microsoft JhengHei"
        p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER

    for row_idx, row_data in enumerate(data, start=1):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            
            # Row backgrounds matching Image 2 style
            if row_idx == 2: # 總可用儲位
                cell.fill.fore_color.rgb = RGBColor(239, 246, 255)
            elif row_idx == 3: # 需求儲位
                cell.fill.fore_color.rgb = RGBColor(248, 250, 252)
            elif row_idx == 4: # 供需差額
                cell.fill.fore_color.rgb = RGBColor(254, 242, 242) if ("-" in val) else RGBColor(240, 253, 244)
            elif row_idx in [5, 6]: # 判定
                cell.fill.fore_color.rgb = RGBColor(255, 255, 255)
            else:
                cell.fill.fore_color.rgb = RGBColor(255, 255, 255)

            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10.5)
            p.font.name = "Microsoft JhengHei"
            p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER
            
            # Text styles
            if row_idx in [2, 3, 4, 5, 6]:
                p.font.bold = True
                
            if "-" in val or "不足" in val or "赤字" in val:
                p.font.color.rgb = RGBColor(220, 38, 38) # Red
            elif "+" in val or "充足" in val or "安全" in val:
                p.font.color.rgb = RGBColor(22, 163, 74) # Green
            else:
                p.font.color.rgb = RGBColor(30, 41, 59)

    # 3 Insight Cards matching Image 2
    card_top = Inches(4.7)
    card_height = Inches(2.25)
    card_width = Inches(3.75)
    spacing = Inches(0.24)

    cards_info = [
        {
            "title": "短期現況（2026～2027）",
            "body": "• 包含 6 座包材帳篷（742板）及露天空間（86板），現行可用儲位充裕。\n• 2026 年盈餘 +484 板、2027 年隨產線成長盈餘收窄至 +134 板，短期營運無立即性短缺風險。",
            "border": RGBColor(37, 99, 235),
            "bg": RGBColor(248, 250, 252)
        },
        {
            "title": "瓶頸警訊（2028 起轉為不足）",
            "body": "• 2028 年因產線正式放量，包材需求跳升至 918 板，可用儲位首度出現 -28 板缺口。\n• 2029～2030 年需求持續攀升至 1,098 及 1,313 板，赤字將迅速擴大至 -208 與 -423 板！",
            "border": RGBColor(245, 158, 11),
            "bg": RGBColor(255, 251, 235)
        },
        {
            "title": "中長期因應對策（Next Steps）",
            "body": "• 導入包材 PWA 系統與安全水位即時預警，落實呆滯料清整與高周轉控管。\n• 評估帳篷區擴建立體貨架，或於 2027 年底前規劃新廠/外租空間，以化解 2028 年後之空間瓶頸。",
            "border": RGBColor(22, 163, 74),
            "bg": RGBColor(240, 253, 244)
        }
    ]

    for i, c in enumerate(cards_info):
        c_left = Inches(0.8) + i * (card_width + spacing)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, card_top, card_width, card_height)
        box.fill.solid()
        box.fill.fore_color.rgb = c["bg"]
        box.line.color.rgb = c["border"]
        box.line.width = Pt(1.5)

        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.18)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.14)
        tf.margin_bottom = Inches(0.14)

        p = tf.paragraphs[0]
        p.text = c["title"]
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RGBColor(15, 23, 42)
        p.font.name = "Microsoft JhengHei"

        p_body = tf.add_paragraph()
        p_body.text = c["body"]
        p_body.font.size = Pt(10)
        p_body.font.color.rgb = RGBColor(51, 65, 85)
        p_body.font.name = "Microsoft JhengHei"
        p_body.space_before = Pt(5)

    # Note
    note_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
    ntf = note_box.text_frame
    ntf.margin_left = ntf.margin_top = ntf.margin_right = ntf.margin_bottom = 0
    np = ntf.paragraphs[0]
    np.text = "說明：可用儲位基準包含 6 座包材帳篷 742 板及完全露天 86 板空間；2027 年起調整為常態安全存放總計 890 板。"
    np.font.size = Pt(10)
    np.font.color.rgb = RGBColor(100, 116, 139)
    np.font.name = "Microsoft JhengHei"

    out_file = os.path.abspath("包材儲位供需推估簡報.pptx")
    prs.save(out_file)
    print(f"PPTX created successfully: {out_file}")

if __name__ == "__main__":
    create_packaging_storage_slide()
