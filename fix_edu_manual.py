# Rewrite the README for 教育訓練教材 cleanly
import os
readme_path = r'C:\GOOGLE ANGET\教育訓練教材\README.md'
content = '''# AI 教育訓練平台 (AI-Assisted Training Platform)

## 🌟 專案簡介
這是一個結合 AI 輔助的教育訓練平台。使用者可以在網頁上傳教育訓練教材，並透過內建的 AI 助理進行摘要、AI 語音朗讀與測驗生成，大幅提升學習效率與自主學習力。

## ✨ 核心功能
*   **教材整合**：支援 Markdown/PDF 格式教材匯入。
*   **AI 助理**：結合 Gemini API，支援上下文記憶與教材問答 (RAG)。
*   **QC 系統與提案改善**：內建 QC 系統提案改善書與人工流程電子化管理。
*   **PWA 雙軌架構與自動化部署**：全面升級 PWA 離線支援與 App 安裝模式，並支援 Cloudflare D1 雲端資料庫一鍵部署！

## 📂 檔案結構
`
教育訓練教材/
├── README.md               # 本專案說明
├── SKILL.md                # AI 代理操作與環境引導
├── setup_env.ps1           # 一鍵安裝環境腳本
├── build_manual_doc.py     # 操作手冊自動生成腳本
├── deliverables/           # 產出物 (操作手冊、QC 提案改善書)
├── 1_Web_網頁版/            # FastAPI 網頁服務核心
└── 2_PWA_App版/             # PWA 離線 App 支援與前端介面
`

## 🚀 快速啟動與環境建置
1. 確認已安裝 Node.js 與 Python 3.10+。
2. 執行 ./setup_env.ps1 進行初始化與套件安裝。
3. **啟動後端**：cd backend && uvicorn main:app --reload --port 8000
4. **啟動前端/PWA**：雙擊 啟動PWA本機測試.bat 或進入 frontend 執行 
pm run dev。
5. 開啟終端機顯示的網址即可開始使用。

## 💡 最新更新 (PWA 與雲端部署)
* **PWA 安裝**：網頁頂部現在會出現「安裝為應用程式」提示，支援手機與電腦版獨立 App 模式。
* **Cloudflare 一鍵上線**：可執行包內的自動部署腳本，無伺服器即可直接上線。
'''
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Rewrote README.md")

# Rewrite the build_manual_doc.py to generate a beautiful manual
build_py_path = r'C:\GOOGLE ANGET\教育訓練教材\build_manual_doc.py'
build_py_content = '''
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
'''
with open(build_py_path, 'w', encoding='utf-8') as f:
    f.write(build_py_content)
print("Rewrote build_manual_doc.py")
