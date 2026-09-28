path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Tabs title
text = text.replace("🧪 品名等級設定", "📦 產品總表 (品名/預設等級/免送樣)")

# 2. Update Table HTML
old_table = """    <!-- 品名等級設定分頁 -->
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
    </div>"""

new_table = """    <!-- 品名等級設定分頁 -->
    <div id="tab-grades" class="tab-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0;">產品總表 (品名/預設等級/免送樣)</h2>
        <div>
          <button onclick="addGradeRow()" style="background: #3b82f6;">+ 新增產品</button>
          <button onclick="saveGrades()" style="background: #10b981;">儲存產品總表</button>
        </div>
      </div>
      
      <table id="gradesTable">
        <thead>
          <tr>
            <th>品名 (Product)</th>
            <th style="width: 200px;">預設等級 (Grade)</th>
            <th style="width: 100px; text-align: center;">自動免送樣</th>
            <th style="width: 80px; text-align: center;">操作</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>"""
text = text.replace(old_table, new_table)


# 3. Update loadConfig
import re
load_match = re.search(r'async function loadConfig\(\) \{.*?\n    \}', text, re.DOTALL)
new_load = """async function loadConfig() {
      try {
        const res = await fetch(API + '?action=getConfig', { cache: 'no-store' });
        const data = await res.json();
        const t = document.querySelector('#configTable tbody');
        t.innerHTML = '';
        
        // Defaults
        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        if (data['OPTIONS_JUDGE_RESULTS'] === undefined) data['OPTIONS_JUDGE_RESULTS'] = 'PASS:合格放行, FAIL:不合格退回';
        if (data['T100_IGNORE_PRODUCTS'] === undefined) data['T100_IGNORE_PRODUCTS'] = 'IPAHQ';
        if (data['OPTIONS_PRODUCTS'] === undefined) data['OPTIONS_PRODUCTS'] = 'IPA,IPAUPS,IPAHQ,CPNE3(T),CPNE4,CPN-P1R,EBR,EBR-P1R,NBAC,NBAC-P1R,CPN,EG,NMP,GAA,ACT,PM,PMA98,heavy-R,DPM,DPM-B1,SEP73,Anone,GBL,PG,EBRR';
        if (data['OPTIONS_GRADES'] === undefined) data['OPTIONS_GRADES'] = '工業級, UPS, IF, 電子級, 回收液';

        window.CURRENT_GRADE_OPTIONS = data['OPTIONS_GRADES'].split(',').map(s=>s.trim()).filter(Boolean);
        
        renderGradesTable(data);

        for(const k in data) {
          if (['OPTIONS_PRODUCT_GRADES_MAP', 'OPTIONS_PRODUCTS', 'T100_IGNORE_PRODUCTS'].includes(k)) continue;
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${String(data[k] || '').replace(/"/g, '&quot;')}"></td></tr>`;
        }
      } catch (err) { console.error(err); }
    }"""
text = text.replace(load_match.group(0), new_load)


# 4. Remove the unused functions that I accidentally added in 2d9476f (addTableRow, renderSingleColumnTable, saveProductsList, saveIgnoreList)
text = re.sub(r'function addTableRow\(.*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'function renderSingleColumnTable\(.*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'async function saveProductsList\(\).*?\n    \}', '', text, flags=re.DOTALL)
text = re.sub(r'async function saveIgnoreList\(\).*?\n    \}', '', text, flags=re.DOTALL)


# 5. Update renderGradesTable, addGradeRow, saveGrades
js_match = re.search(r'function renderGradesTable.*?async function saveGrades\(\) \{.*?\n    \}', text, re.DOTALL)
new_js = """function renderGradesTable(data) {
      const tbody = document.querySelector('#gradesTable tbody');
      tbody.innerHTML = '';
      const prodsStr = data['OPTIONS_PRODUCTS'] || '';
      const gradesMapStr = data['OPTIONS_PRODUCT_GRADES_MAP'] || '';
      const ignoreStr = data['T100_IGNORE_PRODUCTS'] || '';
      
      const allProds = prodsStr.split(',').map(s => s.trim()).filter(Boolean);
      const ignores = ignoreStr.split(',').map(s => s.trim()).filter(Boolean);
      const gradesMap = {};
      gradesMapStr.split(',').map(s => s.trim()).filter(Boolean).forEach(p => {
        const parts = p.split(':');
        if(parts.length >= 2) gradesMap[parts[0].trim()] = parts[1].trim();
      });

      // Ensure keys that have a grade or are ignored are also in the allProds list
      Object.keys(gradesMap).forEach(k => { if(!allProds.includes(k)) allProds.push(k); });
      ignores.forEach(k => { if(!allProds.includes(k)) allProds.push(k); });

      allProds.forEach(prod => {
        addGradeRow(prod, gradesMap[prod] || '', ignores.includes(prod));
      });
    }

    function addGradeRow(prod = '', grade = '', isIgnored = false) {
      const tbody = document.querySelector('#gradesTable tbody');
      const tr = document.createElement('tr');
      const gOpts = (window.CURRENT_GRADE_OPTIONS || ['工業級', 'UPS', 'IF', '電子級', '回收液']).map(g => `<option value="${g}" ${g===grade?'selected':''}>${g}</option>`).join('');
      
      tr.innerHTML = `
        <td><input type="text" class="g-prod" value="${prod.replace(/"/g, '&quot;')}" placeholder="例如: IPAHQ"></td>
        <td>
          <select class="g-grade" style="width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
            <option value="">(無預設)</option>
            ${gOpts}
          </select>
        </td>
        <td style="text-align: center;"><input type="checkbox" class="g-ignore" ${isIgnored ? 'checked' : ''} style="transform: scale(1.5); cursor: pointer;"></td>
        <td style="text-align: center;"><button style="background: #ef4444; padding: 5px 10px;" onclick="this.closest('tr').remove()">刪除</button></td>
      `;
      tbody.appendChild(tr);
    }

    async function saveGrades() {
      const rows = document.querySelectorAll('#gradesTable tbody tr');
      const products = [];
      const gradesMap = [];
      const ignores = [];
      
      rows.forEach(tr => {
        const p = tr.querySelector('.g-prod').value.trim();
        const g = tr.querySelector('.g-grade').value.trim();
        const ignore = tr.querySelector('.g-ignore').checked;
        if (p) {
          products.push(p);
          if (g) gradesMap.push(`${p}:${g}`);
          if (ignore) ignores.push(p);
        }
      });
      
      try {
        await fetch(API, { 
          method: 'POST', 
          headers: {'Content-Type':'application/json'}, 
          body: JSON.stringify({ action: 'updateConfig', configs: { 
            'OPTIONS_PRODUCTS': products.join(','),
            'OPTIONS_PRODUCT_GRADES_MAP': gradesMap.join(','),
            'T100_IGNORE_PRODUCTS': ignores.join(',')
          } }) 
        });
        alert('產品總表已成功儲存！');
        loadConfig();
      } catch (err) {
        alert('儲存失敗');
      }
    }"""
text = text.replace(js_match.group(0), new_js)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
