import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add Tab button
tab_btn_old = """      <button class="tab-btn" onclick="switchTab('tab-settings')">📝 系統參數設定</button>"""
tab_btn_new = """      <button class="tab-btn" onclick="switchTab('tab-settings')">📝 系統參數設定</button>
      <button class="tab-btn" onclick="switchTab('tab-grades')">🧪 品名等級設定</button>"""
text = text.replace(tab_btn_old, tab_btn_new)

# 2. Add Tab content
tab_content = """    <!-- 品名等級設定分頁 -->
    <div id="tab-grades" class="tab-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0;">品名與預設等級對應</h2>
        <div>
          <button onclick="addGradeRow()" style="background: #3b82f6;">+ 新增品名</button>
          <button onclick="saveGrades()" style="background: #10b981;">儲存對應表</button>
        </div>
      </div>
      
      <table id="gradesTable">
        <thead>
          <tr>
            <th>品名 (Product)</th>
            <th>預設等級 (Grade)</th>
            <th style="width: 80px; text-align: center;">操作</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

  </div>"""
text = text.replace("  </div>", tab_content, 1)

# 3. Add script logic
script_logic = """
    function renderGradesTable(mapStr) {
      const tbody = document.querySelector('#gradesTable tbody');
      tbody.innerHTML = '';
      if (!mapStr) return;
      const pairs = mapStr.split(',').map(s => s.trim()).filter(Boolean);
      pairs.forEach(p => {
        const parts = p.split(':');
        if(parts.length >= 2) addGradeRow(parts[0].trim(), parts[1].trim());
      });
    }

    function addGradeRow(prod = '', grade = '') {
      const tbody = document.querySelector('#gradesTable tbody');
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="text" class="g-prod" value="${prod.replace(/"/g, '&quot;')}" placeholder="例如: EBR-P1R"></td>
        <td><input type="text" class="g-grade" value="${grade.replace(/"/g, '&quot;')}" placeholder="例如: 電子級"></td>
        <td style="text-align: center;"><button style="background: #ef4444; padding: 5px 10px;" onclick="this.closest('tr').remove()">刪除</button></td>
      `;
      tbody.appendChild(tr);
    }

    async function saveGrades() {
      const rows = document.querySelectorAll('#gradesTable tbody tr');
      const pairs = [];
      rows.forEach(tr => {
        const p = tr.querySelector('.g-prod').value.trim();
        const g = tr.querySelector('.g-grade').value.trim();
        if (p && g) pairs.push(`${p}:${g}`);
      });
      const finalStr = pairs.join(', ');
      
      try {
        await fetch(API, { 
          method: 'POST', 
          headers: {'Content-Type':'application/json'}, 
          body: JSON.stringify({ action: 'updateConfig', configs: { 'OPTIONS_PRODUCT_GRADES_MAP': finalStr } }) 
        });
        alert('品名等級對應表已成功儲存！');
        loadConfig();
      } catch (err) {
        alert('儲存失敗：' + err);
      }
    }
"""
text = text.replace("    async function login()", script_logic + "\n    async function login()")

# 4. Modify loadConfig to handle OPTIONS_PRODUCT_GRADES_MAP
old_load = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        
        for(const k in data) {
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${data[k].replace(/"/g, '&quot;')}"></td></tr>`;
        }"""

new_load = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        
        renderGradesTable(data['OPTIONS_PRODUCT_GRADES_MAP']);

        for(const k in data) {
          if (k === 'OPTIONS_PRODUCT_GRADES_MAP') continue; // Hide it from settings tab
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${data[k].replace(/"/g, '&quot;')}"></td></tr>`;
        }"""

text = text.replace(old_load, new_load)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
