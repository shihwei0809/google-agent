path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
import re

# Remove unused tabs
tabs_match = re.search(r'<div class="tabs">.*?</div>', text, re.DOTALL)
if tabs_match:
    old_tabs = tabs_match.group(0)
    new_tabs = """<div class="tabs">
      <button class="tab-btn active" onclick="switchTab('tab-accounts')">👥 帳號管理</button>
      <button class="tab-btn" onclick="switchTab('tab-settings')">📝 系統參數設定</button>
      <button class="tab-btn" onclick="switchTab('tab-grades')">🧪 品名與等級設定 (產品總表)</button>
    </div>"""
    text = text.replace(old_tabs, new_tabs)

# Remove unused HTML blocks
text = re.sub(r'<!-- 品名清單設定 -->\s*<div id="tab-products".*?</table>\s*</div>', '', text, flags=re.DOTALL)
text = re.sub(r'<!-- 免送樣產品設定 -->\s*<div id="tab-ignore".*?</table>\s*</div>', '', text, flags=re.DOTALL)

# Remove unused JS functions
text = re.sub(r'function addTableRow\(.*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'function renderSingleColumnTable\(.*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'async function saveProductsList\(.*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'async function saveIgnoreList\(.*?\n    \}', '', text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
