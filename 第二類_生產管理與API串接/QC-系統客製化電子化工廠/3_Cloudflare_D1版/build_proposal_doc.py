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

def create_proposal():
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("【專案導入提案書】\n鴻勝化學 QC 檢驗即時看板與槽車送樣智慧化系統")
    run_title.font.name = "微軟正黑體"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 58, 138)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("提案日期：2026 年 11 月 ｜ 適用版本：v3.2.0 (PWA 原型已就緒) ｜ 提案部門：品質保證課 / 資材課 / 製造處各課室")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    
    def add_h1(text):
        h = doc.add_heading(level=1)
        r = h.add_run(text)
        r.font.name = "微軟正黑體"
        r.font.size = Pt(13.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(5)
        return h

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.space_after = Pt(4)
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "微軟正黑體"
            r_pre.font.size = Pt(10)
            r_pre.font.bold = True
        r = p.add_run(text)
        r.font.name = "微軟正黑體"
        r.font.size = Pt(10)
        return p

    # 一、提案摘要
    add_h1("一、提案摘要 (Executive Summary)")
    add_p("本提案建請公司核准導入「QC 檢驗即時看板系統」：讓每一筆樣品從送樣、等候、檢驗到放行的狀態都集中呈現在同一個畫面，並由 Teams 自動精準通知相關課室，逾期未判定時自動預警。")
    add_p(" 包含 T100 槽車排程帶入、同車多單連續單號智慧勾選合併 (v3.2.0)、Teams 精準分流、2 小時超時預警、實名制判定、完成看板近 2 天動態收合與 90×100 mm 標籤列印。", "• 原型系統完成度：")
    add_p(" 建議先選定 1 個課室（如資材課或二部一課）試行 4 週，以實測量化數據決定全面推廣時程；若廠方偏好快速上線，亦提供 3 週平穩雙軌併行方案（詳見導入計畫）。", "• 建議導入策略：")
    add_p(" ① 核准試行範圍（選定 1 課試行） ② 指派專案負責人與 T100 排程匯入窗口 ③ 同意資訊單位協助 Teams 與 T100 銜接並落實安全設定。", "• 需主管決議事項：")

    # 二、背景與痛點分析
    add_h1("二、背景與現行作業痛點分析 (Pain Points)")
    add_p("化工廠槽車、櫃車、原料進料皆高度依賴 QC 檢驗放行。樣品卡在哪一步，直接影響現場等候與出貨發車時效。現行紙本與口頭交接常見以下斷點：")
    
    table1 = doc.add_table(rows=7, cols=3)
    table1.style = 'Table Grid'
    headers1 = ["作業環節", "常見做法（現況 As-Is）", "產生的風險與管理瓶頸"]
    hdr_cells1 = table1.rows[0].cells
    for i, title in enumerate(headers1):
        hdr_cells1[i].text = title
        set_cell_background(hdr_cells1[i], "1E3A8A")
        for p in hdr_cells1[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data1 = [
        ("送樣登錄", "現場手寫或手動鍵入單號、品名、槽號、車牌、數量等 9 個欄位", "耗時約 3~5 分鐘/車；易抄錯單號或槽號，導致檢驗報告無法對帳"),
        ("同車多單與跨天排程", "業助對同一槽車連續開 3–4 張單（如 EBR-P1R、NBAC-P1R、CPN-P1R），同台車每隔幾天再進廠，人工對單極易混淆", "前幾天未送樣的歷史單號被一併無腦誤併，與 ERP 銷貨單據對不上，影響稽核"),
        ("等候進度追蹤", "現場靠電話、對講機頻繁催單問進度", "現場無法即時掌握哪些在等、已等多久；化驗人員專注度受頻繁打擾"),
        ("槽車逾期滯留", "樣品等候超過 2 小時無警報機制", "槽車卡在廠內，引發壓車費用、司機抱怨、客訴與發車延誤"),
        ("放行結果通知", "判定結果採群組廣播或紙本通知", "非相關課室被洗版造成通知疲勞，關鍵放行通知反而被忽略"),
        ("歷史追溯與統計", "紙本標籤與表單分散留存", "稽核調單困難、月度逢期率與瓶頸統計耗時費力")
    ]
    for row_idx, row_data in enumerate(data1):
        cells = table1.rows[row_idx + 1].cells
        for col_idx, text in enumerate(row_data):
            cells[col_idx].text = text
            if row_idx % 2 == 1:
                set_cell_background(cells[col_idx], "F8FAFC")
            for p in cells[col_idx].paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    add_p("以上斷點的核心根因在於「檢驗狀態沒有集中數位化顯示」。即時看板正是為了補足此一關鍵資訊缺口。")

    # 三、提案目標與範圍
    add_h1("三、提案目標與導入範圍 (Scope)")
    add_p("讓每一筆送樣從進廠到放行的每一步驟皆有完整時間紀錄與負責人，逾期樣品能即時被看見並警示處置。", "• 專案核心目標：")
    add_p(" 槽車送樣五大課室（資材課、二部一課、二部二課、一部一課、一部二課）、品管 QC 實名制判定放行、Teams 精準課室分流通報、90×100 mm 專用標籤列印。", "• 範圍內 (Phase 1)：")
    add_p(" 檢驗數值細項錄入、自動生成 CoA 檢驗證明書、與 T100 ERP 雙向自動回寫（列為第二期優化目標）。", "• 範圍外 (Phase 2 後續規劃)：")
    add_p(" 現場送樣人員、品管化驗員、品管主管、製造處各課主管、系統管理員。", "• 系統使用者：")
    add_p(" 現有 Windows 電腦、平板、手機 (PWA 免安裝即開即用) 與現有 90×100 mm 連續標籤機。", "• 適用硬體設備：")

    # 四、解決方案架構
    add_h1("四、解決方案核心功能 (To-Be Architecture)")
    add_p("即時看板將樣品作業整合為一條流暢的數位履歷鏈，現場同仁只需確認姓名與課室即可 1 秒完成：")
    add_p(" 從 T100 排程下拉選單點選車次，單一單號直接瞬間帶入出通單號、品名、槽號、車牌、數量，完全免手打。", "1. T100 槽車排程智慧鎖定與一鍵帶入：")
    add_p(" 業助連續登打之 3~4 筆單號，系統自動以選取排程日期為基準，預設勾選當天連續單號；跨天單號預設留白；已送樣單號反灰鎖定，確認後自動串接單號並累加總量，徹底杜絕跨天誤併。", "2. 同車多單連續單號智慧勾選 (v3.2.0 防呆核心)：")
    add_p(" 一鍵輸出 3 張滿版標籤（水分/GC 專用標籤 1 張 + Metal 正樣/留樣標籤 2 張），免調邊界完美貼合。", "3. 90×100 mm 專用標籤連續套印：")
    add_p(" 看板即時動態計算等候時長，等候超過 2 小時自動轉為紅底呼吸燈動畫，並推播 Teams 警報卡片至主管與該課室頻道。", "4. 等候即時監控與 2 小時超時預警：")
    add_p(" 品管人員以個人專屬帳密登入，核定 PASS (放行) / FAIL (退回) 並填寫檢驗備註，符合品質稽核可追溯性。", "5. 品管實名制放行判定：")
    add_p(" 判定結果卡片依送樣單位動態分流，只推播給品管主管頻道與該送樣課室頻道（五大課室各自獨立），其他無關課室零干擾。", "6. Microsoft Teams 精準課室分流通知：")
    add_p(" 完成看板預設僅顯示今天與昨天（近 2 天），大前天以前歷史資料由頂部日期起迄查詢器秒查，兼顧整潔度與調閱效率。", "7. 已檢驗完成看板近 2 天動態收合：")

    # 五、預期效益與成效指標
    add_h1("五、預期效益與實測成效指標 (KPIs)")
    add_p("建議試行前 1 週先行量測現況基準（Baseline），以真實數據驗證效益，避免憑空估算：")
    
    table2 = doc.add_table(rows=7, cols=4)
    table2.style = 'Table Grid'
    headers2 = ["指標項目", "量測方式", "現況預估 (待量測確認)", "試行驗收目標"]
    hdr_cells2 = table2.rows[0].cells
    for i, title in enumerate(headers2):
        hdr_cells2[i].text = title
        set_cell_background(hdr_cells2[i], "047857")
        for p in hdr_cells2[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data2 = [
        ("每車送樣登錄時間", "現場送樣開始到送出完成", "3 ~ 5 分鐘 / 車", "5 秒內 (單單號一鍵帶入)"),
        ("跨天誤併單件數", "每月品管與 ERP 銷貨對帳差異", "每月約 3 ~ 5 件", "0 件 (日期智慧對齊防呆)"),
        ("逾期樣品比例", "等候超過 2 小時件數 / 總送樣數", "待現場實測建立基準", "試行期逐週顯著下降"),
        ("送樣到判定平均時長", "系統時間戳記差額統計", "待現場實測建立基準", "建立瓶頸分析與穩定化"),
        ("現場催單通話次數", "現場對講機/電話抽樣登記", "每日估計 20 ~ 30 通", "大幅減少 80% 以上"),
        ("判定結果可追溯率", "具核准人、時間與備註筆數 / 總數", "紙本分散留存不易查閱", "100% 完整數位履歷")
    ]
    for row_idx, row_data in enumerate(data2):
        cells = table2.rows[row_idx + 1].cells
        for col_idx, text in enumerate(row_data):
            cells[col_idx].text = text
            if row_idx % 2 == 1:
                set_cell_background(cells[col_idx], "F0FDF4")
            for p in cells[col_idx].paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    # 六、導入計畫與時程安排
    add_h1("六、導入計畫與驗收門檻 (Implementation Roadmap)")
    add_p("為確保現場同仁平穩過渡，建議採三階段階梯式導入，各階段均設有嚴格「驗收門檻」，通過後始推進至下一階段：")
    
    table3 = doc.add_table(rows=4, cols=4)
    table3.style = 'Table Grid'
    headers3 = ["階段", "建議時程", "重點工作內容", "階梯驗收門檻"]
    hdr_cells3 = table3.rows[0].cells
    for i, title in enumerate(headers3):
        hdr_cells3[i].text = title
        set_cell_background(hdr_cells3[i], "D97706")
        for p in hdr_cells3[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data3 = [
        ("階段 1：種子試行", "第 1 ~ 4 週", "選定 1 個課室（如資材課或二部一課）試辦；量測現況基準；現場教育訓練；落實安全設定（停用預設帳密）", "試行課室連續 2 週 100% 送樣皆由系統登錄，現場無阻力"),
        ("階段 2：全廠推廣", "第 5 ~ 8 週", "擴大推廣至五大課室（資材課、二部一課、二部二課、一部一課、一部二課）；T100 匯入標準化；建立代理人備援機制", "五大課室全面上線使用，逾期件數較基準期顯著下降"),
        ("階段 3：深度優化", "第 9 ~ 12 週", "細分「等候收樣/檢驗中」子狀態；支援 QR Code 掃描；檢驗數據錄入與自動比對；主管週會統計報表固化", "納入公司 ISO/品質管理 SOP，主管每週常態使用看板數據檢討")
    ]
    for row_idx, row_data in enumerate(data3):
        cells = table3.rows[row_idx + 1].cells
        for col_idx, text in enumerate(row_data):
            cells[col_idx].text = text
            if row_idx % 2 == 1:
                set_cell_background(cells[col_idx], "FFFBEB")
            for p in cells[col_idx].paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    add_p("💡 快速上線備選方案：若廠部主管裁示需快速落地，亦可採 3 週方案：第 1 週頻道綁定與印表機測試、第 2 週現場雙軌併行、第 3 週停用紙本並全面切換。上線前務必先完成帳密安全強化。")

    # 七、資源需求與成本評估
    add_h1("七、資源需求與成本評估 (Resources & Cost)")
    add_p("系統前端與微服務原型均已完成開發，主要成本以內部人力調配與現有設備續用為主：")
    
    table4 = doc.add_table(rows=7, cols=3)
    table4.style = 'Table Grid'
    headers4 = ["資源項目", "工作說明與職責", "預估費用 / 成本性質"]
    hdr_cells4 = table4.rows[0].cells
    for i, title in enumerate(headers4):
        hdr_cells4[i].text = title
        set_cell_background(hdr_cells4[i], "475569")
        for p in hdr_cells4[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data4 = [
        ("專案負責人", "由品管主管或指派種子工程師 1 名，負責決策、驗收與跨課室協調", "內部人力工時調配"),
        ("系統開發與維護", "負責防呆邏輯修正、安全補強與後續功能維護升級", "內部人力工時調配"),
        ("雲端高可用平台", "Cloudflare Pages + D1 邊緣分散式資料庫（首年使用免費配額）", "零額外硬體購置費 ($0)"),
        ("Teams 通知串接", "公司既有 Microsoft Teams，由資訊課協助建置各課室頻道與 Webhook/Workflows", "既有軟體授權續用"),
        ("現場操作教育訓練", "針對各送樣課室與化驗室各辦理 1 場（每場約 30 分鐘，附操作手冊）", "內部訓練課程"),
        ("標籤印表機與耗材", "沿用廠內現有之 90×100 mm 連續標籤印表機與專用耗材", "既有設備續用")
    ]
    for row_idx, row_data in enumerate(data4):
        cells = table4.rows[row_idx + 1].cells
        for col_idx, text in enumerate(row_data):
            cells[col_idx].text = text
            if row_idx % 2 == 1:
                set_cell_background(cells[col_idx], "F1F5F9")
            for p in cells[col_idx].paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    # 八、潛在風險分析與防範對策
    add_h1("八、潛在風險分析與防範對策 (Risk Management)")
    
    table5 = doc.add_table(rows=7, cols=3)
    table5.style = 'Table Grid'
    headers5 = ["潛在風險", "對營運與品質之影響", "實施對策與防呆機制"]
    hdr_cells5 = table5.rows[0].cells
    for i, title in enumerate(headers5):
        hdr_cells5[i].text = title
        set_cell_background(hdr_cells5[i], "DC2626")
        for p in hdr_cells5[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    data5 = [
        ("預設管理員密碼外洩", "未授權人員可登入後台變更頻道或刪除排程", "正式上線前全面移除預設密碼 (admin123/PIN 8888)，首次登入強制變更高強度密碼"),
        ("Teams Webhook 退場", "微軟若公告舊版 Connector 退場，通知可能中斷", "系統後端預留支援 Power Automate Workflows 架構，隨時可無縫切換"),
        ("T100 排程漏匯入", "早班若漏匯入排程，現場當天將無排程可下拉", "指定專責排程窗口與代理人；系統保留「手動補單」彈性機制"),
        ("現場抗拒新作業模式", "同仁若不習慣易退回紙本，造成看板資料不完整", "採階梯式試行，先在 1 個課室驗證成功典範，種子同仁帶動全廠推廣"),
        ("離線多人重複判定衝突", "多台設備同時送樣或判定同一車次產生資料覆蓋", "資料庫端內建唯一單號 UUID 與防呆檢查，重複送樣自動警示彈窗"),
        ("單一程式維護風險", "若無標準化文件，後續交接維護易斷層", "嚴格落實 Rule 1~2 標準三件套（README、SKILL、setup_env），操作與維護文件完備")
    ]
    for row_idx, row_data in enumerate(data5):
        cells = table5.rows[row_idx + 1].cells
        for col_idx, text in enumerate(row_data):
            cells[col_idx].text = text
            if row_idx % 2 == 1:
                set_cell_background(cells[col_idx], "FEF2F2")
            for p in cells[col_idx].paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)

    # 九、請求主管核准事項 (簽核區)
    add_h1("九、建請主管核准與決議事項 (Decision Items)")
    add_p("為儘速提升現場槽車放行效率與品質防呆，建請主管裁示並簽核以下事項：")
    add_p(" ☐ 核准專案試行範圍：同意選定 1 個課室（建議：資材課或二部一課）展開為期 4 週之種子試行。")
    add_p(" ☐ 指派專案負責人：指派品質保證課負責人 1 名、各送樣課室種子窗口各 1 名，負責實施決策與進度驗收。")
    add_p(" ☐ 同意資訊單位支援：同意資訊課協助建立五大課室專屬 Teams 頻道，並落實 Webhook 串接與首次安全強化。")
    add_p(" ☐ 授權正式納入全廠作業流程：試行期滿達標（連續 2 週 100% 登錄且無爭議）後，授權全面推廣至五大課室並納入廠內 ISO / SOP 作業規範。")
    
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    
    # 簽核表格
    table_sign = doc.add_table(rows=2, cols=3)
    table_sign.style = 'Table Grid'
    sign_headers = ["提案負責人", "品質保證主管", "廠長 / 執行長核決"]
    for i, title in enumerate(sign_headers):
        table_sign.rows[0].cells[i].text = title
        set_cell_background(table_sign.rows[0].cells[i], "1E293B")
        for p in table_sign.rows[0].cells[i].paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
    
    for c in table_sign.rows[1].cells:
        c.text = "\n\n簽核：_____________________\n日期：    年    月    日\n"
        for p in c.paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.size = Pt(9.5)

    out_docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "鴻勝化學_QC檢驗即時看板系統_導入提案書.docx")
    doc.save(out_docx)
    print(f"✅ 升級版導入提案書已成功產出: {out_docx}")

if __name__ == '__main__':
    create_proposal()
