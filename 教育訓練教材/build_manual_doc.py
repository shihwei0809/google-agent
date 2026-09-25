
import os
try:
    from docx import Document
    from docx.shared import Pt
except ImportError:
    print("請先執行 pip install python-docx")
    exit()

def generate_manual():
    print("開始生成操作手冊...")
    doc = Document()
    
    # 標題
    title = doc.add_heading('AI 教育訓練平台與 QC 系統 - 操作手冊', 0)
    title.alignment = 1
    
    # 簡介
    doc.add_heading('1. 系統簡介', level=1)
    doc.add_paragraph('本系統為結合 AI 輔助的教育訓練平台，並支援最新的 PWA (漸進式網頁應用) 架構與 QC 系統提案改善書管理。使用者可在離線狀態下開啟 App 進行教材閱讀與問答。')
    
    # 環境建置
    doc.add_heading('2. 環境建置與啟動', level=1)
    doc.add_paragraph('1. 執行 setup_env.ps1 進行環境配置。')
    doc.add_paragraph('2. 後端啟動：進入 backend 目錄，執行 uvicorn main:app --reload')
    doc.add_paragraph('3. 前端/PWA 啟動：執行 PWA 專屬啟動腳本 (.bat) 或 npm run dev')
    
    # 使用說明與 PWA
    doc.add_heading('3. 核心功能與 PWA 安裝', level=1)
    doc.add_paragraph('【AI 助理】：於對話框輸入問題，AI 會根據教材自動提供解答。')
    doc.add_paragraph('【PWA 安裝】：使用手機或電腦瀏覽器開啟時，點選畫面上方的「安裝 App」按鈕，即可將系統安裝至桌面，享受全螢幕且離線的流暢體驗！')
    doc.add_paragraph('【QC 系統】：可於系統內匯出提案改善書 (.docx)，涵蓋人工流程與自動化電子流程。')
    
    # Cloudflare 部署
    doc.add_heading('4. Cloudflare 雲端部署', level=1)
    doc.add_paragraph('系統現已支援 Cloudflare D1 + Pages 無伺服器雙軌架構。請點擊「一鍵部署至Cloudflare.bat」，依照畫面指示輸入專案名稱，系統將為您自動建立資料庫並上線發布。')
    
    # 存檔
    deliverables_dir = 'deliverables'
    os.makedirs(deliverables_dir, exist_ok=True)
    filename = os.path.join(deliverables_dir, 'AI教育訓練平台_操作手冊.docx')
    doc.save(filename)
    print(f"手冊生成成功：{filename}")

if __name__ == "__main__":
    generate_manual()
