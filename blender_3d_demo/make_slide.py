import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Top accent line
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = RGBColor(37, 99, 235)
    top_bar.line.fill.background()

    # Title Box
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(10.0), Inches(1.1))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = "危險品儲位中長期供需推估與因應策略（含2028新擴建倉）"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = RGBColor(15, 23, 42)
    p.font.name = "Microsoft JhengHei"

    p2 = tf.add_paragraph()
    p2.text = "崙尾第6層擴充效益、2028新產線放量瓶頸及新增1,776儲位新倉之綜合評估"
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(100, 116, 139)
    p2.font.name = "Microsoft JhengHei"
    p2.space_before = Pt(3)

    # Unit Label
    unit_box = slide.shapes.add_textbox(Inches(10.5), Inches(1.1), Inches(2.0), Inches(0.3))
    utf = unit_box.text_frame
    utf.margin_left = utf.margin_top = utf.margin_right = utf.margin_bottom = 0
    up = utf.paragraphs[0]
    up.text = "單位：板"
    up.font.size = Pt(11)
    up.font.color.rgb = RGBColor(100, 116, 139)
    up.alignment = PP_ALIGN.RIGHT
    up.font.name = "Microsoft JhengHei"

    # Table
    rows = 10
    cols = 6
    left = Inches(0.8)
    top = Inches(1.35)
    width = Inches(11.733)
    height = Inches(3.4)

    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    col_widths = [Inches(4.233), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    headers = ["項目 ＼ 年度", "2026", "2027", "2028", "2029", "2030"]
    data = [
        ["　• 彰濱一廠：第二庫房", "560", "560", "560", "560", "560"],
        ["　• 彰濱二廠：崙尾危倉 (1~5層)", "1,480", "1,480", "1,480", "1,480", "1,480"],
        ["　• 崙尾第6層擴充效益", "+296", "+296", "+296", "+296", "+296"],
        ["　• 2028 新增倉庫 (新增+1,776)", "-", "-", "+1,776", "+1,776", "+1,776"],
        ["總可用儲位供給 (含第6層與新倉)", "2,336", "2,336", "4,112", "4,112", "4,112"],
        ["預估儲位需求 (新產線2028放量)", "2,000", "2,227", "3,445", "3,576", "3,745"],
        ["未加新倉差額 (原2,336板)", "+336", "+109", "-1,109", "-1,240", "-1,409"],
        ["最終供需差額 (含2028新倉)", "+336", "+109", "+667", "+536", "+367"],
        ["儲位充足性綜合判定", "安全充裕", "安全 (微幅充裕)", "安全充裕", "安全充裕", "安全 (餘量遞減)"]
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
            
            # Row backgrounds
            if row_idx == 4: # 新增倉庫行
                cell.fill.fore_color.rgb = RGBColor(254, 243, 199)
            elif row_idx == 5: # 總可用儲位供給
                cell.fill.fore_color.rgb = RGBColor(239, 246, 255)
            elif row_idx == 6: # 預估儲位需求
                cell.fill.fore_color.rgb = RGBColor(248, 250, 252)
            elif row_idx == 7: # 未加新倉差額
                cell.fill.fore_color.rgb = RGBColor(254, 242, 242)
            elif row_idx == 8: # 最終供需差額
                cell.fill.fore_color.rgb = RGBColor(240, 253, 244)
            else:
                cell.fill.fore_color.rgb = RGBColor(255, 255, 255)

            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10)
            p.font.name = "Microsoft JhengHei"
            p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER
            
            # Styling text colors & bold
            if row_idx in [4, 5, 6, 7, 8, 9]:
                p.font.bold = True
                
            if row_idx == 7 and "-" in val:
                p.font.color.rgb = RGBColor(220, 38, 38) # Red for old deficit
            elif row_idx == 8 and "+" in val:
                p.font.color.rgb = RGBColor(22, 163, 74) # Green for surplus
            elif row_idx == 9:
                p.font.color.rgb = RGBColor(22, 163, 74) # All safe!
            elif row_idx == 4 and "+1,776" in val:
                p.font.color.rgb = RGBColor(180, 83, 9) # Amber
            else:
                p.font.color.rgb = RGBColor(30, 41, 59)

    # Bottom 3 Cards (Insight summary)
    card_top = Inches(4.9)
    card_height = Inches(2.15)
    card_width = Inches(3.75)
    spacing = Inches(0.24)

    cards_info = [
        {
            "title": "✅ 短期過渡（2026～2027）",
            "body": "• 崙尾第 6 層開放增加 +296 板，可用儲位達 2,336 板。\n• 2026 年餘 336 板、2027 年維持 +109 板安全餘量，足以支撐新產線建置期之初期存放需求。",
            "border": RGBColor(37, 99, 235),
            "bg": RGBColor(248, 250, 252)
        },
        {
            "title": "🚀 2028 新產線放量與新倉救援",
            "body": "• 2027 產線建置後於 2028 正式放量，需求跳升 55% 至 3,445 板（原庫房將面臨 -1,109 板斷崖赤字）。\n• 2028 年新倉（+1,776 板）及時投入，使總供給躍升至 4,112 板，成功化解缺口並盈餘 +667 板。",
            "border": RGBColor(245, 158, 11),
            "bg": RGBColor(255, 251, 235)
        },
        {
            "title": "🎯 中長期策略建言（2028～2030）",
            "body": "• 新倉加入後，2028～2030 年均維持安全水位，但隨業務成長，盈餘將由 +667 板逐年縮減至 +367 板。\n• 新倉工程必須嚴格控管於 2027 年底前完工驗收，確保 2028 Q1 產線放量時無縫對接。",
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
        tf.margin_top = Inches(0.12)
        tf.margin_bottom = Inches(0.12)

        p = tf.paragraphs[0]
        p.text = c["title"]
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(15, 23, 42)
        p.font.name = "Microsoft JhengHei"

        p_body = tf.add_paragraph()
        p_body.text = c["body"]
        p_body.font.size = Pt(9.5)
        p_body.font.color.rgb = RGBColor(51, 65, 85)
        p_body.font.name = "Microsoft JhengHei"
        p_body.space_before = Pt(4)

    # Output file
    output_path = os.path.abspath("危險品儲位供需推估簡報.pptx")
    prs.save(output_path)
    print(f"PPTX updated successfully at: {output_path}")

if __name__ == "__main__":
    create_presentation()
