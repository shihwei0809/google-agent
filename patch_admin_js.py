path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Modify loadConfig to render the new tables
old_load = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        if (data['OPTIONS_JUDGE_RESULTS'] === undefined) data['OPTIONS_JUDGE_RESULTS'] = 'PASS:合格放行, FAIL:不合格退回';
        if (data['T100_IGNORE_PRODUCTS'] === undefined) data['T100_IGNORE_PRODUCTS'] = 'IPAHQ';
        
        renderGradesTable(data['OPTIONS_PRODUCT_GRADES_MAP']);

        for(const k in data) {
          if (k === 'OPTIONS_PRODUCT_GRADES_MAP') continue; // Hide it from settings tab
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${String(data[k] || '').replace(/"/g, '&quot;')}"></td></tr>`;
        }"""
new_load = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        if (data['OPTIONS_JUDGE_RESULTS'] === undefined) data['OPTIONS_JUDGE_RESULTS'] = 'PASS:合格放行, FAIL:不合格退回';
        if (data['T100_IGNORE_PRODUCTS'] === undefined) data['T100_IGNORE_PRODUCTS'] = 'IPAHQ';
        if (data['OPTIONS_PRODUCTS'] === undefined) data['OPTIONS_PRODUCTS'] = 'IPA,IPAUPS,IPAHQ,CPNE3(T),CPNE4,CPN-P1R,EBR,EBR-P1R,NBAC,NBAC-P1R,CPN,EG,NMP,GAA,ACT,PM,PMA98,heavy-R,DPM,DPM-B1,SEP73,Anone,GBL,PG,EBRR';
        
        renderGradesTable(data['OPTIONS_PRODUCT_GRADES_MAP']);
        renderSingleColumnTable('productsTable', data['OPTIONS_PRODUCTS']);
        renderSingleColumnTable('ignoreTable', data['T100_IGNORE_PRODUCTS']);

        for(const k in data) {
          if (['OPTIONS_PRODUCT_GRADES_MAP', 'OPTIONS_PRODUCTS', 'T100_IGNORE_PRODUCTS'].includes(k)) continue; // Hide from settings tab
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${String(data[k] || '').replace(/"/g, '&quot;')}"></td></tr>`;
        }"""
text = text.replace(old_load, new_load)

# Add render and save functions for single column tables
script_funcs = """    function addTableRow(tableId, values) {
      const tbody = document.querySelector(`#${tableId} tbody`);
      const tr = document.createElement('tr');
      let html = '';
      values.forEach(v => {
        html += `<td><input type="text" value="${v}"></td>`;
      });
      html += `<td style="text-align: center;"><button class="btn-red" onclick="this.closest('tr').remove()">刪除</button></td>`;
      tr.innerHTML = html;
      tbody.appendChild(tr);
    }

    function renderSingleColumnTable(tableId, dataStr) {
      const tbody = document.querySelector(`#${tableId} tbody`);
      tbody.innerHTML = '';
      if(!dataStr) return;
      const items = dataStr.split(',').map(x => x.trim()).filter(Boolean);
      items.forEach(item => {
        addTableRow(tableId, [item]);
      });
    }

    async function saveProductsList() {
      const rows = document.querySelectorAll('#productsTable tbody tr');
      const list = [];
      rows.forEach(tr => {
        const val = tr.querySelector('input').value.trim();
        if(val) list.push(val);
      });
      await fetch(API, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action: 'updateConfig', configs: { OPTIONS_PRODUCTS: list.join(',') } }) });
      alert('品名清單已儲存！');
    }

    async function saveIgnoreList() {
      const rows = document.querySelectorAll('#ignoreTable tbody tr');
      const list = [];
      rows.forEach(tr => {
        const val = tr.querySelector('input').value.trim();
        if(val) list.push(val);
      });
      await fetch(API, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action: 'updateConfig', configs: { T100_IGNORE_PRODUCTS: list.join(',') } }) });
      alert('免送樣清單已儲存！');
    }"""
text = text.replace("    function renderGradesTable", script_funcs + "\n\n    function renderGradesTable")

# Update tab switching logic
old_tabs_arr = "const tabs = ['accounts', 'config', 'grades'];"
new_tabs_arr = "const tabs = ['accounts', 'config', 'products', 'grades', 'ignore'];"
text = text.replace(old_tabs_arr, new_tabs_arr)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
