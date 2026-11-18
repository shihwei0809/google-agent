import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_gantt_slide():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Top accent bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = RGBColor(37, 99, 235)
    top_bar.line.fill.background()

    # Title Box
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.733), Inches(1.0))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = "鴻勝 L02-1 危險品新倉庫建置專案 — 精簡工程甘特圖"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = RGBColor(15, 23, 42)
    p.font.name = "Microsoft JhengHei"

    p2 = tf.add_paragraph()
    p2.text = "專案目標：2028 Q1 啟用 1,776 儲位新倉 | 原 35 項細部工項整併為 6 大核心工程模組"
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(100, 116, 139)
    p2.font.name = "Microsoft JhengHei"
    p2.space_before = Pt(3)

    # Gantt Table
    # Timeline: 2026 Q4 (Nov, Dec), 2027 Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec), 2028 Q1 (Jan-Mar), 2028 Q2 (Apr)
    # Let's do 6 phases
    rows = 7 # Header + 6 phases
    cols = 8 # Phase & Scope, 2026 Q4, 2027 Q1, 2027 Q2, 2027 Q3, 2027 Q4, 2028 Q1, 主責單位
    
    left = Inches(0.8)
    top = Inches(1.4)
    width = Inches(11.733)
    height = Inches(3.6)

    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    col_widths = [Inches(3.433), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.45)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    headers = [
        "核心工程模組 (整併工項說明)",
        "2026 Q4\n(11~12月)",
        "2027 Q1\n(1~3月)",
        "2027 Q2\n(4~6月)",
        "2027 Q3\n(7~9月)",
        "2027 Q4\n(10~12月)",
        "2028 Q1\n(1~3月)",
        "主責/協同單位"
    ]

    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = "Microsoft JhengHei"
        p.alignment = PP_ALIGN.CENTER if col_idx > 0 else PP_ALIGN.LEFT

    phases = [
        {
            "name": "一、發包規劃與建築設計\n• L02-1 決標、建築設計定稿、建照申請",
            "schedule": [True, False, False, False, False, False],
            "owner": "工務課 / 採購課",
            "color": RGBColor(59, 130, 246)
        },
        {
            "name": "二、土木營造與基礎工程\n• 廠區道路地面、危倉結構、雨遮與排水圍牆",
            "schedule": [False, True, True, False, False, False],
            "owner": "工務課 (營造廠)",
            "color": RGBColor(59, 130, 246)
        },
        {
            "name": "三、水電與消防機電工程\n• 全區水電管線、危倉與貨架消防、正式送電",
            "schedule": [False, False, True, True, False, False],
            "owner": "工務課 / 機電商",
            "color": RGBColor(59, 130, 246)
        },
        {
            "name": "四、高架貨架系統與設備\n• 儲位Layout發包、備料安裝、堆高機充電站",
            "schedule": [False, False, False, True, True, False],
            "owner": "資材課 / 設備商",
            "color": RGBColor(245, 158, 11)
        },
        {
            "name": "五、法定驗收與使用執照\n• 消防查驗現勘、建管竣工、使照核發取得",
            "schedule": [False, False, False, False, True, False],
            "owner": "工務 / 環安 / 資材",
            "color": RGBColor(239, 68, 68)
        },
        {
            "name": "六、客戶認證與正式啟用\n• 台積 PCN 審查、保全進駐、危倉合規投產",
            "schedule": [False, False, False, False, False, True],
            "owner": "業務部 / 資材課",
            "color": RGBColor(16, 185, 129)
        }
    ]

    for row_idx, phase in enumerate(phases, start=1):
        # Col 0: Name
        cell_0 = table.cell(row_idx, 0)
        cell_0.fill.solid()
        cell_0.fill.fore_color.rgb = RGBColor(248, 250, 252) if row_idx % 2 == 0 else RGBColor(255, 255, 255)
        p = cell_0.text_frame.paragraphs[0]
        p.text = phase["name"]
        p.font.size = Pt(9.5)
        p.font.name = "Microsoft JhengHei"
        p.font.bold = True
        p.font.color.rgb = RGBColor(15, 23, 42)

        # Timeline cols (1 to 6)
        for col_idx, is_active in enumerate(phase["schedule"], start=1):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            if is_active:
                cell.fill.fore_color.rgb = phase["color"]
                p = cell.text_frame.paragraphs[0]
                p.text = "■ 施作" if row_idx < 5 else ("■ 查驗" if row_idx == 5 else "★ 投產")
                p.font.size = Pt(9.5)
                p.font.bold = True
                p.font.color.rgb = RGBColor(255, 255, 255)
                p.font.name = "Microsoft JhengHei"
                p.alignment = PP_ALIGN.CENTER
            else:
                cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if row_idx % 2 == 0 else RGBColor(255, 255, 255)
                cell.text_frame.text = ""

        # Owner col (7)
        cell_owner = table.cell(row_idx, 7)
        cell_owner.fill.solid()
        cell_owner.fill.fore_color.rgb = RGBColor(248, 250, 252) if row_idx % 2 == 0 else RGBColor(255, 255, 255)
        p = cell_owner.text_frame.paragraphs[0]
        p.text = phase["owner"]
        p.font.size = Pt(9)
        p.font.name = "Microsoft JhengHei"
        p.font.color.rgb = RGBColor(71, 85, 105)
        p.alignment = PP_ALIGN.CENTER

    # Bottom 3 Cards: Clarification & Consolidation logic
    card_top = Inches(5.15)
    card_height = Inches(1.95)
    card_width = Inches(3.75)
    spacing = Inches(0.24)

    cards_info = [
        {
            "title": "📦 為什麼需要精簡？（整併邏輯）",
            "body": "• 原表將『道路/結構/雨遮/排水』與『水電/消防』過度切碎，向主管簡報易失焦。\n• 整併為『土木、機電、貨架、使照、客戶認證』5 大里程碑，掌握高層決策節奏。",
            "border": RGBColor(37, 99, 235),
            "bg": RGBColor(248, 250, 252)
        },
        {
            "title": "⚡ 關鍵路徑管制（Critical Path）",
            "body": "• 貨架備料安裝（2027 Q3~Q4）需配合消防配管無縫進場施作。\n• 使照審查與正式電（2027 Q4）必須在年底前完成，避免影響後續客戶認證。",
            "border": RGBColor(245, 158, 11),
            "bg": RGBColor(255, 251, 235)
        },
        {
            "title": "🎯 2028 Q1 產線放量對接保證",
            "body": "• 業務提出台積 PCN 審查（2028 Q1）需約 1~2 個月審核期。\n• 2028 年 3 月危倉合法合規啟用，正好無縫銜接 2028 年新產線放量暴增之 3,445 板需求！",
            "border": RGBColor(16, 185, 129),
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
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(15, 23, 42)
        p.font.name = "Microsoft JhengHei"

        p_body = tf.add_paragraph()
        p_body.text = c["body"]
        p_body.font.size = Pt(9.5)
        p_body.font.color.rgb = RGBColor(51, 65, 85)
        p_body.font.name = "Microsoft JhengHei"
        p_body.space_before = Pt(4)

    output_path = os.path.abspath("危險品新倉精簡工程甘特圖.pptx")
    prs.save(output_path)
    print(f"Gantt PPTX created at: {output_path}")

if __name__ == "__main__":
    create_gantt_slide()
