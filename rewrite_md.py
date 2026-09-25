import re

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\SOP操作說明書.md'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace Gemini version
text = re.sub(r'Gemini 3\.5 Flash', 'Gemini 3.8 Flash (最新極速版) 及其容錯梯隊', text)

# Replace image section
text = re.sub(
    r'> 📝 預設情況下，若您沒有自己準備圖片，系統會：.*?自動去呼叫免版稅圖片庫（LoremFlickr）來尋找相關的圖片。', 
    '> 📝 **自動 AI 生圖功能**：系統已內建 Pollinations.ai 引擎，只要您在「圖片關鍵字」輸入英文（如 actory worker helmet），系統就會全自動為您「即時生成」一張專屬 AI 圖片！', 
    text, 
    flags=re.DOTALL
)

# Add Scenario D
scenarioD = '''
### 方案 D：Cloudflare 雙軌架構 (一鍵自動部署上雲端) 🌟 最新推薦
當您解壓縮教材包後，會看到 一鍵自動部署上雲端.bat：
1. 雙擊執行 一鍵自動部署上雲端.bat。
2. 系統會詢問「請輸入要建立的專案英文名稱」。
3. 接下來系統會**全自動執行**：創建 D1 雲端資料庫、自動擷取並寫入 database_id、將題庫 schema.sql 結構寫入雲端，並將整個網站打包發布到 Cloudflare Pages！
4. 完成後，您將獲得一個永久的公開專屬網址，員工考題紀錄也會自動寫入 Cloudflare D1 資料庫中，無須管理伺服器。
'''

if '方案 D' not in text:
    text = text.replace('---\n\nSOP 操作說明書閱讀完畢', scenarioD + '\n---\n\nSOP 操作說明書閱讀完畢')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Rewrote MD!")
