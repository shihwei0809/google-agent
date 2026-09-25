import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

scenarioD = '''
---

## 🌟 方案 D：Cloudflare 雙軌架構 (一鍵自動部署上雲端)
當您解壓縮教材包後，會看到 一鍵自動部署上雲端.bat：
1. 雙擊執行 一鍵自動部署上雲端.bat。
2. 系統會詢問「請輸入要建立的專案英文名稱」。
3. 接下來系統會**全自動執行**：創建 D1 雲端資料庫、自動擷取並寫入 database_id、將題庫 schema.sql 結構寫入雲端，並將整個網站打包發布到 Cloudflare Pages！
4. 完成後，您將獲得一個永久的公開專屬網址，員工考題紀錄也會自動寫入 Cloudflare D1 資料庫中，無須管理伺服器。
'''

# Find the end of Scenario C (Google Sheets) inside readmeText
if 'Cloudflare 雙軌架構' not in html:
    html = html.replace('dmin888）。\n   - \u5c07\u525b\u525b\u8907\u88fd\u7684 URL \u8cbc\u5165\u300cGoogle Apps Script API URL\u300d\u6b04\u4f4d\u4e26\u5b58\u6a94\u5373\u53ef\u3002\n\n---\n\n\u795d\u60a8\u6559\u80b2\u8a13\u7df4\u9806\u5229\uff01\n;', 'dmin888）。\n   - \u5c07\u525b\u525b\u8907\u88fd\u7684 URL \u8cbc\u5165\u300cGoogle Apps Script API URL\u300d\u6b04\u4f4d\u4e26\u5b58\u6a94\u5373\u53ef\u3002\n' + scenarioD + '\n---\n\n\u795d\u60a8\u6559\u80b2\u8a13\u7df4\u9806\u5229\uff01\n;')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated index.html readmeText!")
