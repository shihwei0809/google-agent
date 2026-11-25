"""
資材辦公室 系統櫃設計圖（更新位置圖）— 100% 原生向量可編輯 PowerPoint (.pptx) 產生器
完全比照模版繪製，所有牆面、櫃體、門片、編號與尺寸文字皆為 PPT 原生可編輯物件（非圖片）。
"""
import os
import sys

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
except ImportError:
    print("[錯誤] 缺少 python-pptx，請執行：pip install python-pptx")
    sys.exit(1)

NAVY = RGBColor(0x1B, 0x49, 0x65)
SLATE_BG = RGBColor(0xF4, 0xF7, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1E, 0x29, 0x3B)
MUTED = RGBColor(0x47, 0x55, 0x69)
BORDER = RGBColor(0xCB, 0xD5, 0xE1)
RED = RGBColor(0xDC, 0x26, 0x26)
WOOD = RGBColor(0xC8, 0xA9, 0x7E)
WOOD_DARK = RGBColor(0x9E, 0x7B, 0x4F)
DOOR_W = RGBColor(0xFA, 0xF8, 0xF5)
HANDLE = RGBColor(0x8B, 0x5E, 0x34)
BLUE_LIGHT = RGBColor(0xEF, 0xF6, 0xFF)
BLUE_BORDER = RGBColor(0xBF, 0xDB, 0xFE)
FONT = "Microsoft JhengHei"


def add_rect(slide, x, y, w, h, fill=None, line_color=None, line_pt=1.0, rounded=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        sh.adjustments[0] = 0.04
    if fill:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    else:
        sh.fill.background()
    if line_color:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(line_pt)
    else:
        sh.line.fill.background()
    return sh


def add_text(slide, text, x, y, w, h, size=10, bold=False, color=DARK, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Pt(2)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return tb


def add_badge(slide, num, x, y, size=0.26):
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(size), Inches(size))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RED
    sh.line.color.rgb = WHITE
    sh.line.width = Pt(1)
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(num)
    r.font.name = FONT
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = WHITE


def draw_cabinet_elevation(slide, x, y, w, h, cols, rows, open_cols=None):
    open_cols = open_cols or []
    add_rect(slide, x, y, w, h, fill=WOOD, line_color=WOOD_DARK, line_pt=1.0)
    pad = 0.05
    cw = (w - pad * 2) / cols
    rh = (h - pad * 2) / rows
    for r in range(rows):
        for c in range(cols):
            cx = x + pad + c * cw + 0.015
            cy = y + pad + r * rh + 0.015
            is_open = (c in open_cols) and (r == rows - 1)
            add_rect(
                slide, cx, cy, cw - 0.03, rh - 0.03,
                fill=RGBColor(0xB5, 0x91, 0x62) if is_open else DOOR_W,
                line_color=WOOD_DARK, line_pt=0.75
            )
            if not is_open:
                add_rect(slide, cx + cw * 0.44, cy + rh * 0.40, 0.035, min(0.16, rh * 0.28), fill=HANDLE)
            else:
                for s in (1, 2):
                    add_rect(slide, cx + 0.01, cy + (rh - 0.03) * (s / 3), cw - 0.05, 0.025, fill=WOOD_DARK)


def build_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ==================== Slide 1: 系統櫃設計圖（更新位置圖） ====================
    s1 = prs.slides.add_slide(blank)
    add_rect(s1, 0, 0, 13.333, 7.5, fill=SLATE_BG)

    # Header
    add_rect(s1, 0, 0, 13.333, 0.65, fill=NAVY)
    add_text(s1, "系統櫃設計圖（更新位置圖）", 0.3, 0.07, 7.5, 0.5, size=22, bold=True, color=WHITE)
    add_text(s1, "單位：公分（尺寸順序：長×寬×高）", 8.5, 0.12, 4.55, 0.42, size=12, bold=True, color=RGBColor(0xE2, 0xE8, 0xF0), align=PP_ALIGN.RIGHT)

    # Left Card
    add_rect(s1, 0.2, 0.8, 4.95, 6.45, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_rect(s1, 0.36, 0.96, 0.07, 0.26, fill=NAVY)
    add_text(s1, "平面配置圖（俯視圖）", 0.48, 0.91, 3.5, 0.34, size=14, bold=True, color=NAVY)
    add_text(s1, "依現場尺寸繪製，數字為主要牆面尺寸，彩色區塊代表櫃體位置。", 0.36, 1.24, 4.65, 0.24, size=8.5, color=MUTED)

    # Knife-handle floor plan (1 cm = 0.00405 in)
    sc = 0.00405
    ox, oy = 0.72, 1.78
    add_rect(s1, ox, oy, 585 * sc, 270 * sc, fill=RGBColor(0xEF, 0xF6, 0xFF), line_color=RGBColor(0x93, 0xC5, 0xFD), line_pt=0.5)
    add_rect(s1, ox, oy + 270 * sc, 585 * sc, 500 * sc, fill=RGBColor(0xFE, 0xFC, 0xE8), line_color=RGBColor(0xE2, 0xE8, 0xF0), line_pt=0.5)
    add_rect(s1, ox, oy + 770 * sc, 345 * sc, 525 * sc, fill=RGBColor(0xF0, 0xFD, 0xF4), line_color=RGBColor(0xBB, 0xF7, 0xD0), line_pt=0.5)

    # Outer walls (thick dark rects)
    wt = 0.032
    add_rect(s1, ox, oy, 585 * sc, wt, fill=DARK)
    add_rect(s1, ox, oy, wt, 1295 * sc, fill=DARK)
    add_rect(s1, ox + 585 * sc - wt, oy, wt, 770 * sc, fill=DARK)
    add_rect(s1, ox + 345 * sc, oy + 770 * sc - wt, 240 * sc, wt, fill=DARK)
    add_rect(s1, ox + 345 * sc - wt, oy + 770 * sc - wt, wt, 525 * sc + wt, fill=DARK)
    add_rect(s1, ox, oy + 1295 * sc - wt, 345 * sc, wt, fill=DARK)

    # Cabinets on floor plan (all individually editable vector shapes!)
    cabs = [
        ("门字櫃", 10, 10, 565, 50, RGBColor(0x7D, 0xD3, 0xFC)),
        ("新增單門櫃", 10, 275, 45, 70, RGBColor(0x38, 0xBD, 0xF8)),
        ("六門高櫃", 520, 280, 55, 310, RGBColor(0x81, 0x8C, 0xF8)),
        ("家電收納櫃", 375, 700, 200, 60, RGBColor(0xFB, 0xBF, 0x24)),
        ("六門三層矮櫃", 305, 810, 32, 330, RGBColor(0x4A, 0xDE, 0x80)),
    ]
    for name, cx, cy, cw, cd, col in cabs:
        add_rect(s1, ox + cx * sc, oy + cy * sc, cw * sc, cd * sc, fill=col, line_color=DARK, line_pt=0.75)

    # Pillars & Doors
    for px, py, pw, pd in [(65, 270, 60, 60), (285, 700, 60, 70)]:
        add_rect(s1, ox + px * sc, oy + py * sc, pw * sc, pd * sc, fill=RGBColor(0x47, 0x55, 0x69), line_color=DARK, line_pt=0.75)
        add_text(s1, "柱", ox + px * sc, oy + py * sc, pw * sc, pd * sc, size=7.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_rect(s1, ox + 245 * sc, oy + 1285 * sc, 90 * sc, 0.08, fill=RGBColor(0x94, 0xA3, 0xB8), line_color=DARK, line_pt=0.75)
    add_text(s1, "門", ox + 245 * sc, oy + 1282 * sc, 90 * sc, 0.14, size=7, bold=True, color=DARK, align=PP_ALIGN.CENTER)

    # Badges ①-⑤
    add_badge(s1, 1, ox + 1.05, oy + 0.30, 0.22)
    add_badge(s1, 2, ox + 1.85, oy + 1.65, 0.22)
    add_badge(s1, 3, ox + 1.72, oy + 2.50, 0.22)
    add_badge(s1, 4, ox + 0.92, oy + 3.95, 0.22)
    add_badge(s1, 5, ox + 0.05, oy + 1.15, 0.22)

    # Dimensions
    add_text(s1, "585 (上方牆面)", ox, oy - 0.24, 585 * sc, 0.2, size=8.5, bold=True, align=PP_ALIGN.CENTER)
    add_text(s1, "1300", ox - 0.48, oy + 2.45, 0.44, 0.22, size=8.5, bold=True, align=PP_ALIGN.RIGHT)
    add_text(s1, "500", ox + 585 * sc + 0.04, oy + 1.90, 0.40, 0.2, size=8, bold=True)
    add_text(s1, "525", ox + 345 * sc + 0.06, oy + 4.10, 0.40, 0.2, size=8, bold=True)
    add_text(s1, "345 (下方牆面)", ox, oy + 1295 * sc + 0.05, 345 * sc, 0.2, size=8, bold=True, align=PP_ALIGN.CENTER)
    add_text(s1, "240", ox + 345 * sc, oy + 1295 * sc + 0.05, 240 * sc, 0.2, size=8, bold=True, align=PP_ALIGN.CENTER)

    # Legend Box
    lx, ly, lw = 3.45, 1.78, 1.56
    add_rect(s1, lx, ly, lw, 2.85, fill=RGBColor(0xF8, 0xFA, 0xFC), line_color=BORDER, line_pt=0.75, rounded=True)
    add_rect(s1, lx, ly, lw, 0.30, fill=NAVY)
    add_text(s1, "平面圖例與櫃體對照", lx, ly, lw, 0.30, size=8.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    legend = "□  出入口（門 ×2）\n■  結構柱（柱子 ×2）\n①  门字型系統櫃\n②  六門高櫃（右側）\n③  家電收納櫃（內凹）\n④  六門三層矮櫃\n⑤  新增單門櫃（柱左）"
    add_text(s1, legend, lx + 0.08, ly + 0.38, lw - 0.14, 2.38, size=8.5, color=DARK, valign=MSO_ANCHOR.TOP)

    # Card ①: 门字型系統櫃
    add_rect(s1, 5.3, 0.8, 4.55, 3.15, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_badge(s1, 1, 5.45, 0.92, 0.26)
    add_text(s1, "门字型系統櫃（原設計）", 5.76, 0.88, 3.8, 0.32, size=13, bold=True, color=NAVY)
    add_text(s1, "沿上方 585 牆面，左右兩端轉角組合", 5.45, 1.20, 4.2, 0.22, size=8.5, color=MUTED)
    for t, px, pw in [
        ("左側櫃體\n下櫃：100×65×180\n上櫃：100×65×100", 5.45, 1.38),
        ("中間櫃體\n下櫃：400×45×210\n上櫃：400×45×75", 6.90, 1.48),
        ("右側櫃體\n215×65×285", 8.45, 1.25),
    ]:
        add_rect(s1, px, 1.46, pw, 0.62, fill=BLUE_LIGHT, line_color=BLUE_BORDER, line_pt=0.75, rounded=True)
        add_text(s1, t, px + 0.03, 1.48, pw - 0.06, 0.58, size=7.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    draw_cabinet_elevation(s1, 5.45, 2.18, 4.25, 1.62, 7, 2, open_cols=[1, 2, 3, 4])

    # Card ②: 六門高櫃
    add_rect(s1, 10.0, 0.8, 3.13, 3.15, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_badge(s1, 2, 10.15, 0.92, 0.26)
    add_text(s1, "六門高櫃（原設計）", 10.46, 0.88, 2.5, 0.32, size=13, bold=True, color=NAVY)
    add_text(s1, "沿右側直牆 310 公分段", 10.15, 1.20, 2.8, 0.22, size=8.5, color=MUTED)
    draw_cabinet_elevation(s1, 10.22, 1.50, 2.68, 1.82, 6, 2)
    add_text(s1, "310×65×280（下櫃 180＋上櫃 100）\n上下各 6 門・下櫃 3 層・上櫃 2 層", 10.08, 3.38, 2.97, 0.50, size=8.5, bold=True, align=PP_ALIGN.CENTER)

    # Card ③: 家電收納櫃
    add_rect(s1, 5.3, 4.1, 2.52, 3.15, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_badge(s1, 3, 5.44, 4.22, 0.24)
    add_text(s1, "家電收納櫃（原設計）", 5.72, 4.18, 2.0, 0.32, size=11.5, bold=True, color=NAVY)
    add_text(s1, "沿內凹右側 210 公分橫牆", 5.44, 4.48, 2.2, 0.22, size=8, color=MUTED)
    draw_cabinet_elevation(s1, 5.48, 4.82, 2.16, 1.85, 4, 2, open_cols=[0, 1, 2])
    add_text(s1, "下櫃 210×65×180 ｜ 上櫃 200×65×100", 5.34, 6.76, 2.44, 0.40, size=8, bold=True, align=PP_ALIGN.CENTER)

    # Card ④: 六門三層矮櫃
    add_rect(s1, 7.97, 4.1, 2.52, 3.15, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_badge(s1, 4, 8.11, 4.22, 0.24)
    add_text(s1, "六門三層矮櫃（原設計）", 8.39, 4.18, 2.05, 0.32, size=11.5, bold=True, color=NAVY)
    add_text(s1, "沿內側 470 公分直牆配置", 8.11, 4.48, 2.2, 0.22, size=8, color=MUTED)
    draw_cabinet_elevation(s1, 8.15, 5.35, 2.16, 1.15, 6, 1)
    add_text(s1, "330×30×110（六門・內部三層）", 8.02, 6.76, 2.42, 0.40, size=8.5, bold=True, align=PP_ALIGN.CENTER)

    # Card ⑤: 新增單門櫃
    add_rect(s1, 10.64, 4.1, 2.49, 3.15, fill=WHITE, line_color=BORDER, line_pt=1.0, rounded=True)
    add_badge(s1, 5, 10.78, 4.22, 0.24)
    add_text(s1, "新增單門櫃（柱左）", 11.06, 4.18, 2.0, 0.32, size=11.5, bold=True, color=NAVY)
    add_text(s1, "位於柱子左側，單門上下組", 10.78, 4.48, 2.2, 0.22, size=8, color=MUTED)
    draw_cabinet_elevation(s1, 10.80, 4.82, 0.66, 2.05, 1, 2)
    draw_cabinet_elevation(s1, 11.56, 4.82, 0.66, 2.05, 1, 2, open_cols=[0])
    add_text(s1, "上櫃\n70×45×100\n單門・2層\n\n下櫃\n70×45×180\n單門・3層", 12.26, 4.82, 0.84, 2.15, size=7.5, bold=True, color=NAVY)

    # ==================== Slide 2: 面積與櫃體規格明細表 ====================
    s2 = prs.slides.add_slide(blank)
    add_rect(s2, 0, 0, 13.333, 7.5, fill=SLATE_BG)
    add_rect(s2, 0, 0, 13.333, 0.65, fill=NAVY)
    add_text(s2, "資材辦公室 2027 面積統計與櫃體規格表（可直接編輯）", 0.3, 0.07, 10.5, 0.5, size=20, bold=True, color=WHITE)

    rows_data = [
        ["編號", "櫃體 / 區域名稱", "尺寸規格（長×寬×高，公分）", "配置位置與備註"],
        ["①", "门字型系統櫃", "左：下100×65×180 / 上100×65×100；中：下400×45×210 / 上400×45×75；右：215×65×285", "沿上方 585 牆面（原設計）"],
        ["②", "六門高櫃", "310 × 65 × 280（下櫃 180＋上櫃 100）", "沿右側直牆，上下各 6 門"],
        ["③", "家電收納櫃", "下櫃 210 × 65 × 180 ｜ 上櫃 200 × 65 × 100", "主要辦公區右下角內凹橫牆"],
        ["④", "六門三層矮櫃", "330 × 30 × 110", "辦公延伸區右側牆面，內部三層"],
        ["⑤", "新增單門櫃", "上櫃 70 × 45 × 100 ｜ 下櫃 70 × 45 × 180", "新增，位於左上結構柱左側"],
        ["區1", "儲藏室＋置物櫃區", "585 × 270（約 4.78 坪）", "上方藍色區域，與主區間不設門"],
        ["區2", "主要辦公區", "585 × 500（約 8.85 坪）", "7 人辦公桌、印表機、飲水機、盆栽"],
        ["區3", "辦公延伸區", "345 × 525（約 5.48 坪）", "10 人辦公桌、6 人辦公桌、盆栽（純辦公合計 14.33 坪／全區 19.11 坪）"],
    ]
    tbl_shape = s2.shapes.add_table(len(rows_data), 4, Inches(0.4), Inches(0.95), Inches(12.53), Inches(5.8))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(0.9)
    tbl.columns[1].width = Inches(2.4)
    tbl.columns[2].width = Inches(5.3)
    tbl.columns[3].width = Inches(3.93)

    for r_idx, row in enumerate(rows_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = NAVY
            else:
                cell.fill.fore_color.rgb = RGBColor(0xF8, 0xFA, 0xFC) if r_idx % 2 == 0 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx == 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = val
            run.font.name = FONT
            run.font.size = Pt(11 if r_idx == 0 else 10)
            run.font.bold = (r_idx == 0 or c_idx <= 1)
            run.font.color.rgb = WHITE if r_idx == 0 else DARK

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "資材辦公室_系統櫃設計圖_可編輯版.pptx")
    prs.save(out_path)
    print(f"[完成] 已產出 100% 原生向量可編輯 PPTX：{out_path}")


if __name__ == "__main__":
    build_pptx()
