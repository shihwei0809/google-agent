"""
自動生成《倉儲儲位 PWA 記錄系統_操作手冊.docx》與 PDF 轉檔腳本
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT_DOCX = ROOT / "倉儲儲位PWA記錄系統_操作手冊.docx"


def build_manual():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Microsoft JhengHei"
    style.font.size = Pt(11)

    title = doc.add_heading("倉儲儲位 PWA 記錄系統 — 操作手冊", level=0)
    title.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "本系統專為倉庫現場人員設計，可直接透過手機瀏覽器或安裝為 PWA App，"
        "選擇儲位、批號與數量後即時回寫「崙尾倉儲儲位表.xlsm」與「鴻勝儲位表.xlsm」，"
        "並自動統計今日總錄入板數與各批號入/出庫數量供對帳核對。"
    )

    doc.add_heading("一、啟動方式（電腦端）", level=1)
    for step in [
        "1. 確認電腦與手機連上同一個公司 Wi-Fi。",
        "2. 雙擊「2_PWA_App版\\啟動PWA儲位系統.bat」。",
        "3. 視窗會自動檢查 Python 套件並顯示「手機區網網址」（例如 http://192.168.x.x:8010）。",
        "4. 若預設 Port 8010 被佔用，系統會自動切換至下一個可用 Port。",
        "5. 注意：寫入 Excel 前請先關閉電腦上開啟中的 .xlsm 檔案，避免檔案被鎖定。"
    ]:
        doc.add_paragraph(step)

    doc.add_heading("二、手機安裝 PWA App", level=1)
    for step in [
        "1. 手機瀏覽器（Android Chrome / iOS Safari）開啟終端機顯示的區網網址。",
        "2. Android 點擊頂部「立即安裝」橫幅，或瀏覽器選單「加到主畫面」。",
        "3. iOS Safari 點擊「分享」圖示 →「加入主畫面」。",
        "4. 安裝後即可全螢幕操作，且支援斷網離線暫存、連網自動補傳。"
    ]:
        doc.add_paragraph(step)

    doc.add_heading("三、現場錄入儲位操作流程", level=1)
    for step in [
        "1. 頂部選擇倉庫：「崙尾倉儲」或「鴻勝倉庫」。",
        "2. 在「1️⃣ 選擇儲位」選擇區域或輸入儲位代碼搜尋，點選目標儲位卡片。",
        "3. 畫面會顯示該儲位目前 Excel 內的品名、批號與數量。",
        "4. 選擇動作：「➕ 入庫」、「➖ 出庫」或「✏️ 盤點覆寫」。",
        "5. 選擇品名（自動帶出品號）、輸入或快選批號、輸入數量與板數（預設 1 板）。",
        "6. 點擊「✅ 確認送出並回寫 Excel」，系統即完成 .xlsm 回寫並累計今日紀錄。"
    ]:
        doc.add_paragraph(step)

    doc.add_heading("四、今日統計與批號核對（對帳中心）", level=1)
    for step in [
        "1. 切換至底部「📊 今日統計」頁籤。",
        "2. 頂部卡片即時顯示：今日總錄入板數（分入庫/出庫）、入庫總數量、出庫總數量與作業筆數。",
        "3. 「各批號錄入彙整」表格依批號彙整入庫/出庫板數與數量，可直接對照入庫單與出貨單。",
        "4. 點擊「📥 匯出CSV」可下載今日完整對帳表（Excel 直接開啟無亂碼）。"
    ]:
        doc.add_paragraph(step)

    doc.add_heading("五、雲端版 (Cloudflare D1) 與網頁版", level=1)
    doc.add_paragraph(
        "• 1_Web_網頁版/index.html：提供桌機瀏覽器快速檢視今日批號彙整與匯出 CSV。\n"
        "• 3_Cloudflare_D1版/：可執行 一鍵自動部署上雲端.bat 部署至 Cloudflare Pages + D1，"
        "供外部行動網路連線使用。"
    )

    doc.save(str(OUT_DOCX))
    print(f"已產出 Word 操作手冊: {OUT_DOCX}")

    # 嘗試轉檔為 PDF（若本機有 LibreOffice 或 docx2pdf）
    try:
        from docx2pdf import convert
        out_pdf = OUT_DOCX.with_suffix(".pdf")
        convert(str(OUT_DOCX), str(out_pdf))
        print(f"已產出 PDF 操作手冊: {out_pdf}")
    except Exception as e:
        print(f"[提示] 略過 PDF 轉檔（未安裝 docx2pdf 或 Word COM 轉檔不可用）: {e}")


if __name__ == "__main__":
    build_manual()
