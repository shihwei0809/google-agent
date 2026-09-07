# -*- coding: utf-8 -*-
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_manual():
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("【系統操作手冊】鴻勝化學 QC 檢驗即時看板系統 (PWA 雙軌版)")
    run_title.font.name = "微軟正黑體"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(37, 99, 235)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("版本：v1.0 (含 T100 槽車排程智慧自動帶入) | 適用：Windows 電腦 / 平板 / Android / iOS PWA")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    def add_h1(text):
        h = doc.add_heading(level=1)
        r = h.add_run(text)
        r.font.name = "微軟正黑體"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        return h

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_after = Pt(4)
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "微軟正黑體"
            r_pre.font.size = Pt(10.5)
            r_pre.font.bold = True
        r = p.add_run(text)
        r.font.name = "微軟正黑體"
        r.font.size = Pt(10.5)
        return p

    add_h1("一、系統簡介與核心特色")
    add_p("本系統為鴻勝化學專屬之 QC 樣品即時登錄、檢驗進度看板與品管放行管理系統。具備以下核心能力：")
    add_p(" 系統專門鎖定《進出貨排程報表》中「槽車」分頁，自動抽取單號、品名、槽號、櫃號/車牌、數量，提供一鍵下拉選單，免手打 9 欄位。", "1. T100 槽車排程智慧帶入：")
    add_p(" 支援一鍵安裝為 PWA 獨立桌面/手機 App，支援離線操作與本機/區域網路多人協作。", "2. PWA 雙軌獨立架構：")
    add_p(" 當品管人員驗證合格放行時，系統自動透過 LINE Messaging API 廣播至指定群組。", "3. LINE 即時推播：")
    add_p(" 送樣時可一鍵開啟並列印標準 2 吋送樣實體標籤貼紙。", "4. 實體標籤列印：")

    add_h1("二、T100 槽車排程匯入與自動帶入操作流程")
    add_p("1. 打開系統看板，在表單最上方可看見綠色「🚛 T100 槽車排程」工具列。")
    add_p("2. 點擊下拉選單，即可看到系統已預載之今天/明天槽車排程清單（例如：[08:00] ESXM101-20260901013 | IPAUPS | TK624 | PPCU7019228）。")
    add_p("3. 點選目標車次，系統瞬間自動填入：出通單號、動向(出貨)、等級、品名、槽號、車牌/櫃號、數量。")
    add_p("4. 現場人員只需填入「送樣人員」姓名，點擊「確認提交送樣」，1 秒完成送樣登錄。")
    add_p("5. 【每日更新排程】：現場人員每日從 T100 匯出新排程 Excel 後，點擊「📂 匯入最新 T100 排程 Excel」，選取該檔，系統將自動鎖定「槽車」分頁並秒級刷新選單！")

    add_h1("三、品管檢驗與放行判定流程")
    add_p("1. 送樣後樣品出現在左側「待驗中」看板列。")
    add_p("2. 品管人員完成檢驗後，點擊該筆資料右側的「判定」按鈕。")
    add_p("3. 彈出判定視窗，選擇 PASS (合格放行) 或 FAIL (不合格退回)，並輸入檢驗備註。")
    add_p("4. 輸入品管專屬授權 PIN 碼（預設為 8888，可於試算表後台自訂）。")
    add_p("5. 點擊「確認判定」，系統自動移至右側「已檢驗完成」列表，並同步發送 LINE 放行通知。")

    add_h1("四、PWA 獨立 App 安裝指引")
    add_p(" 電腦 Chrome 或 Edge 瀏覽器打開網址，點擊網址列右側之「安裝」圖示，或頂部橫幅「立即安裝」，即可將系統獨立為視窗 App。", "• 電腦端 (Windows / Mac)：")
    add_p(" 使用 Chrome 瀏覽器打開，點擊右上角「...」->「加到主畫面」，桌面即出現專屬 App 圖示。", "• 手機端 (Android)：")
    add_p(" 使用 Safari 瀏覽器打開，點擊下方「分享」按鈕 -> 往下滑點選「加入主畫面」。", "• 手機端 (iOS Safari)：")

    out_docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "鴻勝化學_QC檢驗即時看板系統_操作手冊.docx")
    doc.save(out_docx)
    print(f"✅ 操作手冊已成功產出: {out_docx}")

if __name__ == '__main__':
    create_manual()
