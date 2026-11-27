import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement

# ============================================================
# Executive KPI Dashboard Palette (Matching Reference Style)
# ============================================================
NAVY_DARK    = RGBColor(22, 50, 92)     # #16325C Top Banner / Header
BLUE_ACCENT  = RGBColor(37, 99, 235)    # #2563EB Primary Blue / Pill / Divider
BLUE_PILL    = RGBColor(43, 108, 176)   # #2B6CB0 Cover Tag Pill
GREEN_DARK   = RGBColor(22, 101, 52)    # #166534 Success / KPI Green
AMBER_DARK   = RGBColor(180, 83, 9)     # #B45309 Warning / KPI Amber
RED_DARK     = RGBColor(185, 28, 28)    # #B91C1C Highlight / KPI Crimson
SLATE_BG     = RGBColor(244, 247, 251)  # #F4F7FB Light Canvas
WHITE        = RGBColor(255, 255, 255)
TEXT_DARK    = RGBColor(30, 41, 59)     # #1E293B Main Body
TEXT_MUTED   = RGBColor(100, 116, 139)  # #64748B Subtext / Labels
TEXT_LIGHT   = RGBColor(203, 213, 225)  # #CBD5E1 Subtitle on Navy
BORDER_GRAY  = RGBColor(218, 226, 236)  # #DAE2EC Card Border
ROW_ALT      = RGBColor(248, 250, 252)  # #F8FAFC Table Alt Row
GREEN_BG     = RGBColor(220, 252, 231)  # #DCFCE7 Status Pill BG

FONT_NAME = "Microsoft JhengHei"
FOOTER_TEXT = "鴻勝化學 數位轉型與 AI 系統成果發表  |  資料基準日：2026/11/27  |  製作人：shihwei0809"

BASE_DIR = r"d:\GOOGLE ANGET\專案成果發表_PPT"
IMG_DIR = os.path.join(BASE_DIR, "images")
OUT_PPTX = os.path.join(BASE_DIR, "2026_AI與數位轉型八大專案成果發表_高管量化版.pptx")


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shadow(shape):
    """Add subtle soft drop shadow matching modern executive cards."""
    spPr = shape._element.spPr
    effectLst = OxmlElement('a:effectLst')
    outerShdw = OxmlElement('a:outerShdw')
    outerShdw.set('blurRad', '76200')   # 6 pt
    outerShdw.set('dist', '25400')      # 2 pt
    outerShdw.set('dir', '5400000')     # 90 deg (down)
    outerShdw.set('algn', 'ctr')
    outerShdw.set('rotWithShape', '0')
    srgbClr = OxmlElement('a:srgbClr')
    srgbClr.set('val', '0F172A')
    alpha = OxmlElement('a:alpha')
    alpha.set('val', '14000')           # 14% opacity
    srgbClr.append(alpha)
    outerShdw.append(srgbClr)
    effectLst.append(outerShdw)
    spPr.append(effectLst)


def set_cell_border(cell, border_color="DAE2EC", border_width="6350"):
    tcPr = cell._tc.get_or_add_tcPr()
    for edge in ('lnL', 'lnR', 'lnT', 'lnB'):
        ln = OxmlElement(f'a:{edge}')
        ln.set('w', border_width)
        ln.set('cap', 'flat')
        ln.set('cmpd', 'sng')
        ln.set('algn', 'ctr')
        solidFill = OxmlElement('a:solidFill')
        srgbClr = OxmlElement('a:srgbClr')
        srgbClr.set('val', border_color)
        solidFill.append(srgbClr)
        ln.append(solidFill)
        tcPr.append(ln)


def add_textbox(slide, left, top, width, height, text, font_size=14, bold=False,
                color=TEXT_DARK, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT_NAME
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return tb


def add_footer(slide, page_num=None):
    add_textbox(slide, Inches(0.55), Inches(7.12), Inches(10.8), Inches(0.28),
                FOOTER_TEXT, font_size=9.5, color=TEXT_MUTED)
    if page_num is not None:
        add_textbox(slide, Inches(12.0), Inches(7.12), Inches(0.8), Inches(0.28),
                    f"{page_num} / 12", font_size=9.5, bold=True, color=TEXT_MUTED, align=PP_ALIGN.RIGHT)


def add_header_bar(slide, title, subtitle, badge_text=None):
    # Top navy bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY_DARK
    bar.line.fill.background()

    # Thin bright blue accent bottom edge
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.05), Inches(13.333), Inches(0.055))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = BLUE_ACCENT
    stripe.line.fill.background()

    add_textbox(slide, Inches(0.55), Inches(0.14), Inches(9.8), Inches(0.48),
                title, font_size=22, bold=True, color=WHITE)
    add_textbox(slide, Inches(0.55), Inches(0.64), Inches(9.8), Inches(0.32),
                subtitle, font_size=11.5, color=TEXT_LIGHT)

    if badge_text:
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.65), Inches(0.30), Inches(2.15), Inches(0.42))
        pill.adjustments[0] = 0.25
        pill.fill.solid()
        pill.fill.fore_color.rgb = BLUE_PILL
        pill.line.fill.background()
        tf = pill.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = badge_text
        r.font.name = FONT_NAME
        r.font.size = Pt(11.5)
        r.font.bold = True
        r.font.color.rgb = WHITE


def add_kpi_card(slide, left, top, width, height, label, big_value, subtext, accent_color, val_size=30):
    # White rounded card
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.adjustments[0] = 0.04
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = BORDER_GRAY
    card.line.width = Pt(0.75)
    add_shadow(card)

    # Top colored accent bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.02), top, width - Inches(0.04), Inches(0.085))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = accent_color
    top_bar.line.fill.background()

    # Label
    add_textbox(slide, left + Inches(0.20), top + Inches(0.20), width - Inches(0.40), Inches(0.32),
                label, font_size=12, bold=True, color=TEXT_MUTED)

    # Big KPI Value
    add_textbox(slide, left + Inches(0.20), top + Inches(0.54), width - Inches(0.40), Inches(0.66),
                big_value, font_size=val_size, bold=True, color=accent_color)

    # Subtext
    add_textbox(slide, left + Inches(0.20), top + Inches(1.28), width - Inches(0.40), height - Inches(1.42),
                subtext, font_size=11, color=TEXT_DARK)


def add_callout_box(slide, left, top, width, height, title, bullets, accent_color=NAVY_DARK,
                    body_size=12.5, space_after=6):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.adjustments[0] = 0.04
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = accent_color
    box.line.width = Pt(1.0)
    add_shadow(box)

    # Thick left accent strip
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top + Inches(0.03), Inches(0.11), height - Inches(0.06))
    strip.fill.solid()
    strip.fill.fore_color.rgb = accent_color
    strip.line.fill.background()

    add_textbox(slide, left + Inches(0.26), top + Inches(0.16), width - Inches(0.42), Inches(0.36),
                title, font_size=14, bold=True, color=NAVY_DARK)

    tb = slide.shapes.add_textbox(left + Inches(0.26), top + Inches(0.58), width - Inches(0.44), height - Inches(0.70))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_top = Inches(0.02)
    for idx, (tag, desc) in enumerate(bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        r1 = p.add_run()
        r1.text = f"▸ {tag}："
        r1.font.name = FONT_NAME
        r1.font.size = Pt(body_size)
        r1.font.bold = True
        r1.font.color.rgb = accent_color
        r2 = p.add_run()
        r2.text = desc
        r2.font.name = FONT_NAME
        r2.font.size = Pt(body_size)
        r2.font.color.rgb = TEXT_DARK


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ============================================================
    # SLIDE 1: Cover + Executive KPI Dashboard (Exact Reference Style)
    # ============================================================
    s1 = prs.slides.add_slide(blank)
    set_slide_bg(s1, SLATE_BG)

    # Top Navy Banner (matching screenshot proportion ~38%)
    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(2.75))
    banner.fill.solid()
    banner.fill.fore_color.rgb = NAVY_DARK
    banner.line.fill.background()

    # Bright Blue Divider Stripe
    div = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(2.75), Inches(13.333), Inches(0.07))
    div.fill.solid()
    div.fill.fore_color.rgb = BLUE_ACCENT
    div.line.fill.background()

    # Blue Tag Pill
    pill = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(0.42), Inches(2.55), Inches(0.42))
    pill.fill.solid()
    pill.fill.fore_color.rgb = BLUE_PILL
    pill.line.fill.background()
    tf = pill.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "年度數位轉型成果發表"
    r.font.name = FONT_NAME
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = WHITE

    # Main Title
    add_textbox(s1, Inches(0.58), Inches(1.02), Inches(12.1), Inches(0.82),
                "鴻勝化學 × AI 智慧系統八大成果發表", font_size=36, bold=True, color=WHITE)

    # Subtitle
    add_textbox(s1, Inches(0.60), Inches(1.95), Inches(12.1), Inches(0.42),
                "品管檢驗 · 出貨防呆 · 無紙化檢點 · 智慧倉儲 · 產銷追蹤 · AI 影音教材  |  彙整基準：2026/11",
                font_size=14, color=TEXT_LIGHT)

    # 4 Big KPI Cards
    card_w = Inches(2.85)
    card_h = Inches(2.25)
    card_top = Inches(3.15)
    gap = Inches(0.24)
    start_x = Inches(0.60)

    kpis_s1 = [
        ("正式上線專案", "8 大系統", "涵蓋品管、出貨、檢點、倉儲、\n報表、產銷、行政與 AI 影音", BLUE_ACCENT),
        ("每月預估節省工時", "約 145 小時", "六大日常系統自動化省時合計\n相當於每月釋放近 1 名人力", GREEN_DARK),
        ("高併發壓測實績", "0.37 秒", "50 人同時掃碼報到／檢點\n100% 零錯誤、零覆蓋、零撞號", AMBER_DARK),
        ("數位納管規模", "2,635 格", "崙尾＋鴻勝全倉儲位數位化\n同步追蹤 364 筆＋國際報價", RED_DARK),
    ]
    for i, (lbl, val, sub, clr) in enumerate(kpis_s1):
        add_kpi_card(s1, start_x + i * (card_w + gap), card_top, card_w, card_h, lbl, val, sub, clr, val_size=32)

    # Bottom Summary Callout Box
    add_callout_box(
        s1, Inches(0.60), Inches(5.65), Inches(12.13), Inches(1.25),
        "核心發表重點（2026 年度落地實績）",
        [
            ("零門檻全雲端落地", "採三軌架構，免裝軟體、手機/電腦跨裝置即時同步，現場人員開箱即用、零主機維護費。"),
            ("省時與防呆雙量化", "六大日常系統預估每月節省約 145 小時人工工時，搭配 5 重 OCR 攔截與 1 秒還原，大幅降低作業風險。"),
        ],
        accent_color=NAVY_DARK
    )
    add_footer(s1, 1)

    # ============================================================
    # SLIDE 2: 8 Projects Quantified Overview Table (Reference Slide 3 Style)
    # ============================================================
    s2 = prs.slides.add_slide(blank)
    set_slide_bg(s2, SLATE_BG)
    add_header_bar(s2, "八大核心專案量化成果一覽表",
                   "橫跨品管、出貨、倉儲、產銷與 AI 影音 8 大場景，聚焦「省時量化 × 現場防呆」全面落地",
                   "8 / 8 已上線")

    rows_data = [
        ("01", "QC 檢驗即時看板 & TSC 直印", "品管檢驗", "約省 25h/月 · 90×60mm 純內網秒出紙", "v3.3.8 上線"),
        ("02", "台積三合一單 & COA 視覺核對", "出貨防呆", "約省 20h/月 · 5 重 OCR 100% 攔截誤拍", "V50 上線"),
        ("03", "SOP / WI 檢查表電子化檢點", "無紙化檢點", "約省 30h/月 · 6.1～6.5 全 5 表 0.47s 壓測", "正式上線"),
        ("04", "倉儲儲位管理 PWA 系統", "智慧倉儲", "約省 20h/月 · 納管 2,635 格儲位防誤匯", "v1.0.22 上線"),
        ("05", "勝一 / 鴻勝四大出貨報表系統", "報表自動化", "約省 35h/月 · 三重核對零硬猜＋1 秒還原", "現場運作"),
        ("06", "產銷動態計畫 & IPA 報價船期", "產銷決策", "約省 15h/月 · 日爬 364 筆＋報價與船期", "正式上線"),
        ("07", "企業活動簽到與滿意度系統", "企業行政", "約省 10h/場 · 50 人報到 0.37s 零撞號", "v2.1.0 上線"),
        ("08", "SOP 微電影與 AI 語音產線", "教育訓練", "約省 20h/部 · 0 元 GPU 台灣國語語音克隆", "完成出片"),
    ]

    tbl_shape = s2.shapes.add_table(len(rows_data) + 1, 5, Inches(0.55), Inches(1.38), Inches(12.23), Inches(5.45))
    tbl = tbl_shape.table
    col_widths = [Inches(0.75), Inches(3.25), Inches(1.55), Inches(4.98), Inches(1.70)]
    for idx, w in enumerate(col_widths):
        tbl.columns[idx].width = w

    headers = ["編號", "專案系統名稱", "應用領域", "核心量化指標", "部署狀態"]
    for c, h_text in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_DARK
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        set_cell_border(cell, "16325C")
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if c in (0, 2, 4) else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = h_text
        r.font.name = FONT_NAME
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = WHITE

    for r_idx, row in enumerate(rows_data, start=1):
        bg_clr = WHITE if r_idx % 2 == 1 else ROW_ALT
        for c, val in enumerate(row):
            cell = tbl.cell(r_idx, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = GREEN_BG if c == 4 else bg_clr
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            set_cell_border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c in (0, 2, 4) else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            r.font.name = FONT_NAME
            r.font.size = Pt(12)
            r.font.bold = (c in (0, 1, 4))
            if c == 0:
                r.font.color.rgb = BLUE_ACCENT
            elif c == 4:
                r.font.color.rgb = GREEN_DARK
            else:
                r.font.color.rgb = TEXT_DARK

    add_footer(s2, 2)

    # ============================================================
    # SLIDE 3: Architecture & 4-Pillar Engineering Standard (Reference Slide 2 Style)
    # ============================================================
    s3 = prs.slides.add_slide(blank)
    set_slide_bg(s3, SLATE_BG)
    add_header_bar(s3, "共用技術底座：標準化四階工程架構",
                   "所有系統遵循統一開發、壓測、防呆與維運標準，大幅縮短開發與跨機部署週期",
                   "企業級架構")

    # 4 Horizontal Flow Chevrons
    stages = [
        ("01  三軌部署架構", BLUE_ACCENT),
        ("02  高併發穩定驗證", GREEN_DARK),
        ("03  現場零權限防呆", AMBER_DARK),
        ("04  AI 自動化維運", NAVY_DARK),
    ]
    chev_w = Inches(2.92)
    chev_h = Inches(0.62)
    for i, (st_title, clr) in enumerate(stages):
        shp = s3.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.58) + i * Inches(3.04), Inches(1.48), chev_w, chev_h)
        shp.fill.solid()
        shp.fill.fore_color.rgb = clr
        shp.line.fill.background()
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = st_title
        r.font.name = FONT_NAME
        r.font.size = Pt(13.5)
        r.font.bold = True
        r.font.color.rgb = WHITE

    # 4 Detailed Metric Cards underneath
    arch_cards = [
        ("三軌並行覆蓋", "3 軌", "• 純 Web / 本機 PWA / 雲端版\n• 斷網自動暫存，連線自動補傳\n• 手機、平板、電腦即開即用", BLUE_ACCENT),
        ("高併發壓測通過", "50 人", "• 單列原子寫入 100% 防撞號\n• 0.37s～0.47s 極速即時回應\n• 台灣時間 UTC+8 精準校時", GREEN_DARK),
        ("零 IT 依賴落地", "0 權限", "• 免管理員權限純內網列印代理\n• 純 ASCII 腳本杜絕中文閃退\n• 更新前雙備份＋1 秒還原保護", AMBER_DARK),
        ("永續交接標準化", "4 件套", "• 全案標配 README + SKILL\n• 一鍵 setup_env + Word 手冊\n• 跨機 Git＋Drive 7 天滾動備份", NAVY_DARK),
    ]
    for i, (lbl, val, sub, clr) in enumerate(arch_cards):
        add_kpi_card(s3, Inches(0.58) + i * Inches(3.04), Inches(2.38), Inches(2.90), Inches(3.25),
                     lbl, val, sub, clr, val_size=34)

    add_callout_box(
        s3, Inches(0.58), Inches(5.86), Inches(12.16), Inches(1.05),
        "架構核心效益",
        [("高複製性與零維護成本", "新專案直接複用三軌標準模板與雲端託管，免額外租用主機，實現 0 元託管與快速上線。")],
        accent_color=BLUE_ACCENT
    )
    add_footer(s3, 3)

    # ============================================================
    # SLIDES 4-11: 8 Individual Project Quantified Dashboard Slides
    # ============================================================
    projects = [
        {
            "num": "01",
            "title": "01｜QC 檢驗即時看板與 TSC 行動直印系統",
            "subtitle": "線上正式站：https://qc-samples.pages.dev  |  品管檢驗即時追蹤與標籤直印",
            "badge": "v3.3.8 上線",
            "img": "proj_01_qc.png",
            "kpis": [
                ("每月預估省時", "約 25 小時", "T100 排程自動帶入\n取代手抄送樣與電話催檢", BLUE_ACCENT),
                ("TSC 行動直印", "90×60mm", "純內網 HTTP 同源代理\n突破 iOS 封鎖一鍵秒出紙", GREEN_DARK),
                ("單號自動對齊", "100%", "ESPM 進料 / ESXM 出貨\n防誤植＋Teams 逾期警報", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "紙本送樣難追蹤、人工電話催檢耗時，且手機跨網段印標籤版面易跑位。"),
                ("解法", "整合 T100 排程匯入、單號前綴自動防呆，並建置免管理員純內網列印伺服器。"),
                ("效益", "看板零漏單、Teams 自動催檢，手機免裝 App 直接精準出紙。"),
            ],
        },
        {
            "num": "02",
            "title": "02｜台積三合一單與 COA AI 視覺雙重核對系統",
            "subtitle": "線上正式站：https://coa-check-pwa.pages.dev  |  電子級化學品出貨防呆",
            "badge": "V50 防呆版",
            "img": "proj_02_coa.png",
            "kpis": [
                ("嚴格防呆機制", "5 重卡控", "攔截誤拍三合一／COA\n強制驗證 ESXM 磅單特徵", RED_DARK),
                ("核心欄位比對", "4 大項目", "地點、槽號、批號、料號\n手機拍照 OCR 秒級核對", BLUE_ACCENT),
                ("每月預估省時", "約 20 小時", "拍照秒級比對取代目視\n100% 阻斷誤拍假成功", GREEN_DARK),
            ],
            "bullets": [
                ("痛點", "出貨人工肉眼核對耗時易疲勞，且曾發生誤拿三合一單充當地磅單之假成功風險。"),
                ("解法", "導入 5 重關鍵字與重複圖防呆卡控，升級 PWA Service Worker 自動無感更新。"),
                ("效益", "徹底封堵現場人為疏漏，出貨核對全程數位留痕供品保隨時稽核。"),
            ],
        },
        {
            "num": "03",
            "title": "03｜SOP / WI 檢查表電子化檢點系統 (6.1～6.5)",
            "subtitle": "線上正式站：https://wi-checklist-system.pages.dev  |  儲槽進出貨全面無紙化",
            "badge": "50人壓測通過",
            "img": "proj_03_wi.png",
            "kpis": [
                ("表單數位化", "5 大表單", "完整轉譯 27 頁作業標準\n6.1 槽車泵料～6.5 放櫃", BLUE_ACCENT),
                ("每月預估省時", "約 30 小時", "溢槽自動試算＋簽名庫補簽\n省去紙本歸檔與調閱工時", GREEN_DARK),
                ("原格式匯出", "1 : 1", "A4 PDF & ExcelJS 含簽名\n50 人同時寫入 0.47s 零錯", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "紙本檢點表繁瑣、溢槽容積需人工手算，主管補簽與歷史調閱耗費大量工時。"),
                ("解法", "內建 (A)-(B)=(C) 溢槽自動試算、多台雲端暫存供品管補簽與主管簽名檔庫。"),
                ("效益", "無紙化 1:1 還原法定表單，歷史版本永久鎖定，兼顧現場速度與稽核合規。"),
            ],
        },
        {
            "num": "04",
            "title": "04｜倉儲儲位管理 PWA 系統",
            "subtitle": "線上正式站：https://storage-rack-pwa.pages.dev  |  崙尾倉 × 鴻勝倉即時盤點",
            "badge": "v1.0.22 上線",
            "img": "proj_04_rack.png",
            "kpis": [
                ("納管儲位總數", "2,635 格", "崙尾倉 1,775 格（577 有貨）\n鴻勝倉 860 格（321 有貨）", BLUE_ACCENT),
                ("跨倉誤匯防呆", "100% 鎖定", "自動辨識儲位格式歸屬\n倉庫不符立即紅燈禁匯入", RED_DARK),
                ("每月預估省時", "約 20 小時", "1 秒模糊查品名＆動態濾批號\n大幅縮短盤點找貨時間", GREEN_DARK),
            ],
            "bullets": [
                ("痛點", "傳統 Excel 巨集表無法在倉庫現場手機查詢，批次匯入時易發生跨倉誤覆蓋。"),
                ("解法", "建置自然排序儲位地圖、動態批號連動選單、人員帳號 Excel 批次匯出入。"),
                ("效益", "現場手機即時查儲位與批號，帳料正確率與盤點效率大幅提升。"),
            ],
        },
        {
            "num": "05",
            "title": "05｜勝一 / 鴻勝四大出貨報表自動化產生系統",
            "subtitle": "勝一小包 · 勝一三合一 · 鴻勝三合一 · 鴻勝 N 系列  |  桌面報表批次自動化",
            "badge": "4 大系統",
            "img": "proj_05_reports.png",
            "kpis": [
                ("核對嚴謹度", "3 重核對", "批號＋出貨日＋FabPhase\n零硬編碼猜測、缺碼即警示", BLUE_ACCENT),
                ("每月預估省時", "約 35 小時", "一鍵批次產出 PR 與 COA\n自動算桶數×200與回推日", GREEN_DARK),
                ("安全防錯保護", "1 秒還原", "更新前雙重備份＋語法自檢\n純 ASCII 腳本根治閃退", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "PR 履歷與 COA 報表人工整理易出錯，舊版腳本在中文路徑下易閃退無回饋。"),
                ("解法", "嚴格依對照表檢核、自動標準化 F5 廠區檔名與目錄，導入一鍵更新與秒還原。"),
                ("效益", "批次產單零人為計算錯誤，現場人員遇異常 1 秒無痛退回穩定版。"),
            ],
        },
        {
            "num": "06",
            "title": "06｜鴻勝產銷動態計畫 & IPA 報價船期追蹤平台",
            "subtitle": "線上正式站：https://ipa-quote-vessel-tracker.pages.dev  |  產銷試算與市場情報",
            "badge": "每日自動爬蟲",
            "img": "proj_06_planner.png",
            "kpis": [
                ("國際報價追蹤", "364 筆+", "每日排程自動爬蟲更新\n即時掌握化學品行情趨勢", BLUE_ACCENT),
                ("船期與匯率", "17 筆+", "整合船期動態與即時匯率\n支援 Excel 雙向匯出入", GREEN_DARK),
                ("每月預估省時", "約 15 小時", "自動彙整每日報價與船期\n取代人工跨站查價填表", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "原物料國際行情、船期與內部產銷試算分散多處，決策資訊彙整耗時。"),
                ("解法", "建置三軌產銷動態計畫引擎，串接每日自動報價船期爬蟲並即時同步看板。"),
                ("效益", "採購與生管即時共用單一決策看板，大幅縮短產銷排程反應時間。"),
            ],
        },
        {
            "num": "07",
            "title": "07｜企業活動簽到與滿意度調查雲端系統",
            "subtitle": "線上正式站：https://event-checkin-system.pages.dev  |  大型活動極速報到",
            "badge": "v2.1.0 上線",
            "img": "proj_07_checkin.png",
            "kpis": [
                ("高併發報到", "0.37 秒", "50 人同時掃碼報到實測\n原子配號 100% 零撞號", GREEN_DARK),
                ("每場預估省時", "約 10 小時", "免人工唱名登錄與紙本統計\n出席與問卷報表一鍵匯出", BLUE_ACCENT),
                ("定時切問卷", "UTC+8 校時", "活動結束自動切滿意度頁\n斷網佇列補傳 0 筆遺失", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "大型會議與教育訓練現場報到易塞車，紙本問卷回收率低且人工統計費時。"),
                ("解法", "單列原子寫入防覆蓋、支援代簽補簽、後台全項目彈性開關與定時切問卷。"),
                ("效益", "徹底消除報到排隊瓶頸，問卷即時回收與出席統計一鍵完成。"),
            ],
        },
        {
            "num": "08",
            "title": "08｜企業 SOP 微電影教學與 AI 語音克隆產線",
            "subtitle": "跨專案共用技能：sop-cinema-video  |  《BPM 一般費用報銷單》實務落地",
            "badge": "AI 影音創新",
            "img": "proj_08_video.png",
            "kpis": [
                ("單部預估省時", "約 20 小時", "AI 配音＋自動剪輯混音\n取代傳統重複錄製剪接", BLUE_ACCENT),
                ("台灣國語配音", "0 元 GPU", "Colab T4 免費語音克隆\nWhisper 校對＋音量標準化", GREEN_DARK),
                ("輸出畫質規格", "1080p", "路線 B 僅耗 30 點數\nLanczos 銳化＋個資打碼", AMBER_DARK),
            ],
            "bullets": [
                ("痛點", "純文字 SOP 閱讀意願低，外包拍攝教學影片昂貴且系統改版即過時。"),
                ("解法", "結合 Google Flow 真人微電影過場、免費 T4 語音克隆與 FFmpeg 自動後期引擎。"),
                ("效益", "快速產出高完播率商業級企業教材，100% 兼顧趣味性與會計防呆嚴謹度。"),
            ],
        },
    ]

    for idx, proj in enumerate(projects, start=4):
        sl = prs.slides.add_slide(blank)
        set_slide_bg(sl, SLATE_BG)
        add_header_bar(sl, proj["title"], proj["subtitle"], proj["badge"])

        # Left Zone (width ~8.15"): 3 KPI Cards on top + Concise Callout Box on bottom
        kpi_w = Inches(2.58)
        kpi_h = Inches(2.15)
        kpi_gap = Inches(0.18)
        left_x = Inches(0.55)
        for k_i, (k_lbl, k_val, k_sub, k_clr) in enumerate(proj["kpis"]):
            add_kpi_card(sl, left_x + k_i * (kpi_w + kpi_gap), Inches(1.40), kpi_w, kpi_h,
                         k_lbl, k_val, k_sub, k_clr, val_size=26)

        add_callout_box(
            sl, left_x, Inches(3.78), Inches(8.10), Inches(3.05),
            "核心痛點 × 解決方案 × 落地效益",
            proj["bullets"],
            accent_color=NAVY_DARK,
            body_size=14,
            space_after=14
        )

        # Right Zone: Framed Illustration Card
        img_card = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.92), Inches(1.40), Inches(3.86), Inches(5.43))
        img_card.adjustments[0] = 0.04
        img_card.fill.solid()
        img_card.fill.fore_color.rgb = WHITE
        img_card.line.color.rgb = BORDER_GRAY
        img_card.line.width = Pt(0.75)
        add_shadow(img_card)

        # Subtle header inside image card
        add_textbox(sl, Inches(9.10), Inches(1.56), Inches(3.50), Inches(0.32),
                    f"系統架構示意圖  |  Project {proj['num']}", font_size=10.5, bold=True,
                    color=TEXT_MUTED, align=PP_ALIGN.CENTER)

        img_path = os.path.join(IMG_DIR, proj["img"])
        if os.path.exists(img_path):
            # Fit illustration vertically centered inside card
            sl.shapes.add_picture(img_path, Inches(9.08), Inches(2.45), width=Inches(3.54))

        add_footer(sl, idx)

    # ============================================================
    # SLIDE 12: Executive Summary & Next-Phase Roadmap (Reference Slide 4 Style)
    # ============================================================
    s12 = prs.slides.add_slide(blank)
    set_slide_bg(s12, SLATE_BG)
    add_header_bar(s12, "量化總結與下一階段擴展藍圖",
                   "以「可量化、低成本、高防呆」為核心，持續擴大智慧工廠數位轉型覆蓋率",
                   "Thank You · Q&A")

    # Left Column Card: Quantified Achievements
    left_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.55), Inches(1.42), Inches(5.95), Inches(5.40))
    left_card.adjustments[0] = 0.03
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = WHITE
    left_card.line.color.rgb = BORDER_GRAY
    add_shadow(left_card)

    l_hdr = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(1.42), Inches(5.95), Inches(0.56))
    l_hdr.fill.solid()
    l_hdr.fill.fore_color.rgb = NAVY_DARK
    l_hdr.line.fill.background()
    add_textbox(s12, Inches(0.78), Inches(1.52), Inches(5.5), Inches(0.36),
                "本階段核心量化實績（已驗證落地）", font_size=14.5, bold=True, color=WHITE)

    summary_items = [
        ("8 大系統正式上線", "涵蓋品管、出貨、檢點、倉儲、報表、產銷、活動與影音。", BLUE_ACCENT),
        ("每月預估省約 145 小時", "六大日常作業系統合計，相當於每月釋放近 1 名正職人力。", GREEN_DARK),
        ("50 人高併發 0.37s～0.47s", "實測 100% 零失敗、零覆蓋、零撞號，穩定度達企業級標準。", AMBER_DARK),
        ("全現場防呆 100% 覆蓋", "5 重 OCR 攔截、跨倉誤匯鎖定、報表 1 秒還原保護。", RED_DARK),
    ]
    for i, (m_title, m_desc, clr) in enumerate(summary_items):
        y = Inches(2.20) + i * Inches(1.12)
        dot = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.82), y + Inches(0.05), Inches(0.10), Inches(0.78))
        dot.fill.solid()
        dot.fill.fore_color.rgb = clr
        dot.line.fill.background()
        add_textbox(s12, Inches(1.05), y, Inches(5.2), Inches(0.36), m_title, font_size=15, bold=True, color=clr)
        add_textbox(s12, Inches(1.05), y + Inches(0.38), Inches(5.2), Inches(0.52), m_desc, font_size=12, color=TEXT_DARK)

    # Right Column Card: Next Roadmap
    right_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.83), Inches(1.42), Inches(5.95), Inches(5.40))
    right_card.adjustments[0] = 0.03
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = WHITE
    right_card.line.color.rgb = BORDER_GRAY
    add_shadow(right_card)

    r_hdr = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.83), Inches(1.42), Inches(5.95), Inches(0.56))
    r_hdr.fill.solid()
    r_hdr.fill.fore_color.rgb = BLUE_ACCENT
    r_hdr.line.fill.background()
    add_textbox(s12, Inches(7.06), Inches(1.52), Inches(5.5), Inches(0.36),
                "下一階段推進藍圖（2027 擴展目標）", font_size=14.5, bold=True, color=WHITE)

    roadmap_items = [
        ("Step 1｜全廠無紙化檢點推廣", "複用 SOP/WI 引擎，擴大至全廠設備巡檢與環安衛表單。"),
        ("Step 2｜AI 視覺防呆與主動預警", "導入動態 Gemini 模型與多金鑰備援，串聯 Teams 即時通報。"),
        ("Step 3｜SOP 微電影教材規模化", "以 sop-cinema-video 將各課標準轉化為微電影數位課程。"),
        ("Step 4｜單一雲端大廳統一治理", "透過 google-agent.pages.dev 統一入口，實現零門檻推廣。"),
    ]
    for i, (r_title, r_desc) in enumerate(roadmap_items):
        y = Inches(2.20) + i * Inches(1.12)
        sub_box = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.08), y, Inches(5.45), Inches(0.92))
        sub_box.adjustments[0] = 0.08
        sub_box.fill.solid()
        sub_box.fill.fore_color.rgb = ROW_ALT
        sub_box.line.color.rgb = BORDER_GRAY
        add_textbox(s12, Inches(7.24), y + Inches(0.08), Inches(5.15), Inches(0.34),
                    r_title, font_size=13.5, bold=True, color=NAVY_DARK)
        add_textbox(s12, Inches(7.24), y + Inches(0.42), Inches(5.15), Inches(0.45),
                    r_desc, font_size=11.5, color=TEXT_DARK)

    add_footer(s12, 12)

    prs.save(OUT_PPTX)
    print(f"SAVED: {OUT_PPTX}")
    print(f"SLIDES: {len(prs.slides)}, SIZE: {os.path.getsize(OUT_PPTX)/1024/1024:.2f} MB")


if __name__ == "__main__":
    build_presentation()
