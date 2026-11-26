"""自動產生《SOP與WI檢查表電子化檢點系統_操作手冊.docx》"""
from pathlib import Path
from docx import Document

OUT_DOCX = Path(__file__).resolve().parent / "SOP與WI檢查表電子化檢點系統_操作手冊.docx"


def build():
    doc = Document()
    doc.add_heading("SOP / WI 檢查表電子化檢點系統 操作手冊", level=0)
    doc.add_paragraph("版本：v1.0.0 ｜ 製作人：shihwei0809 ｜ 對應文件：C50110-INV-02-01（3.1版）")

    doc.add_heading("1. 系統簡介與涵蓋表單", level=1)
    forms = [
        "6.1 槽車泵料入儲槽檢查表 — C50110-INV-02-01(05)",
        "6.2 運輸油槽車安檢、清潔度檢核表 — C50110-INV-02-01(03)",
        "6.3 ISO TANK 作業檢點表 — C50110-INV-02-01(04)",
        "6.4 ISO TANK 取樣作業檢點表 — C50110-INV-02-01(02)",
        "6.5 油罐車放櫃作業前檢點表 — C50110-INV-02-01(01)",
    ]
    for f in forms:
        doc.add_paragraph(f, style="List Bullet")

    doc.add_heading("2. 操作流程", level=1)
    steps = [
        "【步驟一】開啟檢點大廳，選擇本次作業要執行的表單（6.1～6.5）。",
        "【步驟二】填寫廠區與設備基本資訊（6.1 支援容積自動試算與泵浦「＼無此項」快捷聯動），完成檢點項目並由現場人員手寫簽名送出。",
        "【步驟三】組長、課(副)長、品管人員於「主管補簽與簽名庫」存入常用簽名檔，往後點一下即可一鍵呼叫簽核（可啟用 PIN 碼保護）。",
        "【步驟四】至「1:1 匯出 PDF / .xlsx」列印 A4 PDF 或下載原生 Excel（含透明手寫簽名圖）。",
        "【步驟五】未來 WI 改版次時，至「模板編輯與改版」修改廠區、表頭或檢點項目並點「一鍵改版升版」，舊紀錄永久鎖定舊版面。",
    ]
    for s in steps:
        doc.add_paragraph(s)

    doc.add_heading("3. 三軌版本啟動與部署", level=1)
    doc.add_paragraph("• 1_Web_網頁版：直接雙擊 index.html 以 Chrome / Edge 開啟。")
    doc.add_paragraph("• 2_PWA_App版：雙擊「啟動PWA本機測試.bat」，自動開啟本機與區網網址，平板可安裝為獨立 App 離線使用。")
    doc.add_paragraph("• 3_Cloudflare_D1版：設定 wrangler.toml 的 database_id 後，雙擊「一鍵自動部署上雲端.bat」上線雲端正式版。")

    doc.save(OUT_DOCX)
    print(f"已生成手冊：{OUT_DOCX}")


if __name__ == "__main__":
    build()
