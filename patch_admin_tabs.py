path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add Tabs to UI
old_tabs = """      <div class="tabs">
        <div class="tab" onclick="switchTab('accounts')">👥 帳號管理</div>
        <div class="tab active" onclick="switchTab('config')">📝 系統參數設定</div>
        <div class="tab" onclick="switchTab('grades')">🧪 品名等級設定</div>
      </div>"""
new_tabs = """      <div class="tabs">
        <div class="tab" onclick="switchTab('accounts')">👥 帳號管理</div>
        <div class="tab active" onclick="switchTab('config')">📝 系統參數設定</div>
        <div class="tab" onclick="switchTab('products')">📦 品名清單設定</div>
        <div class="tab" onclick="switchTab('grades')">🧪 品名等級設定</div>
        <div class="tab" onclick="switchTab('ignore')">🚫 免送樣產品設定</div>
      </div>"""
text = text.replace(old_tabs, new_tabs)

# 2. Add Tab Contents
old_grades_tab = """      <!-- 品名等級設定 -->
      <div id="tab-grades" class="tab-content" style="display:none;">"""
new_tab_contents = """      <!-- 品名清單設定 -->
      <div id="tab-products" class="tab-content" style="display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
          <h2 style="margin:0;">下拉選單品名清單 (OPTIONS_PRODUCTS)</h2>
          <div>
            <button class="btn-blue" onclick="addTableRow('productsTable', ['', ''])">+ 新增品名</button>
            <button class="btn-green" onclick="saveProductsList()">儲存品名清單</button>
          </div>
        </div>
        <table id="productsTable" class="admin-table">
          <thead>
            <tr>
              <th>品名 (Product)</th>
              <th style="width: 100px; text-align: center;">操作</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>

      <!-- 免送樣產品設定 -->
      <div id="tab-ignore" class="tab-content" style="display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
          <h2 style="margin:0;">自動免送樣產品清單 (T100_IGNORE_PRODUCTS)</h2>
          <div>
            <button class="btn-blue" onclick="addTableRow('ignoreTable', ['', ''])">+ 新增免送樣產品</button>
            <button class="btn-green" onclick="saveIgnoreList()">儲存免送樣清單</button>
          </div>
        </div>
        <table id="ignoreTable" class="admin-table">
          <thead>
            <tr>
              <th>免送樣品名 (Product)</th>
              <th style="width: 100px; text-align: center;">操作</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>

      <!-- 品名等級設定 -->
      <div id="tab-grades" class="tab-content" style="display:none;">"""
text = text.replace(old_grades_tab, new_tab_contents)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
