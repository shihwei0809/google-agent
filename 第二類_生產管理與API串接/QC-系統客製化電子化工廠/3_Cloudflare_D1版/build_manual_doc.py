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
    run_sub = p_sub.add_run("版本：v3.3.0 (含同車多單彈性品名配置、重複送樣彈窗防呆、等級智慧動態判定、已檢驗完成近2天動態展示、Microsoft Teams 精準分流) | 適用：Windows 電腦 / 平板 / Android / iOS PWA")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(10)
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
    add_p(" 針對業助在同車次連續開立多張單號（如 EBR-P1R、NBAC-P1R、CPN-P1R 等），系統依排程日期自動預設勾選該日連續單號；管理員可於後台隨時自由增刪允許合併之品名白名單，其餘標準品項（如 GAA、IPA）則永遠為獨立單號免彈窗打擾！", "2. 同車次多單號智慧勾選合併 (v3.3.0)：")
    add_p(" 若點選先前已送樣中或已判定完成放行之車次，系統立即跳出「⚠️ 重複送樣／二次複驗確認」視窗，清楚呈現前次送樣人與檢驗狀態，由同仁自主點選確定二次送樣或取消，徹底杜絕誤送！", "3. 重複送樣／二次複驗彈窗防呆 (v3.3.0)：")
    add_p(" 等級欄位不再死板固定單一選項，而是先比對後台對照表，若無則依品名特徵（-P1R/回收 -> 回收液, UPS -> UPS, IF -> IF, OEM/電子級 -> 電子級, 標準溶劑 -> 工業級）精準智慧判定，表單初始化留白提示，安全防呆。", "4. 產品等級智慧動態判定 (v3.3.0)：")
    add_p(" 右側已檢驗完成列表預設只顯示近 2 天（今天與昨天）案件，維持看板乾淨流暢；歷史案件可隨時由頂部起迄日期查詢器隨選即查。", "5. 已檢驗完成看板保留近 2 天：")
    add_p(" 支援一鍵安裝為 PWA 獨立桌面/手機 App，支援離線操作與本機/區域網路多人協作。", "6. PWA 雙軌獨立架構：")
    add_p(" 依送樣單位（資材課、二部一課、二部二課、一部一課、一部二課）精準路由推送，只通知主管與該送樣課室頻道，其他課室完全不受干擾！", "7. Microsoft Teams 精準分流通知：")
    add_p(" 待檢驗樣品等候超過 2 小時未完成判定，系統自動發出紅字閃爍警報並推播 Teams 警報卡片給主管與該單位！", "8. 2 小時超時智慧預警 (SLA)：")
    add_p(" 送樣時可一鍵開啟並列印標準 2 吋送樣實體標籤貼紙。", "9. 實體標籤列印：")

    add_h1("二、T100 槽車排程匯入、多單合併與自動帶入流程")
    add_p("1. 打開系統看板，在表單最上方可看見綠色「🚛 T100 槽車排程」工具列。")
    add_p("2. 點擊下拉選單，即可看到系統已預載之今天/昨天或指定日期槽車排程清單（例如：[2026-11-04] ESPM411-20261102034 | IPA [槽:TK604A] [車:KEK-0716]）。")
    add_p("3. 【重複送樣與二次複驗彈窗提醒 (v3.3.0)】：若人員選取的排程先前已在系統中送樣或完成判定，系統會立即彈出確認視窗：")
    add_p("   • 視窗內清楚顯示前次送樣時間、送樣人，以及當前狀態（如：已完成檢驗放行 PASS / 檢驗中）。")
    add_p("   • 人員可自行點擊「✅ 確定再次送樣 (複驗/重取樣)」繼續帶入表單，或點擊「✕ 取消」清空選擇防止誤登。")
    add_p("4. 點選目標車次後，系統將自動判斷該車是否有同車次多單號：")
    add_p("   • 【獨立單號品項】：若品名非多單合併品項（如 GAA、IPA），直接瞬間自動填入所有欄位，無需彈窗打擾。")
    add_p("   • 【同車多單允許品項 (v3.3.0)】：若該車次有 2 筆以上單號，自動彈出「🚚 同車次多單號合併確認」勾選視窗：")
    add_p("     - 🎯 智慧自動勾選：系統自動以您點選之「排程日期」為基準，預設將該日同車次的所有連續單號自動打勾！")
    add_p("     - ⚠️ 跨天防呆留白：歷史不同日期的排程單號預設不打勾，避免跨天無腦誤併；現場若真有補送需求才手動勾選。")
    add_p("     - 🔄 二次送樣自由判定：歷史已送樣單號預設不勾，但開放人員視現場需要自主勾選進行二次複驗。")
    add_p("     - 💡 操作按鈕：內建「📅 只勾選選定日期」、「全選可用」、「全不選」、「僅保留原單號 (不合併)」，確認後系統自動將勾選單號以逗點串接填入並智慧累計總數量。")
    add_p("5. 現場人員只需填入「送樣人員」工號或姓名，系統自動依工號帶出全名，確認「送樣單位」，點擊「確認提交送樣」，1 秒完成送樣登錄。")
    add_p("6. 【每日更新排程】：現場人員每日從 T100 匯出新排程 Excel 後，點擊「📂 匯入最新 T100 排程 Excel」，選取該檔，系統將自動鎖定「槽車」分頁並秒級刷新選單！")

    add_h1("三、品管檢驗判定與已檢驗看板管理")
    add_p("1. 送樣後樣品出現在左側「待驗中」看板列，表格即時顯示「等候時長」。")
    add_p("2. 【超時預警】：若等候超過 2 小時，狀態自動轉為紅底呼吸燈動畫「⚠️ 等候 X.X 小時 (逾期)」，GAS 雲端排程自動推播 Teams 紅色警報卡片。")
    add_p("3. 品管人員完成檢驗後，點擊該筆資料右側的「判定」按鈕。")
    add_p("4. 彈出判定視窗，選擇 PASS (合格放行) 或 FAIL (不合格退回)，並輸入檢驗備註。")
    add_p("5. 系統採實名制核准，請輸入您的「個人專屬帳號與密碼」進行驗證。")
    add_p("6. 點擊「確認判定並通知 Teams」，系統自動發送高質感綠色/紅色 Teams 訊息卡片至【品管主管頻道】+【送樣課室頻道】，卡片上會精準標示「核准人」。")
    add_p("7. 【已檢驗完成看板預設保留 2 天 (v3.2.0)】：右側已檢驗完成看板預設只顯示近 2 天（今天與昨天）的合格/完成單據；如欲調閱更早歷史紀錄，只要在看板頂部的「日期起迄查詢器」輸入搜尋日期範圍，即可秒速調閱全歷史檢驗資料。")

    add_h1("四、系統管理後台 (帳號管理與參數設定)")
    add_p("管理員可點擊首頁右上角的「⚙️ 系統後台」按鈕進入管理介面（預設登入帳號：admin / 密碼：admin123）。")
    add_p("1. 【帳號管理分頁】：可新增品管人員帳號，支援完整中文字元，密碼基於資安考量限制至少 8 碼。您可在此隨時修改密碼或刪除離職員工的帳號。")
    add_p("2. 【系統參數設定分頁】：可自訂各課室的 Teams Webhook 頻道連結，以及下拉選單的選項（如：產品、等級、課室）。")
    add_p("3. 設定完成後，點擊綠色的「儲存參數設定」，設定會立刻同步至雲端資料庫生效。")

    add_h1("五、本機 PWA 模擬測試箱與管理員安全防呆機制")
    add_p("為防止現場同仁操作時誤觸測試功能造成資料混亂，系統內建「預設隱藏」與「管理員 PIN 碼權限驗證」防呆機制：")
    add_p(" 系統開啟時「🧪 本機模擬測試箱」工具列預設 100% 隱藏，不占用畫面空間，現場同仁無誤觸風險。", "• 預設安全隱藏：")
    add_p(" 點擊頂部「🔒 解鎖管理功能」按鈕，彈出安全驗證對話框，輸入品管管理員 PIN 碼（預設為 8888，可於試算表後台自訂）後即可展開測試箱。", "• 點擊解鎖管理功能：")
    add_p(" 解鎖後按鈕轉為「🔓 管理功能已解鎖 (點擊上鎖)」，測試完畢可隨時點擊按鈕或工具箱內的「🔒 鎖定隱藏」重新安全上鎖。", "• 隨時一鍵重新鎖定：")
    add_p(" 一鍵在看板最上方注入一筆等候 2.5 小時之樣品，即刻檢驗紅字呼吸燈逾期警示。", "• ⏱️ 注入逾期樣品 (>2小時)：")
    add_p(" 手動觸發逾期巡檢，立即彈出 Teams 紅色超時警報卡片預覽視窗。", "• 🚨 執行逾期巡檢：")
    add_p(" 可填入真實 Teams Incoming Webhook 進行真實推播，或使用內建預覽視窗直接查看卡片排版與分流頻道。", "• ⚙️ Teams Webhook 設定與卡片測試：")

    add_h1("六、PWA 獨立 App 安裝指引")
    add_p(" 電腦 Chrome 或 Edge 瀏覽器打開網址，點擊網址列右側之「安裝」圖示，或頂部橫幅「立即安裝」，即可將系統獨立為視窗 App。", "• 電腦端 (Windows / Mac)：")
    add_p(" 使用 Chrome 瀏覽器打開，點擊右上角「...」->「加到主畫面」，桌面即出現專屬 App 圖示。", "• 手機端 (Android)：")
    add_p(" 使用 Safari 瀏覽器打開，點擊下方「分享」按鈕 -> 往下滑點選「加入主畫面」。", "• 手機端 (iOS Safari)：")

    add_h1("七、9cm × 10cm (90mm × 100mm) 標籤機專用連續列印指南")
    add_p("針對現場與化驗室使用的標籤印表機（如 UniPrinter_D、Zebra、TSC 等），系統全面支援 9cm × 10cm 連續送樣標籤列印：")
    add_p(" 點選待驗樣品右側的「列印」，系統彈出專用設定視窗，預設配置「水分/GC 1 張」+「Metal 2 張」，總計 3 張 90mm × 100mm 連續出紙。", "1. 智慧分流與張數設定：")
    add_p(" 包含檢驗單號、槽號、車牌、送樣人員與時間，並附帶【Karl Fischer 水分 ppm】與【GC 純度 %】手寫記錄欄位。", "2. 水分 & GC 專用標籤 (1/3)：")
    add_p(" 自動分流為【瓶 1 (分析正樣)】與【瓶 2 (留樣存查 / 複測備用)】，並附帶【ICP-MS 案號】與樣品性質勾選欄。", "3. Metal 金屬離子專用標籤 (2/3 與 3/3)：")
    add_p(" 標籤內建 CSS Paged Media `@page { size: 90mm 100mm; margin: 0; }` 規格，標籤機會自動滿版貼合 9cm × 10cm 貼紙，杜絕縮放至 A4 左上角問題。", "4. 免調設定、滿版套印：")

    out_docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "鴻勝化學_QC檢驗即時看板系統_操作手冊.docx")
    doc.save(out_docx)
    print(f"✅ 操作手冊已成功產出: {out_docx}")

if __name__ == '__main__':
    create_manual()
