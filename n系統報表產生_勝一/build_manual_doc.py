# -*- coding: utf-8 -*-
"""
N系小包報表輸出系統 操作手冊產生腳本
自動生成 Word (.docx) 操作手冊
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime
import os
from build_manual_illustrations import main as build_manual_illustrations

OUTPUT_FILE = "N系小包報表輸出系統_操作手冊.docx"

# ─────────────────────────────────────────
# 輔助函式
# ─────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    run = p.runs[0] if p.runs else p.add_run(text)
    run.font.name = 'Microsoft JhengHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    if level == 1:
        run.font.size = Pt(18)
    elif level == 2:
        run.font.size = Pt(14)
    else:
        run.font.size = Pt(12)
    return p

def add_para(doc, text, bold=False, color=None, size=11, indent=0):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    run.font.name = 'Microsoft JhengHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    run.font.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p

def add_bullet(doc, text, indent=1):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    run.font.name = 'Microsoft JhengHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    run.font.size = Pt(11)
    return p

def add_step(doc, number, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    r1 = p.add_run(f"步驟 {number}：")
    r1.font.name = 'Microsoft JhengHei'
    r1._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = RGBColor(0x19, 0x76, 0xD2)
    r2 = p.add_run(text)
    r2.font.name = 'Microsoft JhengHei'
    r2._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    r2.font.size = Pt(11)
    return p

def add_note(doc, text, kind="提示"):
    colors = {"提示": (0xE3, 0xF2, 0xFD), "注意": (0xFF, 0xF3, 0xE0), "警告": (0xFF, 0xEB, 0xEE)}
    bg = colors.get(kind, colors["提示"])
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, f"{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}")
    cp = cell.paragraphs[0]
    run = cp.add_run(f"【{kind}】{text}")
    run.font.name = 'Microsoft JhengHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    run.font.size = Pt(10)
    run.font.bold = (kind in ("注意", "警告"))
    doc.add_paragraph()

def add_illustration(doc, image_name, caption):
    image_path = os.path.join(os.path.dirname(__file__), "tutorial_assets", "manual_illustrations", image_name)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(image_path, width=Inches(5.2))
    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(0)
    if cp.runs:
        cp.runs[0].font.name = 'Microsoft JhengHei'
        cp.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
        cp.runs[0].font.size = Pt(9)
        cp.runs[0].font.color.rgb = RGBColor(0, 0, 0)

def add_table(doc, headers, rows, header_color="1976D2"):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表頭
    for i, h in enumerate(headers):
        cell = tbl.cell(0, i)
        set_cell_bg(cell, header_color)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.font.name = 'Microsoft JhengHei'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 資料列
    for ri, row in enumerate(rows):
        bg = "FFFFFF" if ri % 2 == 0 else "F5F5F5"
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.name = 'Microsoft JhengHei'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
            run.font.size = Pt(10)
    doc.add_paragraph()
    return tbl


# ─────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────

def build_manual():
    build_manual_illustrations()
    doc = Document()

    for style_name in ('Normal', 'List Bullet'):
        doc.styles[style_name].paragraph_format.space_after = Pt(4)
        doc.styles[style_name].paragraph_format.line_spacing = 1.0
    title_style_ppr = doc.styles['Title']._element.get_or_add_pPr()
    title_style_bdr = title_style_ppr.find(qn('w:pBdr'))
    if title_style_bdr is not None:
        title_style_ppr.remove(title_style_bdr)

    # 頁面設定
    section = doc.sections[0]
    section.page_width  = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)

    # ══════════════════════════════════════
    # 封面
    # ══════════════════════════════════════
    doc.add_paragraph()

    title = doc.add_paragraph(style='Title')
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(0)
    title.paragraph_format.keep_with_next = True
    ppr = title._p.get_or_add_pPr()
    p_bdr = ppr.find(qn('w:pBdr'))
    if p_bdr is not None:
        ppr.remove(p_bdr)
    p_bdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'nil')
    p_bdr.append(bottom)
    ppr.append(p_bdr)
    r = title.add_run("N 系小包生產履歷與 COA 批次產生系統")
    r.font.name = 'Microsoft JhengHei'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = sub.add_run("操作手冊")
    r2.font.name = 'Microsoft JhengHei'
    r2._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    r2.font.size = Pt(18)
    r2.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.add_paragraph()

    scope = doc.add_paragraph()
    scope.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = scope.add_run("本版本支援匯入出貨排程、載入生產履歷與 COA 範本，核對後批次產生兩類輸出檔。")
    sr.font.name = 'Microsoft JhengHei'
    sr._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    sr.font.size = Pt(11)
    sr.font.color.rgb = RGBColor(0, 0, 0)

    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dr = date_p.add_run(f"製作日期：{datetime.date.today().strftime('%Y 年 %m 月 %d 日')}")
    dr.font.name = 'Microsoft JhengHei'
    dr._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    dr.font.size = Pt(12)
    dr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    dept_p = doc.add_paragraph()
    dept_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dpr = dept_p.add_run("勝一化工股份有限公司")
    dpr.font.name = 'Microsoft JhengHei'
    dpr._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
    dpr.font.size = Pt(12)
    dpr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # ══════════════════════════════════════
    # 目錄
    # ══════════════════════════════════════
    add_heading(doc, "目錄", level=1)
    toc_items = [
        ("1", "系統概述與功能說明"),
        ("2", "系統啟動"),
        ("3", "主介面說明"),
        ("4", "步驟一：匯入出貨排程"),
        ("5", "步驟二：載入生產履歷 (Chemical_Lorry)"),
        ("6", "步驟三：載入 COA 表單"),
        ("7", "步驟四：設定輸出資料夾模式"),
        ("8", "步驟五：執行批次產生"),
        ("9", "輸出檔案結構說明"),
        ("10", "常見問題 Q&A"),
        ("11", "欄位對照與資料規範"),
    ]
    for num, title_text in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        r = p.add_run(f"{num}. {title_text}")
        r.font.name = 'Microsoft JhengHei'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
        r.font.size = Pt(11)

    doc.add_page_break()

    # ══════════════════════════════════════
    # 1. 系統概述
    # ══════════════════════════════════════
    add_heading(doc, "1. 系統概述與功能說明", level=1)
    add_para(doc, "本系統依據 N 系列小包出貨排程，載入相應來源範本並批次產生下列兩類文件：")
    add_bullet(doc, "生產履歷 (Chemical_Lorry)：自動填入批號、廠區代號、出貨日、製造日期")
    add_bullet(doc, "COA 品質保證書：自動填入批號、出貨日、廠區代號、剩餘天數")
    add_note(doc, "依 main.py 現行設定，批次產生目前輸出單列 Chemical_Lorry 與 COA；三合一單及運輸報表功能未啟用。", kind="注意")
    doc.add_paragraph()
    add_para(doc, "支援產品系列", bold=True)
    add_table(doc,
        ["系列", "說明"],
        [
            ["NSE-115 / NSE-115A", "15P5、其他廠區"],
            ["NSE-1106 / NSE-1106A", "12P8、F20P1、F20P3 等廠區"],
        ]
    )

    add_note(doc, "本系統支援同一批號對應多個不同廠區，並自動各自產生獨立的生產履歷與 COA 副本。", kind="提示")


    # ══════════════════════════════════════
    # 2. 系統啟動
    # ══════════════════════════════════════
    add_heading(doc, "2. 系統啟動", level=1)
    add_step(doc, 1, "找到專案資料夾內的「啟動本機視窗版.bat」，雙擊執行")
    add_step(doc, 2, "等待 Python 環境啟動（約 3–5 秒），系統主介面視窗將自動出現")
    add_step(doc, 3, "確認視窗頂部的「系統狀態」區塊，確保對照表已正確載入（顯示已找到）")
    doc.add_paragraph()
    add_note(doc, "若對照表顯示未找到，請確認同目錄下存在「N系料小包-地點代號對照表.xlsx」，再按右側「重新載入對照表」按鈕。", kind="注意")


    # ══════════════════════════════════════
    # 3. 主介面說明
    # ══════════════════════════════════════
    add_heading(doc, "3. 主介面說明", level=1)
    add_para(doc, "系統主介面由上而下分成以下幾個區塊：", size=11)
    doc.add_paragraph()
    add_table(doc,
        ["區域", "功能說明"],
        [
            ["系統狀態區", "顯示對照表與生產履歷的載入狀態，提供重新載入與選擇檔案的快捷按鈕"],
            ["工具列", "匯入排程、載入生產履歷、載入 COA、清除已載入檔案、帶入今天日期、新增列、清除全部"],
            ["輸出資料夾模式", "選擇產出檔案的資料夾結構（模式 1 帶批號子資料夾 / 模式 2 集中在廠區目錄）"],
            ["排程資料表格", "填寫或匯入出貨排程資料（批號、廠區、料號、出貨日期、到貨日期、採購單號、品名、製造日、保存期限、剩餘天數）"],
            ["產生按鈕", "確認所有資料已就緒後，按此執行批次報表產生"],
        ],
        header_color="003287"
    )

    mock_path = os.path.join(os.path.dirname(__file__), "tutorial_assets", "manual_illustrations", "06_主介面操作區標示.png")
    if os.path.exists(mock_path):
        pic_p = doc.add_paragraph()
        pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic_p.add_run().add_picture(mock_path, width=Inches(5.4))
        cap = doc.add_paragraph("圖 1　主介面操作區總覽（紅框與編號標示操作重點；使用合成資料）")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


    # ══════════════════════════════════════
    # 4. 匯入出貨排程
    # ══════════════════════════════════════
    add_heading(doc, "4. 步驟一：匯入出貨排程", level=1)

    add_heading(doc, "4.1 使用 Excel 或 CSV 匯入", level=2)
    add_step(doc, 1, "點選工具列「從 Excel 匯入排程」按鈕")
    add_step(doc, 2, "選取一個或多個出貨排程 Excel 或 CSV 檔案")
    add_step(doc, 3, "使用日期快速篩選按鈕，或在「指定區間」輸入起始日與結束日；日期條件依出貨日期查詢")
    add_step(doc, 4, "查多日：填入起始日與結束日，例如 2026/10/06 ～ 2026/10/10，再按「查詢」；查詢含起訖兩日")
    add_step(doc, 5, "查單日：只填起始日，例如 2026/10/06，結束日保持空白，再按「查詢」")
    add_step(doc, 6, "兩個日期欄位旁的日曆按鈕可用滑鼠選日期；也可直接輸入日期")
    add_step(doc, 7, "設定顯示筆數並核對預覽；勾選本次要匯入的資料列，確認後檢查批號、數量、地點及出貨日／到貨日")
    add_illustration(doc, "01_排程預覽標示.png", "圖 2　區間查詢：起始日、結束日皆可用日曆選取；查詢結果依出貨日期篩選")
    add_illustration(doc, "07_單日查詢留白示範.png", "圖 3　單日查詢：填起始日、結束日留白，再按查詢")

    add_heading(doc, "4.2 系統自動辨識欄位對應", level=2)
    add_note(doc, "系統會自動掃描 Excel 的欄位標題，以下是對應規則：", kind="提示")
    add_table(doc,
        ["Excel 欄位標題關鍵字", "系統對應欄位", "說明"],
        [
            ["出貨日、出貨日期、出車", "出貨日期", ""],
            ["到貨日、到貨日期、到貨", "到貨日期", ""],
            ["剩餘、剩餘天數", "剩餘天數", "直接由 Excel 抓取（不再動態計算）"],
            ["地點、指送、交貨、廠區", "指送地點", "若匯入失敗，請確認 Excel 欄位名稱是否正確"],
            ["採購單號、採購單", "採購單號 (PO)", "不會誤抓「PO 餘額」欄位"],
            ["品名", "品名", ""],
            ["批號、Lot", "批號", ""],
            ["保存期限", "保存期限", "排除「剩餘保存天數」欄位，精準定位"],
            ["製造、生產日", "製造日", "若匯入失敗，請確認 Excel 欄位名稱是否包含此關鍵字"],
        ]
    )

    add_heading(doc, "4.3 手動輸入", level=2)
    add_step(doc, 1, "直接在表格欄位中點擊並輸入資料")
    add_step(doc, 2, "廠區欄輸入代號後，系統會自動對照表帶出長代號（如 12P8 → 1280）")
    add_illustration(doc, "03_排程欄位核對標示.png", "圖 4　排程資料核對：紅框分別標示批號、地點代號及出貨/到貨日期")
    add_heading(doc, "4.4 排程表格欄位說明", level=2)
    add_table(doc,
        ["欄位名稱", "必填", "說明"],
        [
            ["勾選", "—", "打勾代表此筆資料會被納入報表產生"],
            ["批號", "✔ 必填", "必須為 10 碼；示範值 DEMO000001"],
            ["廠區", "✔ 必填", "台積電廠區代號，如 12P8、F20P1、15P5"],
            ["料號", "建議填", "物料料號，可由對照表自動帶入"],
            ["長代號", "建議填", "廠區英文長代號，如 1280，自動對照帶入"],
            ["出貨日期", "✔ 必填", "出貨日期，格式 YYYY/MM/DD"],
            ["到貨日期", "建議填", "到貨日期，格式 YYYY/MM/DD（產出報表時會優先以此為準）"],
            ["採購單號", "建議填", "台積電採購單號"],
            ["品名", "建議填", "化學品品名，匯入時自動帶入"],
            ["製造日", "建議填", "產品製造日期"],
            ["保存期限", "建議填", "產品保存期限"],
            ["剩餘天數", "建議填", "直接由 Excel 匯入，不再自動相減計算。此值會寫入 COA"],
        ]
    )


    # ══════════════════════════════════════
    # 5. 載入生產履歷
    # ══════════════════════════════════════
    add_heading(doc, "5. 步驟二：載入生產履歷 (Chemical_Lorry)", level=1)
    add_para(doc, "生產履歷為系統自動填入批號、廠區代號（TSMCFab / FabPhase）、出貨日、製造日期的 Excel 範本。")
    doc.add_paragraph()

    add_heading(doc, "5.1 載入步驟", level=2)
    add_step(doc, 1, "點選工具列「載入生產履歷 (Chemical_Lorry)」按鈕")
    add_step(doc, 2, "在檔案選擇視窗中，選擇 Chemical_Lorry*.xlsx 範本（可多選）")
    add_step(doc, 3, "可重複點選按鈕載入不同資料夾（115 系列、1106 系列）的範本，系統會累加不覆蓋")
    add_step(doc, 4, "彈窗顯示「累計已載入 X 份生產履歷（本次新增 Y 份）」及比對結果")
    add_note(doc, "系統採用【累加載入】模式，115 資料夾和 1106 資料夾可分次選取，不用擔心先選的被後選的覆蓋掉。", kind="提示")
    add_note(doc, "若需要重新選擇，請先按「清除已載入檔案」按鈕清空後再重新載入。", kind="注意")
    add_illustration(doc, "02_履歷與COA載入標示.png", "圖 5　來源範本載入：依序選擇生產履歷與 COA 表單")

    add_heading(doc, "5.2 自動填入欄位說明", level=2)
    add_table(doc,
        ["生產履歷欄位", "寫入值", "來源"],
        [
            ["TSMCFab", "廠區長代號（如 1280）", "排程表的「長代號」欄"],
            ["FabPhase", "廠區長代號（如 1280）", "排程表的「長代號」欄"],
            ["DeliveryDate", "出貨日期（YYYY/MM/DD）", "排程表的「出貨日」欄"],
            ["ManufactureDate", "製造日期（YYYY/MM/DD）", "排程表的「製造日期」欄"],
            ["FinalBatchID", "批號", "依原始生產履歷範本的批號自動對應"],
        ]
    )


    # ══════════════════════════════════════
    # 6. 載入 COA
    # ══════════════════════════════════════
    add_heading(doc, "6. 步驟三：載入 COA 表單", level=1)
    add_para(doc, "COA（Certificate of Analysis）品質保證書為 .csv 或 .xlsx 格式，系統自動填入批號、出貨日、廠區代號，並在有 RemainLifeTime 欄位時自動寫入剩餘天數。")
    doc.add_paragraph()

    add_heading(doc, "6.1 載入步驟", level=2)
    add_step(doc, 1, "點選工具列「載入 COA 表單」按鈕")
    add_step(doc, 2, "選擇 COA 原始範本（.csv 或 .xlsx）（可多選）")
    add_step(doc, 3, "可重複點選，跨資料夾分次載入（115 系列、1106 系列），系統累加不覆蓋")
    add_step(doc, 4, "彈窗顯示「本次新增 X 份，累計已載入 Y 份」與各檔案的批號比對結果")
    doc.add_paragraph()

    add_note(doc, "COA 同樣採用【累加載入】模式，可分多次從不同資料夾選取，不需要一次全選。", kind="提示")

    add_heading(doc, "6.2 COA 自動填入欄位說明", level=2)
    add_table(doc,
        ["COA 欄位關鍵字", "寫入值", "寫入欄（Column）"],
        [
            ["FinalBatchID / BatchNo", "批號", "B 欄"],
            ["TSMCFab", "廠區長代號", "B 欄"],
            ["FabPhase", "廠區長代號", "B 欄"],
            ["DeliverDate", "出貨日期", "B 欄"],
            ["ManufacturingDate", "製造日期", "B 欄"],
            ["PONO", "採購單號", "B 欄"],
            ["ShipQty", "出貨數量", "B 欄"],
            ["RemainLifeTime", "剩餘天數（自動）", "G 欄（第 7 欄）"],
        ]
    )

    add_heading(doc, "6.3 COA 產出檔名規則", level=2)
    add_para(doc, "產出的 COA 檔名格式如下：")
    add_para(doc, "  原始前綴 + 批號 + MMDD（出貨月日）+ 廠區代號 + 副檔名", indent=1)
    add_para(doc, "範例：", bold=True)
    add_bullet(doc, "原始檔名：NSE-DEMO COA DEMO000001 TSMC.csv")
    add_bullet(doc, "產出檔名：NSE-DEMO COA DEMO000001 1007 15P5.csv")
    add_note(doc, "「TSMC」會自動被移除，替換為出貨月日（MMDD）與廠區代號。", kind="提示")


    # ══════════════════════════════════════
    # 7. 輸出資料夾模式
    # ══════════════════════════════════════
    add_heading(doc, "7. 步驟四：設定輸出資料夾模式", level=1)
    add_para(doc, "在執行產生報表之前，可透過「輸出資料夾模式」區塊選擇報表的資料夾分層結構：")
    doc.add_paragraph()
    add_table(doc,
        ["模式", "資料夾結構", "適用情境"],
        [
            ["模式 1（預設）", "出貨日資料夾 → 廠區資料夾 → 批號_廠區資料夾 → 檔案", "需要依批號分類管理時使用"],
            ["模式 2", "出貨日資料夾 → 廠區資料夾 → 檔案（直接放入）", "同廠區的報表集中放置，不分批號子目錄"],
        ],
        header_color="4CAF50"
    )
    doc.add_paragraph()
    add_note(doc, "兩種模式會影響本版本輸出的 COA 與單列生產履歷資料夾位置。", kind="提示")


    # ══════════════════════════════════════
    # 8. 執行批次產生
    # ══════════════════════════════════════
    add_heading(doc, "8. 步驟五：執行批次產生", level=1)
    add_step(doc, 1, "確認所有排程列都已填妥資料，並勾選要產生的列")
    add_step(doc, 2, "確認生產履歷與 COA 表單都已成功載入（狀態區顯示已載入）")
    add_step(doc, 3, "選擇「輸出資料夾模式」（模式 1 或 模式 2）")
    add_step(doc, 4, "按下「開始批次產生 Excel 報表」按鈕")
    add_step(doc, 5, "等待系統處理完成，完成後彈出結果彈窗")
    add_step(doc, 6, "開啟輸出目錄確認所有報表檔案")
    doc.add_paragraph()

    add_note(doc, "輸出目錄預設在 main.py 同資料夾下的「N系小包報表輸出_YYYYMMDD」資料夾（以出貨日期命名）。", kind="提示")
    add_note(doc, "同一批號若有多個廠區，系統會各自複製生產履歷與 COA 並分別填入對應的廠區資訊。", kind="注意")
    add_illustration(doc, "04_批次產生標示.png", "圖 6　批次產生前先選輸出模式，資料核對完成後再執行")
    add_illustration(doc, "05_完成結果標示.png", "圖 7　完成後確認成功筆數與輸出路徑，並抽查檔案內容")

    # ══════════════════════════════════════
    # 9. 輸出檔案結構
    # ══════════════════════════════════════
    add_heading(doc, "9. 輸出檔案結構說明", level=1)

    add_heading(doc, "模式 1（依批號子資料夾）", level=2)
    add_para(doc, "N系小包報表輸出_YYYYMMDD/", size=10, indent=0.5)
    add_para(doc, "    └── 15P5/", size=10, indent=0.5)
    add_para(doc, "        └── 1007 15P5 DEMO000001/", size=10, indent=0.5)
    add_para(doc, "            ├── Chemical_Lorry-示範履歷-DEMO000001 1007 15P5.xlsx  ← 生產履歷", size=10, indent=0.5)
    add_para(doc, "            └── NSE DEMO COA DEMO000001 1007 15P5.csv             ← COA", size=10, indent=0.5)
    doc.add_paragraph()

    add_heading(doc, "模式 2（集中在廠區目錄）", level=2)
    add_para(doc, "N系小包報表輸出_YYYYMMDD/", size=10, indent=0.5)
    add_para(doc, "    └── 15P5/", size=10, indent=0.5)
    add_para(doc, "        ├── Chemical_Lorry-示範履歷-DEMO000001 1007 15P5.xlsx", size=10, indent=0.5)
    add_para(doc, "        └── NSE DEMO COA DEMO000001 1007 15P5.csv", size=10, indent=0.5)


    # ══════════════════════════════════════
    # 10. Q&A
    # ══════════════════════════════════════
    add_heading(doc, "10. 常見問題 Q&A", level=1)

    qa_items = [
        ("Q：為什麼「地點」、「料號」、「製造日」欄位無法從 Excel 帶入？",
         "A：這通常是因為您的 Excel 檔案中的表頭名稱不符合系統預設關鍵字。請將您的 Excel 表頭分別修正為包含「地點」、「料號」、「製造日」等字眼，系統即可正常抓取。"),
        ("Q：載入 115 系列的生產履歷後，再載入 1106 系列，115 的資料是否會消失？",
         "A：不會！系統採用「累加載入」模式，每次載入都是新增到清單，不覆蓋舊資料。若需重新選擇，請先按「清除已載入檔案」按鈕。"),
        ("Q：COA 表單找不到對應的批號怎麼辦？",
         "A：彈窗中會顯示「找不到對應批號」的檔案清單。請確認排程表中有填入對應批號，且該列已打勾。"),
        ("Q：為什麼保存期限沒有抓到正確的欄位？",
         "A：系統已加入過濾邏輯，會自動略過「剩餘保存天數」欄位，精準定位「保存期限」欄。若仍有問題，請確認 Excel 的欄位標題是否包含「保存期限」關鍵字。"),
        ("Q：同一批號要出貨到兩個不同廠區，怎麼操作？",
         "A：在排程表格中，新增兩列，填入相同的批號，但廠區填不同的代號。系統會自動為每個廠區各自產生一份生產履歷與 COA。"),
        ("Q：COA 的剩餘天數為什麼有的有寫、有的沒有？",
         "A：系統會掃描 COA 範本內是否有「RemainLifeTime」欄位。有此欄位的 COA 才會自動寫入剩餘天數；若 COA 範本沒有此欄位，則自動跳過，不強制填入。"),
        ("Q：如何清除已載入的 COA 與生產履歷？",
         "A：按工具列的「清除已載入檔案」按鈕，即可將 COA 與 Lorry 的累積清單全部清空，下次載入將重新開始。"),
        ("Q：COA 檔名前面的「第8.1版」等前綴被截斷怎麼辦？",
         "A：此問題已在最新版本修正。系統不再對已去除副檔名的檔名做二次拆分，「第8.1版」等含小數點的前綴會完整保留。"),
    ]

    for q, a in qa_items:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.left_indent = Cm(0.5)
        rq = p_q.add_run(q)
        rq.font.name = 'Microsoft JhengHei'
        rq._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
        rq.font.bold = True
        rq.font.size = Pt(11)
        rq.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

        p_a = doc.add_paragraph()
        p_a.paragraph_format.left_indent = Cm(1)
        ra = p_a.add_run(a)
        ra.font.name = 'Microsoft JhengHei'
        ra._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
        ra.font.size = Pt(11)
        doc.add_paragraph()


    # ══════════════════════════════════════
    # 11. 欄位對照與資料規範
    # ══════════════════════════════════════
    add_heading(doc, "11. 欄位對照與資料規範", level=1)

    add_heading(doc, "11.1 廠區代號對照表（範例）", level=2)
    add_table(doc,
        ["廠區簡稱", "廠區長代號", "備註"],
        [
            ["12P8", "1280", "NSE-1106A 主要廠區"],
            ["F20P1", "1570", "NSE-1106A 廠區"],
            ["F20P3", "1575", "NSE-1106A 廠區"],
            ["15P5", "1500", "NSE-115 廠區"],
            ["18P1", "1810", "NSE-1106 廠區"],
        ]
    )
    add_note(doc, "完整對照表請參考「N系料小包-地點代號對照表.xlsx」，系統讀取此檔後自動帶入。", kind="提示")

    add_heading(doc, "11.2 日期格式規範", level=2)
    add_table(doc,
        ["欄位", "格式", "範例"],
        [
            ["出貨日期", "YYYY/MM/DD", "2026/10/06"],
            ["製造日期", "YYYY/MM/DD", "2026/09/11"],
            ["保存期限", "YYYY/MM/DD", "2027/09/10"],
            ["COA / Lorry 內日期", "YYYY/MM/DD", "2026/10/06"],
        ]
    )

    # ══════════════════════════════════════
    # 儲存
    # ══════════════════════════════════════
    doc.save(OUTPUT_FILE)
    print(f"[OK] 操作手冊已產生：{OUTPUT_FILE}")


if __name__ == "__main__":
    build_manual()
