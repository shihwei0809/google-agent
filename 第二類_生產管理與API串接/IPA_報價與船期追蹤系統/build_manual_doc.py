# -*- coding: utf-8 -*-
"""
自動生成《IPA (異丙醇) 報價與出貨單船期自動追蹤系統_操作手冊.docx》
"""

import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DOCX = os.path.join(BASE_DIR, "IPA_報價與船期追蹤系統_操作手冊.docx")


def build_manual():
    doc = Document()

    title = doc.add_heading("IPA (異丙醇) 報價與出貨單船期自動追蹤系統 - 操作手冊", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph(
        f"版本：v1.0.0 (三軌架構標準版) ｜ 產出日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("一、 系統核心功能總覽", level=1)
    bullets = [
        "1. 雙單位即時自動換算：系統每日自動抓取最新 USD/TWD 與 USD/CNY 即期匯率，將所有國內外報價自動換算為【台幣/公斤 (TWD/KG)】與【美金/公噸 (USD/MT)】，並同步計算 160KG 桶裝成本與 20MT ISO Tank 整槽貨值。",
        "2. 上游丙酮/丙烯 ➔ IPA 加工價差雷達：同時監控異丙醇 (IPA) 與上游原料（丙酮 Acetone、丙烯 Propylene），當丙酮急漲導致加工價差收斂低於成本警戒線時，系統自動亮燈預警提前鎖單。",
        "3. 出貨單「櫃號 + 船名」自動反查船公司：無須事先知道哪家船公司，只要輸入出貨單上的櫃號（如 WHLU5581920、EXFU8839201、NRSU2849102），系統即依前 4 碼自動識別船公司或 ISO Tank 槽罐商，並提供 AIS 船位、台灣港務局靠泊預報與船公司查櫃一鍵跳轉。",
        "4. 三軌架構與離線優先支援：完整提供 1_Web_網頁版、2_PWA_App版（可安裝於桌面/手機、支援斷網暫存與連網自動補傳）及 3_Cloudflare_D1版。"
    ]
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")

    doc.add_heading("二、 各版本快速啟動與安裝步驟", level=1)
    doc.add_heading("1. 本機 PWA 看板與爬蟲伺服器版 (2_PWA_App版 - 最推薦)", level=2)
    doc.add_paragraph("• 步驟 1：打開專案資料夾下的「2_PWA_App版」。")
    doc.add_paragraph("• 步驟 2：雙擊執行「啟動PWA本機測試.bat」。")
    doc.add_paragraph("• 步驟 3：系統會自動檢查 Python 環境、啟動本機伺服器（預設 http://localhost:8088，若被佔用自動切換至下一個可用 Port）並印出區網共享 IP，接著自動開啟瀏覽器畫面。")
    doc.add_paragraph("• 步驟 4：點擊畫面頂部藍色橫幅「立即安裝」，即可將系統安裝為獨立桌面或手機 App。")

    doc.add_heading("2. 設定每天早上 08:00 自動背景爬蟲排程", level=2)
    doc.add_paragraph("• 在專案根目錄雙擊「一鍵設定每日自動爬蟲排程.bat」。")
    doc.add_paragraph("• 系統會自動在 Windows 工作排程器建立每日 08:00 定時任務，每天自動更新匯率、換算雙單位報價並輸出當日 Excel (CSV) 日報。")

    doc.add_heading("3. 純網頁版 (1_Web_網頁版) 與 雲端版 (3_Cloudflare_D1版)", level=2)
    doc.add_paragraph("• 1_Web_網頁版：直接雙擊 index.html 即可在任何瀏覽器離線或連線使用雙單位換算與櫃號反查。")
    doc.add_paragraph("• 3_Cloudflare_D1版：雙擊「一鍵自動部署上雲端.bat」，即可透過 Wrangler 部署至 Cloudflare Pages + D1 雲端資料庫。")

    doc.add_heading("三、 常見櫃號前 4 碼 (SCAC / BIC) 自動識別對照表", level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "櫃號前 4 碼"
    hdr[1].text = "自動識別船公司 / 槽罐營運商"
    hdr[2].text = "櫃型分類"

    rows_data = [
        ("EGLV / EISU", "長榮海運 (Evergreen)", "一般危險品貨櫃 (桶裝 IPA)"),
        ("YMLU / YMMU", "陽明海運 (Yang Ming)", "一般危險品貨櫃 (桶裝 IPA)"),
        ("WHLU / WHSU", "萬海航運 (Wan Hai)", "一般危險品貨櫃 (桶裝 IPA)"),
        ("TSLU", "德翔海運 (T.S. Lines)", "一般危險品貨櫃 (桶裝 IPA)"),
        ("ONEY / NYKU", "海洋網聯 (ONE)", "一般危險品貨櫃 (桶裝 IPA)"),
        ("NRSU / JOTU", "NRS 日陸物流 / JOT (日本主力槽車)", "ISO Tank 液體化學槽罐櫃"),
        ("EXFU", "EXSIF Worldwide (全球最大化工槽罐商)", "ISO Tank 液體化學槽罐櫃"),
        ("STTU / HOYU", "Stolt / Hoyer (國際化學槽罐物流)", "ISO Tank 液體化學槽罐櫃"),
    ]
    for code, carrier, btype in rows_data:
        row_cells = table.add_row().cells
        row_cells[0].text = code
        row_cells[1].text = carrier
        row_cells[2].text = btype

    doc.save(OUT_DOCX)
    print(f"✅ 操作手冊已成功生成: {OUT_DOCX}")


if __name__ == "__main__":
    build_manual()
