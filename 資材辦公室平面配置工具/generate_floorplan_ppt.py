"""
資材辦公室 室內平面配置圖（俯視圖）— 100% 原生向量可編輯 PowerPoint (.pptx)
完全比照簡報模版重繪，零圖片，所有牆面、桌椅、櫃體、柱子、門、尺寸箭頭、標註線與表格皆可在 PPT 個別調整。
"""
import os
import sys

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.oxml.ns import qn
    from pptx.oxml import parse_xml
except ImportError:
    print("[錯誤] 缺少 python-pptx，請執行：pip install python-pptx")
    sys.exit(1)

# Palette matching the template
NAVY = RGBColor(0x1D, 0x4B, 0x83)
BLUE_HDR = RGBColor(0x28, 0x67, 0xAB)
BLUE_LIGHT_BG = RGBColor(0xDE, 0xE9, 0xF7)
CARD_BORDER = RGBColor(0xA6, 0xC2, 0xDF)
CALLOUT_BORDER = RGBColor(0x5B, 0x9B, 0xD5)
WALL_DARK = RGBColor(0x3F, 0x46, 0x4F)
STORAGE_BLUE = RGBColor(0xD2, 0xE4, 0xF5)
MAIN_GREEN = RGBColor(0xCB, 0xE5, 0xB4)
EXT_GREEN = RGBColor(0xE2, 0xF0, 0xD3)
DESK_FILL = RGBColor(0xE5, 0xC9, 0xA3)
DESK_BORDER = RGBColor(0xB5, 0x94, 0x6B)
CHAIR_GRAY = RGBColor(0x94, 0x9B, 0xA6)
CAB_CREAM = RGBColor(0xF7, 0xF3, 0xEA)
CAB_BORDER = RGBColor(0xB8, 0xAE, 0x9C)
PILLAR_GRAY = RGBColor(0x5E, 0x67, 0x73)
DOOR_GRAY = RGBColor(0xB4, 0xBA, 0xC4)
TEXT_DARK = RGBColor(0x2B, 0x33, 0x3E)
TEXT_MUTED = RGBColor(0x47, 0x55, 0x69)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Microsoft JhengHei"


def add_rect(slide, x, y, w, h, fill=None, line_color=None, line_pt=1.0, rounded=False, radius=0.08):
    st = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(st, Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        sh.adjustments[0] = radius
    if fill is not None:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    else:
        sh.fill.background()
    if line_color is not None:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(line_pt)
    else:
        sh.line.fill.background()
    return sh


def add_text(slide, text, x, y, w, h, size=11, bold=False, color=TEXT_DARK, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, underline=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Pt(2)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.underline = underline
    r.font.color.rgb = color
    return tb


def add_line(slide, x1, y1, x2, y2, color=WALL_DARK, pt=1.0, dashed=False, arrows=False):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(pt)
    ln = conn.line._get_or_add_ln()
    if dashed:
        ln.append(parse_xml('<a:prstDash xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" val="dash"/>'))
    if arrows:
        ln.append(parse_xml('<a:headEnd xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="triangle" w="med" len="med"/>'))
        ln.append(parse_xml('<a:tailEnd xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="triangle" w="med" len="med"/>'))
    return conn


def add_dot(slide, cx, cy, r=0.038, color=WALL_DARK):
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r), Inches(r * 2), Inches(r * 2))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def build_floorplan_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])

    # White slide background
    add_rect(s, 0, 0, 13.333, 7.5, fill=WHITE)

    # ==================== 1. Top Diagonal Banner ====================
    add_rect(s, 0.2, 0.16, 12.93, 0.56, fill=BLUE_LIGHT_BG, rounded=True, radius=0.06)
    add_rect(s, 0.2, 0.16, 8.45, 0.56, fill=NAVY, rounded=True, radius=0.06)
    add_text(s, "室內平面配置圖（俯視圖）", 0.42, 0.17, 7.5, 0.54, size=22, bold=True, color=WHITE)

    # ==================== 2. Left Column: 辦公室人數 & 空間說明 ====================
    # 辦公室人數
    add_rect(s, 0.2, 0.98, 2.45, 0.36, fill=BLUE_HDR, rounded=True, radius=0.18)
    add_text(s, "辦公室人數", 0.34, 0.98, 2.2, 0.36, size=12, bold=True, color=WHITE)
    add_rect(s, 0.2, 1.42, 2.58, 0.72, fill=WHITE, line_color=CARD_BORDER, line_pt=1.0, rounded=True, radius=0.12)
    add_text(s, "合計：", 0.40, 1.54, 0.85, 0.48, size=14, color=TEXT_DARK)
    add_text(s, "34", 1.32, 1.48, 0.75, 0.56, size=24, bold=True, color=NAVY, align=PP_ALIGN.CENTER, underline=True)
    add_text(s, "人", 2.08, 1.54, 0.45, 0.48, size=14, color=TEXT_DARK)

    # 空間說明
    add_rect(s, 0.2, 2.38, 1.50, 0.34, fill=BLUE_HDR, rounded=True, radius=0.18)
    add_text(s, "空間說明", 0.34, 2.38, 1.3, 0.34, size=11.5, bold=True, color=WHITE)
    add_rect(s, 0.2, 2.78, 3.20, 1.32, fill=WHITE, line_color=CARD_BORDER, line_pt=1.0, rounded=True, radius=0.08)
    notes = "●  主要辦公／作業區（綠色區域）\n●  儲藏室＋置物櫃＋文件櫃（藍色區域）\n●  兩處出入口（門），2 處柱子"
    add_text(s, notes, 0.34, 2.86, 2.95, 1.18, size=10.5, color=TEXT_DARK, valign=MSO_ANCHOR.MIDDLE)

    # ==================== 3. Center Floor Plan (100% Native Editable Shapes) ====================
    # Coordinate mapping: origin (ox, oy), scale sc (1 cm = 0.00456 in)
    # Width 585 -> 2.67 in? Wait, in template it's wider (~4.9 in wide, 5.95 in tall -> X scale ~0.00845, Y scale ~0.00456 for clear readability!)
    ox, oy = 3.92, 1.02
    sx = 0.00842   # 585 cm -> 4.926 in
    sy = 0.00455   # 1300 cm -> 5.915 in (270->1.23, 500->2.275, 525->2.39)

    w_top = 585 * sx
    w_ext = 345 * sx
    h_sto = 140 * sy   # visual proportion matching template (~0.64 in)
    h_main = 490 * sy  # ~2.23 in
    h_ext = 665 * sy   # ~3.02 in
    h_tot = h_sto + h_main + h_ext

    # Floor zones
    add_rect(s, ox, oy, w_top, h_sto, fill=STORAGE_BLUE)
    add_rect(s, ox, oy + h_sto, w_top, h_main, fill=MAIN_GREEN)
    add_rect(s, ox, oy + h_sto + h_main, w_ext, h_ext, fill=EXT_GREEN)

    # Storage pill label
    add_rect(s, ox + 1.52, oy + 0.17, 1.88, 0.30, fill=WHITE, line_color=CALLOUT_BORDER, line_pt=1.0, rounded=True, radius=0.45)
    add_text(s, "儲藏室＋置物櫃＋文件櫃", ox + 1.52, oy + 0.17, 1.88, 0.30, size=9.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # Thick dark exterior walls (individually editable!)
    wt = 0.095
    add_rect(s, ox - wt / 2, oy - wt / 2, w_top + wt, wt, fill=WALL_DARK)                         # Top
    add_rect(s, ox - wt / 2, oy - wt / 2, wt, h_tot + wt, fill=WALL_DARK)                         # Left
    add_rect(s, ox + w_top - wt / 2, oy - wt / 2, wt, h_sto + h_main + wt, fill=WALL_DARK)        # Upper Right
    add_rect(s, ox + w_ext - wt / 2, oy + h_sto + h_main - wt / 2, w_top - w_ext + wt, wt, fill=WALL_DARK)  # Step Wall
    add_rect(s, ox + w_ext - wt / 2, oy + h_sto + h_main - wt / 2, wt, h_ext + wt, fill=WALL_DARK)          # Lower Right
    add_rect(s, ox - wt / 2, oy + h_tot - wt / 2, w_ext + wt, wt, fill=WALL_DARK)                 # Bottom
    # Partition wall between storage and main (right side near door)
    add_rect(s, ox, oy + h_sto - 0.03, w_top, 0.06, fill=WALL_DARK)

    # ---- Cabinets (cream blocks, all editable!) ----
    # Left wall of main area (3 vertical blocks)
    for i in range(3):
        add_rect(s, ox + 0.06, oy + h_sto + 0.06 + i * 0.45, 0.32, 0.43, fill=CAB_CREAM, line_color=CAB_BORDER, line_pt=0.75)
    # Top wall of main area (4 horizontal blocks)
    for i in range(4):
        add_rect(s, ox + 1.38 + i * 0.64, oy + h_sto + 0.06, 0.62, 0.33, fill=CAB_CREAM, line_color=CAB_BORDER, line_pt=0.75)
    # Right wall of main area (4 vertical blocks)
    for i in range(4):
        add_rect(s, ox + w_top - 0.40, oy + h_sto + 0.25 + i * 0.39, 0.34, 0.37, fill=CAB_CREAM, line_color=CAB_BORDER, line_pt=0.75)
    # Bottom-right corner of main area (2 horizontal blocks)
    for i in range(2):
        add_rect(s, ox + w_top - 1.38 + i * 0.50, oy + h_sto + h_main - 0.40, 0.48, 0.34, fill=CAB_CREAM, line_color=CAB_BORDER, line_pt=0.75)
    # Right wall of extension area (4 vertical blocks)
    for i in range(4):
        add_rect(s, ox + w_ext - 0.36, oy + h_sto + h_main + 0.36 + i * 0.52, 0.29, 0.50, fill=CAB_CREAM, line_color=CAB_BORDER, line_pt=0.75)

    # ---- Printer & Water Dispenser ----
    add_rect(s, ox + 0.52, oy + h_sto + 0.08, 0.38, 0.28, fill=RGBColor(0xE2, 0xE8, 0xF0), line_color=PILLAR_GRAY, line_pt=0.75, rounded=True, radius=0.15)
    add_rect(s, ox + 0.60, oy + h_sto + 0.14, 0.22, 0.06, fill=PILLAR_GRAY)
    add_rect(s, ox + 0.08, oy + h_sto + h_main - 0.36, 0.30, 0.30, fill=WHITE, line_color=CALLOUT_BORDER, line_pt=0.75, rounded=True, radius=0.15)
    add_dot(s, ox + 0.23, oy + h_sto + h_main - 0.24, r=0.07, color=CALLOUT_BORDER)
    add_text(s, "飲水機", ox + 0.02, oy + h_sto + h_main - 0.06, 0.44, 0.18, size=7.5, color=TEXT_MUTED, align=PP_ALIGN.CENTER)

    # ---- 7-Person Desk + 7 Chairs ----
    dx7, dy7, dw7, dh7 = ox + 1.24, oy + h_sto + 0.74, 2.12, 0.60
    add_rect(s, dx7, dy7, dw7, dh7, fill=DESK_FILL, line_color=DESK_BORDER, line_pt=1.0, rounded=True, radius=0.08)
    add_text(s, "7人", dx7, dy7, dw7, dh7, size=13, bold=True, color=RGBColor(0x6B, 0x4E, 0x2E), align=PP_ALIGN.CENTER)
    # 3 top chairs, 3 bottom chairs, 1 left chair
    for i in range(3):
        cx = dx7 + 0.22 + i * 0.72
        add_rect(s, cx, dy7 - 0.23, 0.26, 0.18, fill=CHAIR_GRAY, rounded=True, radius=0.25)
        add_rect(s, cx, dy7 + dh7 + 0.05, 0.26, 0.18, fill=CHAIR_GRAY, rounded=True, radius=0.25)
    add_rect(s, dx7 - 0.22, dy7 + 0.17, 0.17, 0.26, fill=CHAIR_GRAY, rounded=True, radius=0.25)

    # ---- 10-Person Desk + 6 Chairs ----
    dx10, dy10, dw10, dh10 = ox + 1.02, oy + h_sto + h_main + 0.06, 0.58, 1.85
    add_rect(s, dx10, dy10, dw10, dh10, fill=DESK_FILL, line_color=DESK_BORDER, line_pt=1.0, rounded=True, radius=0.08)
    add_text(s, "10人", dx10, dy10, dw10, dh10, size=12, bold=True, color=RGBColor(0x6B, 0x4E, 0x2E), align=PP_ALIGN.CENTER)
    for i in range(3):
        cy = dy10 + 0.16 + i * 0.63
        add_rect(s, dx10 - 0.22, cy, 0.17, 0.26, fill=CHAIR_GRAY, rounded=True, radius=0.25)
        add_rect(s, dx10 + dw10 + 0.05, cy, 0.17, 0.26, fill=CHAIR_GRAY, rounded=True, radius=0.25)

    # ---- 6-Person Desk + 4 Chairs ----
    dx6, dy6, dw6, dh6 = ox + 1.02, oy + h_sto + h_main + 2.10, 0.58, 0.80
    add_rect(s, dx6, dy6, dw6, dh6, fill=DESK_FILL, line_color=DESK_BORDER, line_pt=1.0, rounded=True, radius=0.08)
    add_text(s, "6人", dx6, dy6, dw6, dh6, size=12, bold=True, color=RGBColor(0x6B, 0x4E, 0x2E), align=PP_ALIGN.CENTER)
    for i in range(2):
        cy = dy6 + 0.08 + i * 0.42
        add_rect(s, dx6 - 0.22, cy, 0.17, 0.24, fill=CHAIR_GRAY, rounded=True, radius=0.25)
        add_rect(s, dx6 + dw6 + 0.05, cy, 0.17, 0.24, fill=CHAIR_GRAY, rounded=True, radius=0.25)

    # ---- Pillars & Doors (on top layer) ----
    add_rect(s, ox + 0.98, oy + h_sto + 0.08, 0.32, 0.30, fill=PILLAR_GRAY)
    add_text(s, "柱", ox + 0.98, oy + h_sto + 0.08, 0.32, 0.30, size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_rect(s, ox + w_ext - 0.34, oy + h_sto + h_main - 0.28, 0.58, 0.56, fill=PILLAR_GRAY)
    add_text(s, "柱子", ox + w_ext - 0.34, oy + h_sto + h_main - 0.28, 0.58, 0.56, size=10.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # Doors
    add_rect(s, ox + w_top - 0.88, oy + h_sto - 0.12, 0.62, 0.24, fill=DOOR_GRAY, line_color=PILLAR_GRAY, line_pt=0.75)
    add_text(s, "門", ox + w_top - 0.88, oy + h_sto - 0.12, 0.62, 0.24, size=10, bold=True, color=TEXT_DARK, align=PP_ALIGN.CENTER)

    add_rect(s, ox + w_ext - 0.68, oy + h_tot - 0.12, 0.56, 0.24, fill=DOOR_GRAY, line_color=PILLAR_GRAY, line_pt=0.75)
    add_text(s, "門", ox + w_ext - 0.68, oy + h_tot - 0.12, 0.56, 0.24, size=10, bold=True, color=TEXT_DARK, align=PP_ALIGN.CENTER)

    # ---- 3 Area Callout Boxes with Leader Lines ----
    # 4.78 坪 (left-top)
    add_rect(s, 2.86, 1.02, 0.96, 0.60, fill=WHITE, line_color=CALLOUT_BORDER, line_pt=1.2, rounded=True, radius=0.14)
    add_text(s, "面積\n4.78 坪", 2.86, 1.02, 0.96, 0.60, size=10.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_line(s, 3.82, 1.32, ox + 0.55, 1.32, color=PILLAR_GRAY, pt=1.0)
    add_dot(s, ox + 0.55, 1.32)

    # 8.85 坪 (right-mid)
    add_rect(s, 7.36, 4.70, 1.02, 0.60, fill=WHITE, line_color=CALLOUT_BORDER, line_pt=1.2, rounded=True, radius=0.14)
    add_text(s, "面積\n8.85 坪", 7.36, 4.70, 1.02, 0.60, size=10.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_line(s, 7.47, 4.70, 7.47, oy + h_sto + 1.56, color=PILLAR_GRAY, pt=1.0)
    add_dot(s, 7.47, oy + h_sto + 1.56)

    # 5.48 坪 (left-bottom)
    add_rect(s, 2.06, 5.15, 1.02, 0.60, fill=WHITE, line_color=CALLOUT_BORDER, line_pt=1.2, rounded=True, radius=0.14)
    add_text(s, "面積\n5.48 坪", 2.06, 5.15, 1.02, 0.60, size=10.5, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_line(s, 3.08, 5.45, ox + 0.60, 5.45, color=PILLAR_GRAY, pt=1.0)
    add_dot(s, ox + 0.60, 5.45)

    # ---- Dimension Arrows (585, 270, 500, 525, 1300, 345, 240) ----
    # Top 585
    add_line(s, ox, oy - 0.16, ox + w_top, oy - 0.16, color=WALL_DARK, pt=1.0, arrows=True)
    add_rect(s, ox + w_top / 2 - 0.28, oy - 0.28, 0.56, 0.22, fill=WHITE)
    add_text(s, "585", ox + w_top / 2 - 0.28, oy - 0.28, 0.56, 0.22, size=10.5, bold=True, align=PP_ALIGN.CENTER)

    # Right inner: 270, 500, 525
    rx1 = ox + w_top + 0.24
    add_line(s, rx1, oy, rx1, oy + h_sto, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "270", rx1 + 0.06, oy + h_sto / 2 - 0.11, 0.45, 0.22, size=10, bold=True)

    add_line(s, rx1, oy + h_sto, rx1, oy + h_sto + h_main, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "500", rx1 + 0.06, oy + h_sto + h_main / 2 - 0.11, 0.45, 0.22, size=10, bold=True)

    add_line(s, rx1, oy + h_sto + h_main, rx1, oy + h_tot, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "525", rx1 + 0.06, oy + h_sto + h_main + h_ext / 2 - 0.11, 0.45, 0.22, size=10, bold=True)

    # Right outer: 1300
    rx2 = rx1 + 0.56
    add_line(s, rx2, oy, rx2, oy + h_tot, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "1300", rx2 + 0.05, oy + h_tot / 2 - 0.12, 0.55, 0.24, size=11, bold=True)

    # Dashed extension lines down to bottom dimension
    add_line(s, ox + w_ext, oy + h_tot, ox + w_ext, oy + h_tot + 0.26, color=RGBColor(0x94, 0xA3, 0xB8), pt=0.8, dashed=True)
    add_line(s, ox + w_top, oy + h_sto + h_main, ox + w_top, oy + h_tot + 0.26, color=RGBColor(0x94, 0xA3, 0xB8), pt=0.8, dashed=True)

    # Bottom 345 & 240
    by = oy + h_tot + 0.22
    add_line(s, ox, by, ox + w_ext, by, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "345", ox + w_ext / 2 - 0.26, by + 0.03, 0.52, 0.22, size=10.5, bold=True, align=PP_ALIGN.CENTER)

    add_line(s, ox + w_ext, by, ox + w_top, by, color=WALL_DARK, pt=1.0, arrows=True)
    add_text(s, "240", ox + w_ext + (w_top - w_ext) / 2 - 0.26, by + 0.03, 0.52, 0.22, size=10.5, bold=True, align=PP_ALIGN.CENTER)

    # ==================== 4. Right Column: 面積統計 & 圖例說明 ====================
    rx = 10.18
    rw = 2.95

    # 面積統計
    add_rect(s, rx, 0.98, rw, 0.36, fill=BLUE_HDR, rounded=True, radius=0.14)
    add_text(s, "面積統計", rx + 0.14, 0.98, 2.0, 0.36, size=12, bold=True, color=WHITE)
    add_rect(s, rx, 1.32, rw, 1.94, fill=WHITE, line_color=CARD_BORDER, line_pt=1.0)

    stat_rows = [
        (MAIN_GREEN, "主要辦公區", "8.85 坪"),
        (EXT_GREEN, "辦公延伸區", "5.48 坪"),
        (STORAGE_BLUE, "儲藏室＋置物櫃＋文件櫃", "4.78 坪"),
    ]
    for i, (col, lbl, val) in enumerate(stat_rows):
        ry = 1.32 + i * 0.39
        add_line(s, rx, ry + 0.39, rx + rw, ry + 0.39, color=CARD_BORDER, pt=0.6)
        add_rect(s, rx + 0.12, ry + 0.11, 0.22, 0.17, fill=col, line_color=TEXT_MUTED, line_pt=0.6)
        add_text(s, lbl, rx + 0.40, ry + 0.03, 1.75, 0.33, size=9.5, color=TEXT_DARK)
        add_text(s, val, rx + 2.12, ry + 0.03, 0.76, 0.33, size=10, color=TEXT_DARK, align=PP_ALIGN.RIGHT)
    add_line(s, rx + 2.12, 1.32, rx + 2.12, 2.49, color=CARD_BORDER, pt=0.6)

    # 面積合計
    add_text(s, "面積合計", rx + 0.45, 2.66, 1.05, 0.42, size=12, bold=True, color=TEXT_DARK)
    add_text(s, "14.3", rx + 2.06, 2.62, 0.58, 0.46, size=15, bold=True, color=NAVY, align=PP_ALIGN.RIGHT, underline=True)
    add_text(s, "坪", rx + 2.64, 2.66, 0.28, 0.42, size=11, color=TEXT_DARK)

    # 圖例說明
    add_rect(s, rx, 3.52, rw, 0.36, fill=BLUE_HDR, rounded=True, radius=0.14)
    add_text(s, "圖例說明", rx + 0.14, 3.52, 2.0, 0.36, size=12, bold=True, color=WHITE)
    add_rect(s, rx, 3.86, rw, 2.14, fill=WHITE, line_color=CARD_BORDER, line_pt=1.0)

    legends = [
        ("wall", "實牆／隔間"),
        ("green", "辦公／作業空間"),
        ("blue", "儲藏／收納空間"),
        ("door", "門（出入口）"),
        ("pillar", "柱子（結構柱）"),
    ]
    for i, (kind, lbl) in enumerate(legends):
        ly = 4.02 + i * 0.38
        ix = rx + 0.22
        if kind == "wall":
            add_rect(s, ix, ly + 0.03, 0.40, 0.24, fill=WHITE, line_color=WALL_DARK, line_pt=2.2)
        elif kind == "green":
            add_rect(s, ix, ly + 0.03, 0.40, 0.24, fill=MAIN_GREEN, line_color=TEXT_MUTED, line_pt=0.75)
        elif kind == "blue":
            add_rect(s, ix, ly + 0.03, 0.40, 0.24, fill=STORAGE_BLUE, line_color=TEXT_MUTED, line_pt=0.75)
        elif kind == "door":
            add_rect(s, ix, ly + 0.03, 0.40, 0.24, fill=DOOR_GRAY, line_color=PILLAR_GRAY, line_pt=0.75)
            add_text(s, "門", ix, ly + 0.03, 0.40, 0.24, size=8.5, bold=True, color=TEXT_DARK, align=PP_ALIGN.CENTER)
        elif kind == "pillar":
            add_rect(s, ix, ly + 0.03, 0.40, 0.24, fill=PILLAR_GRAY)
        add_text(s, lbl, ix + 0.56, ly, 1.95, 0.30, size=10.5, color=TEXT_DARK)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "資材辦公室_室內平面配置圖_可編輯版.pptx")
    prs.save(out_path)
    print(f"[完成] 已產出 100% 原生向量可編輯平面配置圖 PPTX：{out_path}")


if __name__ == "__main__":
    build_floorplan_pptx()
