# -*- coding: utf-8 -*-
"""
永豐 Shioaji 即時看盤儀表板 - 操作與部署手冊自動生成腳本
"""
import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = Path(__file__).resolve().parent
DOCX_PATH = BASE_DIR / "永豐Shioaji即時看盤儀表板_操作手冊.docx"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_manual():
    doc = Document()

    # 設定邊界
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 封面 / 大標題
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("永豐 Shioaji 即時看盤儀表板\n操作手冊與技術架構指南")
    title_run.font.name = "微軟正黑體"
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("AGY 本機端專屬高效能看盤終端 · 雙軌實盤/模擬盤架構 · TradingView 視覺化\n版本：v1.0.0 | 產出日期：2026 年 11 月\n")
    sub_run.font.name = "微軟正黑體"
    sub_run.font.size = Pt(11)
    sub_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph("─" * 48).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 1. 系統介紹
    h1 = doc.add_heading("一、 系統簡介與核心特色", level=1)
    h1.runs[0].font.name = "微軟正黑體"

    p = doc.add_paragraph(
        "本系統為專為台灣股市與期貨交易者打造之本機私有化即時看盤終端。相較於常見的 Google Colab "
        "運算環境，本系統直接於本地端（AGY 環境）以 FastAPI 搭配 WebSocket 與 TradingView Lightweight Charts 驅動，"
        "兼具 100% 憑證金鑰安全、長時間盤中不斷線推播，以及極低延遲的視覺化介面。"
    )
    p.runs[0].font.name = "微軟正黑體"

    features = [
        ("雙軌運行架構", "內建「高仿真即時模擬盤」與「Shioaji 實盤連線」，免金鑰即可開箱體驗全功能。"),
        ("安全零洩漏", "永豐 API Key、Secret 與 CA 憑證均保存在本機端，無需上傳至任何雲端伺服器。"),
        ("TradingView 視覺化", "採用官方 Lightweight-Charts，流暢繪製秒級即時 K 線、成交量長條圖與分時折線。"),
        ("最佳五檔與逐筆流水帳", "即時委託深度百分比長條圖，搭配內外盤精確標記的即時逐筆明細。"),
        ("一鍵批次啟動", "內建智慧偵測腳本（啟動看盤儀表板.bat），自動安裝套件、切換佔用 Port 並開啟瀏覽器。"),
    ]
    for title, desc in features:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(f"【{title}】：")
        r1.font.bold = True
        r1.font.name = "微軟正黑體"
        r2 = bp.add_run(desc)
        r2.font.name = "微軟正黑體"

    # 2. 檔案目錄結構
    h2 = doc.add_heading("二、 完整目錄結構說明", level=1)
    h2.runs[0].font.name = "微軟正黑體"

    tree_text = (
        "C:\\GOOGLE ANGET\\shioaji-market-dashboard\\\n"
        "├── server.py                   # FastAPI 後端伺服器、WebSocket 廣播與模擬行情引擎\n"
        "├── 啟動看盤儀表板.bat           # 本機一鍵啟動腳本（自動偵測環境、Port切換、開瀏覽器）\n"
        "├── setup_env.ps1              # PowerShell 一鍵依賴環境自動安裝腳本\n"
        "├── requirements.txt           # Python 核心依賴清單\n"
        "├── .env                       # 本機環境變數與金鑰配置檔\n"
        "├── .env.example               # 環境變數設定範本\n"
        "├── README.md                  # 人類閱讀之專案說明與操作指引\n"
        "├── SKILL.md                   # AI 代理標準引導規範說明文件\n"
        "├── build_manual_doc.py        # 自動產生此操作手冊之腳本\n"
        "├── 永豐Shioaji即時看盤儀表板_操作手冊.docx # 本操作手冊檔案\n"
        "└── static/\n"
        "    ├── index.html             # 看盤儀表板前端主網頁（響應式三欄專業終端佈局）\n"
        "    ├── style.css              # 高質感深色主題樣式（彭博/TradingView風格）\n"
        "    └── app.js                 # TradingView 圖表繪製、WebSocket 監聽與五檔渲染邏輯\n"
    )
    p_tree = doc.add_paragraph()
    r_tree = p_tree.add_run(tree_text)
    r_tree.font.name = "Consolas"
    r_tree.font.size = Pt(9.5)

    # 3. 操作指引與快速上手
    h3 = doc.add_heading("三、 快速上手步驟", level=1)
    h3.runs[0].font.name = "微軟正黑體"

    steps = [
        "第一步：雙擊專案目錄下的「啟動看盤儀表板.bat」，程式將自動檢查 Python 與相依套件，若正常則於 2 秒後自動在預設瀏覽器開啟看盤畫面。",
        "第二步：進入看盤畫面後，預設以「高仿真即時模擬盤」運行，您會看到台積電 (2330)、鴻海 (2317)、聯發科 (2454) 等標的每秒跳動最新成交價、K 線與五檔盤況。",
        "第三步：點擊頂部標的膠囊或輸入代號（如 0050、TXF），即可快速切換檢視該標的之歷史 K 線與即時跳動行情。",
        "第四步（若有永豐金證券 API 金鑰）：點擊右上角「⚙️ 設定」，選擇「Shioaji 永豐正式實盤串流」，填入 API Key 與 Secret Key 後點擊「儲存並套用」，系統即無縫切換為券商真實即時串流。",
    ]
    for i, s in enumerate(steps, 1):
        sp = doc.add_paragraph()
        sr = sp.add_run(s)
        sr.font.name = "微軟正黑體"

    # 4. 技術架構與與 Colab 之差異對比
    h4 = doc.add_heading("四、 AGY 本機端 vs Google Colab 方案對比", level=1)
    h4.runs[0].font.name = "微軟正黑體"

    table = doc.add_table(rows=5, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["評比維度", "Google Colab 方案", "AGY 本機端方案 (本專案)"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        set_cell_background(cell, "1E293B")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("憑證與金鑰資安", "須上傳雲端/掛載 Google Drive，有密鑰洩漏風險", "100% 留存在本地端，零金鑰上傳風險"),
        ("連線持續性", "閒置 15~30 分鐘自動中斷，最多 12 小時重置", "本地常駐背景程序，全天候盤中不斷線"),
        ("前端畫面豐富度", "僅能使用陽春 ipywidgets 或靜態圖刷幀", "TradingView K線、動態五檔柱狀圖、逐筆流水帳"),
        ("日常開啟便捷度", "每次需開啟網頁、重新登入並執行各格代碼", "雙擊 .bat 檔 2 秒自動完成偵測與啟動"),
    ]
    for i, row in enumerate(data, 1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = val
            fill = "F8FAFC" if i % 2 == 1 else "FFFFFF"
            set_cell_background(cell, fill)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    doc.save(str(DOCX_PATH))
    print(f"手冊已成功生成: {DOCX_PATH}")

if __name__ == "__main__":
    create_manual()
