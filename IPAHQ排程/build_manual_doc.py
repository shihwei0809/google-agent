import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_manual():
    doc = Document()
    
    # 標題
    title = doc.add_heading('勝一化工 - 槽車出貨排程系統 操作手冊與 Q&A', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph('更新日期：2026 年 9 月\n').alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 壹、系統簡介
    doc.add_heading('壹、系統簡介與登入', level=1)
    p = doc.add_paragraph()
    p.add_run('正式雲端網址：').bold = True
    p.add_run('https://google-agent-4gzi.onrender.com\n')
    p.add_run('本系統提供 24/7 雲端連線，主要用於「業務匯入基準班表」、「技服主管指派充填手」、「運輸公司填報車牌」以及「技服人員即時手機推播與已讀確認」。\n\n')
    p.add_run('帳號與密碼說明：\n').bold = True
    p.add_run('• 系統管理員：admin / shihwei\n')
    p.add_run('• 業務：sales\n')
    p.add_run('• 技服主管：tech_mgr\n')
    p.add_run('• 運輸公司：transporter\n')
    p.add_run('• 技服人員：直接使用您的姓名登入（如：林聖龍、胡富閔）\n')
    p.add_run('（※ 所有帳號預設密碼皆為 123，登入後可於系統內修改）')
    
    # 貳、各角色操作流程
    doc.add_heading('貳、各角色標準操作流程', level=1)
    
    doc.add_heading('1. 業務人員 (sales)', level=2)
    doc.add_paragraph('步驟一：登入後點擊「業務 / 主管 / 管理員面板」。\n'
                      '步驟二：點擊【選擇 Excel 檔案】，上傳每日的「空白基準班表」。\n'
                      '步驟三：系統會自動建立今日排程清單，並儲存相關訂單資訊。')
                      
    doc.add_heading('2. 技服主管 (tech_mgr)', level=2)
    doc.add_paragraph('步驟一：在主管面板點擊【選擇 Excel 檔案】，上傳包含「充填手」指派的技服排程表。\n'
                      '步驟二：系統會自動將資料與業務基準表進行比對，顯示比對預覽畫面。\n'
                      '步驟三：點擊【確認匯入】。系統會提示共有幾位技服人員有新任務。\n'
                      '步驟四：點擊【確定】即可一鍵發送手機推播通知給所有被指派的技服人員！')
                      
    doc.add_heading('3. 技服人員 (手機端操作)', level=2)
    doc.add_paragraph('步驟一：手機收到推播通知後，點擊通知將自動開啟系統（免重複登入）。\n'
                      '步驟二：畫面上方會詢問是否允許發送通知，請務必點擊【允許】。\n'
                      '步驟三：首頁會列出您專屬的「當天」與「明天」出貨任務。\n'
                      '步驟四：確認任務內容後，點擊每張卡片右下角的綠色【確認已讀】按鈕，電腦端即會同步顯示您的確認時間。')

    doc.add_heading('4. 運輸公司 (transporter)', level=2)
    doc.add_paragraph('步驟一：登入後，點擊【運輸公司專用】上傳含有車牌與司機的排班表。\n'
                      '步驟二：比對完成後，司機資訊將自動填補至系統中，完成最後一哩路的資料拼圖。')

    # 參、常見問題與解答 (Q&A)
    doc.add_heading('參、常見問題與解答 (Q&A)', level=1)
    
    qa_list = [
        ("Q1：如果我（技服人員）手機沒有收到推播通知怎麼辦？", 
         "A1：請確認兩件事：\n1. 首次使用時，瀏覽器上方會跳出「要求傳送通知」的權限，必須選擇「允許」。\n2. 確保您使用的手機瀏覽器為 Chrome (Android) 或 Safari (iPhone)，並將網址透過瀏覽器選單「加入主畫面」，變成桌面 App 後開啟，推播功能最穩定。"),
        
        ("Q2：主管如果不小心重複上傳同一份 Excel，已經按「已讀」的人會再收到一次推播嗎？", 
         "A2：不會的！系統有「智慧保留機制」。如果您已經按過已讀，且主管重新匯入時「負責人」沒有換人，系統會保留您的已讀狀態，並且不會再重複發送推播轟炸您。"),
        
        ("Q3：如果是「換人」接手該任務，前一個人的已讀狀態會怎樣？", 
         "A3：只要系統偵測到負責的「充填手」變更了，就會自動將該筆任務重置為「🔴 未讀」，並發送全新的推播通知給新接手的人員！"),
        
        ("Q4：主管在匯入技服排程時，可以選擇「先匯入但不發推播」嗎？", 
         "A4：可以！匯入完成後系統會跳出確認視窗，詢問「是否立即發送推播通知？」。若您點擊【取消】，資料依然會存入資料庫，但不會驚動任何人員。您可以在確認無誤後，再請人員自行上網查看。"),
        
        ("Q5：伺服器會不會因為閒置太久而休眠，導致登入很慢？", 
         "A5：不會。我們已經設定了雙重保活機制（程式內部每 10 分鐘心跳 + 外部 UptimeRobot 每 5 分鐘打卡），系統 24 小時全天候秒開不延遲。"),
         
        ("Q6：忘記密碼怎麼辦？", 
         "A6：請聯繫系統管理員 (shihwei) 幫您重置密碼，預設重置密碼皆為 123。")
    ]
    
    for q, a in qa_list:
        p_q = doc.add_paragraph()
        p_q.add_run(q).bold = True
        
        p_a = doc.add_paragraph(a)
        p_a.paragraph_format.left_indent = Inches(0.2)
        p_a.paragraph_format.space_after = Pt(14)
        
    # 肆、系統跨平台 PWA 安裝指引
    doc.add_heading('肆、手機版桌面 App 安裝指引 (PWA)', level=1)
    doc.add_paragraph('本系統支援「漸進式網路應用程式 (PWA)」，強烈建議技服人員與主管將其安裝至手機桌面，操作體驗如同原生 App：\n\n'
                      '【Android / 安卓手機】\n'
                      '1. 使用 Chrome 瀏覽器開啟正式網址。\n'
                      '2. 點擊右上角「三個點」選單。\n'
                      '3. 選擇「加到主畫面」或「安裝應用程式」。\n\n'
                      '【iPhone / iOS 手機】\n'
                      '1. 使用 Safari 瀏覽器開啟正式網址。\n'
                      '2. 點擊畫面底部的「分享」圖示（方框往上的箭頭）。\n'
                      '3. 往下滑點擊「加入主畫面」。')

    docx_path = os.path.join(os.path.dirname(__file__), '勝一出貨排程管理系統_操作手冊與QA.docx')
    pdf_path = os.path.join(os.path.dirname(__file__), '勝一出貨排程管理系統_操作手冊與QA.pdf')
    
    doc.save(docx_path)
    print("Docx generated:", docx_path)

    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc_com = word.Documents.Open(docx_path)
        doc_com.SaveAs(pdf_path, FileFormat=17)
        doc_com.Close()
        word.Quit()
        print("PDF generated:", pdf_path)
    except Exception as e:
        print("PDF export skipped:", e)

if __name__ == '__main__':
    create_manual()
