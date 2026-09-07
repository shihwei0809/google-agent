# -*- coding: utf-8 -*-
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import win32com.client

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_manual():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    doc = docx.Document()
    
    # 邊界設定
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # 主標題
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("【系統操作手冊】IPA 生產排程與進耗存整合系統 v3.1")
    run_title.font.name = "微軟正黑體"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 64, 175)
    
    # 副標題
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("版本：v3.1 (PWA 獨立 App 雙軌版) | 適用設備：Windows 電腦 / Android 手機 / iPhone / 平板")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_paragraph("―" * 58)
    
    # 第一章：系統簡介與核心定位
    doc.add_heading("一、 系統簡介與雙廠區架構", level=1)
    doc.add_paragraph(
        "本系統為「IPA 生產排程與進耗存整合系統 v3.1」，採用 React 18 與 Tailwind CSS 打造高動態響應儀表板，"
        "支援 Google Apps Script 雲端同步與 PWA 獨立離線 App 運作模式。核心劃分兩大廠區獨立運作："
    )
    
    plants_info = [
        ("🏭 彰濱一廠 (共用原料池)", "配置 5 大原料槽 (TK604A, TK604B, TK696, TK697, TK693) 納入「共用原料池 (Shared Pool)」合併扣減，並配置 TK652 下腳料槽。"),
        ("🏭 彰濱二廠 (獨立儲槽區)", "配置獨立原料槽 TK617 (LG) 與 TK618 (日本) 專槽專用，並具備 TK611 (支援回吃 🔄) 與 TK613 (不可回吃 ⛔) 下腳料槽。")
    ]
    for p_name, p_desc in plants_info:
        p = doc.add_paragraph()
        r = p.add_run(f"◆ {p_name}：\n")
        r.bold = True
        r.font.color.rgb = RGBColor(30, 64, 175)
        p.add_run(p_desc)
        
    # 第二章：v3.1 重點功能
    doc.add_heading("二、 v3.1 重點核心功能特色", level=1)
    features = [
        ("🚀 二廠試開俥運轉日區間速設", "產線可獨立設定運轉日區間 (trialStartDay ~ trialEndDay)，提供一鍵「⚡ 批次套用至二廠產線」，非運轉日製程耗用自動歸零。"),
        ("⚠️ 雙向臨界警示機制", "原料槽存量低於安全存量下限 (預設 50T) 標註紅底警示；下腳料槽結存超出滿槽上限 (預設 200T) 即時觸發紅底閃爍警示。"),
        ("📦 雙模式試算引擎", "支援「全月流速滿載模式 (FLOW)」與「產銷排產首日動態模式 (SALES)」切換，後者自動偵測首個有排產之日期並動態裁切顯示區間。"),
        ("📅 4 個月份跨月連續傳承", "動態呈現 4 個月份預估，前月最後一日之結存餘量自動繼承為次月 1 號期初庫存。"),
        ("⚙️ Config 自由設定頁", "線上免改程式碼即可動態新增/刪除產線與儲槽，即時切換共用池及回吃狀態。")
    ]
    for f_title, f_desc in features:
        p = doc.add_paragraph()
        r = p.add_run(f"【{f_title}】\n")
        r.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        p.add_run(f_desc)
        
    # 第三章：PWA 安裝指引
    doc.add_heading("三、 三端 PWA 獨立 App 安裝指引", level=1)
    doc.add_paragraph("本系統全面支援 PWA (Progressive Web App) 技術，可於電腦及行動端安裝為獨立視窗 App：")
    
    install_steps = [
        ("電腦端 (Windows / Mac - Chrome / Edge)", "開啟伺服器網址後，點擊網址列右側的「安裝」圖示，或頂部橫幅「⚡ 立即安裝 App」，桌面即建立專屬獨立圖示。"),
        ("Android 手機 / 平板 / 現場 PDA", "瀏覽器開啟網址後，點擊頂部智慧橫幅「立即安裝」，或由右上角功能表選擇「新增至主畫面」。"),
        ("iPhone / iPad (iOS Safari)", "由 Safari 瀏覽器打開網址，點擊底部工具列中間的「分享」圖示 (向上箭頭)，滑動選單點擊「加入主畫面」即可完成。")
    ]
    for s_title, s_desc in install_steps:
        p = doc.add_paragraph()
        r = p.add_run(f"● {s_title}：\n")
        r.bold = True
        r.font.color.rgb = RGBColor(2, 132, 199)
        p.add_run(s_desc)
        
    # 第四章：儲存、備份與報表匯出
    doc.add_heading("四、 雲端儲存、備份還原與報表匯出", level=1)
    doc.add_paragraph(
        "1. 自動儲存：所有數值異動 2 秒後自動觸發防抖儲存，同步至 Google 試算表 (ID: 1UdTuMJPW8QJ5XAP_ptWvPooEvnLHLaZcLEgYj8qlSPU)。\n"
        "2. 歷史快照：點擊「💾 備份存檔」可自訂名稱建立完整資料庫快照；點擊「📂 讀取」可隨時回溯還原歷史紀錄。\n"
        "3. Excel 報表：點擊「📥 匯出報表」即可一鍵下載帶有 UTF-8 BOM 格式之 CSV 檔案，Excel 開啟不亂碼。"
    )

    doc_path = os.path.join(script_dir, "IPA生產排程與進耗存整合系統_操作手冊.docx")
    pdf_path = os.path.join(script_dir, "IPA生產排程與進耗存整合系統_操作手冊.pdf")
    
    doc.save(doc_path)
    print(f"[✓] 成功產生 Word 操作手冊: {doc_path}")
    
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc_pdf = word.Documents.Open(os.path.abspath(doc_path))
        doc_pdf.SaveAs(os.path.abspath(pdf_path), FileFormat=17) # 17 = wdFormatPDF
        doc_pdf.Close()
        word.Quit()
        print(f"[✓] 成功轉換 PDF 操作手冊: {pdf_path}")
    except Exception as e:
        print(f"[!] PDF 轉換失敗或未安裝 Word: {e}")

if __name__ == '__main__':
    create_manual()
