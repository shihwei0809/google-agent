"""
一鍵產生《鴻勝資材部季年報智慧分析系統_操作手冊.docx》與 .pdf
"""
import os
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_DIR = Path(__file__).resolve().parent
DOCX_PATH = BASE_DIR / "鴻勝資材部季年報智慧分析系統_操作手冊.docx"
PDF_PATH = BASE_DIR / "鴻勝資材部季年報智慧分析系統_操作手冊.pdf"


def build_manual():
    doc = Document()

    title = doc.add_heading("鴻勝資材部｜進出貨與季年報智慧分析系統 操作手冊", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph("本系統支援 BI 匯出 PDF（文字型與掃描型 AI OCR）及 Excel 明細檔自動解析，提供月報、季報、半年報、年報之 MoM / QoQ / YoY 差異比較、異常預警與 PPT 簡報文案/統計表圖卡一鍵產出。")
    p.runs[0].font.size = Pt(11)

    sections = [
        ("一、三軌啟動與安裝方式", [
            "1. 純網頁版 (1_Web_網頁版)：直接雙擊 index.html 即可在瀏覽器離線解析與分析。",
            "2. PWA 本機區網版 (2_PWA_App版)：雙擊「啟動PWA本機測試.bat」，系統會自動安裝套件、偵測可用 Port 並顯示區網 IP，同事可透過網址連線並點擊頂部「立即安裝」變成桌面 App。",
            "3. Cloudflare D1 雲端版 (3_Cloudflare_D1版)：設定 wrangler.toml 的 database_id 後，雙擊「一鍵自動部署上雲端.bat」即可全球跨裝置多人同步查詢。",
        ]),
        ("二、上傳解析 BI PDF 與 Excel 步驟", [
            "1. 點選上方「📤 上傳解析 (PDF / Excel)」分頁。",
            "2. 直接將 BI 匯出的 .xlsx / .xls（如 04.日報表-進貨一覽表、08.進貨、07.月出貨明細）或 .pdf 檔拖曳至上傳區。",
            "3. 文字型 PDF 會直接以零成本解析；若為掃描圖檔 PDF，系統會自動降級呼叫 Gemini Vision OCR 擷取數據。",
            "4. 核對下方「解析預覽表」無誤後，點擊「💾 確認寫入資料庫」（斷網時自動暫存，連網秒補傳）。",
        ]),
        ("三、原料進出貨與倉庫棧板雙獨立報表", [
            "1. 「🚛 原料進出貨分析」專注於大車進貨/出貨公噸 (MT)、車次、單車載重與 BI Top 5 品名/客戶鑽取，支援月報/季報/半年報/年報與 YoY / MoM / QoQ 差異比較。",
            "2. 「🏭 倉庫棧板報表」獨立統計 7 大作業項目（原料進貨、客供包材進貨、自用包材進貨、成品入庫、調撥、換標或理貨作業、出貨）與平均每工作日作業板數。",
            "3. 兩份報表於「📝 雙 PPT 簡報 & 匯出」拆分為兩份完全獨立的摘要文案、高解析圖卡與可編輯 PowerPoint (.pptx) 簡報檔。",
        ]),
        ("四、PPT 簡報文案、圖卡匯出與異常預警", [
            "1. 切至「📝 簡報文案 & 一鍵匯出」，點擊「📋 一鍵複製文案」即可貼進 PowerPoint；點擊「📑 下載可編輯 PPTX 簡報 (.pptx)」可直接產生原生簡報檔。",
            "2. 點擊「🖼️ 下載高解析簡報圖卡 (PNG)」產出圖卡，或點擊「📊 匯出完整 Excel 報表」下載多分頁彙總檔。",
            "3. 於「🚨 異常預警」檢視波動超過 ±15%（可自由調整）的月份；於「📋 日常管理 (P.5)」與「🎯 重要工作進度 (P.6~8)」皆可直接拖曳上傳 Excel / Word (.docx) / PPT (.pptx) / PDF / 截圖或貼上文字自動解析批次匯入，亦可下載標準 Excel 範本。",
        ]),
    ]

    for heading, bullets in sections:
        doc.add_heading(heading, level=1)
        for b in bullets:
            para = doc.add_paragraph(b, style="List Bullet")
            para.runs[0].font.size = Pt(10.5)

    doc.save(DOCX_PATH)
    print(f"[完成] 已產出 Word 操作手冊：{DOCX_PATH}")

    # Try converting to PDF if docx2pdf or Word COM is available
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        d = word.Documents.Open(str(DOCX_PATH))
        d.SaveAs(str(PDF_PATH), FileFormat=17)
        d.Close()
        word.Quit()
        print(f"[完成] 已產出 PDF 操作手冊：{PDF_PATH}")
    except Exception as e:
        print(f"[提示] Word 自動轉 PDF 略過（可用 Word 開啟另存 PDF）：{e}")


if __name__ == "__main__":
    build_manual()
